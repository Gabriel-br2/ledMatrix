import os
import threading

import numpy as np

from app.__base__ import baseApp
from app.modules.git_module import GitHub
from app.modules.snake_module import snake
from tools.font import Font
from tools.image_rescale import image
from utils import cfg
from utils.registry import register_object


@register_object("app", "git_app")
class git_app(baseApp):
    def __init__(self, app_id: int = 0) -> None:
        super().__init__(app_id=app_id, name="GIT Hub App")
        self.fetching_info: bool = True
        self.fetching: bool = False
        self.fps_app: float = 0.05
        self.base: np.array = None
        self.map_ready: bool = False

        path: str = cfg.config["main"]["path"]
        self.module: GitHub = GitHub(path=path + f"processed_resource/commits/")
        self.snake: snake = snake((150, 0, 255))
        self.module.load()

        is_outdated = self.module.date_check()
        load_failed = self.module.base_mat is None

        if is_outdated or load_failed:
            self.fetching = True
            self.map_ready = False
            self.base = np.zeros(
                (cfg.config["screen"]["y_max"], cfg.config["screen"]["x_max"], 3)
            )
            thread_load = threading.Thread(target=self.threading_load)
            thread_load.start()
        else:
            self.fetching = False
            self.map_ready = True
            self.base = self.module.base_mat.copy()
            self.snake.convert_matrix(self.base)
            self.snake.choose_target()

        self.title = Font(
            tam=5, text=f"GitHub: {os.getenv("GIT_USER")}", offset=(20, 1)
        )

        self.last_repo = Font(
            tam=5,
            text=f"last push in repo: {self.module.last}",
            offset=(26, 1),
            map_color=[0, 18],
            color=[(255, 255, 255), (150, 0, 255)],
        )

        self.title.limit(43)
        self.last_repo.limit(43)

        self.total_frames: int = max(self.title.frames, self.last_repo.frames)

        self.title.extern_limit(self.total_frames)
        self.last_repo.extern_limit(self.total_frames)

        thread_info = threading.Thread(target=self.threading_info)
        thread_info.start()

        self.logo = image(img=path + "resource/giticon.png", scale=(16, 16))

    def threading_info(self) -> None:
        self.module.get_last_repo_updated()

        self.last_repo.update_text(text=f"Last push in repo: {self.module.last}")
        self.last_repo.limit(43)

        self.total_frames: int = max(self.title.frames, self.last_repo.frames)
        self.title.extern_limit(self.total_frames)
        self.last_repo.extern_limit(self.total_frames)

        self.fetching_info = False

    def threading_load(self) -> None:
        self.module.pipeline()
        self.module.load()

        if self.module.base_mat is not None:
            self.base = self.module.base_mat.copy()
            self.snake.convert_matrix(self.base)
            self.snake.reset_cycle()
        else:
            self.base = np.zeros(
                (cfg.config["screen"]["y_max"], cfg.config["screen"]["x_max"], 3)
            )
            self.map_ready = False
            self.fetching = False
            return

        self.map_ready = True
        self.fetching = False

    def main_loop_app(self, base: np.array) -> np.array:
        if self.module.date_check() and not self.fetching:
            self.fetching = True
            self.map_ready = False
            thread_load = threading.Thread(target=self.threading_load)
            thread_load.start()
        base[:] = self.base

        if not self.fetching and self.map_ready:
            self.snake.go_for_target()
            base = self.snake.put_head(base=base)

        base = self.title.put(base=base)
        base = self.last_repo.put(base=base)
        base[-self.logo.scaleY - 1 : -1, -self.logo.scaleX - 1 : -1] = self.logo.resized

        self.title += 1
        self.last_repo += 1

        return base

    def reset_snake_state(self) -> None:
        if self.map_ready:
            self.snake.reset_cycle()

        if not self.fetching_info:
            self.fetching_info = True
            thread_info = threading.Thread(target=self.threading_info)
            thread_info.start()

    def on_exit(self) -> None:
        pass

    def _button_short_click(self) -> None:
        self.reset_snake_state()

    def _button_left(self) -> None:
        pass

    def _button_right(self) -> None:
        pass

    def _button_long_click(self) -> None:
        pass
