#!/usr/bin/env python3.8
# coding: utf-8

import pygame as pg
import numpy as np

from abc import *
from enum import *
from typing import *
from pathlib import Path
import copy

from ton.cell import *
from ton.program import *
from ton.neighborhood import *
from ton.texture import *
from ton.utils import *
from ton.constants import *


class Toolbar:
    def __init__(self, height: int):
        self._selected = 0
        self.height = height
        self.offset = 0
        self.layout = [
            Wire,
            Diode,
            Anchor,
            Integer,
            Adder,
            Chip
        ]

    @property
    def selected(self) -> int:
        return self._selected

    @selected.setter
    def selected(self, value: int):
        self._selected = max(0, min(value, len(self.layout) - 1))
        # value = max(0, min(value, len(self.layout) - 1))

        if 0 <= value < self.offset:
            self.offset = value
        elif value >= self.offset + self.height - 1:
            self.offset = value - self.height + 1

    @property
    def cell_type(self) -> Type[Cell]:
        return self.layout[self.selected]

    def draw(self, surface: pg.Surface):
        visible_layout = self.layout[self.offset:self.offset+self.height]
        for i, cell_type in enumerate(visible_layout):
            rect = pg.Rect((0, CELL_SIZE * i), (CELL_SIZE, CELL_SIZE))
            cell_type().draw(surface.subsurface(rect), Neighborhood({}))

            if self.offset + i == self.selected:
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
        self.nesting = []
        self.intermediate = None
        self.cursor = Cursor(0, 0)
        self.toolbar = Toolbar(height=16)
        self.clock = pg.time.Clock()
        self.timer = 0
        self.steps_per_second = 10
        self.evaluating = False
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
            if (event.key == pg.K_q and event.mod & pg.KMOD_CTRL):
                self.quit()
            elif event.key == pg.K_s and event.mod & pg.KMOD_CTRL:
                self.save()
            elif event.key == pg.K_l and event.mod & pg.KMOD_CTRL:
                self.program = Program.empty(*self.program.size)
            elif event.key == pg.K_r and event.mod & pg.KMOD_CTRL:
                self.program = Program.load(self.path)
                self.nesting = []
            elif event.key == pg.K_SPACE:
                self.board.step()
            elif event.key == pg.K_RETURN:
                self.evaluating = not self.evaluating
            elif event.key == pg.K_s:
                self.cursor.mode = CursorMode.SET
            elif event.key == pg.K_m and isinstance(self.pointed, Chip):
                p = self.pointed.copy()
                self.toolbar.layout.append(lambda: p)
            elif event.key == pg.K_d:
                print(self.pointed.info())
            elif event.key == pg.K_TAB and isinstance(self.pointed, Chip):
                self.nesting.append(self.pointed.board)
            elif event.key == pg.K_ESCAPE and event.mod & pg.KMOD_SHIFT:
                self.nesting = []
            elif event.key == pg.K_ESCAPE and self.nesting:
                self.nesting.pop()
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
        return self.board.cells[self.cursor.pos]

    @pointed.setter
    def pointed(self, cell: Cell):
        self.board.cells[self.cursor.pos] = cell

    @property
    def board(self) -> Program:
        if self.nesting:
            return self.nesting[-1]
        else:
            return self.program

    def update(self, dt: float):
        if self.evaluating:
            self.timer += dt

            if self.timer > 1 / self.steps_per_second:
                self.timer = 0
                self.program.step()

    def draw(self):
        w, h = self.window.get_size()
        screen = pg.Surface((w - CELL_SIZE, h), pg.SRCALPHA).convert_alpha()
        screen.fill((50, 50, 50))
        self.board.draw(screen)

        if self.board.in_bounds(*self.cursor.pos):
            if self.cursor.mode not in (CursorMode.DELETE, CursorMode.SET):
                for direction, (nx, ny) in Neighborhood.around(*self.cursor.pos):
                    neighbors = self.board.get_neighbors(nx, ny)
                    neighbors.cells[direction.opposite()] = self.toolbar.cell_type()
                    if self.board.in_bounds(nx, ny):
                        self.board.cells[nx, ny].draw(screen.subsurface(to_rect(nx, ny)), neighbors)

            cursor_surface = screen.subsurface(self._get_cursor_rect())
            self.cursor.draw(cursor_surface, self.board.get_neighbors(*self.cursor.pos), self.toolbar.cell_type)

        self.window.fill((0, 0, 0))
        self.window.blit(screen, (CELL_SIZE, 0))

        toolbar_surface = self.window.subsurface(self._get_toolbar_rect())
        self.toolbar.draw(toolbar_surface)

    def quit(self):
        self.running = False

    def run(self):
        self.running = True

        while self.running:
            dt = self.clock.tick(MAX_FPS) / 1000

            for event in pg.event.get():
                self.handle(event)

            self.update(dt)
            self.draw()

            pg.display.update()

