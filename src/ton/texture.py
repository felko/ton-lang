#!/usr/bin/env python3.7
# coding: utf-8

import pygame as pg

from abc import *
from typing import *
from pathlib import Path

from .types import *
from .utils import *
from .constants import *


class Texture(Drawable):
    @abstractstaticmethod
    def load(name: str) -> 'Texture':
        raise NotImplementedError


class SimpleTexture(Texture):
    def __init__(self, texture: pg.Surface):
        self.texture = texture

    @classmethod
    def load(cls, name: str) -> Texture:
        path = str(ASSETS_DIR / (name + '.png'))
        return cls(_load_tile_image(ASSETS_DIR / (name + '.png')))

    def draw(self, surface: pg.Surface, opacity: float = 1.0):
        t = self.texture.copy()
        t.set_alpha(int(opacity * 255))
        surface.blit(t, self.texture.get_rect())


class RotatableTexture(SimpleTexture):
    def draw(self, surface: pg.Surface, rotation: Rotation, opacity: float = 1.0):
        t = self.texture.copy()
        t.set_alpha(int(opacity * 255))
        surface.blit(pg.transform.rotate(t, rotation.value), self.texture.get_rect())


class ConnexTexture(Texture):
    def __init__(self, textures: Dict[Connex, pg.Surface]):
        self.textures = textures

    @classmethod
    def load(cls, name: str) -> Texture:
        textures = {}

        for path in (ASSETS_DIR / name).glob('*.png'):
            if path.stem == '0':
                textures[Connex(0)] = _load_tile_image(path)
                continue

            connex = Connex(0)
            for c in path.stem:
                connex |= Connex[c]

            textures[connex] = _load_tile_image(path)

        return cls(textures)

    def draw(self, surface: pg.Surface, connex: Connex, opacity: float = 1.0):
        texture = self.textures[connex].copy()
        texture.set_alpha(int(opacity * 255))
        surface.blit(texture, texture.get_rect())


def _load_tile_image(path):
    img = pg.image.load(str(path)).convert_alpha()
    return pg.transform.scale(img, (CELL_SIZE, CELL_SIZE))
