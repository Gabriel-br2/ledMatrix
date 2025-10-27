from io import BytesIO
from typing import Any

import numpy as np
import requests
from PIL import Image

from utils.log import log


class image:
    def __init__(self, img: Any, scale: tuple, error: str = None) -> None:
        self.color_map = np.array([[0, 0, 0], [255, 255, 255]], dtype=np.uint8)

        self.scaleY, self.scaleX = scale

        if type(img) == str:
            if img.startswith("/"):
                self.img = Image.open(img)

            elif img.startswith("http"):
                self.img = self._fetch_image(img=img)

        else:
            self.img = img

        try:
            self.pixels = np.asarray(self.img, np.uint8)

        except Exception as e:
            log.error(f"Error loading image: {e}")
            if error is not None:
                self.img = Image.open(error)
                self.pixels = np.asarray(self.img, np.uint8)

        self.resized = self.resize(nh=scale[0], nw=scale[1])

    def resize(self, nh: int, nw: int) -> np.ndarray:
        if self.pixels.ndim == 2:
            self.pixels: np.ndarray = self.color_map[self.pixels]

        self.pixels: np.ndarray = np.transpose(self.pixels, (2, 0, 1))
        channels = self.pixels.shape[0]

        self.mat_Image: np.array = np.zeros((channels, nh, nw), np.uint8)

        for channel in range(channels):
            self.mat_Image[channel] = self._resize_NN_channel(
                pixels=self.pixels[channel], nsize=(nh, nw)
            )

        return np.transpose(self.mat_Image, (1, 2, 0))

    def _fetch_image(self, img: str) -> Any:
        response: Any = requests.get(img, timeout=5)
        content: Any = response.content

        image_bytes = BytesIO(content)
        return Image.open(image_bytes)

    def _resize_NN_channel(self, pixels: np.ndarray, nsize: tuple) -> np.ndarray:
        nh, nw = nsize
        height, width = pixels.shape[0], pixels.shape[1]

        npixels = np.zeros(nsize, np.uint8)
        dx = (width - 1) / (nw - 1)
        dy = (height - 1) / (nh - 1)

        for i in range(nh):
            for j in range(nw):
                x, y = j * dx, i * dy
                intx, inty = int(x), int(y)
                distx, disty = x - intx, y - inty

                if distx > 0.5:
                    intx = intx + 1
                if disty > 0.5:
                    inty = inty + 1

                npixels[i, j] = pixels[inty, intx]
        return npixels


if __name__ == "__main__":
    img_path = "/home/gabriel/Documents/code/ledMatrix/resource/giticon.png"

    path_treat = image(img_path, scale=(32, 32))
    path_treat.show()
