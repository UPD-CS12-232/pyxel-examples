# pyright: strict

from argparse import ArgumentParser
from math import cos, sin
from random import Random
from typing import Final

import pyxel

import pyxelgrid as pg


TITLE: Final[str] = "Lights Out"
DEFAULT_N: Final[int] = 8
DEFAULT_DIM: Final[int] = 40


class LightsOutGame(pg.PyxelGrid[bool]):
    def __init__(self, n: int) -> None:
        self.win = False
        self.rand = Random()
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
                    self.move(im, jm)

        self.check_win()


    def check_win(self) -> None:
        if not self.win:
            if all(not self[i, j] for i in range(self.r) for j in range(self.c)):
                self.win = True


    def new_game(self) -> None:
        self.win = False

        # clear grid
        for i in range(self.r):
            for j in range(self.c):
                self[i, j] = False

        # randomize
        for i in range(self.r):
            for j in range(self.c):
                if self.rand.randrange(2):
                    self.move(i, j)


    def move(self, i: int, j: int) -> None:
        if not self.in_bounds(i, j):
            raise ValueError("Cannot move out of bounds")
        for di, dj in (0, 0), (0, +1), (0, -1), (+1, 0), (-1, 0):
            if self.in_bounds(ni := i + di, nj := j + dj):
                self.flip(ni, nj)


    def flip(self, i: int, j: int) -> None:
        self[i, j] = not self[i, j]


    def draw_cell(self, i: int, j: int, x: int, y: int) -> None:
        # draw light
        if self[i, j]:
            pyxel.rect(x + 1, y + 1, self.dim - 2, self.dim - 2, 6)
        else:
            pyxel.rectb(x + 1, y + 1, self.dim - 2, self.dim - 2, 1)


    def pre_draw_grid(self) -> None:
        # background color
        pyxel.cls(0)


    def post_draw_grid(self) -> None:
        if self.win:
            th = pyxel.frame_count / 14
            x = self.width / 2 * (1 + 0.4 * cos(th)) - 18
            y = self.height / 2 * (1 + 0.4 * sin(th))
            pyxel.text(x, y, "YOU WIN!!", 11)


def main():
    parser = ArgumentParser()

    parser.add_argument('-n', type=int, default=DEFAULT_N)

    args = parser.parse_args()

    LightsOutGame(args.n).run(title=TITLE)


if __name__ == '__main__':
    main()
