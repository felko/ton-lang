#!/usr/bin/env python3.8
# coding: utf-8

__all__ = [
    'Cell',
    'Empty',
    'Link',
    'Wire',
    'Tube',
    'Anchor',
    'Value',
    'Integer',
    'Boolean',
    'Equals',
    'Directional',
    'Diode',
    'Transistor',
    'Processor',
    'Adder',
    'Debug',
    'Chip',
    'Import',
    'List_',
    'Append',
    'Pop',
    'Mu'
]

import pygame as pg
import numpy as np

import random
import copy
from abc import *
from typing import *
from pathlib import Path

from ton.program import *
from ton.texture import *
from ton.neighborhood import *
from ton.utils import *
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

    @classmethod
    def draw_icon(cls, surface: pg.Surface, opacity: float = 1.0):
        cls.texture.draw(surface, opacity=opacity)

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

    def debug(self):
        d = {'__type__': type(self).__name__}
        for slot in self.__slots__:
            d[slot] = getattr(self, slot)
        return d

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


class Link(Cell):
    __slots__ = []

    texture: ConnexTexture

    def get_pins(self) -> Set[Direction]:
        return set(Direction)

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        has_pin = lambda direction, cell: direction.opposite() in cell.get_pins()
        connex = Connex(0)
        for direction, cell in neighbors.cells.items():
            if cell is None or has_pin(direction, cell):
                connex |= Connex.from_direction(direction)
        self.texture.draw(surface, connex, opacity)


class Wire(Link):
    __slots__ = []

    texture = ConnexTexture.load('wire')

    def step(self, neighbors: Neighborhood) -> Cell:
        values = neighbors.filter(lambda _, cell: isinstance(cell, Value))

        if values:
            return random.choice(list(values.get_cells()))

        processors = neighbors.filter(lambda _, cell: isinstance(cell, Processor))
        candidates = []

        for direction, processor in processors:
            if processor.is_fed() and processor.will_provide(direction.opposite()):
                outputs = processor.process(processor.arguments)
                side = processor.get_direction_side(direction.opposite())
                candidates.append((processor, outputs[side]))

        if candidates:
            processor, value = random.choice(candidates)
            processor.fired = True
            return value

        cells_or_edges = []
        for cell in neighbors.cells.values():
            if cell is None or isinstance(cell, (Link, Processor, Anchor, Chip)):
                cells_or_edges.append(cell)

        if len(cells_or_edges) >= 2:
            return self
        else:
            return Empty()


class Tube(Link):
    __slots__ = ['value', 'flow']

    texture = ConnexTexture.load('tube')

    def __init__(self, value: Optional['Value'] = None, flow: Optional[Connex] = Connex(0)):
        self.value = value
        self.flow = flow

    def step(self, neighbors: Neighborhood) -> Cell:
        values = list(neighbors.filter(lambda _, cell: isinstance(cell, Value)).get_cells())
        flow = Connex(0)

        for direction, cell in neighbors:
            c = Connex.from_direction(direction.opposite())

            if isinstance(cell, Tube) \
                 and cell.value is not None \
                 and cell.flow & Connex.from_direction(direction):
                values.append(cell.value)
                flow |= c

        if values:
            self.value = random.choice(values)
        else:
            self.value = None
            
        self.flow = flow

        return self

    def debug(self):
        return {
            '__type__': 'Tube',
            'flow': repr(self.flow),
            'value': None if self.value is None else self.value.debug()
        }

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
       if self.value is None:
           super().draw(surface, neighbors, opacity)
       else:
           reduced_size = CELL_SIZE * 3/4
           value_surface = pg.Surface((reduced_size, reduced_size))
           self.value.draw(surface, neighbors, opacity)
        

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

    def get_direction_side(self, direction: Direction) -> Side:
        return direction.side_relative_to(self.direction)

    def rotate(self, rotation: Rotation):
        self.direction = self.direction.rotated(rotation)

    def next_state(self):
        self.rotate(Rotation.R90)

    def previous_state(self):
        self.rotate(Rotation.R270)

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        self.texture.draw(surface, self.direction.relative_rotation_to(Direction.N), opacity)

    def debug(self):
        d = super().debug()
        d['direction'] = self.direction.name
        return d


