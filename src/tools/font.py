from typing import Tuple

import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from utils import cfg
from utils import log


class Font:
    def __init__(
        self,
        tam: int,
        text: str,
        offset: Tuple[int, int],
        map_color: list[int] = None,
        color: list[Tuple[int, int, int]] = [(255, 255, 255)],
    ) -> None:

        self.tam: int = tam
        self.text: str = text
        self.offset: Tuple[int, int] = offset
        self.color: list[Tuple[int, int, int]] = color
        self.actual_frame: int = 0
        self.frames: int = 1
        self.map_color = map_color

        self._load_font()
        self._pixel()

    def __add__(self, other: int) -> int:
        self.actual_frame = (self.actual_frame + other) % self.frames
        return self

    def update_text(self, text: str) -> None:
        self.text = text
        self._pixel()

    def _load_font(self):
        base_path: str = cfg.config["main"]["path"]
        path: str = base_path + "resource/tiny.otf"

        try:
            self.font = ImageFont.truetype(path, self.tam)
        except OSError:
            log.error(f"ERROR: Not possible to load font: '{path}'.")
            log.error("Using font base.")
            self.font = ImageFont.load_default()

    def _pixel(self) -> None:
        width: int = int(self.font.getlength(self.text))
        image_width = max(width, 1)
        image: Image = Image.new("RGB", (image_width, self.tam), color=(0, 0, 0))
        draw: ImageDraw = ImageDraw.Draw(image)

        if self.map_color is None:
            draw.text((0, 0), self.text, font=self.font, fill=self.color[0])

        else:
            current_x = 0
            num_segments = len(self.map_color)
            num_colors = len(self.color)

            for i in range(num_segments):
                start_index = self.map_color[i]
                current_color = self.color[min(i, num_colors - 1)]

                if i == num_segments - 1:
                    end_index = len(self.text)
                else:
                    end_index = self.map_color[i + 1]

                segment_text = self.text[start_index:end_index]

                if segment_text:
                    draw.text(
                        (current_x, 0), segment_text, font=self.font, fill=current_color
                    )

                    current_x += int(self.font.getlength(segment_text))

        self.original_image_mat = np.array(image)
        self.image_mat = [np.array(image)]
        self.h, self.w = self.original_image_mat.shape[:2]

    def limit(self, lim: int) -> np.array:
        image_array = self.original_image_mat
        width: int = image_array.shape[1]

        if width > lim:
            pad_config = ((0, 0), (0, lim), (0, 0))
            padded_mat = np.pad(
                image_array, pad_config, mode="constant", constant_values=0
            )

            final_matrix = []

            num_windows = width + 1
            for start in range(num_windows):
                end = start + lim
                sub_matrix = padded_mat[:, start:end, :]
                final_matrix.append(sub_matrix)

            self.image_mat = np.stack(final_matrix)

        else:
            pad_amount = lim - width
            pad_width_tuple = ((0, 0), (0, pad_amount), (0, 0))
            padded_mat = np.pad(
                image_array, pad_width_tuple, mode="constant", constant_values=0
            )

            self.image_mat = np.stack([padded_mat])

        self.frames = len(self.image_mat)
        self.w = lim

    def extern_limit(self, lim: int) -> None:
        current_frames = self.frames

        if current_frames < lim:
            num_frames_to_add = lim - current_frames

            frame_shape = (self.h, self.w, 3)

            blank_frames_stack = np.zeros(
                (num_frames_to_add,) + frame_shape, dtype=self.image_mat.dtype
            )

            self.image_mat = np.concatenate(
                (self.image_mat, blank_frames_stack), axis=0
            )

            self.frames = len(self.image_mat)

    def carousel(self) -> None:
        original_width: int = self.original_image_mat.shape[1]
        lim: int = self.w

        if original_width > lim:
            pad_config = ((0, 0), (0, lim), (0, 0))
            padded_mat = np.pad(
                self.original_image_mat, pad_config, mode="constant", constant_values=0
            )

            strip_width = original_width + lim
            new_frames = []

            for start in range(original_width + 1, strip_width):
                end = start + lim

                part1 = padded_mat[:, start:strip_width, :]
                part2_width = end - strip_width
                part2 = padded_mat[:, 0:part2_width, :]

                sub_matrix = np.concatenate((part1, part2), axis=1)
                new_frames.append(sub_matrix)

            if new_frames:
                new_frames_stack = np.stack(new_frames)
                self.image_mat = np.concatenate(
                    (self.image_mat, new_frames_stack), axis=0
                )

            self.frames = len(self.image_mat)

    def put(self, base: np.array) -> np.array:
        h, w = self.offset

        base[h : self.h + h, w : self.w + w] = self.image_mat[self.actual_frame]

        return base
