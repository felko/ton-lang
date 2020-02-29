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


def load_tile_image(path):
    img = pg.image.load(str(path)).convert_alpha()
    return pg.transform.scale(img, (CELL_SIZE, CELL_SIZE))


# https://nerdparadise.com/programming/pygameblitopacity
def blit_alpha(target, source, location, opacity):
        x = location[0]
        y = location[1]
        temp = pg.Surface((source.get_width(), source.get_height())).convert()
        temp.blit(target, (-x, -y))
        temp.blit(source, (0, 0))
        temp.set_alpha(int(opacity * 255))
        target.blit(temp, location)
