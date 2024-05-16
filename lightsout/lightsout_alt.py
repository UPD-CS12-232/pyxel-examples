# pyright: strict

from argparse import ArgumentParser
from dataclasses import dataclass
import random

import pyxel

import pyxelgrid as pg


TITLE = "Lights Out!"
DEFAULT_N = 8
DEFAULT_DIM = 40


@dataclass
class CellState:
    on: bool


class LightsOutGame(pg.PyxelGrid[CellState]):
    def __init__(self, n: int) -> None:
        self.win = False
        super().__init__(n, n, dim=DEFAULT_DIM)


    def init(self) -> None:
        pyxel.mouse(True)  # show mouse

        self.new_game()


    def update(self) -> None:

        # N = new game
        if pyxel.btnp(pyxel.KEY_N):
            self.new_game()

        if not self.win:
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                im, jm = self.mouse_cell()
                if self.in_bounds(im, jm):
                    self.move_on_cell(im, jm)

            # check win
            self._check_win()


    def _check_win(self) -> None:
        if not self.win:
            if all(not self[i, j].on for i in range(self.r) for j in range(self.c)):
                self.win = True


    def new_game(self) -> None:
        self.win = False

        # clear grid
        for i in range(self.r):
            for j in range(self.c):
                self[i, j] = CellState(on=False)

        # randomize
        for i in range(self.r):
            for j in range(self.c):
                if random.randrange(2):
                    # use move_on_cell instead of flip_cell so we're sure that the puzzle is solvable
                    self.move_on_cell(i, j)


    def move_on_cell(self, i: int, j: int) -> None:
        if not self.in_bounds(i, j):
            raise ValueError("Cannot move out of bounds")
        for di, dj in (0, 0), (0, +1), (0, -1), (+1, 0), (-1, 0):
            if self.in_bounds(ni := i + di, nj := j + dj):
                self.flip_cell(ni, nj)


    def flip_cell(self, i: int, j: int) -> None:
        if not self.in_bounds(i, j):
            raise ValueError("Cannot flip out of bounds")
        self[i, j].on = not self[i, j].on


    def draw_cell(self, i: int, j: int, x: int, y: int) -> None:
        # draw light
        if self[i, j].on:
            pyxel.rect(x + 1, y + 1, self.dim - 2, self.dim - 2, 11 if (i, j) == self.mouse_cell() else 6)
        else:
            pyxel.rectb(x + 1, y + 1, self.dim - 2, self.dim - 2, 3 if (i, j) == self.mouse_cell() else 1)


    def pre_draw_grid(self) -> None:
        # background color for the whole grid
        pyxel.cls(11 if self.win else 0)


def main():
    parser = ArgumentParser()

    parser.add_argument('-n', type=int, default=DEFAULT_N)

    args = parser.parse_args()

    LightsOutGame(args.n).run(title=TITLE)


if __name__ == '__main__':
    main()
