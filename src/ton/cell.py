#!/usr/bin/env python3.8
# coding: utf-8

__all__ = [
    'Cell',
    'Empty',
    'Wire',
    'Anchor',
    'Value',
    'Integer',
    'Directional',
    'Diode',
    'Processor',
    'Adder',
    'Debug',
    'Chip',
    'Import',
    'List',
    'Append',
    'Pop'
]

import pygame as pg
import numpy as np

import random
import copy
from abc import *
from pathlib import Path

from ton.program import *
from ton.texture import *
from ton.neighborhood import *
from ton.type import *
from ton.constants import *


class Cell(object):
    __slots__ = []

    texture: Texture

    @abstractmethod
    def step(self, neighborhood: Neighborhood) -> 'Cell':
        raise NotImplementedError

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    def on_create(self, neighbors: Neighborhood):
        pass

    def on_click(self):
        pass

    def next_state(self):
        pass

    def previous_state(self):
        pass

    def get_pins(self) -> Set[Direction]:
        return set()

    def info(self) -> str:
        return f"<{type(self).__name__}>"

    def copy(self) -> 'Cell':
        return copy.copy(self)

    @abstractmethod
    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        raise NotImplementedError

    def __getstate__(self):
        return dict(
            (slot, getattr(self, slot))
            for slot in self.__slots__
            if hasattr(self, slot)
        )

    def __setstate__(self, state):
        for slot, value in state.items():
            object.__setattr__(self, slot, value)


class Empty(Cell):
    __slots__ = []

    def step(self, neighbors: Neighborhood) -> Cell:
        return self

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        pass


class Wire(Cell):
    __slots__ = []

    texture = ConnexTexture.load('wire')

    def step(self, neighbors: Neighborhood) -> Cell:
        values = neighbors.filter(lambda _, cell: isinstance(cell, Value))

        if values:
            return random.choice(list(values.get_cells()))
        else:
            cells_or_edges = []
            for cell in neighbors.cells.values():
                if cell is None or isinstance(cell, (Wire, Processor, Anchor, Chip)):
                    cells_or_edges.append(cell)

            if len(cells_or_edges) >= 2:
                return self
            else:
                return Empty()

    def get_pins(self) -> Set[Direction]:
        return set(Direction)

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        has_pin = lambda direction, cell: direction.opposite() in cell.get_pins()
        connex = Connex(0)
        for direction, cell in neighbors.cells.items():
            if cell is None or has_pin(direction, cell):
                connex |= Connex.from_direction(direction)
        self.texture.draw(surface, connex, opacity)


class Anchor(Cell):
    __slots__ = []

    texture = SimpleTexture.load('anchor')

    def step(self, neighbors: Neighborhood) -> Cell:
        return self

    def get_pins(self) -> Set[Direction]:
        return set(Direction)

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        self.texture.draw(surface, opacity)


class Directional(Cell):
    __slots__ = ['direction']

    texture: RotatableTexture
    
    def __init__(self, direction: Direction = Direction.N):
        self.direction = direction

    def get_side_direction(self, side: Side) -> Direction:
        return side.direction_relative_to(self.direction)

    def rotate(self, rotation: Rotation):
        self.direction = self.direction.rotated(rotation)

    def next_state(self):
        self.rotate(Rotation.R90)

    def previous_state(self):
        self.rotate(Rotation.R270)

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        self.texture.draw(surface, self.direction.relative_rotation_to(Direction.N), opacity)


class Processor(Directional):
    __slots__ = ['direction', 'inputs', 'outputs', 'arguments']

    def __init__(self, direction: Direction, inputs: Dict[Side, Tuple[str, Type[Cell]]], outputs: Set[Side]):
        super().__init__(direction)
        self.inputs = inputs
        self.outputs = outputs
        self.arguments = {}
        self.return_values = {}

    @abstractmethod
    def process(self, **kwargs):
        raise NotImplementedError

    def get_pins(self) -> Set[Direction]:
        pins = set()

        for direction in Direction:
            try:
                self.get_parameter_towards(direction)
            except KeyError:
                continue
            else:
                pins.add(direction)

        for side in self.outputs:
            pins.add(self.get_side_direction(side))

        return pins

    def get_parameter_towards(self, direction: Direction) -> Tuple[str, Type[Cell]]:
        return self.inputs[self.direction.side_relative_to(direction)]

    def is_fed(self) -> bool:
        return all(
            param in self.arguments
            and isinstance(self.arguments[param], type)
            for param, type in self.inputs.values()
        )

    def is_waiting_for(self, direction: Direction) -> bool:
        try:
            return not self.is_fed() and self.get_parameter_towards(direction)[0] in self.arguments
        except KeyError:
            return False

    def will_provide(self, direction: Direction) -> bool:
        return self.direction.side_relative_to(direction) in self.outputs

    def get_output(self, direction: Direction) -> Cell:


    def has_pin(self, direction: Direction) -> bool:
        return self.is_waiting_for(direction) or self.will_provide(direction)

    def step(self, neighbors: Neighborhood) -> Cell:
        for direction, cell in neighbors:
            try:
                name, type_ = self.inputs[self.direction.side_relative_to(direction)]
            except KeyError:
                continue
            else:
                if isinstance(cell, type_):
                    self.arguments[name] = cell
                    
        if self.is_fed():
            return self.process(**self.arguments)
        else:
            return self


class Diode(Processor):
    __slots__ = ['direction', 'inputs', 'outputs', 'arguments']

    texture = RotatableTexture.load('diode')

    def __init__(self, direction: Direction = Direction.N):
        super().__init__(
            direction,
            inputs={Side.BACK: ('value', Value)},
            outputs={Side.FRONT}
        )

    def process(self, value) -> Cell:
        return value

    def step(self, neighbors: Neighborhood) -> Cell:
        cell = neighbors[self.get_side_direction(Side.BACK)]
        if isinstance(cell, Value):
            return cell
        else:
            return self


