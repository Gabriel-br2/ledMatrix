import os

import numpy as np

from app.__base__ import baseApp
from utils import cfg
from utils.log import log
from utils.registry import register_object


@register_object("app", "spotify")
class app(baseApp):
    def __init__(self, app_id: int = 0) -> None:
        super().__init__(app_id=app_id, name="spotify")
        self.fps_app: float = 0.01
        self.total_frames: int = 1

        path: str = cfg.config["main"]["path"]

    def main_loop_app(self, base: np.array) -> None:
        base[0, 0] = (255, 255, 255)
        return base

    def _button_left(self) -> None:
        pass

    def _button_right(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def _button_short_click(self) -> None:
        pass

    def _button_long_click(self) -> None:
        pass
