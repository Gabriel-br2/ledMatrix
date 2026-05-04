"""
Application Entry Point and App Lifecycle Manager.
DEV     : Gabriel Rocha de Souza
PROJECT : ledMatrix
"""

import gc
import importlib
import os
import pkgutil
import time
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Callable

import numpy as np
from dotenv import load_dotenv

from screen import Screen
from utils import cfg
from utils.log import log
from utils.registry import get_registry

load_dotenv()

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

type ButtonEvent = str
type AppIndex = int


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FRAME_RATE: float = 0.05

NAV_DELTA: dict[ButtonEvent, int] = {
    "left_click": -1,
    "right_click": +1,
    "short_click": 0,
}


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class AppState:
    """Holds the mutable runtime state of the running application loop."""

    current_app: AppIndex = 0
    displayed_app: AppIndex = -1  # forces first render
    change_mode: bool = False
    matrix: np.ndarray = field(
        default_factory=lambda: np.zeros(
            (
                cfg.config["screen"]["y_max"],
                cfg.config["screen"]["x_max"],
                3,
            )
        )
    )


# ---------------------------------------------------------------------------
# App Manager
# ---------------------------------------------------------------------------


class AppManager:
    """
    Owns the main loop and coordinates app loading, switching, and rendering.

    Responsibilities
    ----------------
    - Discover and register all apps located under ``src/app/``.
    - React to button events forwarded by :class:`Screen`.
    - Drive the frame loop, delegating drawing to the active app instance.
    """

    def __init__(self) -> None:
        self._state: AppState = AppState()
        self._registry: list[Any] = []
        self._active_app: Any = None

        self._screen: Screen = Screen(button_handler=self._on_button_event)

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _load_apps(self) -> None:
        """Dynamically import every module under ``src/app/`` to trigger registration."""
        apps_path = os.path.join(os.path.dirname(__file__), "app")

        for _, module_name, _ in pkgutil.iter_modules([apps_path]):
            importlib.import_module(f"app.{module_name}")

        self._registry = get_registry()

        log.info(f"Apps loaded: {len(self._registry)}")

    def _instantiate_app(self, index: AppIndex) -> Any:
        """Return a fresh instance of the app at *index* in the registry."""
        app_class: Callable[..., Any] = self._registry[index][2]
        return app_class(app_id=index)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _navigate(self, event: ButtonEvent) -> None:
        """
        Apply navigation logic for left/right/short/long clicks.

        Only ``long_click`` toggles *change_mode*; directional clicks work
        only while *change_mode* is active and change the active app index.
        """
        s = self._state

        if event == "long_click":
            s.change_mode = True
            log.info("Change mode activated.")
            return

        if not s.change_mode:
            return

        delta = NAV_DELTA.get(event, None)

        if delta is None:
            return

        old_index = s.current_app
        s.current_app = (s.current_app + delta) % len(self._registry)

        if event == "short_click":
            s.change_mode = False
            log.info("Change mode deactivated.")

        if old_index != s.current_app:
            self._swap_app(old_index, s.current_app)

    def _swap_app(self, old: AppIndex, new: AppIndex) -> None:
        """Teardown the running app and boot the next one."""
        log.info(f"Unloading app [{old}] → loading app [{new}].")
        self._active_app.on_exit()
        del self._active_app
        gc.collect()
        self._active_app = self._instantiate_app(new)

    # ------------------------------------------------------------------
    # Button callback (called from Screen's thread)
    # ------------------------------------------------------------------

    def _on_button_event(self, event: ButtonEvent) -> None:
        if event is None:
            return

        log.info(f"Button event: {event!r}")

        # Let the active app decide whether it consumes the event or passes it up.
        nav_event: ButtonEvent = self._active_app.button_press(
            button_event=event,
            change=self._state.change_mode,
        )
        self._navigate(nav_event)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the device and enter the rendering loop."""
        log.info("Starting device...")

        self._load_apps()

        if not self._registry:
            log.error("No apps found. Shutting down.")
            return

        self._active_app = self._instantiate_app(self._state.current_app)

        try:
            self._loop()
        except KeyboardInterrupt:
            log.info("Keyboard interrupt — shutting down.")
        finally:
            log.info("Device turned off.")

    def _loop(self) -> None:
        """Inner rendering loop, separated for clarity and testability."""
        s = self._state

        while self._screen.running:

            # Reset the frame buffer when the active app changes.
            if s.displayed_app != s.current_app:
                s.matrix = np.zeros_like(s.matrix)
                s.displayed_app = s.current_app

            s.matrix, long_press = self._active_app.main_loop(base=s.matrix)

            self._navigate(long_press)

            self._screen.display(matriz=s.matrix, change=s.change_mode)

            time.sleep(FRAME_RATE + self._active_app.fps_app)

            self._active_app += 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    manager = AppManager()
    manager.run()
