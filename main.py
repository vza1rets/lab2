import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO, Union
import winreg




@dataclass
class Point:
    x: float
    y: float

    def __str__(self) -> str:
        return f"Point({self.x:g}, {self.y:g})"


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
        return f"Circle({self.center}, {self.radius:g})"


Shape = Union[Point, Line, Circle]



NUM = r"[-+]?\d*\.?\d+"
POINT_RE = re.compile(rf"Point\(\s*({NUM})\s*,\s*({NUM})\s*\)")
LINE_RE = re.compile(
    rf"Line\(\s*Point\(\s*({NUM})\s*,\s*({NUM})\s*\)\s*,\s*"
    rf"Point\(\s*({NUM})\s*,\s*({NUM})\s*\)\s*\)"
)
CIRCLE_RE = re.compile(
    rf"Circle\(\s*Point\(\s*({NUM})\s*,\s*({NUM})\s*\)\s*,\s*({NUM})\s*\)"
)


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



REG_PATH = r"Software\Shapes"
REG_VALUE = "LogPath"


def save_log_path(path: str) -> None:
    abs_path = str(Path(path).expanduser().resolve())
    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE
    ) as key:
        winreg.SetValueEx(key, REG_VALUE, 0, winreg.REG_SZ, abs_path)


def load_log_path() -> str | None:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ
        ) as key:
            value, _ = winreg.QueryValueEx(key, REG_VALUE)
            return value or None
    except FileNotFoundError:
        return None


def resolve_log_stream(cli_path: str | None) -> tuple[TextIO, bool]:
    if cli_path:
        save_log_path(cli_path)
        return open(cli_path, "a", encoding="utf-8"), True

    saved = load_log_path()
    if saved:
        return open(saved, "a", encoding="utf-8"), True

    return sys.stderr, False



def read_shapes(path: str, log: TextIO) -> list[Shape]:
    shapes: list[Shape] = []
    with open(path, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                shapes.append(parse_line(line))
            except ValueError as e:
                print(f"{path}:{lineno}: {e}", file=log)
    return shapes



def op_print(shapes: list[Shape]) -> None:
    for s in shapes:
        print(s)


def op_count(shapes: list[Shape]) -> None:
    print(len(shapes))


OPERATIONS = {
    "print": op_print,
    "count": op_count,
}



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shapes",
        description="Читает файл с фигурами и выполняет операцию над списком.",
    )
    parser.add_argument(
        "-f", "--file",
        required=True,
        metavar="PATH",
        help="путь к обрабатываемому файлу",
    )
    parser.add_argument(
        "-o", "--oper",
        required=True,
        choices=sorted(OPERATIONS),
        help="операция над списком фигур: print или count",
    )
    parser.add_argument(
        "--log",
        nargs="?",
        const="",
        default=None,
        metavar="PATH",
        help="файл для логов; без PATH берётся запомненный ранее",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    log, needs_close = resolve_log_stream(args.log)
    try:
        try:
            shapes = read_shapes(args.file, log)
        except FileNotFoundError:
            print(f"Файл не найден: {args.file}", file=log)
            return 1
        except OSError as e:
            print(f"Ошибка чтения {args.file}: {e}", file=log)
            return 1

        OPERATIONS[args.oper](shapes)
        return 0
    finally:

        if needs_close:
            log.close()


if __name__ == "__main__":
    sys.exit(main())