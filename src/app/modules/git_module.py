"""
GitHub API Connector — Commit Heatmap Generator.
DEV     : Gabriel Rocha de Souza
PROJECT : ledMatrix
"""

import functools
import glob
import os
import time
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Callable
from typing import cast
from typing import TypeVar

import numpy as np
import requests
from PIL import Image

from utils import cfg
from utils.log import log


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

type CommitDate = list[int]  # [year, month, day]

F = TypeVar("F", bound=Callable[..., Any])


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_API_BASE: str = "https://api.github.com"
_TIMEOUT: int = 5
_MAX_LEVEL: int = 3  # commit density cap (maps to 4 shades: 0–3)
_SHADE_STEP: int = 85  # 85 * 3 = 255


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


def _retry_on_network_error(
    max_attempts: int = 3,
    delay: float = 2.0,
) -> Callable[[F], F]:
    """Re-attempt an API call up to *max_attempts* times on network failure."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    if attempt == max_attempts:
                        log.error(
                            f"[RETRY] '{func.__name__}' failed after "
                            f"{max_attempts} attempts: {e}"
                        )
                        raise
                    log.warning(
                        f"[RETRY] '{func.__name__}' attempt {attempt}/{max_attempts} "
                        f"failed ({e}). Retrying in {delay}s…"
                    )
                    time.sleep(delay)

        return cast(F, wrapper)

    return decorator


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class _GitHubConfig:
    """Credentials and derived URLs loaded once at startup."""

    user: str
    token: str

    @property
    def auth_header(self) -> dict[str, str]:
        return {"Authorization": f"token {self.token}"}

    @property
    def repos_url(self) -> str:
        return f"{_API_BASE}/users/{self.user}/repos"

    def commits_url(self, repo_name: str) -> str:
        return f"{_API_BASE}/repos/{self.user}/{repo_name}/commits"

    @classmethod
    def from_env(cls) -> "_GitHubConfig":
        user = os.getenv("GIT_USER", "")
        token = os.getenv("GIT_TOKEN", "")

        if not user or not token:
            log.warning("GIT_USER or GIT_TOKEN not set in environment.")

        return cls(user=user, token=token)


@dataclass
class _WallpaperState:
    """Mutable state produced during a single pipeline run."""

    commits: list[CommitDate] = field(default_factory=list)
    week_mat: np.ndarray | None = None  # shape (7, tamY) — density grid
    base_mat: np.ndarray | None = None  # shape (tamY, tamX, 3) — RGB image
    active_points: list[list[int]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------


class GitHub:
    """
    Fetches commit history from the GitHub API and renders it as a
    pixel-art heatmap saved to disk, mirroring the GitHub contribution graph.

    Workflow (call :meth:`pipeline` to execute it all at once)
    ----------------------------------------------------------
    1. Delete stale cached wallpapers.
    2. Fetch all repos for the authenticated user.
    3. Fetch commits for each repo and sort by recency.
    4. Build a ``(7, tamY)`` density matrix (week-day × week-offset).
    5. Render a ``(tamY, tamX, 3)`` RGB image and save it as a PNG.

    Parameters
    ----------
    path:
        Directory where cached wallpaper PNGs are stored.
    """

    def __init__(self, path: str) -> None:
        self._cfg: _GitHubConfig = _GitHubConfig.from_env()
        self._state: _WallpaperState = _WallpaperState()

        self.path: Path = Path(path)
        self.last: str = ""

        self.x_max: int = cfg.config["screen"]["x_max"]
        self.y_max: int = cfg.config["screen"]["y_max"]

        self._today: datetime = datetime.today()
        self._today_str: str = self._today.strftime("%Y-%m-%d")
        self._filename: Path = self.path / f"github_wallpaper_{self._today_str}.png"

        # Expose the rendered matrix for the app layer.
        self.base_mat: np.ndarray | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def wallpaper_exists(self) -> bool:
        """True when today's cached wallpaper is already on disk."""
        return self._filename.exists()

    def needs_refresh(self) -> bool:
        """
        Return True when today's wallpaper is missing or stale.
        Re-evaluates the date so midnight rollovers are detected correctly
        without needing to reinstantiate the class.
        """
        now = datetime.today()

        if now.date() != self._today.date():
            self._today = now
            self._today_str = now.strftime("%Y-%m-%d")
            self._filename = self.path / f"github_wallpaper_{self._today_str}.png"

        return not self._filename.exists()

    def pipeline(self) -> None:
        """Fetch data and generate today's wallpaper from scratch."""
        log.info(f"Generating new wallpaper for {self._today_str}…")

        try:
            self._delete_old_wallpapers()
            self._fetch_repos()
            self._fetch_commits()
            self._build_week_matrix()
            self._render_wallpaper()
            self._save()
            log.info(f"Wallpaper saved: {self._filename}")

        except requests.exceptions.RequestException as e:
            log.warning(f"Network error while fetching GitHub API: {e}")
        except Exception as e:
            log.error(f"Unexpected error in GitHub pipeline: {e}")

    def load(self) -> None:
        """Load today's cached wallpaper from disk into :attr:`base_mat`."""
        try:
            self.base_mat = np.array(Image.open(self._filename))
        except FileNotFoundError:
            log.error(f"Wallpaper file not found: {self._filename}")
        except Exception as e:
            log.error(f"Error loading wallpaper '{self._filename}': {e}")

    def get_last_repo_updated(self) -> None:
        """Fetch the most recently pushed repo and store its name in :attr:`last`."""
        params = {"sort": "pushed", "direction": "desc", "per_page": 1}

        try:
            response = requests.get(
                self._cfg.repos_url,
                headers=self._cfg.auth_header,
                params=params,
                timeout=_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            if data:
                repo = data[0]
                self.last = repo["name"]
                log.info(f"Last repo: {self.last} (pushed at: {repo['pushed_at']})")
            else:
                log.warning("No repos found for this user.")

        except requests.exceptions.RequestException as e:
            log.warning(f"Network error in get_last_repo_updated: {e}")
        except Exception as e:
            log.error(f"Unexpected error in get_last_repo_updated: {e}")

    # ------------------------------------------------------------------
    # Pipeline steps
    # ------------------------------------------------------------------

    def _delete_old_wallpapers(self) -> None:
        pattern = str(self.path / "github_wallpaper_*.png")

        for file_path in glob.glob(pattern):
            if Path(file_path) != self._filename:
                os.remove(file_path)
                log.info(f"Deleted stale wallpaper: {file_path}")

    @_retry_on_network_error(max_attempts=3, delay=2.0)
    def _fetch_repos(self) -> None:
        response = requests.get(
            url=self._cfg.repos_url,
            headers=self._cfg.auth_header,
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        self._state.commits = []  # reset before re-fetch
        self._repos = response.json()

    @_retry_on_network_error(max_attempts=3, delay=2.0)
    def _fetch_commits(self) -> None:
        commits: list[CommitDate] = []

        for repo in self._repos:
            url = self._cfg.commits_url(repo["name"])
            response = requests.get(
                url, headers=self._cfg.auth_header, timeout=_TIMEOUT
            )

            if response.status_code != 200:
                continue

            for commit in response.json():
                raw_date = commit["commit"]["author"]["date"].split("T")[0]
                parts = list(map(int, raw_date.split("-")))
                commits.append(parts)

        # Sort ascending by recency (most recent first).
        self._state.commits = sorted(commits, key=self._days_ago)

    def _build_week_matrix(self) -> None:
        """
        Populate a ``(7, y_max)`` matrix where each cell holds the commit
        density (0–3) for that weekday × week-offset bucket.
        """
        mat = np.zeros((7, self.y_max), dtype=int)

        for date in self._state.commits:
            year, month, day = date
            delta = self.today - datetime(year, month, day)
            week_off = delta.days // 7
            week_day = datetime(year, month, day).weekday()

            if 0 <= week_off < self.y_max:
                count = self._state.commits.count(date)
                mat[week_day][self.y_max - 1 - week_off] = min(count, _MAX_LEVEL)

        self._state.week_mat = mat

    def _render_wallpaper(self) -> None:
        """
        Convert :attr:`_state.week_mat` into an RGB pixel matrix.

        Each commit bucket is rendered as a 2×2 green block whose brightness
        encodes the density level (0 = black, 3 = full green).
        """
        mat = self._state.week_mat
        base = np.zeros((self.y_max, self.x_max, 3), dtype=int)
        points: list[list[int]] = []

        x, y = 0, 0
        for weekday in range(7):
            for week_off in range(self.y_max):
                level = mat[weekday][week_off] if mat is not None else 0
                shade = level * _SHADE_STEP

                if shade > 0:
                    points.append([weekday * 2, week_off * 2])

                # Paint a 2×2 block in the green channel.
                for dy in range(2):
                    for dx in range(2):
                        base[y + dy][x + dx][1] = shade

                x += 2
            y += 2
            x = 0

        self._state.active_points = points
        self._state.base_mat = base
        self.base_mat = base

    def _save(self) -> None:
        if self._state.base_mat is None:
            log.error("Nothing to save: base_mat was never generated.")
            return

        image = Image.fromarray(self._state.base_mat.astype(np.uint8), "RGB")
        image.save(self._filename)
        log.info(f"Wallpaper written to {self._filename}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def today(self) -> datetime:
        return self._today

    def _days_ago(self, date: CommitDate) -> int:
        """Return the number of days between *date* and today (used for sorting)."""
        year, month, day = date
        return abs((self._today - datetime(year, month, day)).days)
