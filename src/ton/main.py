#!/usr/bin/env python3.8
# coding: utf-8

import os
import fire
from pathlib import Path

from ton.constants import *

import pygame as pg

pg.init()
window = pg.display.set_mode(SCREEN_SIZE)

pg.display.set_icon(pg.transform.scale2x(pg.image.load(str(ASSETS_DIR / 'jam.png'))))
pg.display.set_caption('ton')

from ton.program import *
from ton.editor import *


class CLI:
    """
    ton-lang editor and interpreter
    """

    def __init__(self, pwd):
        os.chdir(pwd)

    def edit(path):
        """
        Edit a program
        """

        editor = Editor(path, window)
        editor.run()

        pg.quit()

    def new(path: Path, width: int, height: int):
        """
        Creates a new empty program with given dimensions
        """

        program = Program.empty(width, height)
        editor = Editor(path, window)

        pg.quit()

    def run(path: Path, x: int, y: int):
        """
        Executes a program and returns the final state of the cell
        at the given position
        """

        program = Program.load(path)
        return program.get_cell(x, y)


def main():
    fire.Fire(CLI)
