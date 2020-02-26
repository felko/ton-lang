#!/usr/bin/env python3.7
# coding: utf-8

import pygame as pg

from typing import *

from .constants import *


def to_tile(x: int, y: int) -> Tuple[int, int]:
    return (x // CELL_SIZE, y // CELL_SIZE)


def to_pixels(x: int, y: int) -> Tuple[int, int]:
    return (x * CELL_SIZE, y * CELL_SIZE)


def to_rect(x: int, y: int) -> pg.Rect:
    return pg.Rect(to_pixels(x, y), (CELL_SIZE, CELL_SIZE))
