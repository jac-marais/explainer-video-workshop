#!/usr/bin/env python3
"""Tile t*.png stills in numeric time order into DIR/sheet.png, labelled in seconds.

  scripts/run/py scripts/film/sheet.py DIR [COLS]

COLS defaults to 4 and must be a positive integer. Each tile is 640x360 with a
24-pixel label strip. Empty folders and nonnumeric still names fail clearly.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def contact_sheet(directory, columns=4):
    if not isinstance(columns, int) or columns < 1:
        raise ValueError("columns must be a positive integer")
    files = list(directory.glob("t*.png"))
    if not files:
        raise ValueError(f"no t*.png stills in {directory}")
    try:
        times = {path: float(path.stem[1:]) for path in files}
    except ValueError as error:
        raise ValueError("t*.png names must contain numeric times") from error
    if any(not (0 <= time < float("inf")) for time in times.values()):
        raise ValueError("still times must be finite and nonnegative")
    files.sort(key=lambda path: times[path])
    width, height, label_height = 640, 360, 24
    rows = (len(files) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * width, rows * (height + label_height)), (40, 40, 40))
    drawing = ImageDraw.Draw(sheet)
    for index, path in enumerate(files):
        with Image.open(path) as image:
            tile = image.convert("RGB").resize((width, height))
        left, top = (index % columns) * width, (index // columns) * (height + label_height)
        sheet.paste(tile, (left, top + label_height))
        drawing.text((left + 6, top + 6), f"{times[path]:g} s", fill=(255, 255, 255))
    output = directory / "sheet.png"
    sheet.save(output)
    return output, len(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("directory", type=Path)
    parser.add_argument("columns", type=int, nargs="?", default=4)
    arguments = parser.parse_args()
    try:
        output, count = contact_sheet(arguments.directory, arguments.columns)
    except (ValueError, OSError) as error:
        raise SystemExit(str(error)) from error
    print(output, count)


if __name__ == "__main__":
    main()