class Processor(Directional):
    __slots__ = ['direction', 'inputs', 'outputs', 'arguments', 'fired']

    pin_input_texture = RotatableTexture.load('pin_input')
    pin_output_texture = RotatableTexture.load('pin_output')

    def __init__(self, direction: Direction, inputs: Dict[Side, Type[Cell]], outputs: Set[Side]):
        super().__init__(direction)
        self.inputs = inputs
        self.outputs = outputs
        self.arguments = {}
        self.fired = False

    @abstractmethod
    def process(self, arguments: Dict[Side, Cell]) -> Dict[Side, Cell]:
        raise NotImplementedError

    def get_pins(self) -> Set[Direction]:
        pins = set()

        for direction in Direction:
            if self.get_direction_side(direction) in self.inputs:
                pins.add(direction)

        for side in self.outputs:
            pins.add(self.get_side_direction(side))

        return pins

    def get_parameter_towards(self, direction: Direction) -> Type[Cell]:
        return self.inputs[self.direction.side_relative_to(direction)]

    def is_fed(self) -> bool:
        return all(
            side in self.arguments
            and isinstance(self.arguments[side], type)
            for side, type in self.inputs.items()
        )

    def is_waiting_for(self, direction: Direction) -> bool:
        return self.get_direction_side(direction) not in self.arguments

    def will_provide(self, direction: Direction) -> bool:
        return self.get_direction_side(direction) in self.outputs

    def has_pin(self, direction: Direction) -> bool:
        return self.is_waiting_for(direction) or self.will_provide(direction)

    def step(self, neighbors: Neighborhood) -> Cell:
        if self.fired:
            return Empty()
        
        for direction, cell in neighbors:
            side = self.get_direction_side(direction)
            try:
                type_ = self.inputs[side]
            except KeyError:
                continue
            else:
                if isinstance(cell, type_):
                    self.arguments[side] = cell

        return self

    def info(self) -> str:
        return f"<{type(self).__name__}>"

    def debug(self):
        d = {
            '__type__': self.name(),
            'direction': self.direction.name,
            'inputs': {side.name: param.name() for side, param in self.inputs.items()},
            'outputs': [side.name for side in self.outputs],
            'is_fed': self.is_fed(),
            'arguments': {side.name: cell.debug() for side, cell in self.arguments.items()},
            'is_waiting_for': list(map(lambda d: d.name, filter(self.is_waiting_for, Direction))),
            'will_provide': list(map(lambda d: d.name, filter(self.will_provide, Direction))),
            'fired': self.fired
        }
        return d

    def draw_pin_overlay(self, surface: pg.Surface):
        for side in self.inputs.keys():
            self.pin_input_texture.draw(surface, self.get_side_direction(side).relative_rotation_to(Direction.N))

        for side in self.outputs:
            self.pin_output_texture.draw(surface, self.get_side_direction(side).relative_rotation_to(Direction.N))

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        super().draw(surface, neighbors, opacity)
        self.draw_pin_overlay(surface)



class Diode(Processor):
    __slots__ = ['direction', 'inputs', 'outputs', 'arguments', 'fired']

    texture = RotatableTexture.load('diode')

    def __init__(self, direction: Direction = Direction.N):
        super().__init__(
            direction,
            inputs={Side.BACK: Value},
            outputs={Side.FRONT}
        )

    def process(self, inputs: Dict[Side, Cell]) -> Dict[Side, Cell]:
        return {
            Side.FRONT: inputs[Side.BACK]
        }


class Transistor(Processor):
    __slots__ = ['direction', 'inputs', 'outputs', 'arguments', 'fired']

    texture = RotatableTexture.load('transistor')

    def __init__(self, direction: Direction = Direction.N):
        super().__init__(
            direction,
            inputs={Side.BACK: Value, Side.LEFT: Boolean},
            outputs={Side.FRONT}
        )

    def process(self, inputs: Dict[Side, Cell]) -> Dict[Side, Cell]:
        if inputs[Side.LEFT].value:
            return {Side.FRONT: inputs[Side.BACK]}
        else:
            return {Side.FRONT: Empty()}

        
class Adder(Processor):
    __slots__ = ['direction', 'inputs', 'outputs', 'arguments', 'fired']
    
    texture = RotatableTexture.load('adder')

    def __init__(self, direction: Direction = Direction.N):
        super().__init__(
            direction,
            inputs={Side.LEFT: Integer, Side.RIGHT: Integer},
            outputs={Side.FRONT}
        )

    def process(self, inputs: Dict[Side, Cell]) -> Dict[Side, Cell]:
        x = inputs[Side.LEFT].value
        y = inputs[Side.RIGHT].value
        return {
            Side.FRONT: Integer(x + y)
        }


