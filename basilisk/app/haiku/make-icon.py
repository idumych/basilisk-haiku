#!/usr/bin/env python3
"""make-icon.py: writes Basilisk's Haiku vector icon (HVIF) as an .rdef.

Based on the beos-app-platforms make-hvif-icon.py encoder (Haiku's flat
icon format, src/libs/icon/flat_icon/FlatIconFormat.h). The outlines are
traced from basilisk/branding/official/default256.png.

    python3 basilisk/app/haiku/make-icon.py basilisk/app/haiku/icon.rdef [preview.svg]
"""
import math
import struct
import sys

STYLE_SOLID = 1
STYLE_GRADIENT = 2
GRADIENT_LINEAR = 0
GRADIENT_FLAG_TRANSFORM = 1 << 1
PATH_FLAG_CLOSED = 1 << 1
PATH_FLAG_NO_CURVES = 1 << 3
SHAPE_PATH_SOURCE = 10


def coord(value):
    if value == int(value) and -32 <= value <= 95:
        return bytes([int(value) + 32])
    fixed = int(round((value + 128.0) * 102.0))
    return bytes([0x80 | (fixed >> 8), fixed & 0xff])


def float24(value):
    if value == 0:
        return b"\0\0\0"
    bits = struct.unpack("<I", struct.pack("<f", value))[0]
    sign = bits >> 31
    exponent = ((bits >> 23) & 0xff) - 127 + 32
    mantissa = (bits & 0x7fffff) >> 6
    packed = (sign << 23) | (exponent << 17) | mantissa
    return bytes([packed >> 16, (packed >> 8) & 0xff, packed & 0xff])


def solid(r, g, b, a=255):
    return {"kind": "solid", "color": (r, g, b, a)}


def vertical_gradient(top, bottom, y0, y1):
    """A linear gradient from y0 (colour top) to y1 (colour bottom)."""
    return {"kind": "gradient", "stops": [(0, top), (255, bottom)],
            "y0": y0, "y1": y1}


def encode_style(style):
    if style["kind"] == "solid":
        return bytes([STYLE_SOLID]) + bytes(style["color"])
    # Gradient space runs from -64 to 64 along x; map it onto y0..y1.
    half = (style["y1"] - style["y0"]) / 128.0
    matrix = [0.0, half, -half, 0.0, 32.0, (style["y0"] + style["y1"]) / 2]
    out = bytes([STYLE_GRADIENT, GRADIENT_LINEAR, GRADIENT_FLAG_TRANSFORM,
                 len(style["stops"])])
    for value in matrix:
        out += float24(value)
    for offset, color in style["stops"]:
        out += bytes([offset]) + bytes(color)
    return out


def encode_path(points):
    assert 2 <= len(points) <= 255
    out = bytes([PATH_FLAG_CLOSED | PATH_FLAG_NO_CURVES, len(points)])
    for x, y in points:
        out += coord(round(x, 2)) + coord(round(y, 2))
    return out


def circle(cx, cy, r, steps=48):
    return [(cx + r * math.cos(2 * math.pi * i / steps),
             cy + r * math.sin(2 * math.pi * i / steps)) for i in range(steps)]


# Outlines traced from basilisk/branding/official/default256.png, scaled
# from 256 px to the 64-unit HVIF grid (see tools note in the header).
HEAD = [
    (41.25, 54), (44, 56.5), (43.25, 56.5), (40.25, 58), (39.25, 58), (39.25, 58.25),
    (38.25, 58.25), (37.25, 58.75), (35.75, 58.75), (35.75, 59), (26.75, 58.75), (26.75, 58.5),
    (23, 57.75), (22.5, 57.25), (21.75, 57.25), (17.75, 55.25), (17.5, 54.75), (16.25, 54.25),
    (15.75, 53.5), (15.25, 53.5), (14.5, 52.5), (14, 52.5), (10.5, 48.75), (10.5, 48.25),
    (9.75, 47.75), (9.75, 47.25), (8.75, 46.25), (8.25, 44.75), (7.75, 44.5), (6, 39.75),
    (6.25, 39.75), (6.25, 38.25), (6.5, 38.25), (7, 31.75), (7.25, 31.75), (7.25, 30.25),
    (7.5, 30.25), (8.5, 24.5), (8.75, 24.5), (10, 20.5), (12.75, 17.25), (14.75, 16.25),
    (15.75, 16.25), (15.75, 16), (24.25, 14.75), (24.25, 14.5), (26.25, 14.25), (26.25, 14),
    (28, 13.75), (28.75, 13.25), (31.25, 13.25), (31.25, 13.5), (33.25, 13.75), (35.25, 14.75),
    (36, 14.75), (37.5, 15.5), (37.75, 16), (38.25, 16), (38.5, 16.5), (39, 16.5),
    (39.25, 17), (39.75, 17), (40.25, 17.75), (40.75, 17.75), (41.75, 18.75), (43.25, 19),
    (44.5, 19.75), (44.75, 22), (46.25, 24.5), (47.5, 30), (48.75, 31.5), (48.75, 32),
    (52.5, 35.75), (55, 37), (57.5, 37.75), (57.5, 38), (54.75, 37.75), (54.75, 37.5),
    (53.75, 37.5), (53.75, 37.25), (52, 36.75), (52, 37.75), (53, 39.5), (53.75, 42),
    (53.25, 41.75), (53, 40.75), (52.5, 40.5), (51.25, 38), (50.5, 37.5), (50.5, 37),
    (49.75, 36.5), (49.75, 36), (48.75, 35.25), (48.75, 34.75), (47.75, 34), (47.75, 33.5),
    (46.25, 31.75), (45.5, 30.25), (44.5, 26.5), (43.25, 24.5), (42.5, 24.5), (42.5, 24.75),
    (41.75, 24.75), (41.25, 25.25), (40.25, 25.25), (39.5, 25.75), (38.5, 25.75), (37.75, 26.25),
    (35.75, 26.5), (35.75, 26.75), (34.25, 27), (32.25, 28), (27.75, 31.75), (27.75, 32.25),
    (27, 32.75), (26, 34.75), (26, 36.75), (26.5, 37), (26.75, 38), (27.5, 38.5),
    (27.75, 39.5), (28.25, 39.75), (28.5, 40.75), (29, 41), (29.5, 42.5), (30, 42.75),
    (31, 44.75), (34.5, 48.25), (35, 48.25), (37, 50.25), (37.5, 50.25),
]

