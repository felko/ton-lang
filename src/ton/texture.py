#!/usr/bin/env python3.7
# coding: utf-8

import pygame as pg

from abc import *
from typing import *
from pathlib import Path

from .constants import *
from .types import *


class Texture(Drawable):
    @abstractstaticmethod
    def load(name: str) -> 'Texture':
        raise NotImplementedError

    @abstractmethod
    def draw(self, surface: pg.Surface):
        raise NotImplementedError


class SimpleTexture(Texture):
    def __init__(self, texture: pg.Surface):
        self.texture = texture

    @staticmethod
    def load(name: str) -> Texture:
        path = str(ASSETS_DIR / (name + '.png'))
        return SimpleTexture(pg.image.load(str(ASSETS_DIR / (name + '.png'))).convert_alpha())

    def draw(self, surface: pg.Surface):
        surface.blit(self.texture, self.texture.get_rect())


class RotatableTexture(SimpleTexture):
    def draw(self, surface: pg.Surface, rotation: Rotation = Rotation.R0):
        surface.blit(pg.transform.rotate(self.texture, rotation.value))


class ConnexTexture(Texture):
    def __init__(self, textures: Dict[Connex, pg.Surface]):
        self.textures = textures

    @staticmethod
    def load(name: str) -> Texture:
        textures = {}

        for path in (ASSETS_DIR / name).glob('*.png'):
            if path.stem == '0':
                textures[Connex(0)] = pg.image.load(str(path)).convert_alpha()
                continue

            connex = Connex(0)
            for c in path.stem:
                connex |= Connex[c]

            textures[connex] = pg.image.load(str(path)).convert_alpha()

        return ConnexTexture(textures)

    def draw(self, surface: pg.Surface, connex: Connex):
        texture = self.textures[connex]
        surface.blit(texture, texture.get_rect())