class Equals(Processor):
    __slots__ = ['direction', 'inputs', 'outputs', 'arguments', 'fired']

    texture = RotatableTexture.load('equals')

    def __init__(self, direction: Direction = Direction.N):
        super().__init__(
            direction,
            inputs={Side.LEFT: Value, Side.RIGHT: Value},
            outputs={Side.FRONT}
        )

    def process(self, inputs: Dict[Side, Cell]) -> Dict[Side, Cell]:
        return {
            Side.FRONT: Boolean(inputs[Side.LEFT] == inputs[Side.RIGHT])
        }


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

    @abstractmethod
    def __eq__(self, other):
        raise NotImplementedError

    def get_pins(self) -> Set[Direction]:
        return set(Direction)
    
    def step(self, neighbors: Neighborhood) -> Cell:
        processors = neighbors.filter(lambda _, cell: isinstance(cell, Processor))

        for direction, processor in processors:
            if not processor.is_fed():
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

    def __eq__(self, other):
        return isinstance(other, Integer) and self.value == other.value

    @classmethod
    def draw_icon(self, surface: pg.Surface, opacity: float = 1.0):
        texture = self.font.render('x', True, (0, 0, 0))
        texture = pg.transform.scale(texture, (CELL_SIZE - 4, CELL_SIZE - 4))
        blit_alpha(surface, Value.background.texture, (0, 0), opacity)
        blit_alpha(surface, texture, (2, 2), opacity)

    def next_state(self):
        self.value += 1

    def previous_state(self):
        self.value -= 1

    def info(self) -> str:
        return str(self.value)

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        texture = self.font.render(str(self.value), True, (0, 0, 0))
        texture = pg.transform.scale(texture, (CELL_SIZE - 4, CELL_SIZE - 4))
        blit_alpha(surface, Value.background.texture, (0, 0), opacity)
        blit_alpha(surface, texture, (2, 2), opacity)


class Boolean(Value):
    __slots__ = ['value']

    false_texture = SimpleTexture.load('false')
    true_texture = SimpleTexture.load('true')

    def __init__(self, value: bool = True):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, Boolean) and self.value == other.value

    @classmethod
    def draw_icon(self, surface: pg.Surface, opacity: float = 1.0):
        self.true_texture.draw(surface, opacity)

    def next_state(self):
        self.value = not self.value

    def previous_state(self):
        self.value = not self.value

    def into(self) -> str:
        return str(self.value)

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        if self.value:
            self.true_texture.draw(surface, opacity)
        else:
            self.false_texture.draw(surface, opacity)


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

    def debug(self):
        return {
            '__type__': 'Chip',
            'direction': self.direction.name,
            'board': [[self.board.cell[x, y].debug() for x in range(self.board.width)] for y in range(self.board.height)]
        }

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

    def debug(self):
        d = super().debug()
        return d


class Import(Chip):
    __slots__ = ['direction', 'board', 'path']

    texture = RotatableTexture.load('file')

    def __init__(self, path: Path, direction: Direction = Direction.N):
        super().__init__(direction, Program.load(path))
        self.path = path

    def info(self) -> str:
        return f"<Import {self.path.name!r}>"


class List_(Value):
    __slots__ = ['values']

    texture = SimpleTexture.load('list')
    
    def __init__(self, values: List[Value] = ()):
        self.values = list(values)

    def __eq__(self, other):
        return isinstance(other, List_) and all(x == y for x, y in zip(self.values, other.values))

    @classmethod
    def name(cls) -> str:
        return "List"

    def info(self) -> str:
        return f"[{', '.join(map(lambda cell: cell.info(), self.values))}]"

    def debug(self):
        return {
            '__type__': type(self).__name__,
            'values': [value.debug() for value in self.values]
        }

    def copy(self) -> 'List':
        return copy.deepcopy(self)

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        self.texture.draw(surface, opacity)


class Append(Processor):
    __slots__ = ['direction', 'inputs', 'outputs', 'arguments', 'fired']

    texture = RotatableTexture.load('append')

    def __init__(self, direction: Direction = Direction.N):
        super().__init__(
            direction,
            inputs={Side.LEFT: Value, Side.BACK: List_},
            outputs={Side.FRONT}
        )

    def process(self, inputs: Dict[Side, Cell]) -> Dict[Side, Cell]:
        lst = inputs[Side.BACK].copy()
        lst.values.append(inputs[Side.LEFT])
        return {
            Side.FRONT: lst
        }


class Pop(Processor):
    __slots__ = ['direction', 'inputs', 'outputs', 'arguments', 'fired']

    texture = RotatableTexture.load('pop')

    def __init__(self, direction: Direction = Direction.N):
        super().__init__(
            direction,
            inputs={Side.BACK: List_},
            outputs={Side.FRONT, Side.LEFT}
        )

    def process(self, inputs: Dict[Side, Cell]) -> Dict[Side, Cell]:
        lst = inputs[Side.BACK].copy()
        x = lst.values.pop(0)
        return {
            Side.FRONT: lst,
            Side.LEFT: x
        }


class Mu(Cell):
    __slots__ = ['program']

    texture = SimpleTexture.load('mu')

    def __init__(self, program: 'Program' = None):
        self.program = Program.empty(16, 16) if program is None else program.copy()

    def step(self, neighbors: Neighborhood):
        return self

    def draw(self, surface: pg.Surface, neighbors: Neighborhood, opacity: float = 1.0):
        self.texture.draw(surface)
