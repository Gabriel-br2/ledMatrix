"""
Abstract Base Class for all ledMatrix Applications.
DEV     : Gabriel Rocha de Souza
PROJECT : ledMatrix
"""

import time
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Callable

import numpy as np

from utils.log import log


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

type ButtonEvent = str


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LONG_PRESS_THRESHOLD_S: float = 1.0
SHORT_PRESS_THRESHOLD_S: float = 0.05


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class _EnterButtonTracker:
    """
    Tracks the physical state of the enter/space button to distinguish
    short clicks from long presses without blocking the render loop.
    """

    long_press_triggered: bool = False
    press_start_time: float = 0.0
    last_state: int = 0

    def on_press(self, current_time: float) -> None:
        """Record the moment the button was pressed down."""
        self.press_start_time = current_time
        self.long_press_triggered = False

    def held_duration(self) -> float:
        """Return how long the button has been held, in seconds."""
        return time.time() - self.press_start_time

    def resolve_release(self, current_time: float) -> ButtonEvent | None:
        """
        Decide what event to emit on button release.

        Returns ``'short_click'`` if the press was brief and no long-press
        was already fired, otherwise ``None``.
        """
        if self.long_press_triggered:
            return None

        duration = current_time - self.press_start_time
        return "short_click" if duration >= SHORT_PRESS_THRESHOLD_S else None


# ---------------------------------------------------------------------------
# Base App
# ---------------------------------------------------------------------------


class baseApp(ABC):
    """
    Contract every ledMatrix app must fulfil.

    Subclasses implement the four abstract button handlers and
    :meth:`main_loop_app`. The base class owns the enter-button state
    machine and the long-press detection that runs inside :meth:`main_loop`.

    Parameters
    ----------
    app_id:
        Index of this app in the global registry.
    name:
        Human-readable display name used in logs and ``__str__``.
    """

    def __init__(self, app_id: int, name: str) -> None:
        self.name: str = name
        self.app_id: int = app_id
        self.actual_frame: int = 0
        self.total_frames: int | None = None
        self.fps_app: float = 0.0

        self._enter_tracker: _EnterButtonTracker = _EnterButtonTracker()

        self._button_dispatch: dict[ButtonEvent, Callable[[], None]] = {
            "short_click": self._button_short_click,
            "long_click": self._button_long_click,
            "left_click": self._button_left,
            "right_click": self._button_right,
        }

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __add__(self, other: int) -> "baseApp":
        if self.total_frames is None:
            raise NotImplementedError(
                f"'{self.name}' must set total_frames before the render loop starts."
            )
        self.actual_frame = (self.actual_frame + other) % self.total_frames
        return self

    def __str__(self) -> str:
        return (
            f"App ID: {self.app_id} | Name: {self.name} | "
            f"Frame: {self.actual_frame}/{self.total_frames}"
        )

    # ------------------------------------------------------------------
    # Core loop (called by AppManager)
    # ------------------------------------------------------------------

    def main_loop(self, base: np.ndarray) -> tuple[np.ndarray, ButtonEvent | None]:
        """
        Run one render tick and check for a long-press event.

        Returns
        -------
        tuple[np.ndarray, ButtonEvent | None]
            The updated frame matrix and an optional navigation event
            (``'long_click'`` when threshold is crossed, else ``None``).
        """
        long_press: ButtonEvent | None = None
        tracker = self._enter_tracker

        if tracker.last_state and not tracker.long_press_triggered:
            if tracker.held_duration() >= LONG_PRESS_THRESHOLD_S:
                long_press = self.button_press(button_event="long_click", change=True)
                tracker.long_press_triggered = True

        return self.main_loop_app(base=base), long_press

    # ------------------------------------------------------------------
    # Input dispatch (called by Screen's button handler)
    # ------------------------------------------------------------------

    def button_press(
        self, button_event: ButtonEvent, change: bool
    ) -> ButtonEvent | None:
        """
        Translate a raw button event into a dispatchable action.

        Enter press/release events are routed through the state machine in
        :class:`_EnterButtonTracker`.  All other mapped events dispatch
        immediately, unless the device is in change-mode and the event is
        a directional click (those are consumed by :class:`AppManager`).

        Returns the action string that was resolved, or ``None``.
        """
        log.debug(f"Button press received: {button_event!r}")
        action: ButtonEvent | None = None

        if button_event in ("enter_press", "enter_release"):
            action = self._handle_enter_event(button_event)
        elif button_event in self._button_dispatch:
            action = button_event

        if action is not None:
            is_nav_in_change_mode = action in ("left_click", "right_click") and change
            if not is_nav_in_change_mode:
                self._button_dispatch[action]()

        return action

    # ------------------------------------------------------------------
    # Abstract interface — subclasses must implement
    # ------------------------------------------------------------------

    @abstractmethod
    def main_loop_app(self, base: np.ndarray) -> np.ndarray:
        """Render one frame onto *base* and return the updated matrix."""

    @abstractmethod
    def on_exit(self) -> None:
        """Clean up resources when this app is unloaded."""

    @abstractmethod
    def _button_short_click(self) -> None:
        """React to a confirmed short press of the enter button."""

    @abstractmethod
    def _button_left(self) -> None:
        """React to a left arrow key event."""

    @abstractmethod
    def _button_right(self) -> None:
        """React to a right arrow key event."""

    @abstractmethod
    def _button_long_click(self) -> None:
        """React to a long press of the enter button."""

    # ------------------------------------------------------------------
    # Internal — enter button state machine
    # ------------------------------------------------------------------

    def _handle_enter_event(self, event: ButtonEvent) -> ButtonEvent | None:
        tracker = self._enter_tracker
        current_time = time.time()

        if event == "enter_press" and not tracker.last_state:
            tracker.on_press(current_time)
            tracker.last_state = 1
            return None

        if event == "enter_release" and tracker.last_state:
            tracker.last_state = 0
            return tracker.resolve_release(current_time)

        return None
