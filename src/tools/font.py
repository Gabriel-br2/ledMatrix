"""
Bitmap Font Renderer with Scrolling and Segmented Color Support.
DEV     : Gabriel Rocha de Souza
PROJECT : ledMatrix
"""

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Callable
from typing import cast
from typing import TypeVar

import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from utils import cfg
from utils.log import log


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

type Color = tuple[int, int, int]
type ColorMap = list[int]

F = TypeVar("F", bound=Callable)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_COLOR: Color = (255, 255, 255)
CANVAS_COLOR: Color = (0, 0, 0)


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


def _invalidates_pixels(method: F) -> F:
    """Re-renders the pixel buffer after any method that mutates text or color."""

    def wrapper(self: "Font", *args, **kwargs):
        result = method(self, *args, **kwargs)
        self._render()
        return result

    return cast(F, wrapper)


# ---------------------------------------------------------------------------
# Font
# ---------------------------------------------------------------------------


class Font:
    """
    Renders a string into a numpy pixel buffer using a bitmap font.

    Supports
    --------
    - Segmented coloring via *map_color* + *color* lists.
    - Horizontal scroll via :meth:`limit` (window slide) and :meth:`carousel`
      (infinite loop).
    - Frame-by-frame animation via ``+=`` operator.
    - Compositing onto an existing base matrix via :meth:`put`.

    Parameters
    ----------
    size:
        Font size in pixels.
    text:
        Initial string to render.
    offset:
        ``(row, col)`` position where the text is composited on the base matrix.
    color:
        List of RGB colors. Without *map_color*, only the first entry is used.
    map_color:
        Character-index breakpoints that map each text segment to a color slot.
    """

    def __init__(
        self,
        size: int,
        text: str,
        offset: tuple[int, int],
        color: None | list[Color] = None,
        map_color: None | ColorMap = None,
    ) -> None:

        self.size: int = size
        self.text: str = text
        self.offset: tuple[int, int] = offset
        self.color: list[Color] = color or [DEFAULT_COLOR]
        self.map_color: ColorMap | None = map_color

        self.actual_frame: int = 0
        self.frames: int = 1

        self._pil_font: ImageFont.FreeTypeFont | ImageFont.ImageFont = self._load_font()
        self._render()

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __iadd__(self, step: int) -> "Font":
        self.actual_frame = (self.actual_frame + step) % self.frames
        return self

    # ------------------------------------------------------------------
    # Public API — text mutation
    # ------------------------------------------------------------------

    @_invalidates_pixels
    def update_text(self, text: str) -> None:
        """Replace the displayed string and re-render the pixel buffer."""
        self.text = text

    # ------------------------------------------------------------------
    # Public API — layout
    # ------------------------------------------------------------------

    def limit(self, lim: int) -> None:
        """
        Constrain the render width to *lim* pixels.

        - If the text is wider than *lim*, generates one sliding window frame
          per pixel offset so the caller can animate horizontal scrolling.
        - If the text is narrower, pads with black to exactly *lim* pixels.
        """
        src = self._original
        width = src.shape[1]

        if width > lim:
            padded = self._pad_right(src, lim)
            frames = [padded[:, s : s + lim, :] for s in range(width + 1)]
        else:
            frames = [self._pad_right(src, lim)]

        self.image_mat = np.stack(frames)
        self.frames = len(self.image_mat)
        self.w = lim

    def extern_limit(self, lim: int) -> None:
        """Extend the frame buffer with blank frames until it reaches *lim* frames."""
        deficit = lim - self.frames

        if deficit <= 0:
            return

        blank = np.zeros((deficit, self.h, self.w, 3), dtype=self.image_mat.dtype)
        self.image_mat = np.concatenate((self.image_mat, blank), axis=0)
        self.frames = len(self.image_mat)

    def carousel(self) -> None:
        """
        Append wrap-around frames after :meth:`limit` so the text loops
        seamlessly when the animation reaches the end.
        """
        src = self._original
        lim = self.w
        orig_w = src.shape[1]

        if orig_w <= lim:
            return

        strip_w = orig_w + lim
        padded = self._pad_right(src, lim)

        new_frames = []
        for start in range(orig_w + 1, strip_w):
            end = start + lim
            part1 = padded[:, start:strip_w, :]
            part2 = padded[:, 0 : end - strip_w, :]
            new_frames.append(np.concatenate((part1, part2), axis=1))

        if new_frames:
            self.image_mat = np.concatenate(
                (self.image_mat, np.stack(new_frames)), axis=0
            )
            self.frames = len(self.image_mat)

    def put(self, base: np.ndarray) -> np.ndarray:
        """
        Composite the current frame onto *base* at :attr:`offset`.

        Parameters
        ----------
        base:
            The ``(H, W, 3)`` matrix to draw onto (modified in-place).
        """
        row, col = self.offset

        try:
            base[row : row + self.h, col : col + self.w] = self.image_mat[
                self.actual_frame
            ]
        except IndexError as e:
            log.error(f"Font.put index error: {e}")

        return base

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_font(self) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        path = Path(cfg.config["main"]["path"]) / "resource" / "tiny.otf"

        try:
            return ImageFont.truetype(str(path), self.size)
        except OSError:
            log.error(f"Cannot load font at '{path}'. Falling back to default.")
            return ImageFont.load_default()

    def _render(self) -> None:
        """
        Rasterise :attr:`text` into :attr:`_original` and reset the frame buffer.
        Called once at construction and again whenever the text changes.
        """
        font = self._pil_font
        width = max(int(font.getlength(self.text)), 1)
        canvas = Image.new("RGB", (width, self.size), color=CANVAS_COLOR)
        draw = ImageDraw.Draw(canvas)

        if self.map_color is None:
            draw.text((0, 0), self.text, font=font, fill=self.color[0])
        else:
            self._draw_segmented(draw, font)

        self._original = np.array(canvas)
        self.image_mat = np.stack([self._original])
        self.h, self.w = self._original.shape[:2]
        self.frames = 1
        self.actual_frame = 0

    def _draw_segmented(
        self,
        draw: ImageDraw.ImageDraw,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    ) -> None:
        """Render :attr:`text` in multiple colors according to :attr:`map_color`."""
        segments = cast(ColorMap, self.map_color)
        num_colors = len(self.color)
        cursor_x = 0

        for i, start in enumerate(segments):
            end = segments[i + 1] if i + 1 < len(segments) else len(self.text)
            segment = self.text[start:end]
            color = self.color[min(i, num_colors - 1)]

            if segment:
                draw.text((cursor_x, 0), segment, font=font, fill=color)
                cursor_x += int(font.getlength(segment))

    @staticmethod
    def _pad_right(array: np.ndarray, cols: int) -> np.ndarray:
        """Return *array* padded on the right with *cols* black columns."""
        pad = ((0, 0), (0, cols), (0, 0))
        return np.pad(array, pad, mode="constant", constant_values=0)