class Adder(Processor):
    __slots__ = ['direction', 'inputs', 'outputs', 'arguments']
    
    texture = RotatableTexture.load('adder')

    def __init__(self, direction: Direction = Direction.N):
        super().__init__(
            direction,
            inputs={Side.LEFT: ('x', Integer), Side.RIGHT: ('y', Integer)},
            outputs={Side.FRONT}
        )

    def process(self, x, y):
        return Integer(x.value + y.value)

    def info(self) -> str:
        if self.arguments:
            return f"<Adder {' '.join(map(lambda assoc: f'{assoc[0]}={assoc[1].info()}', self.arguments.items()))}>"
        else:
            return super().info()


class Debug(Cell):
    __slots__ = []

    texture = SimpleTexture.load('console')

    def __init__(self):
        super().__init__()

    def get_pins(self) -> Set[Direction]:
        return set(Direction)

    def step(self, neighbors: Neighborhood) -> Cell:
        for neighbor in neighbors.filter(lambda _, cell: isinstance(cell, Value)).get_cells():
            print(neighbor.info())
        return self

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        self.texture.draw(surface, opacity)


class Value(Cell):
    __slots__ = []

    background = SimpleTexture.load('value')

    def __init__(self):
        self.index = None

    def get_pins(self) -> Set[Direction]:
        return set(Direction)
    
    def step(self, neighbors: Neighborhood) -> Cell:
        processors = neighbors.filter(lambda _, cell: isinstance(cell, Processor))

        for direction, processor in processors:
            if processor.has_pin(direction.opposite()):
                return self

        anchors = neighbors.filter(lambda _, cell: isinstance(cell, Anchor))
        if anchors:
            return self
        else:
            return Empty()


class Integer(Value):
    __slots__ = ['value']

    font = pg.font.Font(str(ASSETS_DIR / 'Oxanium-ExtraBold.ttf'), CELL_SIZE)

    def __init__(self, value: int = 0):
        self.value = value

    def next_state(self):
        self.value += 1

    def previous_state(self):
        self.value -= 1

    def info(self) -> str:
        return f"<Integer value={self.value}>"

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        texture = self.font.render(str(self.value), True, (0, 0, 0))
        texture = pg.transform.scale(texture, (CELL_SIZE - 4, CELL_SIZE - 4))
        blit_alpha(surface, Value.background.texture, (0, 0), opacity)
        blit_alpha(surface, texture, (2, 2), opacity)


class Chip(Directional):
    __slots__ = ['direction', 'board']

    texture = RotatableTexture.load('chip')

    def __init__(self, direction: Direction = Direction.N, board: Optional['Program'] = None):
        super().__init__(direction)
        self.board = board or Program.empty(16, 16)

    def get_pins(self) -> Set[Direction]:
        return set(Direction)

    def get_side(self, side: Side) -> Iterable[Tuple[int, int]]:
        w, h = self.board.size

        if side == Side.FRONT:
            for x in range(w):
                yield x, 0
        elif side == Side.BACK:
            for x in range(w):
                yield x, h-1
        elif side == Side.LEFT:
            for y in range(h):
                yield 0, y
        else:
             for y in range(h):
                 yield w-1, y

    def enumerate_side(self, side: Side) -> Iterable[Tuple[Tuple[int, int], Cell]]:
        for pos in self.get_side(side):
            yield pos, self.board.cells[pos]

    def copy(self):
        return copy.deepcopy(self)

    def step(self, neighbors: Neighborhood) -> Cell:
        for side in Side:
            direction = side.direction_relative_to(self.direction)
            for pos, cell in self.enumerate_side(side):
                if isinstance(cell, Wire):
                    arg = neighbors[direction]
                    if isinstance(arg, Value):
                        self.board.cells[pos] = arg

        self.board.step()

        for side in Side:
            for _, cell in self.enumerate_side(side):
                if isinstance(cell, Value):
                    return cell

        return self


class Import(Chip):
    __slots__ = ['direction', 'board', 'path']

    texture = RotatableTexture.load('file')

    def __init__(self, path: Path, direction: Direction = Direction.N):
        super().__init__(direction, Program.load(path))
        self.path = path

    def info(self) -> str:
        return f"<Import {self.path.name!r}>"


class List(Value):
    __slots__ = ['value']

    texture = SimpleTexture.load('list')
    
    def __init__(self, value: List[Value] = ()):
        self.value = list(value)

    def info(self) -> str:
        return f"[{', '.join(map(lambda cell: cell.info, self.value))}]"

    def copy(self) -> 'List':
        return copy.deepcopy(self)

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        self.texture.draw(surface, opacity)


class Append(Processor):
    __slots__ = ['direction', 'inputs', 'outputs', 'arguments']

    texture = RotatableTexture.load('append')

    def __init__(self, direction: Direction = Direction.N):
        super().__init__(
            direction,
            inputs={Side.LEFT: ('x', Value), Side.RIGHT: ('xs', List)},
            outputs={Side.FRONT}
        )

    def process(self, x: Value, xs: List):
        lst = xs.copy()
        lst.value.append(x)
        return lst


class Pop(Processor):
    __slots__ = ['direction', 'inputs', 'outputs', 'arguments']

    texture = RotatableTexture.load('pop')

    def __init__(self, direction: Direction = Direction.N):
        super().__init__(
            direction,
            inputs={Side.LEFT: ('xs', Value)},
            outputs={Side.FRONT, Side.LEFT}
        )

    def process(self, x: Value, xs: List):
        lst = xs.copy()
        lst.value.append(x)
        return lst
