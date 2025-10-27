import os
from typing import List
from typing import Set

import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL import ImageSequence

from app.__base__ import baseApp
from tools.image_rescale import image as image_tool
from utils import cfg
from utils.registry import register_object


@register_object("app", "gif_app")
class gif_app(baseApp):
    def __init__(self, app_id: int = 0) -> None:
        super().__init__(app_id=app_id, name="GIF Viewer")
        self.current_giff: int = 0
        self.fps_app: float = 0.01

        path: str = cfg.config["main"]["path"]
        diff, gif_path = self.check_processed_gifs(
            dir_base=path + "resource/gifs",
            dir_processed=path + "processed_resource/gifs",
        )

        self.gif_path = gif_path
        self.total_gifs: int = len(gif_path)
        for base, processed in diff.items():
            self.create_gif(base, processed)

        gif_app
        self.current: np.array = self.load(gif_path[self.current_giff])
        self.total_frames: int = len(self.current)

    def check_processed_gifs(self, dir_base: str, dir_processed: str) -> List[str]:
        if not os.path.isdir(dir_base):
            raise FileNotFoundError(f"Gif base directory not found: {dir_base}")
        if not os.path.isdir(dir_processed):
            raise FileNotFoundError(
                f"Gif processed directory not found: {dir_processed}"
            )

        def explore(dir_name: str) -> set[tuple[str]]:
            files_names: Set[str] = set()
            files_paths: Set[str] = set()

            for item_name in os.listdir(dir_name):
                completed_path: str = os.path.join(dir_name, item_name)
                if os.path.isfile(completed_path):
                    files_names.add(item_name)
                    files_paths.add(completed_path)
            return files_names, files_paths

        base_names, base_paths = explore(dir_base)
        processed_names, processed_paths = explore(dir_processed)

        unitary_files: Set[str] = base_names - processed_names
        diff: dict[str] = {
            dir_base + "/" + i: dir_processed + "/" + i for i in unitary_files
        }

        total_paths = list(processed_paths) + list(diff.values())
        total_paths.sort()

        return diff, total_paths

    def load(self, path: str) -> List[np.array]:
        img_gif = Image.open(path)
        frames: List[np.array] = []

        for frame in ImageSequence.Iterator(img_gif):
            frame_rgba = frame.convert("RGB")
            frames.append(np.array(frame_rgba, np.uint8))

        return frames

    def create_gif(self, path_input: str, path_output: str) -> None:
        img_gif = Image.open(path_input)
        frames_pil: List[Image.Image] = []
        frames: List[np.array] = []
        timers: List[int] = []

        for frame in ImageSequence.Iterator(img_gif):
            frame_rgba = frame.convert("RGBA")
            frame_rescaled = image_tool(
                img=frame_rgba,
                scale=(cfg.config["screen"]["y_max"], cfg.config["screen"]["x_max"]),
            )

            frames.append(frame_rescaled.resized)
            frames_pil.append(
                Image.fromarray(frame_rescaled.resized.astype(np.uint8), "RGBA")
            )
            timers.append(frame.info["duration"])

        frames_pil = [
            Image.fromarray(frame.astype(np.uint8), "RGBA") for frame in frames
        ]

        frames_pil[0].save(
            path_output,
            save_all=True,
            append_images=frames_pil[1:],
            duration=timers,
            loop=0,
            optimize=False,
        )

    def main_loop_app(self, base: np.array) -> None:
        return self.current[self.actual_frame]

    def change_gif(self, change: int) -> None:
        self.current_giff = (self.current_giff + change) % self.total_gifs
        self.current: np.array = self.load(self.gif_path[self.current_giff])
        self.total_frames: int = len(self.current)

    def _button_left(self) -> None:
        self.change_gif(change=-1)

    def _button_right(self) -> None:
        self.change_gif(change=+1)

    def on_exit(self) -> None:
        pass

    def _button_short_click(self) -> None:
        pass

    def _button_long_click(self) -> None:
        pass
