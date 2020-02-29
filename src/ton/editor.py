#!/usr/bin/env python3.7
# coding: utf-8

import pygame as pg
import numpy as np

from abc import *
from enum import *
from typing import *
from pathlib import Path

from .program import *
from .texture import *
from .utils import *
from .constants import *


TOOLBAR_LAYOUT = [
    Wire,
    Integer,
    Adder
]


class Toolbar:
    def __init__(self):
        self._selected = 0

    @property
    def selected(self) -> int:
        return self._selected

    @selected.setter
    def selected(self, value: int):
        self._selected = value % len(TOOLBAR_LAYOUT)

    @property
    def cell_type(self) -> Type[Cell]:
        return TOOLBAR_LAYOUT[self.selected]

    def draw(self, surface: pg.Surface):
        for i, cell_type in enumerate(TOOLBAR_LAYOUT):
            rect = pg.Rect((0, CELL_SIZE * i), (CELL_SIZE, CELL_SIZE))
            cell_type().draw(surface.subsurface(rect), Neighborhood({}))

            if i == self.selected:
                Cursor.texture.draw(surface.subsurface(rect))


class CursorMode(IntEnum):
    NONE = auto()
    CREATE = auto()
    DELETE = auto()
    SET = auto()

    
class Cursor(Drawable):
    texture = SimpleTexture.load('cursor')

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.mode = CursorMode.NONE

    @property
    def pos(self) -> Tuple[int, int]:
        return self.x, self.y

    @pos.setter
    def pos(self, value: Tuple[int, int]):
        self.x, self.y = value

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, cell_type: Type[Cell]):
        if self.mode not in (CursorMode.DELETE, CursorMode.SET):
            cell_type().draw(surface, neighbors, opacity=.2)
            
        self.texture.draw(surface)


class Editor:
    def __init__(self, path: Path, window: pg.Surface):
        self.path = path
        self.program = Program.load(path)
        self.intermediate = None
        self.cursor = Cursor(0, 0)
        self.toolbar = Toolbar()
        self.clock = pg.time.Clock()
        self.running = False
        self.window = window

    def _get_cursor_rect(self) -> pg.Rect:
        return to_rect(*self.cursor.pos)

    def _get_toolbar_rect(self) -> pg.Rect:
        return pg.Rect((0, 0), (CELL_SIZE, SCREEN_HEIGHT))

    def save(self):
        self.program.save(self.path)

    def update_pointed(self):
        if self.program.in_bounds(*self.cursor.pos):
            if self.cursor.mode == CursorMode.CREATE:
                self.pointed = self.toolbar.cell_type()
            elif self.cursor.mode == CursorMode.DELETE:
                self.pointed = Empty()

    def handle(self, event: 'pg.Event'):
        if event.type == pg.KEYDOWN:
            if (event.key == pg.K_q and event.mod & pg.KMOD_CTRL) or event.key == pg.K_ESCAPE:
                self.quit()
            elif event.key == pg.K_s and event.mod & pg.KMOD_CTRL:
                self.save()
            elif event.key == pg.K_l and event.mod & pg.KMOD_CTRL:
                self.program = Program.empty(*self.program.size)
            elif event.key == pg.K_SPACE:
                self.program.step()
            elif event.key == pg.K_s:
                self.cursor.mode = CursorMode.SET
        elif event.type == pg.KEYUP:
            if event.key == pg.K_s:
                self.cursor.mode = CursorMode.NONE
        elif event.type == pg.QUIT:
            self.quit()
        elif event.type == pg.MOUSEMOTION:
            self.cursor.pos = to_tile(*event.pos)
            self.cursor.x -= 1
            self.update_pointed()
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.cursor.mode = CursorMode.CREATE
            elif event.button == 3:
                self.cursor.mode = CursorMode.DELETE
            elif event.button == 4:
                if self.cursor.mode == CursorMode.SET:
                    self.pointed.previous_state()
                else:
                    self.toolbar.selected -= 1
            elif event.button == 5:
                if self.cursor.mode == CursorMode.SET:
                    self.pointed.next_state()
                else:
                    self.toolbar.selected += 1
                
            self.update_pointed()

        elif event.type == pg.MOUSEBUTTONUP:
            if event.button in (1, 3):
                self.cursor.mode = CursorMode.NONE

    @property
    def pointed(self) -> Cell:
        return self.program.cells[self.cursor.pos]

    @pointed.setter
    def pointed(self, cell: Cell):
        self.program.cells[self.cursor.pos] = cell

    def update(self, dt: float):
        pass

    def draw(self):
        w, h = self.window.get_size()
        screen = pg.Surface((w - CELL_SIZE, h), pg.SRCALPHA).convert_alpha()
        screen.fill(0x505050FF)
        self.program.draw(screen)

        if self.program.in_bounds(*self.cursor.pos):
            for direction, (nx, ny) in Neighborhood.around(*self.cursor.pos):
                neighbors = self.program.get_neighbors(nx, ny)
                neighbors.cells[direction.opposite()] = self.toolbar.cell_type()
                if self.program.in_bounds(nx, ny):
                    self.program.cells[nx, ny].draw(screen.subsurface(to_rect(nx, ny)), neighbors)

            cursor_surface = screen.subsurface(self._get_cursor_rect())
            self.cursor.draw(cursor_surface, self.program.get_neighbors(*self.cursor.pos), self.toolbar.cell_type)

        self.window.fill(0x00000000)
        self.window.blit(screen, (CELL_SIZE, 0))

        toolbar_surface = self.window.subsurface(self._get_toolbar_rect())
        self.toolbar.draw(toolbar_surface)

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

