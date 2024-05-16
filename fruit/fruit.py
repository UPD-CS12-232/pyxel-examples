# pyright: strict

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from itertools import islice, product
from random import Random
from typing import Final

import pyxel

import pyxelgrid as pg


TITLE: Final[str] = "Fruit"
FRUIT_RESOURCE_FILE: Final[str] = "fruit.pyxres"
FPS: Final[int] = 60

# grid size

R: Final[int] = 10
C: Final[int] = 20

# dimensions

DIM: Final[int] = 16
IPADDING: Final[int] = 3
PADDING: Final[int] = 18
HEAD: Final[int] = 5
FOOT: Final[int] = 25


# colors

COLOR_OUTLINE: Final[int] = 5
COLOR_TEXT_INFO: Final[int] = 1
COLOR_TEXT_GAME_OVER: Final[int] = 8
COLOR_HP_BAR: Final[int] = 3

COLOR_BG: Final[int] = 0
COLOR_BG_GAMEOVER: Final[int] = 0
COLOR_BG_MOUSE: Final[int] = 14

COLOR_RESOURCE_TRANSPARENT: Final[int] = 0


# HP details

HP_INIT: Final[int] = 100
HP_DEC: Final[int] = 6
HP_DENOM: Final[int] = 1000

DHP_ROTTEN_MUL: Final[int] = -10
DHP_MUL: Final[int] = 5
DHP_BASE_GOOD: Final[int] = 3
DHP_BASE: Final[int] = 1


# SFX details

SFX_GOOD: Final[int] = 0
SFX_BAD: Final[int] = 1
SFX_VGOOD: Final[int] = 4
SFX_VBAD: Final[int] = 5
SFX_NEUTRAL: Final[int] = 3
SFX_GAME_OVER: Final[int] = 2

SFX_CH_GOOD: Final[int] = 0
SFX_CH_BAD: Final[int] = 1
SFX_CH_GAME_OVER: Final[int] = 2


def shuffled[T](rand: Random, seq: Iterable[T]) -> list[T]:
    seql = list(seq)
    rand.shuffle(seql)
    return seql


def frame_wait_for_frame(framec: int) -> int:
    assert framec >= 0
    base = int(round(FPS / 5 * 6 * max(1 / 4.5, 90 / 60 * 1.25 / (1.7 * framec / FPS / 60 + 1.25))))
    return base - max(0, min(11, int(framec / FPS / 60) - 4))

assert frame_wait_for_frame(10**18) >= 5


class FruitType(Enum):
    MANGO = 0
    BANANA = 1
    APPLE = 2

@dataclass(frozen=True)
class Fruit:
    fruit_type: FruitType
    rotten: bool = False


GREAT_FRUIT_TYPES: Final[frozenset[FruitType]] = frozenset({FruitType.APPLE})


