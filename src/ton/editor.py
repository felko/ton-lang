#!/usr/bin/env python3.7
# coding: utf-8

import pygame as pg
import numpy as np

from abc import *
from enum import *

from .program import *
from .texture import *
from .utils import *
from .constants import *


class CellMenu:
    def __init__(self):
        pass


class CursorMode(IntEnum):
    NONE = auto()
    CREATE = auto()
    DELETE = auto()

    
class Cursor(Drawable):
    texture = SimpleTexture.load('cursor')

    cell_types = [
        Wire,
        Integer,
        Adder
    ]

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.mode = CursorMode.NONE
        self._cell_index = 0

    @property
    def cell_index(self):
        return self._cell_index

    @cell_index.setter
    def cell_index(self, value):
        self._cell_index = value % len(self.cell_types)

    @property
    def cell_type(self):
        return self.cell_types[self.cell_index]

    @property
    def pos(self):
        return self.x, self.y

    @pos.setter
    def pos(self, value):
        self.x, self.y = value

    def draw(self, surface: pg.Surface, neighbors: Neighborhood):
        if self.mode != CursorMode.DELETE:
            self.cell_type().draw(surface, neighbors, opacity=.1)
            
        self.texture.draw(surface)


class Editor:
    def __init__(self, path, screen):
        self.path = path
        self.program = Program.load(path)
        self.intermediate = None
        self.cursor = Cursor(0, 0)
        self.clock = pg.time.Clock()
        self.running = False
        self.screen = screen

    def _get_cursor_rect(self):
        return to_rect(*self.cursor.pos)

    def save(self):
        self.program.save(self.path)

    def update_pointed(self):
        if self.program.in_bounds(*self.cursor.pos):
            if self.cursor.mode == CursorMode.CREATE:
                self.pointed = self.cursor.cell_type()
            elif self.cursor.mode == CursorMode.DELETE:
                self.pointed = Empty()

    def handle(self, event):
        if event.type == pg.KEYDOWN:
            if (event.key == pg.K_q and event.mod & pg.KMOD_CTRL) or event.key == pg.K_ESCAPE:
                self.quit()
            elif event.key == pg.K_s and event.mod & pg.KMOD_CTRL:
                self.save()
            elif event.key == pg.K_l and event.mod & pg.KMOD_CTRL:
                self.program = Program.empty(*self.program.size)
        elif event.type == pg.QUIT:
            self.quit()
        elif event.type == pg.MOUSEMOTION:
            self.cursor.pos = to_tile(*event.pos)
            self.update_pointed()
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.cursor.mode = CursorMode.CREATE
            elif event.button == 3:
                self.cursor.mode = CursorMode.DELETE
            elif event.button == 4:
                self.cursor.cell_index -= 1
            elif event.button == 5:
                self.cursor.cell_index += 1
                
            self.update_pointed()

        elif event.type == pg.MOUSEBUTTONUP:
            self.cursor.mode = CursorMode.NONE

    @property
    def pointed(self) -> Cell:
        self.program.cells[self.cursor.pos]

    @pointed.setter
    def pointed(self, cell: Cell):
        self.program.cells[self.cursor.pos] = cell

    def update(self, dt: float):
        pass

    def draw(self):
        self.screen.fill(0x50505000)
        self.program.draw(self.screen)

        if self.program.in_bounds(*self.cursor.pos):
            for direction, (nx, ny) in Neighborhood.around(*self.cursor.pos):
                neighbors = self.program.get_neighbors(nx, ny)
                neighbors.cells[direction.opposite()] = self.cursor.cell_type()
                if self.program.in_bounds(nx, ny):
                    self.program.cells[nx, ny].draw(self.screen.subsurface(to_rect(nx, ny)), neighbors)

            cursor_surface = self.screen.subsurface(self._get_cursor_rect())
            self.cursor.draw(cursor_surface, self.program.get_neighbors(*self.cursor.pos))

    def quit(self):
        self.running = False

    def run(self):
        self.running = True

        self.program.cells[3, 4] = Adder(Direction.N)

        while self.running:
            dt = self.clock.tick(MAX_FPS)

            for event in pg.event.get():
                self.handle(event)

            self.update(dt)
            self.draw()

            pg.display.update()

