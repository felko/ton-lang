#!/usr/bin/env python3.7
# coding: utf-8

__all__ = [
    'Cell',
    'Empty',
    'Wire'
]

import pygame as pg
import numpy as np

import copy
from abc import *

from .texture import *
from .neighborhood import *
from .types import *


class Cell(Drawable):
    texture: Texture

    @abstractmethod
    def step(self, neighborhood: Neighborhood) -> 'Cell':
        raise NotImplementedError

    def on_create(self, neighbors: Neighborhood):
        pass

    def on_click(self):
        pass

    def copy(self) -> 'Cell':
        return copy.copy(self)

    @abstractmethod
    def draw(self, surface: pg.Surface, neighbors: Neighborhood):
        raise NotImplementedError


class Empty(Cell):
    texture = SimpleTexture(pg.Surface((CELL_SIZE, CELL_SIZE)))

    def step(self, neighbors: Neighborhood) -> Cell:
        return self

    def draw(self, surface: pg.Surface, neighbors: Neighborhood):
        self.texture.draw(surface)


class Wire(Cell):
    texture = ConnexTexture.load('wire')

    def step(self, neighbors: Neighborhood) -> Cell:
        return self

    def draw(self, surface: pg.Surface, neighbors: Neighborhood):
        neighboring_wires = neighbors.filter(lambda cell: isinstance(cell, Wire))
        self.texture.draw(surface, neighboring_wires.get_connex())
