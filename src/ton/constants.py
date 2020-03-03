#!/usr/bin/env python3.7
# coding: utf-8

from pathlib import Path

MAX_FPS = 30
CELL_SIZE = 32

SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 512 + CELL_SIZE, 512

CURSOR_OPACITY = .2

PROJECT_DIR = Path(__file__).parent.parent.parent
ASSETS_DIR = PROJECT_DIR / 'assets'
