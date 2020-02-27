#!/usr/bin/env python3.7
# coding: utf-8

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

    def get_pins(self) -> Set[Direction]:
        return set()

    def copy(self) -> 'Cell':
        return copy.copy(self)

    @abstractmethod
    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        raise NotImplementedError


class Empty(Cell):
    def step(self, neighbors: Neighborhood) -> Cell:
        return self

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        pass


class Wire(Cell):
    texture = ConnexTexture.load('wire')

    def step(self, neighbors: Neighborhood) -> Cell:
        return self

    def get_pins(self) -> Set[Direction]:
        return set(Direction)

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        has_pin = lambda direction, cell: direction.opposite() in cell.get_pins()
        neighboring_wires = neighbors.filter(has_pin)
        self.texture.draw(surface, neighboring_wires.get_connex(), opacity)


class Directional(Cell):
    def __init__(self, direction: Direction = Direction.N):
        self.direction = direction

    def rotate(self, rotation: Rotation):
        self.direction = self.direction.rotated(rotation)



class Processor(Directional):
    def __init__(self, direction: Direction, inputs: Dict[Side, Tuple[str, type]]):
        super().__init__(direction)
        self.inputs = inputs
        self.arguments = {}

    @abstractclassmethod
    def process(cls, **kwargs):
        raise NotImplementedError

    def get_pins(self) -> Set[Direction]:
        return set(Direction)

    def get_input_name_towards(self, direction: Direction) -> str:
        return self.inputs[self.direction.side_relative_to(direction)][0]

    def is_fed(self) -> bool:
        return all(param in self.argments for param in self.inputs.values())

    def is_waiting_for(self, direction: Direction) -> bool:
        return self.get_input_name_towards(direction) in self.arguments

    def step(self, neighbors: Neighborhood) -> Cell:
        if self.fed():
            return self.process(**self.arguments)
        else:
            for direction, cell in neighbors:
                if direction in self.inputs:
                    name, type_ = self.inputs[self.direction.side_relative_to(direction)]
                    if isinstance(cell, type_):
                        self.arguments[name] = cell
            return self


class Adder(Processor):
    texture = RotatableTexture.load('adder')

    def __init__(self, direction: Direction = Direction.N):
        super().__init__(
            direction,
            inputs={Side.LEFT: ('x', Integer), Side.RIGHT: ('y', Integer)},
        )

    @classmethod
    def process(cls, x, y):
        return Integer(x.value + y.value)
    
    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        self.texture.draw(surface, self.direction.relative_rotation_to(Direction.N), opacity)


class Value(Cell):
    def step(self, neighbors: Neighborhood) -> Cell:
        processors = neighbors.filter(lambda _, cell: isinstance(cell, Processor))

        for direction, processor in processors:
            if processor.is_waiting_for(direction.opposite()):
                return self

        return Empty()


class Integer(Value):
    font = pg.font.Font(str(ASSETS_DIR / 'Oxanium-ExtraBold.ttf'), 10)

    def __init__(self, value: int = 0):
        self.value = value

    def get_pins(self) -> Set[Direction]:
        return set(Direction)

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        texture = self.font.render(str(self.value), True, (0, 0, 0))
        texture.set_alpha(opacity)
        surface.blit(texture, (CELL_SIZE, CELL_SIZE))
