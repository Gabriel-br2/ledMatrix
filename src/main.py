import gc
import importlib
import os
import pkgutil
import time
from typing import Any

import numpy as np
from dotenv import load_dotenv

from registry import get_registry
from screen import screen
from utils import cfg
from utils.log import log

load_dotenv()

# 0: main screen
# 1: git hub
# 2: spotify
# 3: gif viewer
# 4: wather update
# 5: pet virtual
# 6: calendario


class AppManager:
    def __init__(self):
        self.sideX: int = cfg.config["screen"]["x_max"]
        self.sideY: int = cfg.config["screen"]["y_max"]
        self.frame_rate: float = 0.05

        self.apps_registry: list[Any] = []
        self.current_app_instance: Any = None
        self.current_app_on_display: int = None
        self.current_app: int = 0
        self.change_mode: bool = False

        self.scr: screen = screen(button_handler=self.button_event_handler)

        self.map_change = {
            "left_click": -1,
            "right_click": +1,
            "short_click": 0,
        }

    def load_and_register_apps(self) -> None:
        apps_path = os.path.join(os.path.dirname(__file__), "app")
        for _, module_name, _ in pkgutil.iter_modules([apps_path]):
            importlib.import_module(f"app.{module_name}")
        log.info("All apps loaded.")

        self.apps_registry = get_registry()
        total_apps: int = len(self.apps_registry)
        log.info(f"Total apps loaded: {total_apps} and inicialized")

    def change_app(self, change: int) -> None:
        old_app_index: int = self.current_app

        if self.change_mode and change in ["left_click", "right_click", "short_click"]:
            self.current_app = (self.current_app + self.map_change[change]) % len(
                self.apps_registry
            )
            log.info(f"Button event action result: {self.current_app}")

            if change == "short_click":
                log.info("Change mode deactivated.")
                self.change_mode = False

        elif change == "long_click":
            log.info("Change mode activated.")
            self.change_mode = True

        if old_app_index != self.current_app:
            log.info(f"Unloading app {old_app_index}, loading app {self.current_app}")

            self.current_app_instance.on_exit()
            del self.current_app_instance
            gc.collect()

            self.current_app_instance = self.apps_registry[self.current_app][2](
                app_id=self.current_app
            )

    def button_event_handler(self, event: str) -> None:
        if event is not None:
            log.info(f"Button event received: {event}")
            change = self.current_app_instance.button_press(
                button_event=event, change=self.change_mode
            )
            self.change_app(change=change)

    def run(self):
        log.info("Starting Device...")

        self.load_and_register_apps()

        if not self.apps_registry:
            log.error("No apps found. Shutting down.")
            return

        self.current_app_instance = self.apps_registry[self.current_app][2](
            app_id=self.current_app
        )

        try:
            while self.scr.running:
                if self.current_app_on_display != self.current_app:
                    main_mat = np.zeros((self.sideY, self.sideX, 3))
                    self.current_app_on_display = self.current_app

                main_mat, long_press = self.current_app_instance.main_loop(
                    base=main_mat
                )
                self.change_app(change=long_press)

                self.scr.display(matriz=main_mat, change=self.change_mode)
                time.sleep(self.frame_rate + self.current_app_instance.fps_app)
                self.current_app_instance += +1

        except KeyboardInterrupt:
            log.info("Shutting down device...")

        # except Exception as e:
        #    log.error(f"An error occurred: {e}")

        finally:
            log.info("Device turned off.")


if __name__ == "__main__":
    manager = AppManager()
    manager.run()