class FruitGame(pg.PyxelGrid[Fruit | None]):
    def __init__(self) -> None:
        self.rand = Random()
        super().__init__(R, C,
            x_l=PADDING,
            x_r=PADDING,
            y_u=PADDING + HEAD + IPADDING,
            y_d=IPADDING + FOOT + PADDING,
            dim=DIM)


    def init(self) -> None:
        pyxel.mouse(True)  # show mouse
        pyxel.load(FRUIT_RESOURCE_FILE)

        self.new_game()


    def update(self) -> None:

        # N = new game
        if pyxel.btnp(pyxel.KEY_N):
            self.new_game()

        # game logic
        if not self.game_over:
            self.game_logic_update()


    def game_logic_update(self) -> None:
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            im, jm = self.mouse_cell()
            self.consume(im, jm)

        # decrement HP if wait time over
        if self.frame_since_last() >= self.frame_wait:
            self.dec_hp()

        # game over condition
        if self.hp <= 0:
            if not self.game_over:
                pyxel.play(SFX_CH_GAME_OVER, SFX_GAME_OVER)
            self.game_over = True


    def frame_since_last(self) -> int:
        return pyxel.frame_count - self.frame_last


    def frame_since_start(self) -> int:
        return pyxel.frame_count - self.frame_start


    def new_game(self) -> None:
        self.frame_start = pyxel.frame_count
        self.score = 0
        self.game_over = False
        self.hp = HP_INIT
        self.update_wait()
        self.distribute_fruits()


    def update_wait(self) -> None:
        self.frame_last = pyxel.frame_count
        self.frame_wait = frame_wait_for_frame(self.frame_since_start())


    def dec_hp(self) -> None:
        self.update_wait()
        self.hp -= HP_DEC


    def distribute_fruits(self) -> None:

        cells = [(i, j) for i in range(self.r) for j in range(self.c)]

        # clear all cells
        for i, j in cells:
            self[i, j] = None

        # distribute fruits to random cells
        scells = iter(shuffled(self.rand, cells))
        for i, j in islice(scells, 4): self[i, j] = Fruit(FruitType.MANGO)
        for i, j in islice(scells, 4): self[i, j] = Fruit(FruitType.BANANA)
        for i, j in islice(scells, 1): self[i, j] = Fruit(FruitType.APPLE)
        for i, j in islice(scells, 3): self[i, j] = Fruit(FruitType.MANGO, rotten=True)
        for i, j in islice(scells, 3): self[i, j] = Fruit(FruitType.BANANA, rotten=True)
        for i, j in islice(scells, 1): self[i, j] = Fruit(FruitType.APPLE, rotten=True)


    def consume(self, ic: int, jc: int) -> None:
        # consume the 3x3 grid centered at (ic, jc)
        ate = False
        vgood = False
        good = False
        bad = False
        vbad = False
        for di, dj in product((-1, 0, +1), repeat=2):
            if self.in_bounds(i := ic + di, j := jc + dj) and (fruit := self[i, j]):
                great = fruit.fruit_type in GREAT_FRUIT_TYPES
                base = DHP_BASE_GOOD if great else DHP_BASE
                mult = DHP_ROTTEN_MUL if fruit.rotten else DHP_MUL
                delta = base * mult
                self.score += max(delta, 0)
                self.hp += delta

                ate = True
                if delta > 0:
                    if great:
                        vgood = True
                    else:
                        good = True
                else:
                    if great:
                        vbad = True
                    else:
                        bad = True

        # play sound
        if vgood or good:
            pyxel.play(SFX_CH_GOOD, SFX_VGOOD if vgood else SFX_GOOD)
        if vbad or bad:
            pyxel.play(SFX_CH_BAD, SFX_VBAD if vbad else SFX_BAD)
        if not ate:
            pyxel.play(SFX_CH_GOOD, SFX_NEUTRAL)

        # redistribute fruits
        if ate:
            self.distribute_fruits()


    def draw_cell(self, i: int, j: int, x: int, y: int) -> None:
        # Highlight the cell if near the mouse
        if not self.game_over:
            im, jm = self.mouse_cell()
            if max(abs(im - i), abs(jm - j)) <= 1:
                pyxel.blt(x, y, 0, 0, self.dim * 2, self.dim, self.dim, COLOR_RESOURCE_TRANSPARENT)

        # draw fruit
        if fruit := self[i, j]:
            pyxel.blt(x, y, 0, self.dim * fruit.fruit_type.value, self.dim * fruit.rotten, self.dim, self.dim, COLOR_RESOURCE_TRANSPARENT)


    def pre_draw_grid(self) -> None:
        # background color
        pyxel.cls(COLOR_BG_GAMEOVER if self.game_over else COLOR_BG)

        # outline
        opad = 2
        pyxel.rectb(
            self.x_l - opad,
            self.y_u - opad,
            self.dim * self.c + opad * 2,
            self.dim * self.r + opad * 2,
            COLOR_OUTLINE)


    def post_draw_grid(self) -> None:

        # timer
        pyxel.text(PADDING, PADDING, str(self.score), COLOR_TEXT_INFO)

        # controls
        pyxel.text(self.x_l + self.c * self.dim * 2 / 3, PADDING, "N = NEW GAME", COLOR_TEXT_INFO)

        # game-over text
        if self.game_over:
            pyxel.text(self.x_l + self.c * self.dim / 3, PADDING, "GAME OVER!", COLOR_TEXT_GAME_OVER)

        # HP bar
        frac = max(0, min(1, self.hp / HP_DENOM))
        pyxel.rect(PADDING, self.y(self.r) + IPADDING, frac * self.dim * self.c, FOOT, COLOR_HP_BAR)


def main():
    FruitGame().run(title=TITLE, fps=FPS)


if __name__ == '__main__':
    main()
