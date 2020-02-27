#!/usr/bin/env python3.7
# coding: utf-8

import operator as op
from functools import reduce
from typing import *

from .types import *


class Neighborhood:
    def __init__(self, cells: Dict[Direction, 'Cell'] = None):
        cells = cells or {}
        self.cells = {
            direction: cells.get(direction, None)
            for direction in Direction
        }

    def filter(self, predicate: Callable[[Direction, 'Cell'], bool]):
        cells = {}
        for direction, cell in self.cells.items():
            if cell is not None and predicate(direction, cell):
                cells[direction] = cell
            else:
                cells[direction] = None

        return Neighborhood(cells)

    def __iter__(self) -> Iterable[Tuple[Direction, 'Cell']]:
        for direction, cell in self.cells.items():
            if cell is not None:
                yield direction, cell

    def cells(self) -> Iterable['Cell']:
        for cell in self.cells.values():
            if cell is not None:
                yield cell

    def directions(self) -> Iterable[Direction]:
        for direction, cell in self:
            if cell is not None:
                yield direction

    def get_connex(self) -> Connex:
        return reduce(
            op.or_,
            map(Connex.from_direction, self.directions()),
            Connex(0)
        )

    def __getitem__(self, direction: Direction) -> 'Cell':
        return self.cells[direction]

    def __setitem__(self, direction: Direction, cell: 'Cell'):
        self.cells[direction] = cell

    @staticmethod
    def around(x, y):
        yield Direction.N, (x, y-1)
        yield Direction.S, (x, y+1)
        yield Direction.E, (x+1, y)
        yield Direction.W, (x-1, y)
