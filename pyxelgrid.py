# pyright: strict

"""A grid-based pyxel game class.

The standard usage involves subclassing `PyxelGrid` with a concrete class and overriding some of the
functions, e.g.,

.. highlight:: python
.. code-block:: python

    class MyGame(PyxelGrid[int]):

        def __init__(self):
            super().__init__(r=5, c=7, dim=10)  # 5 rows, 7 columns, cell side length 10 pixels

        def init(self) -> None:
            # called once at initialization time
            ...

        def update(self) -> None:
            # called every frame
            ...

        def draw_cell(self, i: int, j: int, x: int, y: int) -> None:
            # draws cell (i, j)
            ...

        def pre_draw_grid(self) -> None:
            # performs graphics drawing before the main grid is drawn
            # drawing the background image (e.g. via pyxel.cls) can be done here
            ...


        def post_draw_grid(self) -> None:
            # performs graphics drawing after the main grid is drawn
            ...

Note that no method is required to be overridden.

To run the game, call the `run()` method, e.g.,

.. highlight:: python
.. code-block:: python

    my_game = MyGame()

    # The keyword arguments are passed directly to pyxel.init
    my_game.run(title="My Game", fps=60)

The `run()` method automatically initializes `pyxel` for you, so you don't have to call `pyxel.init`
or `pyxel.run`.

The grid has `r` rows and `c` columns, and each cell of the grid is a square with a side
length of `dim` pixels. You can specify a "padding" on all four sides: `x_l` pixels to the
left, `x_r` pixels to the right, `y_u` pixels above, and `y_d` pixels below. (Every padding
defaults to 0.)

Individual cells are addressed by two coordinates `i` and `j`, representing the row and
column numbers, respectively. Row numbers start from the top, and column numbers start from
the right. These are both zero-indexed, so the top-left and bottom-right cells have
coordinates `(0, 0)` and `(r-1, c-1)`, respectively.

Each cell can hold a value or state, of (generic) type `T`. For example, `PyxelGrid[int]`
represents a grid of `int`s. Note that the cell's state must first be initialized before
using.

On drawing time, the `pre_draw_grid()` method is first called, then all cells are drawn individually
in row-major order, then finally the `post_draw_grid()` method is called.

By default, the grid is drawn as a single "layer". You can specify additional layers on top
of it by passing in `layerc` (which defaults to 0). Every layer is drawn one after the
other. The layers are drawn in increasing order (indexed `0` to `layerc - 1`) after the main grid.
Each layer is drawn in a similar way as the main grid; `pre_draw_layer()` is called, then the cells
are drawn in row-major order (via `draw_cell_layer()), then finally, `post_draw_layer()` is called.
"""

from itertools import product
from typing import Any, Final, Generic, TypeVar

import pyxel as pyx

_DIM: Final[int] = 8

T = TypeVar('T')

