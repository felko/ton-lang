#!/usr/bin/env python3.7
# coding: utf-8

import pygame as pg
import numpy as np

from abc import *

from .program import *
from .texture import *
from .utils import *
from .constants import *


class CellMenu:
    def __init__(self):
        pass

    
class Cursor(Drawable):
    texture = SimpleTexture.load('cursor')

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.pressed = False

    @property
    def pos(self):
        return self.x, self.y

    @pos.setter
    def pos(self, value):
        self.x, self.y = value

    def draw(self, surface: pg.Surface):
        self.texture.draw(surface)


class Editor:
    def __init__(self, program, screen):
        self.program = program
        self.intermediate = None
        self.cursor = Cursor(0, 0)
        self.clock = pg.time.Clock()
        self.running = False
        self.screen = screen

    @staticmethod
    def new_program(path: Path, screen: pg.Surface):
        return Editor(Program.empty(path), screen)

    @staticmethod
    def load_program(path: Path, screen: pg.Surface):
        return Editor(Program.load(path), screen)

    def _get_cursor_rect(self):
        return to_rect(*self.cursor.pos)

    def handle(self, event):
        if event.type == pg.KEYDOWN:
            if (event.key == pg.K_q and event.mod & pg.KMOD_CTRL) or event.key == pg.K_ESCAPE:
                self.quit()
        elif event.type == pg.QUIT:
            self.quit()
        elif event.type == pg.MOUSEMOTION:
            self.cursor.pos = to_tile(*event.pos)
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.cursor.pressed = True
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                self.cursor.pressed = False

    @property
    def pointed(self) -> Cell:
        self.program.cells[self.cursor.pos]

    @pointed.setter
    def pointed(self, cell: Cell):
        self.program.cells[self.cursor.pos] = cell

    def update(self, dt: float):
        if self.cursor.pressed and self.program.in_bounds(*self.cursor.pos):
            self.pointed = Wire()

    def draw(self):
        self.screen.fill(0x101010)
        self.program.draw(self.screen)

        cursor_surface = self.screen.subsurface(self._get_cursor_rect())
        self.cursor.draw(cursor_surface)

    def quit(self):
        self.running = False

    def run(self):
        self.running = True

        while self.running:
            dt = self.clock.tick(MAX_FPS)

            for event in pg.event.get():
                self.handle(event)

            self.update(dt)
            self.draw()

            pg.display.update()

