"""
Snake AI — Heatmap Dot Consumer.
DEV     : Gabriel Rocha de Souza
PROJECT : ledMatrix
"""

import random
from typing import Callable
from typing import cast
from typing import TypeVar

import numpy as np

from utils.log import log


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

type Color = tuple[int, int, int]
type Coord = tuple[int, int]
type GridCoord = list[int]  # [j, k]

F = TypeVar("F", bound=Callable)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_INITIAL_POS: list[GridCoord] = [[0, 0], [1, 0], [2, 0], [3, 0]]

_DIRECTION_MAP: dict[str, tuple[int, int]] = {
    "w": (0, -1),
    "a": (1, -1),
    "s": (0, 1),
    "d": (1, 1),
}

_ALL_DIRECTIONS: list[str] = ["w", "a", "s", "d"]


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


def _requires_matrix(method: F) -> F:
    """Guard: skips execution if main_mat has not been populated yet."""

    def wrapper(self: "snake", *args, **kwargs):
        if self.main_mat.size == 0:
            log.warning(f"[snake] '{method.__name__}' called before convert_matrix().")
            return
        return method(self, *args, **kwargs)

    return cast(F, wrapper)


# ---------------------------------------------------------------------------
# Snake
# ---------------------------------------------------------------------------


class snake:
    """
    Greedy snake AI that navigates a downscaled boolean grid, consuming
    lit pixels (value == 1) and erasing them from the source image matrix.

    The snake operates on a grid that is half the resolution of the display
    matrix — each snake cell maps to a 2×2 block of display pixels.

    Parameters
    ----------
    color:
        RGB color used to paint the snake body on the display matrix.
    """

    def __init__(self, color: Color) -> None:
        self.color: Color = color
        self.actual_target: Coord = (0, 0)

        self.initial_pos: list[GridCoord] = [list(p) for p in _INITIAL_POS]
        self.pos: list[GridCoord] = list(self.initial_pos)

        self.main_mat: np.ndarray = np.array([[]])
        self.main_image_matrix: np.ndarray | None = None

        self.original_main_mat: np.ndarray | None = None
        self.original_image_matrix: np.ndarray | None = None

    # ------------------------------------------------------------------
    # Public API — setup
    # ------------------------------------------------------------------

    def convert_matrix(self, matrix: np.ndarray) -> None:
        """
        Derive a downscaled boolean grid from a full-resolution RGB *matrix*.

        Each 2×2 block is collapsed to a single cell: the cell is ``1`` if
        any pixel in the block is non-zero, ``0`` otherwise.
        """
        self.main_image_matrix = matrix
        self.original_image_matrix = matrix.copy()

        matrix_2d = matrix.any(axis=2)
        j_total, k_total = matrix_2d.shape
        new_j: int = j_total // 2
        new_k: int = k_total // 2

        matrix_trunc = matrix_2d[0 : new_j * 2, 0 : new_k * 2]
        matrix_blocked = matrix_trunc.reshape(new_j, 2, new_k, 2).transpose(0, 2, 1, 3)
        matrix_final = matrix_blocked.any(axis=(2, 3))

        self.original_main_mat = matrix_final.astype(int)
        self.main_mat = (
            self.original_main_mat.copy()
            if self.original_main_mat is not None
            else np.array([[]])
        )

    def reset_cycle(self) -> None:
        """Restore the snake and the grid to their initial state."""
        self.pos = list(self.initial_pos)

        if self.original_main_mat is not None:
            self.main_mat = self.original_main_mat.copy()

        if (
            self.original_image_matrix is not None
            and self.main_image_matrix is not None
        ):
            np.copyto(self.main_image_matrix, self.original_image_matrix)

        self.choose_target()

    # ------------------------------------------------------------------
    # Public API — per-frame
    # ------------------------------------------------------------------

    @_requires_matrix
    def choose_target(self) -> None:
        """Pick a random lit cell as the next target."""
        indices_j, indices_k = np.where(self.main_mat == 1)

        if len(indices_j) == 0:
            log.info("Snake cleared the table.")
            self.actual_target = (0, 0)
            return

        coord = list(zip(indices_j, indices_k))
        chosen_small_coord = random.choice(coord)
        self.actual_target = (chosen_small_coord[0] * 2, chosen_small_coord[1] * 2)

    @_requires_matrix
    def go_for_target(self) -> None:
        """
        Advance the snake one step toward :attr:`actual_target`.

        Priority: axis with the larger delta first.
        Fallback: try all remaining directions in random order.
        When the snake reaches a lit cell, it consumes it and picks a new target.
        """
        head_small = self.pos[-1]
        target_small = (self.actual_target[0] // 2, self.actual_target[1] // 2)

        delta_j = target_small[0] - head_small[0]
        delta_k = target_small[1] - head_small[1]

        # Re-acquire target if the current one was already consumed.
        try:
            target_exists = self.main_mat[target_small[0], target_small[1]] == 1
        except IndexError:
            target_exists = False

        if not target_exists and delta_j == 0 and delta_k == 0:
            self.choose_target()
            target_small = (self.actual_target[0] // 2, self.actual_target[1] // 2)
            delta_j = target_small[0] - head_small[0]
            delta_k = target_small[1] - head_small[1]

        # Primary direction.
        if abs(delta_j) > abs(delta_k):
            direction = "s" if delta_j > 0 else "w"
        elif abs(delta_k) > 0:
            direction = "d" if delta_k > 0 else "a"
        else:
            if self.actual_target == (0, 0) and head_small == [0, 0]:
                log.info("Snake finished — resetting cycle.")
                self.reset_cycle()
                return
            direction = random.choice(_ALL_DIRECTIONS)

        # Attempt primary move, then fallbacks.
        if not self.move(direction):
            fallbacks = [d for d in _ALL_DIRECTIONS if d != direction]
            random.shuffle(fallbacks)

            for alt_direction in fallbacks:
                if self.move(alt_direction):
                    break
            else:
                return  # completely stuck

        # Consume the cell if the new head landed on a lit pixel.
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

    def put_head(self, base: np.ndarray) -> np.ndarray:
        """Paint every snake segment as a 2×2 block onto *base*."""
        for coord_position in self.pos:
            pos_j = int(coord_position[0]) * 2
            pos_k = int(coord_position[1]) * 2

            base[pos_j, pos_k] = self.color
            base[pos_j, pos_k + 1] = self.color
            base[pos_j + 1, pos_k] = self.color
            base[pos_j + 1, pos_k + 1] = self.color

        return base

    # ------------------------------------------------------------------
    # Internal — movement
    # ------------------------------------------------------------------

    def move(self, direction: str) -> bool:
        """
        Attempt to extend the snake in *direction*.

        Returns True on success, False if the move is out-of-bounds or
        would collide with the snake's own body.
        """
        if direction not in _DIRECTION_MAP:
            return False

        axis, change = _DIRECTION_MAP[direction]

        current_head = self.pos[-1]
        new_head = list(current_head)
        new_head[axis] += change

        max_j, max_k = self.main_mat.shape
        if not (0 <= new_head[0] < max_j and 0 <= new_head[1] < max_k):
            return False

        if new_head in self.pos:
            return False

        self.pos.append(new_head)
        return True

    def remove_tail(self) -> None:
        """Drop the oldest segment of the snake body."""
        if len(self.pos) > 1:
            self.pos.pop(0)
