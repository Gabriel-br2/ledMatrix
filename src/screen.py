from typing import Any
from typing import Callable

import numpy as np
import pygame

from utils import cfg
from utils.log import log


class screen:
    def __init__(self, button_handler: Callable[str, None]) -> None:
        pygame.init()

        self.running: bool = True
        self.actual_frame: list = []
        self.last_change_state: bool = None
        self.button_handler: Callable[str, None] = button_handler

        self.x_max: int = cfg.config["screen"]["x_max"]
        self.y_max: int = cfg.config["screen"]["y_max"]

        self.tam_pixel: int = cfg.config["screen"]["tam_pixel"]
        self.tam_space: int = cfg.config["screen"]["tam_space"]

        self.screen: screen = pygame.display.set_mode(
            (
                (self.tam_pixel * self.x_max) + (self.tam_space * (self.x_max + 1)),
                (self.tam_pixel * self.y_max) + (self.tam_space * (self.y_max + 1)),
            )
        )

        self.map_buttons: dict[Any, str] = {
            pygame.KEYDOWN: {
                pygame.K_LEFT: "left_click",
                pygame.K_RIGHT: "right_click",
                pygame.K_SPACE: "enter_press",
            },
            pygame.KEYUP: {
                pygame.K_SPACE: "enter_release",
            },
        }

        self.INVERT_THRESHOLD: int = 750

        log.info("Screen initialized.")

    def _button_press(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                log.info("Quit event detected. Shutting down screen.")
                self.running = False

            if event.type in self.map_buttons:
                action = self.map_buttons.get(event.type, None)
                event = action.get(event.key, None)

                self.button_handler(event)

    def display(self, matriz: np.array, change: bool) -> None:
        self._button_press()

        if (
            not np.array_equal(matriz, self.actual_frame)
            or self.last_change_state != change
        ):
            self.actual_frame = np.copy(matriz)
            self.last_change_state = change

            self.screen.fill((37, 37, 37))

            y = self.tam_space

            for j in range(self.y_max):
                x = self.tam_space

                for k in range(self.x_max):
                    color = matriz[j][k].copy()
                    if change:
                        if j in [0, self.y_max - 1] or k in [0, self.x_max - 1]:
                            color = (255, 255, 255)

                    pygame.draw.rect(
                        self.screen, color, ((x, y, self.tam_pixel, self.tam_pixel))
                    )

                    x += self.tam_pixel + self.tam_space
                y += self.tam_pixel + self.tam_space

            pygame.display.flip()

            if not self.running:
                pygame.quit()
