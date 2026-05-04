"""
Pygame Display Driver and Input Handler.
DEV     : Gabriel Rocha de Souza
PROJECT : ledMatrix
"""

from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Callable

import numpy as np
import pygame

from utils import cfg
from utils.log import log


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

type ButtonHandler = Callable[[str], Any]
type Color = tuple[int, int, int]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BACKGROUND_COLOR: Color = (37, 37, 37)
BORDER_COLOR: Color = (255, 255, 255)

LONG_PRESS_THRESHOLD_MS: int = 750


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class _DisplayConfig:
    """Immutable geometry derived from the project config at startup."""

    x_max: int
    y_max: int
    pixel_size: int
    gap_size: int

    @property
    def window_width(self) -> int:
        return self.pixel_size * self.x_max + self.gap_size * (self.x_max + 1)

    @property
    def window_height(self) -> int:
        return self.pixel_size * self.y_max + self.gap_size * (self.y_max + 1)

    @classmethod
    def from_cfg(cls) -> "_DisplayConfig":
        s = cfg.config["screen"]
        return cls(
            x_max=s["x_max"],
            y_max=s["y_max"],
            pixel_size=s["tam_pixel"],
            gap_size=s["tam_space"],
        )


@dataclass
class _RenderState:
    """Tracks the last rendered frame to skip redundant draws."""

    last_frame: np.ndarray = field(default_factory=lambda: np.array([]))
    last_change_mode: bool | None = None

    def is_dirty(self, frame: np.ndarray, change: bool) -> bool:
        """Return True when the display needs to be redrawn."""
        return (
            not np.array_equal(frame, self.last_frame)
            or self.last_change_mode != change
        )

    def update(self, frame: np.ndarray, change: bool) -> None:
        self.last_frame = np.copy(frame)
        self.last_change_mode = change


# ---------------------------------------------------------------------------
# Button mapping
# ---------------------------------------------------------------------------

_BUTTON_MAP: dict[int, dict[int, str]] = {
    pygame.KEYDOWN: {
        pygame.K_LEFT: "left_click",
        pygame.K_RIGHT: "right_click",
        pygame.K_SPACE: "enter_press",
    },
    pygame.KEYUP: {
        pygame.K_SPACE: "enter_release",
    },
}


# ---------------------------------------------------------------------------
# Screen
# ---------------------------------------------------------------------------


class Screen:
    """
    Owns the Pygame window, the render loop, and keyboard input dispatch.

    On every call to :meth:`display` it:

    1. Drains the Pygame event queue and forwards mapped keys to *button_handler*.
    2. Redraws the LED grid only when the pixel matrix or the change-mode flag
       has actually changed (dirty-check via :class:`_RenderState`).

    Parameters
    ----------
    button_handler:
        Callable invoked with a ``str`` event name whenever a mapped key fires.
    """

    def __init__(self, button_handler: ButtonHandler) -> None:
        pygame.init()

        self._cfg: _DisplayConfig = _DisplayConfig.from_cfg()
        self._state: _RenderState = _RenderState()
        self._handler: ButtonHandler = button_handler

        self.running: bool = True

        self._surface: pygame.Surface = pygame.display.set_mode(
            (self._cfg.window_width, self._cfg.window_height)
        )

        log.info("Screen initialized.")

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def _poll_events(self) -> None:
        """Drain the Pygame event queue and dispatch mapped button events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                log.info("Quit event detected. Shutting down screen.")
                self.running = False
                return

            key_map = _BUTTON_MAP.get(event.type)
            if key_map is None:
                continue

            action = key_map.get(event.key)
            if action is not None:
                self._handler(action)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _draw(self, matrix: np.ndarray, change: bool) -> None:
        """Render the full LED grid to the Pygame surface."""
        cfg = self._cfg
        self._surface.fill(BACKGROUND_COLOR)

        y = cfg.gap_size

        for row in range(cfg.y_max):
            x = cfg.gap_size

            for col in range(cfg.x_max):
                color: Color = tuple(matrix[row][col])

                if change and (row in (0, cfg.y_max - 1) or col in (0, cfg.x_max - 1)):
                    color = BORDER_COLOR

                pygame.draw.rect(
                    self._surface,
                    color,
                    (x, y, cfg.pixel_size, cfg.pixel_size),
                )
                x += cfg.pixel_size + cfg.gap_size

            y += cfg.pixel_size + cfg.gap_size

        pygame.display.flip()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def display(self, matriz: np.ndarray, change: bool) -> None:
        """
        Poll input events and conditionally redraw the LED matrix.

        Parameters
        ----------
        matriz:
            A ``(y_max, x_max, 3)`` uint8 array of RGB pixel values.
        change:
            When *True*, the border pixels are highlighted to signal
            that the device is in app-switching mode.
        """
        self._poll_events()

        if not self._state.is_dirty(matriz, change):
            return

        self._state.update(matriz, change)
        self._draw(matriz, change)

        if not self.running:
            pygame.quit()
