import os
import threading

import numpy as np

from app.__base__ import baseApp
from app.modules.git_module import GitHub
from registry import register_object
from tools.font import Font
from tools.image_rescale import image
from utils import cfg


@register_object("app", "git_app")
class git_app(baseApp):
    def __init__(self, app_id: int = 0) -> None:
        super().__init__(app_id=app_id, name="GIT Hub App")
        self.total_frames: int = 1
        self.fetching_info: bool = False
        self.fetching: bool = False
        self.fps_app: float = 0.01

        path: str = cfg.config["main"]["path"]
        self.module: GitHub = GitHub(path=path + f"processed_resource/commits/")

        if self.module.date_check():
            self.fetching = True
            thread = threading.Thread(target=self.threading_load, args=(False,))
            thread.start()

        self.module.load()

        self.title = Font(tam=5, text=f"GitHub", offset=(20, 1))
        self.Account = Font(tam=5, text=f"{os.getenv("GIT_USER")}", offset=(26, 1))

        self.logo = image(img=path + "resource/giticon.png", scale=(16, 16))

    def threading_load(self, load: bool) -> None:
        self.module.pipeline()
        if load:
            self.module.load()
        self.fetching = False

    def main_loop_app(self, base: np.array) -> np.array:
        if self.module.date_check() and not self.fetching:
            self.fetching = True
            thread_load = threading.Thread(target=self.threading_load, args=(True,))
            thread_load.start()

        if self.module.base_mat is not None:
            base = self.module.base_mat

        base = self.title.put(base=base)
        base = self.Account.put(base=base)
        base[-self.logo.scaleY - 1 : -1, -self.logo.scaleX - 1 : -1] = self.logo.resized

        return base

    def on_exit(self) -> None:
        pass

    def _button_short_click(self) -> None:
        pass

    def _button_left(self) -> None:
        pass

    def _button_right(self) -> None:
        pass

    def _button_long_click(self) -> None:
        pass
