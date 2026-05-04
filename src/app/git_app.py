"""
GitHub Contribution Heatmap App.
DEV     : Gabriel Rocha de Souza
PROJECT : ledMatrix
"""

import os
import threading
from dataclasses import dataclass
from dataclasses import field

import numpy as np

from app.__base__ import baseApp
from app.modules.git_module import GitHub
from app.modules.snake_module import snake
from tools.font import Font
from tools.image_rescale import ImageRescale
from utils import cfg
from utils.log import log
from utils.registry import register_object


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_FONT_SIZE: int = 5
_TEXT_LIMIT: int = 43
_LOGO_SIZE: int = 16

_TEXT_COLOR_WHITE: tuple = (255, 255, 255)
_TEXT_COLOR_PURPLE: tuple = (150, 0, 255)
_SNAKE_COLOR: tuple = (150, 0, 255)


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class _TextState:
    """Groups the two scrolling Font objects and their shared frame count."""

    title: Font
    last_repo: Font
    total_frames: int = 1

    def sync_frames(self) -> None:
        """Align both fonts to the same total frame count."""
        self.total_frames = max(self.title.frames, self.last_repo.frames)
        self.title.extern_limit(self.total_frames)
        self.last_repo.extern_limit(self.total_frames)

    def advance(self) -> None:
        self.title += 1
        self.last_repo += 1

    def put(self, base: np.ndarray) -> np.ndarray:
        base = self.title.put(base=base)
        base = self.last_repo.put(base=base)
        return base


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


@register_object("app", "git_app")
class GitApp(baseApp):
    """
    Displays the GitHub contribution heatmap with an animated snake overlay.

    Startup sequence
    ----------------
    1. Try to load today's cached wallpaper from disk.
    2. If missing or stale → spawn ``_thread_load`` to fetch from the API.
    3. Spawn ``_thread_info`` immediately to refresh the last-pushed repo label.
    """

    def __init__(self, app_id: int = 0) -> None:
        super().__init__(app_id=app_id, name="GitHub App")

        self.fps_app: float = 0.05

        path: str = cfg.config["main"]["path"]

        # --- Module ---
        self.module: GitHub = GitHub(path=path + "processed_resource/commits/")
        self.module.load()

        # --- State flags ---
        self._fetching: bool = False
        self._fetching_info: bool = False
        self._map_ready: bool = False

        # --- Canvas ---
        _empty = self._empty_canvas()
        self.base: np.ndarray = _empty

        # --- Snake ---
        self.snake: snake = snake(_SNAKE_COLOR)

        # --- Boot: wallpaper ---
        if self.module.needs_refresh() or self.module.base_mat is None:
            log.info("Wallpaper missing or stale — fetching from API.")
            self._start_load_thread()
        else:
            self.base = self.module.base_mat.copy()
            self.snake.convert_matrix(self.base)
            self.snake.choose_target()
            self._map_ready = True

        # --- Text ---
        self._text: _TextState = self._build_text_state()

        # --- Info thread (last repo label) ---
        self._start_info_thread()

        # --- Logo ---
        self.logo: ImageRescale = ImageRescale(
            source=path + "resource/giticon.png",
            scale=(_LOGO_SIZE, _LOGO_SIZE),
        )

        self.total_frames: int = self._text.total_frames

    # ------------------------------------------------------------------
    # baseApp contract
    # ------------------------------------------------------------------

    def main_loop_app(self, base: np.ndarray) -> np.ndarray:
        # Trigger a refresh if the cached wallpaper is now outdated.
        if self.module.needs_refresh() and not self._fetching:
            log.info("Date rollover detected — refreshing wallpaper.")
            self._map_ready = False
            self._start_load_thread()

        base[:] = self.base

        if not self._fetching and self._map_ready:
            self.snake.go_for_target()
            base = self.snake.put_head(base=base)

        base = self._text.put(base)

        sy, sx = self.logo.scaleY, self.logo.scaleX
        base[-sy - 1 : -1, -sx - 1 : -1] = self.logo.resized

        self._text.advance()
        self.total_frames = self._text.total_frames

        return base

    def on_exit(self) -> None:
        pass

    def _button_short_click(self) -> None:
        self._reset_snake_and_info()

    def _button_left(self) -> None:
        pass

    def _button_right(self) -> None:
        pass

    def _button_long_click(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Threads
    # ------------------------------------------------------------------

    def _start_load_thread(self) -> None:
        self._fetching = True
        threading.Thread(target=self._thread_load, daemon=True).start()

    def _start_info_thread(self) -> None:
        self._fetching_info = True
        threading.Thread(target=self._thread_info, daemon=True).start()

    def _thread_load(self) -> None:
        """Background: fetch API → generate wallpaper → reload."""
        self.module.pipeline()
        self.module.load()

        if self.module.base_mat is not None:
            self.base = self.module.base_mat.copy()
            self.snake.convert_matrix(self.base)
            self.snake.reset_cycle()
            self._map_ready = True
        else:
            log.error("Wallpaper generation failed — displaying blank canvas.")
            self.base = self._empty_canvas()
            self._map_ready = False

        self._fetching = False

    def _thread_info(self) -> None:
        """Background: fetch last-pushed repo and update the label."""
        self.module.get_last_repo_updated()

        self._text.last_repo.update_text(f"Last push in repo: {self.module.last}")
        self._text.last_repo.limit(_TEXT_LIMIT)
        self._text.sync_frames()
        self.total_frames = self._text.total_frames

        self._fetching_info = False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _reset_snake_and_info(self) -> None:
        if self._map_ready:
            self.snake.reset_cycle()

        if not self._fetching_info:
            self._start_info_thread()

    def _build_text_state(self) -> _TextState:
        username = os.getenv("GIT_USER", "")

        title = Font(
            size=_FONT_SIZE,
            text=f"GitHub: {username}",
            offset=(20, 1),
        )

        last_repo = Font(
            size=_FONT_SIZE,
            text=f"last push in repo: {self.module.last}",
            offset=(26, 1),
            map_color=[0, 18],
            color=[_TEXT_COLOR_WHITE, _TEXT_COLOR_PURPLE],
        )

        title.limit(_TEXT_LIMIT)
        last_repo.limit(_TEXT_LIMIT)

        state = _TextState(title=title, last_repo=last_repo)
        state.sync_frames()
        return state

    @staticmethod
    def _empty_canvas() -> np.ndarray:
        y = cfg.config["screen"]["y_max"]
        x = cfg.config["screen"]["x_max"]
        return np.zeros((y, x, 3), dtype=np.uint8)
