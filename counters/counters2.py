# pyright: strict

from typing import Final

import pyxel

import pyxelgrid as pg


TITLE: Final[str] = "Counter Grid"
FPS: Final[int] = 60
R: Final[int] = 5
C: Final[int] = 7
DIM: Final[int] = 11
PADDING: Final[int] = 10
BG: Final[int] = 0
BG_MOUSE: Final[int] = 14
FONT_W: Final[int] = 3
FONT_H: Final[int] = 5


class Counters(pg.PyxelGrid[int]):
    def __init__(self) -> None:
        super().__init__(R, C, x_l=PADDING, x_r=PADDING, y_u=PADDING, y_d=PADDING, dim=DIM)


    def init(self) -> None:
        pyxel.mouse(True)  # show mouse
        self.reset()


    def reset(self) -> None:
        # initialize everything to zero
        for i in range(self.r):
            for j in range(self.c):
                self[i, j] = 0


    def update(self) -> None:
        # R = reset
        if pyxel.btnp(pyxel.KEY_R):
            self.reset()

        # left click = increase
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            i, j = self.mouse_cell()
            self.update_counter(i, j, +1)

        # right click = decrease
        if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            i, j = self.mouse_cell()
            self.update_counter(i, j, -1)


    def update_counter(self, i: int, j: int, delta: int) -> None:
        if self.in_bounds(i, j):
            self[i, j] = (self[i, j] + delta) % 10


    def draw_cell(self, i: int, j: int, x: int, y: int) -> None:
        # Highlight the cell with the mouse
        if self.mouse_cell() == (i, j):
            pyxel.rectb(x, y, self.dim, self.dim, BG_MOUSE)

        # Draw the text
        # the extra terms are an attempt to "center" the text
        # this particular code only works for single digits I guess...
        pyxel.text(
                x + (self.dim - FONT_W) / 2,
                y + (self.dim - FONT_H) / 2,
                str(self[i, j]),
                self[i, j] + 1)


    def pre_draw_grid(self) -> None:
        pyxel.cls(BG)


def main():
    Counters().run(title=TITLE, fps=FPS)


if __name__ == '__main__':
    main()
