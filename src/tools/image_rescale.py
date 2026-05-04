"""
Image Loader and Nearest-Neighbour Rescaler.
DEV     : Gabriel Rocha de Souza
PROJECT : ledMatrix
"""

from io import BytesIO
from pathlib import Path
from typing import Callable
from typing import cast
from typing import TypeVar

import numpy as np
import requests
from PIL import Image

from utils.log import log


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

type Scale = tuple[int, int]  # (height, width)

F = TypeVar("F", bound=Callable)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BINARY_COLOR_MAP: np.ndarray = np.array([[0, 0, 0], [255, 255, 255]], dtype=np.uint8)

_REQUEST_TIMEOUT: int = 5


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


def _requires_pixels(method: F) -> F:
    """Guard: raises RuntimeError if the pixel buffer was never populated."""

    def wrapper(self: "ImageRescale", *args, **kwargs):
        if self.pixels is None:
            raise RuntimeError(
                f"Cannot call '{method.__name__}': image failed to load."
            )
        return method(self, *args, **kwargs)

    return cast(F, wrapper)


# ---------------------------------------------------------------------------
# ImageRescale
# ---------------------------------------------------------------------------


class ImageRescale:
    """
    Loads an image from a file path or URL and rescales it using
    nearest-neighbour interpolation implemented in pure NumPy.

    Parameters
    ----------
    source:
        Either an absolute file path (``/…``), an HTTP/HTTPS URL, or an
        already-open :class:`PIL.Image.Image` instance.
    scale:
        Target ``(height, width)`` in pixels.
    fallback:
        Optional file path rendered when *source* fails to load.
    """

    def __init__(
        self,
        source: str | Image.Image,
        scale: Scale,
        fallback: str | None = None,
    ) -> None:

        self.scaleX: int
        self.scaleY: int

        self.scaleX, self.scaleY = scale

        self.scale: Scale = scale
        self.pixels: np.ndarray | None = None
        self.resized: np.ndarray | None = None

        pil_image = self._open(source)

        if pil_image is None and fallback is not None:
            log.warning("Primary source failed. Loading fallback image.")
            pil_image = self._open(fallback)

        if pil_image is not None:
            self.pixels = np.asarray(pil_image, dtype=np.uint8)
            self.resized = self._resize(target_h=scale[0], target_w=scale[1])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @_requires_pixels
    def resize(self, target_h: int, target_w: int) -> np.ndarray:
        """Return a freshly rescaled copy at *(target_h, target_w)*."""
        return self._resize(target_h=target_h, target_w=target_w)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _open(self, source: str | Image.Image) -> Image.Image | None:
        """Resolve *source* to a PIL Image, or return None on failure."""
        if isinstance(source, Image.Image):
            return source

        path = str(source)

        try:
            if path.startswith("/") or path.startswith("."):
                return Image.open(Path(path))

            if path.startswith("http"):
                return self._fetch(path)

        except Exception as e:
            log.error(f"Failed to open image from '{path}': {e}")

        return None

    def _fetch(self, url: str) -> Image.Image:
        """Download an image from *url* and return it as a PIL Image."""
        response = requests.get(url, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))

    def _resize(self, target_h: int, target_w: int) -> np.ndarray:
        """
        Rescale :attr:`pixels` to *(target_h, target_w)* using
        nearest-neighbour interpolation, channel by channel.
        """
        pixels = self.pixels
        assert pixels is not None, "Image pixels must be loaded before resizing."

        # Expand indexed (binary) images to RGB.
        if pixels.ndim == 2:
            pixels = _BINARY_COLOR_MAP[pixels]

        # Shape: (channels, H, W) for per-channel processing.
        chw = np.transpose(pixels, (2, 0, 1))
        result = np.zeros((chw.shape[0], target_h, target_w), dtype=np.uint8)

        for c in range(chw.shape[0]):
            result[c] = self._nn_channel(chw[c], target_h, target_w)

        return np.transpose(result, (1, 2, 0))

    @staticmethod
    def _nn_channel(src: np.ndarray, target_h: int, target_w: int) -> np.ndarray:
        """
        Nearest-neighbour resize of a single 2-D channel.

        Uses half-pixel rounding: the nearest source pixel is selected by
        rounding the real-valued coordinate rather than truncating it.
        """
        src_h, src_w = src.shape
        out = np.zeros((target_h, target_w), dtype=np.uint8)

        dx = (src_w - 1) / (target_w - 1)
        dy = (src_h - 1) / (target_h - 1)

        for i in range(target_h):
            for j in range(target_w):
                src_x = j * dx
                src_y = i * dy

                col = int(src_x + 0.5)
                row = int(src_y + 0.5)

                # Clamp to valid bounds.
                col = min(col, src_w - 1)
                row = min(row, src_h - 1)

                out[i, j] = src[row, col]

        return out
