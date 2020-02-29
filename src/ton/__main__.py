#!/usr/bin/env python3.7
# coding: utf-8

import os
import fire

from .constants import *

import pygame as pg

pg.init()
window = pg.display.set_mode(SCREEN_SIZE)

pg.display.set_icon(pg.transform.scale2x(pg.image.load(str(ASSETS_DIR / 'jam.png'))))
pg.display.set_caption('ton')

from .program import *
from .editor import *


class CLI:
    """
    ton-lang editor and interpreter
    """

    def __init__(self, pwd):
        os.chdir(pwd)

    def edit(self, path):
        """
        Edit a program
        """

        editor = Editor(path, window)
        editor.run()

        pg.quit()

    def new(self, path, width: int, height: int):
        """
        Creates a new empty program with given dimensions
        """

        program = Program.empty(width, height)
        program.save(path)

    def run(self, path, x: int, y: int):
        """
        Executes a program and returns the final state of the cell
        at the given position
        """

        program = Program.load(path)
        return program.get_cell(x, y)

    
if __name__ == '__main__':
    fire.Fire(CLI)
