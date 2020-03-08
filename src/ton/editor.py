#!/usr/bin/env python3.8
# coding: utf-8

import pygame as pg
import numpy as np

from abc import *
from enum import *
from typing import *
from pathlib import Path
import copy
import json

from ton.cell import *
from ton.program import *
from ton.neighborhood import *
from ton.texture import *
from ton.utils import *
from ton.type import *
from ton.constants import *


def make_import(path: Path):
    class ImportedFile(Import):
        def __init__(self, direction: Direction = Direction.N):
            super().__init__(path, direction)

        @classmethod
        def name(cls) -> str:
            return path.stem

    return ImportedFile


class Toolbar:
    font = pg.font.Font(str(ASSETS_DIR / 'Oxanium-ExtraBold.ttf'), 16)

    def __init__(self, height: int):
        self._selected = 0
        self.height = height
        self.offset = 0
        self.selected_name_timer = 0
        self.selected_name_cooldown = 1
        self.selected_name_fadeout = 1/8
        self.layout = [
            Wire,
            Diode,
            Transistor,
            Anchor,
            Mu,
            Integer,
            Boolean,
            List_,
            Equals,
            Adder,
            Append,
            Pop,
            Chip,
            Debug
        ] # + list(map(make_import, Path.cwd().glob('*.ton')))

    @property
    def selected(self) -> int:
        return self._selected

    @selected.setter
    def selected(self, value: int):
        self._selected = max(0, min(value, len(self.layout) - 1))

        if 0 <= value < self.offset:
            self.offset = value
        elif value >= self.offset + self.height - 1:
            self.offset = value - self.height + 1

    @property
    def cell_type(self) -> Type[Cell]:
        return self.layout[self.selected]

    def scroll(self, amount: int):
        self.selected += amount
        self.selected_name_timer = self.selected_name_cooldown

    def update(self, dt: float):
        self.selected_name_timer = max(self.selected_name_timer - dt, 0)

    def draw(self, surface: pg.Surface):
        visible_layout = self.layout[self.offset:self.offset+self.height]

        for i, cell_type in enumerate(visible_layout):
            rect = pg.Rect((0, CELL_SIZE * i), (CELL_SIZE, CELL_SIZE))
            cell_type.draw_icon(surface.subsurface(rect))

            if self.offset + i == self.selected:
                Cursor.texture.draw(surface.subsurface(rect))

        if self.selected_name_timer > 0:
            cell_name = self.font.render(self.cell_type.name(), True, (255, 255, 255), None)
            # def blit_alpha(target, source, location, opacity):
            timer = self.selected_name_cooldown - self.selected_name_timer
            blit_alpha(
                surface,
                cell_name,
                (CELL_SIZE + 8, (self.selected - self.offset) * CELL_SIZE + round(CELL_SIZE / 2 - cell_name.get_height() / 2)),
                1 - (timer/self.selected_name_cooldown)**(1/self.selected_name_fadeout)
            )


class CursorMode(IntEnum):
    NONE = auto()
    CREATE = auto()
    DELETE = auto()
    SET = auto()
    INFO = auto()

    
class Cursor(Drawable):
    texture = SimpleTexture.load('cursor')
    font = pg.font.Font(str(ASSETS_DIR / 'Oxanium-ExtraBold.ttf'), max(16, round(CELL_SIZE * 1 / 2)))

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

    def get_rect(self) -> pg.Rect:
        return to_rect(*self.pos)

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, cell_type: Type[Cell], pointed: Cell):
        square = surface.subsurface(self.get_rect())

        if self.mode in (CursorMode.NONE, CursorMode.CREATE):
            cell_type().draw(square, neighbors, opacity=.2)
            
        self.texture.draw(square)

        if self.mode == CursorMode.INFO:
            info = self.font.render(pointed.info(), True, (255, 255, 255), (0, 0, 0))
            surface.blit(info, (CELL_SIZE * (self.x + 1) + round(CELL_SIZE / 8), CELL_SIZE * self.y + round(CELL_SIZE / 2 - info.get_height() / 2)))


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
                self.evaluating = False
                self.nesting = []
            elif event.key == pg.K_SPACE:
                self.board.step()
            elif event.key == pg.K_RETURN:
                self.evaluating = not self.evaluating
            elif event.key == pg.K_s:
                self.cursor.mode = CursorMode.SET
            elif event.key == pg.K_m and type(self.pointed) is Chip:
                p = self.pointed.copy()
                self.toolbar.layout.append(lambda: p)
            elif event.key == pg.K_d:
                print(json.dumps(self.pointed.debug(), indent=4))
            elif event.key == pg.K_i:
                self.cursor.mode = CursorMode.INFO
            elif event.key == pg.K_TAB and type(self.pointed) is Chip:
                self.nesting.append(self.pointed.board)
            elif event.key == pg.K_ESCAPE and event.mod & pg.KMOD_SHIFT:
                self.nesting = []
            elif event.key == pg.K_ESCAPE and self.nesting:
                self.nesting.pop()
        elif event.type == pg.KEYUP:
            if event.key == pg.K_s:
                self.cursor.mode = CursorMode.NONE
            elif event.key == pg.K_i:
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
                    self.toolbar.scroll(-1)

            elif event.button == 5:
                if self.cursor.mode == CursorMode.SET:
                    self.pointed.next_state()
                else:
                    self.toolbar.scroll(1)

                
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
        self.toolbar.update(dt)
        
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
            if self.cursor.mode in (CursorMode.NONE, CursorMode.CREATE):
                for direction, (nx, ny) in Neighborhood.around(*self.cursor.pos):
                    neighbors = self.board.get_neighbors(nx, ny)
                    neighbors.cells[direction.opposite()] = self.toolbar.cell_type()
                    if self.board.in_bounds(nx, ny):
                        self.board.cells[nx, ny].draw(screen.subsurface(to_rect(nx, ny)), neighbors)

            self.cursor.draw(screen, self.board.get_neighbors(*self.cursor.pos), self.toolbar.cell_type, self.pointed)

        self.window.fill((0, 0, 0))
        self.window.blit(screen, (CELL_SIZE, 0))

        self.toolbar.draw(self.window)

    def quit(self):
        self.running = False

    def run(self):
        self.running = True

        pg.display.set_caption(f"ton — {str(self.path)}")

        while self.running:
            dt = self.clock.tick(MAX_FPS) / 1000

            for event in pg.event.get():
                self.handle(event)

            self.update(dt)
            self.draw()

            pg.display.update()

