#!/usr/bin/env python3.7
# coding: utf-8

import os
import fire

from .constants import *


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

        import pygame as pg
        pg.init()

        screen = pg.display.set_mode(SCREEN_SIZE)

        import ton.editor

        editor = ton.editor.Editor.load_program(path, screen)
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
