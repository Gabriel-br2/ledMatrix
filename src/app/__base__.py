import time
from typing import Any
from typing import Callable

import numpy as np

from utils.log import log


class baseApp:
    def __init__(self, app_id: int, name: str) -> None:
        self.name: str = name
        self.app_id: int = app_id
        self.actual_frame: int = 0
        self.total_frames: int = None
        self.fps_app: int = 0

        self.buttons_options: dict[str, Callable[..., None]] = {
            "short_click": self._button_short_click,
            "long_click": self._button_long_click,
            "left_click": self._button_left,
            "right_click": self._button_right,
        }

        self.enter_button_tracker: dict[str, Any] = {
            "long_press_triggered": False,
            "press_start_time": 0.0,
            "last_state": 0,
        }

        self.LONG_PRESS_THRESHOLD_S: float = 1.0
        self.SHORT_PRESS_THRESHOLD_S: float = 0.05

    def __add__(self, other: int) -> int:
        if self.total_frames is None:
            raise NotImplementedError("total_frames is not implemented in baseApp.")

        self.actual_frame = (self.actual_frame + other) % self.total_frames
        return self

    def __str__(self) -> str:
        return f"App ID: {self.app_id}, Name: {self.name}, Frame: {self.actual_frame}/{self.total_frames}"

    def main_loop(self, base: np.array) -> np.array:
        last_state: int = self.enter_button_tracker["last_state"]
        long_triggered: bool = self.enter_button_tracker["long_press_triggered"]
        press_start_time: float = self.enter_button_tracker["press_start_time"]
        long_press: int = 0

        if last_state and not long_triggered:
            duration: float = time.time() - press_start_time

            if duration >= self.LONG_PRESS_THRESHOLD_S:
                long_press = self.button_press(button_event="long_click", change=True)

                self.enter_button_tracker["long_press_triggered"] = True

        return self.main_loop_app(base=base), long_press

    def button_press(self, button_event: str, change: bool) -> int:
        action_to_run: str | None = None
        log.debug(f"Button press received: {button_event}")

        if button_event in ["enter_press", "enter_release"]:
            action = 1 if button_event == "enter_press" else 0
            action_to_run = self._update_enter_button_state(new_state=action)

        elif button_event in self.buttons_options:
            action_to_run = button_event

        if action_to_run is not None:
            if not (action_to_run in ["left_click", "right_click"] and change):
                self.buttons_options.get(action_to_run)()

        return action_to_run

    def _update_enter_button_state(self, new_state: int) -> str | None:
        current_time: float = time.time()
        last_state: int = self.enter_button_tracker["last_state"]
        response: Any = None

        if new_state and not last_state:
            self.enter_button_tracker["press_start_time"] = current_time
            self.enter_button_tracker["long_press_triggered"] = False

        elif not new_state and last_state:
            start_time: float = self.enter_button_tracker["press_start_time"]
            long_triggered: bool = self.enter_button_tracker["long_press_triggered"]

            if not long_triggered:
                duration: float = current_time - start_time

                if duration >= self.SHORT_PRESS_THRESHOLD_S:
                    response = "short_click"

        self.enter_button_tracker["last_state"] = new_state
        return response

    def on_exit(self) -> None:
        raise NotImplementedError("on_exit function is not implemented in baseApp.")

    def main_loop_app(self, base: np.array) -> None:
        raise NotImplementedError(
            "main_loop_app function is not implemented in baseApp."
        )

    def _button_short_click(self):
        raise NotImplementedError(
            "_button_short_click function is not implemented in baseApp."
        )

    def _button_left(self):
        raise NotImplementedError(
            "_button_left function is not implemented in baseApp."
        )

    def _button_right(self):
        raise NotImplementedError(
            "_button_right function is not implemented in baseApp."
        )

    def _button_long_click(self):
        raise NotImplementedError(
            "_button_long_click function is not implemented in baseApp."
        )
