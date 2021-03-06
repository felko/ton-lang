#!/usr/bin/env python3.8
# coding: utf-8

__all__ = [
    'Texture',
    'SimpleTexture',
    'RotatableTexture',
    'ConnexTexture'
]

import pygame as pg

from abc import *
from typing import *
from pathlib import Path

from ton.type import *
from ton.utils import *
from ton.constants import *


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
        return cls(load_tile_image(ASSETS_DIR / (name + '.png')))

    def draw(self, surface: pg.Surface, opacity: float = 1.0):
        blit_alpha(surface, self.texture, (0, 0), opacity)


class RotatableTexture(SimpleTexture):
    def draw(self, surface: pg.Surface, rotation: Rotation = Rotation.R0, opacity: float = 1.0):
        blit_alpha(surface, pg.transform.rotate(self.texture, rotation.value), (0, 0), opacity)


class ConnexTexture(Texture):
    def __init__(self, textures: Dict[Connex, pg.Surface]):
        self.textures = textures

    @classmethod
    def load(cls, name: str) -> Texture:
        textures = {}

        for path in (ASSETS_DIR / name).glob('*.png'):
            if path.stem == '0':
                textures[Connex(0)] = load_tile_image(path)
                continue

            connex = Connex(0)
            for c in path.stem:
                connex |= Connex[c]

            textures[connex] = load_tile_image(path)

        return cls(textures)

    def draw(self, surface: pg.Surface, connex: Connex = Connex(0), opacity: float = 1.0):
        blit_alpha(surface, self.textures[connex], (0, 0), opacity)
