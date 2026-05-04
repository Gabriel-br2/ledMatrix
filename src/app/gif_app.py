"""
GIF Viewer App — Animated GIF Player with Pre-processing Pipeline.
DEV     : Gabriel Rocha de Souza
PROJECT : ledMatrix
"""

import os
import random
from pathlib import Path

import numpy as np
from PIL import Image
from PIL import ImageSequence

from app.__base__ import baseApp
from tools.image_rescale import ImageRescale
from utils import cfg
from utils.log import log
from utils.registry import register_object


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

type GifFrames = list[np.ndarray]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_EXCLUDED_INDICES: frozenset[int] = frozenset({2})  # GIF slots to skip on random pick


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


@register_object("app", "gif_app")
class GifApp(baseApp):
    """
    Plays animated GIFs from disk, rescaling them to the display resolution
    on first use and caching the result as a processed GIF.

    Navigation
    ----------
    - Left arrow  → previous GIF.
    - Right arrow → next GIF.
    """

    def __init__(self, app_id: int = 0) -> None:
        super().__init__(app_id=app_id, name="GIF Viewer")

        self.fps_app: float = 0.01

        path: str = cfg.config["main"]["path"]

        pending, self._gif_paths = self._scan_gifs(
            raw_dir=Path(path) / "resource" / "gifs",
            processed_dir=Path(path) / "processed_resource" / "gifs",
        )

        for raw, processed in pending.items():
            log.info(f"Pre-processing GIF: {raw.name}")
            self._preprocess(raw, processed)

        self._total_gifs: int = len(self._gif_paths)
        self._current_index: int = self._pick_random()

        self.current: GifFrames = self._load(self._gif_paths[self._current_index])
        self.total_frames: int | None = len(self.current)

    # ------------------------------------------------------------------
    # baseApp contract
    # ------------------------------------------------------------------

    def main_loop_app(self, base: np.ndarray) -> np.ndarray:
        return self.current[self.actual_frame]

    def on_exit(self) -> None:
        pass

    def _button_left(self) -> None:
        self._change_gif(delta=-1)

    def _button_right(self) -> None:
        self._change_gif(delta=+1)

    def _button_short_click(self) -> None:
        pass

    def _button_long_click(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Internal — GIF management
    # ------------------------------------------------------------------

    def _change_gif(self, delta: int) -> None:
        """Advance or rewind the GIF carousel by *delta* steps."""
        self._current_index = (self._current_index + delta) % self._total_gifs
        self.current = self._load(self._gif_paths[self._current_index])
        self.total_frames: int | None = len(self.current)

    def _pick_random(self) -> int:
        """Return a random GIF index, skipping :data:`_EXCLUDED_INDICES`."""
        available = [i for i in range(self._total_gifs) if i not in _EXCLUDED_INDICES]
        return random.choice(available) if available else 0

    # ------------------------------------------------------------------
    # Internal — file I/O
    # ------------------------------------------------------------------

    @staticmethod
    def _scan_gifs(
        raw_dir: Path,
        processed_dir: Path,
    ) -> tuple[dict[Path, Path], list[Path]]:
        """
        Compare *raw_dir* and *processed_dir* to find GIFs that need processing.

        Returns
        -------
        pending:
            Mapping of ``raw_path → processed_path`` for unprocessed GIFs.
        all_processed:
            Sorted list of all paths in *processed_dir* (including newly pending).
        """
        if not raw_dir.is_dir():
            raise FileNotFoundError(f"GIF source directory not found: {raw_dir}")
        if not processed_dir.is_dir():
            raise FileNotFoundError(
                f"GIF processed directory not found: {processed_dir}"
            )

        raw_names = {f.name for f in raw_dir.iterdir() if f.is_file()}
        processed_names = {f.name for f in processed_dir.iterdir() if f.is_file()}

        unprocessed = raw_names - processed_names

        pending: dict[Path, Path] = {
            raw_dir / name: processed_dir / name for name in unprocessed
        }

        all_processed = sorted(
            [processed_dir / name for name in processed_names] + list(pending.values())
        )

        return pending, all_processed

    @staticmethod
    def _load(path: Path) -> GifFrames:
        """Load a GIF from *path* and return its frames as a list of RGB arrays."""
        gif = Image.open(path)
        frames: GifFrames = []

        for frame in ImageSequence.Iterator(gif):
            frames.append(np.array(frame.convert("RGB"), dtype=np.uint8))

        return frames

    @staticmethod
    def _preprocess(raw: Path, output: Path) -> None:
        """
        Rescale every frame of *raw* to the display resolution and save the
        result as a new GIF at *output*.

        The processed file is used on all subsequent loads, avoiding per-frame
        rescaling at runtime.
        """
        target_h: int = cfg.config["screen"]["y_max"]
        target_w: int = cfg.config["screen"]["x_max"]

        gif = Image.open(raw)
        frames_pil: list[Image.Image] = []
        timers: list[int] = []

        for frame in ImageSequence.Iterator(gif):
            rescaled = ImageRescale(
                source=frame.convert("RGBA"),
                scale=(target_h, target_w),
            )
            frames_pil.append(
                Image.fromarray(rescaled.resized.astype(np.uint8), "RGBA")
                if rescaled.resized
                else frame.convert("RGBA")
            )
            timers.append(frame.info.get("duration", 100))

        frames_pil[0].save(
            output,
            save_all=True,
            append_images=frames_pil[1:],
            duration=timers,
            loop=0,
            optimize=False,
        )
        log.info(f"GIF saved to: {output}")
