#!/usr/bin/env python3.7
# coding: utf-8

import pygame as pg
import numpy as np

import operator as op
import itertools
from functools import reduce
from pathlib import Path
import pickle
from typing import *

from .cell import *
from .neighborhood import *
from .types import *
from .utils import *
from .constants import *


class Program(Drawable):
    def __init__(self, cells: np.ndarray):
        self.cells = cells

    @staticmethod
    def empty(width: int, height: int) -> 'Program':
        cells = [[Empty() for _ in range(width)] for _ in range(height)]
        return Program(np.array(cells, Cell))

    @staticmethod
    def load(path: Path) -> 'Program':
        with Path(path).open('rb') as file:
            return pickle.load(file)

    @property
    def size(self):
        h, w = self.cells.shape
        return w, h

    def save(self, path: Path):
        with open(path, 'wb') as file:
            pickle.dump(self, file)

    def _all_coords(self) -> Iterable[Tuple[int, int]]:
        h, w = self.cells.shape
        yield from itertools.product(range(w), range(h))

    def in_bounds(self, x: int, y: int) -> bool:
        h, w = self.cells.shape
        return x in range(w) and y in range(h)

    def get_neighbors(self, x: int, y: int) -> Neighborhood:
        neighbors = Neighborhood()
        for direction, (nx, ny) in Neighborhood.around(x, y):
            if self.in_bounds(nx, ny):
                neighbors[direction] = self.cells[nx, ny]
        return neighbors

    def step(self):
        next_cells = self.cells.copy()

        for x, y in self._all_coords():
            neighbors = self.get_neighbors(x, y)
            next_cells[x, y] = self.cells[x, y].step(neighbors)

        self.cells = next_cells

    def draw(self, surface: pg.Surface):
        for x, y in self._all_coords():
            tile_rect = to_rect(x, y)
            tile_surface = surface.subsurface(tile_rect)
            neighbors = self.get_neighbors(x, y)
            self.cells[x, y].draw(tile_surface, neighbors)