TONGUE_TIP = [
    (36.75, 5.25), (38.25, 5.5), (38.25, 5.75), (35.5, 5.5), (35.5, 5.25), (29, 5.25),
    (29, 5.5), (26, 5.75), (26, 6), (25, 6), (25, 6.25), (22, 7),
    (18, 9), (17.75, 9.5), (16.75, 9.75), (17, 9.25), (19.25, 8.25), (20, 7.5),
    (20.75, 7.5), (23, 6.25), (26.75, 5.5), (26.75, 5.25), (28.25, 5.25), (28.25, 5),
]

EYE = [
    (32.25, 20.5), (31.5, 20.5), (31, 20), (31.25, 19.25), (33.75, 19.25), (34, 19.5),
    (33.75, 20.25),
]


def build():
    styles = [
        solid(21, 150, 119),        # 0 Basilisk green
        solid(255, 255, 255),       # 1 white
        solid(10, 96, 74),          # 2 dark rim
    ]
    shapes = [
        (2, circle(32, 32, 31.8)),
        (0, circle(32, 32, 31.2)),
        (1, circle(32, 32, 27.1)),
        (0, HEAD),
        (0, TONGUE_TIP),
        (1, EYE),
    ]
    return styles, shapes


def encode(styles, shapes):
    out = b"ncif"
    out += bytes([len(styles)])
    for style in styles:
        out += encode_style(style)
    out += bytes([len(shapes)])
    for _, points in shapes:
        out += encode_path(points)
    out += bytes([len(shapes)])
    for index, (style, _) in enumerate(shapes):
        out += bytes([SHAPE_PATH_SOURCE, style, 1, index, 0])
    return out


def svg(styles, shapes):
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" '
             'width="256" height="256">', '<defs>']
    for index, style in enumerate(styles):
        if style["kind"] == "gradient":
            (o0, c0), (o1, c1) = style["stops"]
            lines.append(
                f'<linearGradient id="g{index}" gradientUnits="userSpaceOnUse"'
                f' x1="0" y1="{style["y0"]}" x2="0" y2="{style["y1"]}">'
                f'<stop offset="0" stop-color="rgb{c0[:3]}"/>'
                f'<stop offset="1" stop-color="rgb{c1[:3]}"/>'
                '</linearGradient>')
    lines.append('</defs>')
    for style_index, points in shapes:
        style = styles[style_index]
        if style["kind"] == "gradient":
            fill = f'url(#g{style_index})'
            opacity = 1
        else:
            fill = f'rgb{style["color"][:3]}'
            opacity = style["color"][3] / 255
        path = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        lines.append(f'<polygon points="{path}" fill="{fill}" '
                     f'fill-opacity="{opacity:.2f}"/>')
    lines.append('</svg>')
    return "\n".join(lines)


def main():
    styles, shapes = build()
    data = encode(styles, shapes)
    hex_data = data.hex().upper()
    rows = [hex_data[i:i + 64] for i in range(0, len(hex_data), 64)]
    with open(sys.argv[1], "w") as rdef:
        rdef.write("// Generated by basilisk/app/haiku/make-icon.py; don't edit.\n")
        rdef.write("resource vector_icon {\n")
        for row in rows:
            rdef.write(f'\t$"{row}"\n')
        rdef.write("};\n")
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w") as preview:
            preview.write(svg(styles, shapes))
    print(f"{len(data)} bytes of HVIF")


if __name__ == "__main__":
    main()