class PyxelGrid(Generic[T]):
    def __init__(self,
            r: int, c: int, *,
            dim: int = _DIM,
            x_l: int = 0,
            x_r: int = 0,
            y_u: int = 0,
            y_d: int = 0,
            layerc: int = 0):
        """Create a PyxelGrid instance which represents a Pyxel game that's inherently
        "grid-based"."""

        if not r > 0: raise ValueError(f"r must be positive; got {r=}")
        if not c > 0: raise ValueError(f"c must be positive; got {c=}")

        self._r = r
        self._c = c
        self._x_l = x_l
        self._x_r = x_r
        self._y_u = y_u
        self._y_d = y_d
        self._layerc = layerc
        self._dim = dim
        self._cell_state: dict[tuple[int, int], T] = {}
        super().__init__()

    @property
    def r(self) -> int:
        """The number of rows."""
        return self._r

    @property
    def c(self) -> int:
        """The number of columns."""
        return self._c

    @property
    def x_l(self) -> int:
        """The padding to the left, in pixels."""
        return self._x_l

    @property
    def x_r(self) -> int:
        """The padding to the right, in pixels."""
        return self._x_r

    @property
    def y_u(self) -> int:
        """The padding above, in pixels."""
        return self._y_u

    @property
    def y_d(self) -> int:
        """The padding below, in pixels."""
        return self._y_d

    @property
    def dim(self) -> int:
        """The side length of a grid cell, in pixels."""
        return self._dim

    @property
    def layerc(self) -> int:
        """The number of layers."""
        return self._layerc

    def run(self, **options: Any) -> None:
        """Initialize and run the game.

        This calls pyxel's `init` function and then `run` after that. Between those two calls,
        the `init()` method of the class is called. You should do your initialization in this
        method.
        """
        pyx.init(self.width, self.height, **options)
        self.init()
        pyx.run(self.update, self._draw)

    def in_bounds(self, i: int, j: int) -> bool:
        """Returns whether cell `(i, j)` is inside the grid or not."""
        return 0 <= i < self.r and 0 <= j < self.c

    def mouse_cell(self) -> tuple[int, int]:
        """Returns the coordinates of the cell 'containing' the mouse cursor.

        Note that the coordinates returned may be "outside" the grid; use the `in_bounds()` method
        to check whether the cell is inside the grid or not.
        """
        return (pyx.mouse_y - self.y_u) // self.dim, (pyx.mouse_x - self.x_l) // self.dim

    def check_in_bounds(self, i: int, j: int) -> None:
        """Raises an IndexError if cell `(i, j)` is outside the grid."""
        if not self.in_bounds(i, j):
            raise IndexError(f"Index out of bounds: {(i, j)}")

    def __getitem__(self, ij: tuple[int, int]) -> T:
        """Returns the "state" of cell `(i, j)`.

        This raises an `IndexError` if `(i, j)` is outside the grid or if its state hasn't been
        initialized yet.
        """
        self.check_in_bounds(*ij)
        if ij not in self._cell_state:
            raise IndexError(f"Cell {ij} is not yet initialized")
        return self._cell_state[ij]

    def pop(self, ij: tuple[int, int]) -> T:
        """Pops the "state" of cell `(i, j)`, returning it into an uninitialized state.

        This raises an `IndexError` if `(i, j)` is outside the grid or if its state hasn't been
        initialized yet.
        """
        self.check_in_bounds(*ij)
        if ij not in self._cell_state:
            raise IndexError(f"Cell {ij} is not yet initialized")
        return self._cell_state.pop(ij)

    def __setitem__(self, ij: tuple[int, int], state: T) -> None:
        """Sets the "state" of cell `(i, j)` to the given value.

        This raises an `IndexError` if `(i, j)` is outside the grid.
        """
        self.check_in_bounds(*ij)
        self._cell_state[ij] = state

    def y(self, i: int) -> int:
        """Converts the row index `i` into a y-coordinate value.

        Note that `i = 0` refers to the topmost boundary of the grid, while `i = r` refers to the
        bottommost boundary of the grid. This method takes into account the padding values; `y(0)`
        doesn't return the value `0` if the top padding is nonzero.
        """
        return i * self.dim + self.y_u

    def x(self, j: int) -> int:
        """Converts the column index `j` into a x-coordinate value.

        Note that `j = 0` refers to the leftmost boundary of the grid, while `j = c` refers to the
        rightmost boundary of the grid. This method takes into account the padding values; `y(0)`
        doesn't return the value `0` if the left padding is nonzero.
        """
        return j * self.dim + self.x_l

    @property
    def width(self) -> int:
        """Returns the intended width of the grid, in pyxels.

        This incorporates the padding values.
        """
        return round(self.x(self.c) + self.x_r)

    @property
    def height(self) -> int:
        """Returns the intended height of the grid, in pyxels.

        This incorporates the padding values.
        """
        return round(self.y(self.r) + self.y_d)

    def _draw_grid(self) -> None:
        for i, j in product(range(self.r), range(self.c)):
            self.draw_cell(i, j, self.x(j), self.y(i))

    def _draw_layer(self, layeri: int) -> None:
        for i, j in product(range(self.r), range(self.c)):
            self.draw_cell_layer(i, j, self.x(j), self.y(i), layeri)

    def _draw(self) -> None:
        """Draws the whole grid for a given frame.

        This is intended to be passed to `pyxel.run`.
        """
        self.pre_draw_grid()
        self._draw_grid()
        self.post_draw_grid()
        for layeri in range(self.layerc):
            self.pre_draw_layer(layeri)
            self._draw_layer(layeri)
            self.post_draw_layer(layeri)

    def init(self) -> None:
        """Initializes the game, before running it.

        This is automatically called by the `run()` method, after calling `pyxel.init` but before
        calling `pyxel.run`.

        This is intended to be overridden.
        """
        pass

    def update(self) -> None:
        """Updates the game state by one frame.

        This is intended to be passed to `pyxel.run`.

        This is intended to be overridden.
        """
        pass

    def draw_cell(self, i: int, j: int, x: int, y: int) -> None:
        """Draws cell `(i, j)` in the main grid.

        Its topleft corner pixel has coordinates (x, y).

        This is intended to be overridden.
        """
        pass

    def draw_cell_layer(self, i: int, j: int, x: int, y: int, layeri: int) -> None:
        """Draws cell `(i, j)` in layer `layeri`.

        This is intended to be overridden.
        """
        pass

    def pre_draw_grid(self) -> None:
        """Performs draw commands before drawing the main grid.

        This is intended to be overridden.
        """
        pass

    def post_draw_grid(self) -> None:
        """Performs draw commands after drawing the main grid.

        This is intended to be overridden.
        """
        pass

    def pre_draw_layer(self, layeri: int) -> None:
        """Performs draw commands before drawing the main grid for layer `layeri`.

        This is intended to be overridden.
        """
        pass

    def post_draw_layer(self, layeri: int) -> None:
        """Performs draw commands after drawing the main grid for layer `layeri`.

        This is intended to be overridden.
        """
        pass
