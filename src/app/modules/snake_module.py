import os
import random

import numpy as np

from utils import cfg
from utils.log import log


class snake:
    def __init__(self, color: tuple[int, int, int]) -> None:
        self.color: tuple[int, int, int] = color
        self.actual_target: tuple[int, int] = (0, 0)

        self.initial_pos: list[list[int, int]] = [[0, 0], [1, 0], [2, 0], [3, 0]]
        self.pos: list[list[int, int]] = list(self.initial_pos)

        self.main_mat: np.ndarray = np.array([[]])
        self.main_image_matrix: np.ndarray | None = None

        self.original_main_mat: np.ndarray | None = None
        self.original_image_matrix: np.ndarray | None = None

    def reset_cycle(self) -> None:
        self.pos = list(self.initial_pos)

        if self.original_main_mat is not None:
            self.main_mat = self.original_main_mat.copy()

        if (
            self.original_image_matrix is not None
            and self.main_image_matrix is not None
        ):
            np.copyto(self.main_image_matrix, self.original_image_matrix)

        self.choose_target()

    def convert_matrix(self, matrix: np.ndarray) -> None:
        self.main_image_matrix = matrix
        self.original_image_matrix = matrix.copy()

        matrix_2d: np.array = matrix.any(axis=2)
        j_total, k_total = matrix_2d.shape
        new_j: int = j_total // 2
        new_k: int = k_total // 2
        matrix_trunc = matrix_2d[0 : new_j * 2, 0 : new_k * 2]
        matrix_blocked = matrix_trunc.reshape(new_j, 2, new_k, 2).transpose(0, 2, 1, 3)
        matrix_final = matrix_blocked.any(axis=(2, 3))

        self.original_main_mat = matrix_final.astype(int)
        self.main_mat = self.original_main_mat.copy()

    def choose_target(self) -> None:
        indices_j, indices_k = np.where(self.main_mat == 1)

        if len(indices_j) == 0:
            log.info("snake cleaned table")
            self.actual_target = (0, 0)
            return

        coord = list(zip(indices_j, indices_k))
        chosen_small_coord = random.choice(coord)
        self.actual_target = (chosen_small_coord[0] * 2, chosen_small_coord[1] * 2)

    def put_head(self, base: np.array) -> np.array:
        for coord_position in self.pos:
            pos_j = int(coord_position[0]) * 2
            pos_k = int(coord_position[1]) * 2

            base[pos_j + 0, pos_k + 0] = self.color
            base[pos_j + 0, pos_k + 1] = self.color
            base[pos_j + 1, pos_k + 0] = self.color
            base[pos_j + 1, pos_k + 1] = self.color
        return base

    def remove_tail(self) -> None:
        if len(self.pos) > 1:
            self.pos.pop(0)

    def move(self, direction: str) -> bool:
        direction_map = {"w": (0, -1), "a": (1, -1), "s": (0, 1), "d": (1, 1)}

        if direction not in direction_map:
            return False

        axis, change = direction_map[direction]

        current_head = self.pos[-1]
        new_head = list(current_head)
        new_head[axis] += change

        max_j, max_k = self.main_mat.shape
        if not (0 <= new_head[0] < max_j and 0 <= new_head[1] < max_k):
            return False

        for segment in self.pos:
            if segment == new_head:
                return False

        self.pos.append(new_head)
        return True

    def go_for_target(self) -> None:
        head_small = self.pos[-1]
        target_small = (self.actual_target[0] // 2, self.actual_target[1] // 2)

        delta_j = target_small[0] - head_small[0]
        delta_k = target_small[1] - head_small[1]

        direction = ""

        try:
            target_exists = self.main_mat[target_small[0], target_small[1]] == 1
        except IndexError:
            target_exists = False

        if not target_exists and (delta_j == 0 and delta_k == 0):
            self.choose_target()
            target_small = (self.actual_target[0] // 2, self.actual_target[1] // 2)
            delta_j = target_small[0] - head_small[0]
            delta_k = target_small[1] - head_small[1]

        if abs(delta_j) > abs(delta_k):
            direction = "s" if delta_j > 0 else "w"
        elif abs(delta_k) > 0:
            direction = "d" if delta_k > 0 else "a"
        else:
            if self.actual_target == (0, 0) and head_small == [0, 0]:
                log.info("reset_cycle")
                self.reset_cycle()
                return
            direction = random.choice(["w", "a", "s", "d"])

        move_successful = self.move(direction)

        if not move_successful:
            all_directions = ["w", "a", "s", "d"]
            if direction in all_directions:
                all_directions.remove(direction)
            random.shuffle(all_directions)

            for alt_direction in all_directions:
                move_successful = self.move(alt_direction)
                if move_successful:
                    break

        if not move_successful:
            return
        new_head = self.pos[-1]

        try:
            if self.main_mat[new_head[0], new_head[1]] == 1:
                self.main_mat[new_head[0], new_head[1]] = 0

                if self.main_image_matrix is not None:
                    j_grande = new_head[0] * 2
                    k_grande = new_head[1] * 2
                    self.main_image_matrix[
                        j_grande : j_grande + 2, k_grande : k_grande + 2
                    ] = (0, 0, 0)

                self.choose_target()
        except IndexError:
            pass

        self.remove_tail()
