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
        return Rotation((self.value - other.value) % 360)

    def __neg__(self):
        return self + Rotation.R180

class Direction(IntEnum):
    N = auto()
    S = auto()
    E = auto()
    W = auto()

    def side_relative_to(self, other: 'Direction') -> 'Side':
        if self == other:
            return Side.FRONT
        elif self.opposite() == other:
            return Side.BACK
        elif self.rotated(Rotation.R90) == other:
            return Side.RIGHT
        else:
            return Side.LEFT

    def relative_rotation_to(self, other: 'Direction') -> Rotation:
        relative_to_north = {
            Direction.N: Rotation.R0,
            Direction.S: Rotation.R180,
            Direction.E: Rotation.R270,
            Direction.W: Rotation.R90
        }

        return relative_to_north[self] - relative_to_north[other]

    @staticmethod
    def from_rotation_to(rotation: Rotation, direction: 'Direction') -> 'Direction':
        relative_to_north = {
            Rotation.R0: Direction.N,
            Rotation.R90: Direction.W,
            Rotation.R180: Direction.S,
            Rotation.R270: Direction.E
        }

        return relative_to_north[rotation - direction.relative_rotation_to(Direction.N)]

    def rotated(self, rotation: Rotation) -> 'Direction':
        return Direction.from_rotation_to(rotation + self.relative_rotation_to(Direction.N), Direction.N)


    def opposite(self) -> 'Direction':
        return self.rotated(Rotation.R180)


class Side(IntEnum):
    FRONT = auto()
    LEFT = auto()
    BACK = auto()
    RIGHT = auto()

    def relative_to(self, direction: Direction) -> Direction:
        return {

        }[self]


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
    def draw(self, surface: pg.Surface, *args, **kwargs):
        raise NotImplementedError
