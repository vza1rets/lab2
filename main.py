import argparse
import sys
import re
from dataclasses import dataclass
from typing import List, Union


@dataclass
class Point:
    x: float
    y: float

    def __str__(self) -> str:
        return f"Point({self.x}, {self.y})"


@dataclass
class Line:
    start: Point
    end: Point

    def __str__(self) -> str:
        return f"Line({self.start}, {self.end})"


@dataclass
class Circle:
    center: Point
    radius: float

    def __str__(self) -> str:
        return f"Circle({self.center}, {self.radius})"


Shape = Union[Point, Line, Circle]

NUM = r"[-+]?\d*\.?\d+"
POINT_RE = re.compile(rf"Point\(\s*({NUM})\s*,\s*({NUM})\s*\)")
LINE_RE  = re.compile(rf"Line\(\s*Point\(\s*({NUM})\s*,\s*({NUM})\s*\)\s*,\s*"
                      rf"Point\(\s*({NUM})\s*,\s*({NUM})\s*\)\s*\)")
CIRCLE_RE = re.compile(rf"Circle\(\s*Point\(\s*({NUM})\s*,\s*({NUM})\s*\)\s*,\s*({NUM})\s*\)")


def parse_line(line: str) -> Shape:
    s = line.strip()
    if not s:
        raise ValueError("пустая строка")

    if m := CIRCLE_RE.fullmatch(s):
        cx, cy, r = map(float, m.groups())
        return Circle(Point(cx, cy), r)

    if m := LINE_RE.fullmatch(s):
        x1, y1, x2, y2 = map(float, m.groups())
        return Line(Point(x1, y1), Point(x2, y2))

    if m := POINT_RE.fullmatch(s):
        x, y = map(float, m.groups())
        return Point(x, y)

    raise ValueError(f"не удалось разобрать: {s!r}")

def read_shapes(path: str) -> list[Shape]:
    shapes: list[Shape] = []
    with open(path, encoding="utf-8") as f:
        for num, raw in enumerate(f, 1):
            line = raw.strip()
            try:
                shapes.append(parse_line(line))
            except ValueError as e:
                print(f"{path}:{num}: {e}")
    return shapes


if __name__ == "__main__":
    shapes = read_shapes("shapes.txt")
    for s in shapes:
        print(s)
    print(f"Всего: {len(shapes)}")