import glob
import os
from datetime import datetime

import numpy as np
import requests
from PIL import Image

from utils import cfg
from utils.log import log


class GitHub:
    def __init__(self, path: str) -> None:
        self.user: str = os.getenv("GIT_USER")
        self.token: str = os.getenv("GIT_TOKEN")

        self.url_repos: str = f"https://api.github.com/users/{self.user}/repos"
        self.auth: dict[str, str] = {"Authorization": f"token {self.token}"}

        self.last: str = ""
        self.base_mat = None
        self.path: str = path
        self.point: list = []
        self.commits: list = []
        self.mat: np.array = None
        self.data_repos: list = []

        self.tamX: int = cfg.config["screen"]["x_max"]
        self.tamY: int = cfg.config["screen"]["y_max"]

        self.date_check()

    def date_check(self):
        self.today: datetime = datetime.today()
        self.today_str: str = self.today.strftime("%Y-%m-%d")
        self.filename: str = self.path + f"github_wallpaper_{self.today_str}.png"

        return not os.path.exists(self.filename)

    def pipeline(self):
        log.info(f"Gen new wallpaper for {self.today_str}...")
        try:
            self._delete_old_wallpapers()

            self._get_repo()
            self._get_commits()
            self._create_WeekMat()
            self._create_Wallpaper()
            self._save()

            log.info(f"Wallpaper saved: {self.filename}")

        except requests.exceptions.RequestException as e:
            log.warning(f"Connection error to fetch GitHub API: {e}")
        except Exception as e:
            log.error(f"Error in fetch gitHub API: {e}")

    def _delete_old_wallpapers(self) -> None:
        pattern: str = self.path + "github_wallpaper_*.png"
        old_files = glob.glob(pattern)

        for file_path in old_files:
            if file_path != self.filename:
                os.remove(file_path)

    def _get_repo(self) -> None:
        response_repos: requests = requests.get(
            url=self.url_repos, headers=self.auth, timeout=5
        )
        response_repos.raise_for_status()
        self.data_repos = response_repos.json()

    def _days(self, data) -> int:
        data_format = datetime(data[0], data[1], data[2])
        return abs((self.today - data_format).days)

    def _get_commits(self) -> None:
        for repo in self.data_repos:
            url_commits = (
                f"https://api.github.com/repos/{self.user}/{repo['name']}/commits"
            )
            response_commits = requests.get(url_commits, headers=self.auth, timeout=5)
            if response_commits.status_code == 200:
                dados_commits = response_commits.json()
                for commit in dados_commits:
                    date = commit["commit"]["author"]["date"]
                    date = list(date.split("T"))
                    date = list(map(int, list(date[0].split("-"))))
                    self.commits.append(date)

        self.commits = sorted(self.commits, key=self._days, reverse=False)

    def _create_Wallpaper(self) -> None:
        base = np.zeros((self.tamY, self.tamX, 3), dtype=int)

        x, y = 0, 0
        for b in range(7):
            for a in range(self.tamY):
                color = self.mat[b][a] * 85

                if color == 0:
                    self.mat[b][a] = False
                else:
                    self.mat[b][a] = True
                    self.point.append([b * 2, a * 2])

                base[y][x][1] = color
                base[y][x + 1][1] = color
                base[y + 1][x][1] = color
                base[y + 1][x + 1][1] = color
                x += 2
            y += 2
            x = 0

        self.base_mat = base

    def _create_WeekMat(self) -> None:
        self.mat = np.zeros((7, self.tamY), dtype=int)
        for date in self.commits:
            year, month, day = date
            formated_data = datetime(year, month, day)
            delta = self.today - formated_data
            week = delta.days // 7
            week_day = formated_data.weekday()
            if 0 <= week < self.tamY:
                value = min(self.commits.count(date), 3)
                self.mat[week_day][self.tamY - 1 - week] = value

    def _save(self) -> None:
        if self.base_mat is None:
            log.error("Error: base_mat not gen corrected. Nothing to save.")
            return

        matrix_redefinition = self.base_mat.astype(np.uint8)
        image = Image.fromarray(matrix_redefinition, "RGB")

        image.save(self.filename)
        log.info("New github commit image saved")

    def load(self) -> np.array:
        try:
            imagem = Image.open(self.filename)
            self.base_mat = np.array(imagem)
        except FileNotFoundError:
            log.error(f"Error: file {self.filename} not found.")
        except Exception as e:
            log.error(f"Error in {self.filename} git fetch: {e}")

    def get_last_repo_updated(self) -> dict | None:
        query_params = {"sort": "pushed", "direction": "desc", "per_page": 1}

        try:
            response = requests.get(
                self.url_repos, headers=self.auth, params=query_params, timeout=5
            )
            response.raise_for_status()

            data = response.json()

            if data:
                ultimo_repo = data[0]
                nome_repo = ultimo_repo["name"]
                ultimo_push = ultimo_repo["pushed_at"]
                log.info(f"last Repo: {nome_repo} (last push: {ultimo_push})")
                self.last = nome_repo
            else:
                log.warning("Repo not found")

        except requests.exceptions.RequestException as e:
            log.warning(f"Connection Error in last_repo_updated: {e}")
        except Exception as e:
            log.error(f"Error in last_repo_updated: {e}")
