# pyright: strict

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum, auto
from itertools import islice, product
from math import hypot
from random import Random
from typing import Final

import pyxel

import pyxelgrid as pg


TITLE: Final[str] = "Maze"
R: Final[int] = 21
C: Final[int] = 31
DIM: Final[int] = 9
VIS: Final[int] = 7
HEAD: Final[int] = 20

Cell = tuple[int, int]


class CellType(Enum):
    PATH = auto()
    OBSTACLE = auto()
    EXIT = auto()


@dataclass
class State:
    cell_type: CellType
    seen: bool = False


class DisjointSets[T]:
    def __init__(self, objs: Iterable[T]):
        self.parent = {obj: obj for obj in objs}
        super().__init__()

    def __getitem__(self, i: T) -> T:
        if self.parent[i] == i:
            return i
        else:
            self.parent[i] = self[self.parent[i]]
            return self.parent[i]

    def union(self, i: T, j: T) -> bool:
        if (i := self[i]) == (j := self[j]): return False
        self.parent[i] = j
        return True


class MazeGame(pg.PyxelGrid[State]):
    def __init__(self) -> None:
        self.win = False
        self.solid = False
        self.loc = 0, 0
        self.rand = Random()
        super().__init__(R, C, y_u=HEAD, dim=DIM)


    def init(self) -> None:
        self.new_game()


    def update(self) -> None:

        # N = new game
        if pyxel.btnp(pyxel.KEY_N):
            self.new_game()

        if pyxel.btnp(pyxel.KEY_S):
            self.solid = not self.solid

        if not self.win:
            holdf = 8
            repeatf = 2
            if pyxel.btnp(pyxel.KEY_UP, hold=holdf, repeat=repeatf):
                self.try_move(-1, 0)
            if pyxel.btnp(pyxel.KEY_DOWN, hold=holdf, repeat=repeatf):
                self.try_move(+1, 0)
            if pyxel.btnp(pyxel.KEY_LEFT, hold=holdf, repeat=repeatf):
                self.try_move(0, -1)
            if pyxel.btnp(pyxel.KEY_RIGHT, hold=holdf, repeat=repeatf):
                self.try_move(0, +1)

        self.check_win()


    def try_move(self, di: int, dj: int) -> None:
        i, j = self.loc
        if self.in_bounds(ni := i + di, nj := j + dj):
            if self[ni, nj].cell_type != CellType.OBSTACLE:
                self.loc = ni, nj
                self.visit()


    def check_win(self) -> None:
        if not self.win:
            if self[self.loc].cell_type == CellType.EXIT:
                self.win = True


    def new_game(self) -> None:
        self.win = False


        # even indices are 'corners'
        corners = [(i, j) for i in range(0, self.r, 2) for j in range(0, self.c, 2)]

        def generate_loc_end_pairs():
            while True:
                loc = li, lj = self.rand.choice(corners)
                end = ei, ej = self.rand.choice(corners)
                if loc != end:
                    yield abs(li - ei) + abs(lj - ej), loc, end

        _, self.loc, end = max(islice(generate_loc_end_pairs(), 3))


        # clear grid
        for i in range(self.r):
            for j in range(self.c):
                self[i, j] = State(CellType.OBSTACLE)
        for i, j in corners:
            self[i, j].cell_type = CellType.PATH
        self[end].cell_type = CellType.EXIT


        # generate random maze
        components = DisjointSets(corners)

        def edgeseq() -> Iterable[tuple[Cell, Cell, Cell]]:
            for i1, j1 in corners:
                for di, dj in (+1, 0), (0, +1):
                    im, jm = i1 + di, j1 + dj
                    i2, j2 = im + di, jm + dj
                    if self.in_bounds(i2, j2):
                        yield (i1, j1), (i2, j2), (im, jm)

        edges = [*edgeseq()]
        self.rand.shuffle(edges)
        for x, y, mid in edges:
            assert self[mid].cell_type == CellType.OBSTACLE
            if components.union(x, y):
                self[mid].cell_type = CellType.PATH


        # visit initial cell
        self.visit()


    def visit(self) -> None:
        i, j = self.loc
        for di, dj in product(range(-VIS, VIS + 1), repeat=2):
            if hypot(di, dj) <= VIS:
                if self.in_bounds(ni := i + di, nj := j + dj):
                    self[ni, nj].seen = True


    def draw_clouds(self, x: int, y: int) -> None:
        cloud_res = 3
        for dx, dy in product(range(cloud_res), repeat=2):
            cx = x + dx * self.dim / cloud_res
            cy = y + dy * self.dim / cloud_res
            color = 1 if pyxel.noise(cx / 4 / self.dim, cy / 4 / self.dim, pyxel.frame_count / 80) >= 0.1 else 0
            pyxel.rect(cx, cy, self.dim / cloud_res, self.dim / cloud_res, color)


    def draw_cell(self, i: int, j: int, x: int, y: int) -> None:
        if self[i, j].seen:
            match self[i, j].cell_type:
                case CellType.PATH:
                    pyxel.rect(x, y, self.dim, self.dim, 3)

                case CellType.OBSTACLE:
                    if self.solid:
                        pyxel.rect(x, y, self.dim, self.dim, 4)
                    else:
                        self.draw_clouds(x, y)

                case CellType.EXIT:
                    pyxel.rect(x, y, self.dim, self.dim, 3)
                    w = 3
                    col = 11
                    pyxel.rect(x + (self.dim - w) / 2, y, w, self.dim, col)
                    pyxel.rect(x, y + (self.dim - w) / 2, self.dim, w, col)
        
        else:
            self.draw_clouds(x, y)

        if (i, j) == self.loc:
            pyxel.circ(x + self.dim / 2, y + self.dim / 2, self.dim / 4, 5)


    def pre_draw_grid(self) -> None:
        # background color
        pyxel.cls(0)


    def post_draw_grid(self) -> None:
        if self.win:
            pyxel.text(2, 2, "WIN!!!", 11)

        pyxel.text(2, 11, "CONTROLS: N, S, ARROW KEYS", 3)


def main():
    MazeGame().run(title=TITLE)


if __name__ == '__main__':
    main()
