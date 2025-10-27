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
        color: Tuple[int, int, int] = (255, 255, 255),
    ) -> None:

        self.tam: int = tam
        self.text: str = text
        self.offset: Tuple[int, int] = offset
        self.color: Tuple[int, int, int] = color
        self.frame: int = 0

        self._load_font()
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

        image: Image = Image.new("RGB", (width, self.tam), color=(0, 0, 0))
        draw: ImageDraw = ImageDraw.Draw(image)
        draw.text((0, 0), self.text, font=self.font, fill=self.color)

        self.image_mat = [np.array(image)]
        self.h, self.w = self.image_mat[0].shape[:2]

    def limit(self, lim: int) -> np.array:
        image_array = self.image_mat[0]
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

        self.w = lim

    def put(self, base: np.array, actual_frame: int = 0) -> np.array:
        h, w = self.offset
        try:
            base[h : self.h + h, w : self.w + w] = self.image_mat[actual_frame]
        except Exception as e:
            pass

        return base
