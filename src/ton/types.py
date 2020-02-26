#!/usr/bin/env python3.7
# coding: utf-8

import pygame as pg

from enum import *
from abc import *


class Rotation(IntEnum):
    R0 = 0
    R90 = 90
    R180 = 180
    R270 = 270

    def __add__(self, other):
        return Rotation((self.value + other.value) % 360)

    def __sub__(self, other):
        return Rotatin((self.value - other.value) % 360)

    def __neg__(self):
        return self + Rotation.R180


class Direction(IntEnum):
    N = auto()
    S = auto()
    E = auto()
    W = auto()

    def rotate(self, rotation: Rotation) -> 'Direction':
        return Direction((Rotation(self.value * 90) + rotation).value // 90)

    def opposite(self) -> 'Direction':
        return self.rotate(Rotation.R180)


class Connex(IntFlag):
    N = auto()
    S = auto()
    E = auto()
    W = auto()

    @staticmethod
    def from_direction(direction: Direction) -> 'Connex':
        return Connex[direction.name]


class Drawable(ABC):
    @abstractmethod
    def draw(self, surface: pg.Surface):
        raise NotImplementedError
