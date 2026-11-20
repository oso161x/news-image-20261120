#!/usr/bin/env python3
"""The World -- Friday 20 November 2026.

A make.fun entry for @kebomas786. One Python 3 program, standard
library only, that draws the front page of a newspaper summing up
the world's news of Friday 20 November 2026 and writes it to
/output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).

Stories, researched 20 Nov 2026 against live reporting:
  1. Lead -- Severe Cyclonic Storm Akvan crosses the Andhra
     Pradesh-Odisha coast near Gopalpur at noon; 300,000+ people
     evacuated, 423 rescue teams deployed, 69 trains cancelled.
     Sources: India Meteorological Department via The Daily Jagran,
     Urban Acres, Wikipedia (Cyclone Akvan).
  2. Business -- Anthropic raises $81.3 billion in the largest IPO
     on record; shares rise 17% on debut as US stocks fall.
     Sources: SimpleLife.news daily digest, Times of India school
     headlines (Anthropic $1.5tn valuation / IPO coverage).
  3. War in Ukraine -- Missile debris sets a three-storey building
     ablaze in Kyiv's Obolonskyi district in the early hours of
     Friday; a projectile also lands near the Dutch embassy.
     Source: Reuters, 20 Nov 2026.
  4. Diplomacy -- Trump, Xi and Putin sign a four-point "peace
     declaration" in Shenzhen saying a nuclear war must never be
     fought; it says nothing about Ukraine or Iran and sets no
     arms-control talks. Trump holds a White House news conference
     at noon on Friday. Sources: Reuters (via Devdiscourse wrapup),
     AP, Xinhua/TASS via AmeriLedger, Aju Press (full text).
  5. Also today -- GTA VI takes an estimated $2.36bn in first-day
     sales (Sensor Tower, via Business Today / Deadline); a Houthi
     strike damages a landmark tower in Riyadh, Saudi Arabia
     confirms; Trump pardons baseball star Pete Rose posthumously;
     Henry Nicholls hits 113 not out as New Zealand reach 317-6
     against India in Wellington (Reuters).

Everything on the page is drawn procedurally by this file: its own
tiny scanline rasterizer, its own 5x7 bitmap font, and its own
minimal PNG writer. No network, no external files, no copied
artwork. The output is byte-identical on every run.
"""

import math
import os
import struct
import zlib

# ---------------------------------------------------------------- canvas

W = H = 1024
PAPER = (247, 242, 231)
INK = (24, 24, 22)
RULE = (24, 24, 22)
SOFT = (96, 90, 78)
SEA = (178, 205, 224)
LAND = (232, 214, 176)
COAST = (120, 110, 80)
STORM = (52, 84, 128)
FLAME = (214, 96, 32)
EMBER = (240, 178, 60)
SMOKE = (120, 118, 112)
STEEL = (150, 152, 148)
DARKSTEEL = (96, 98, 96)
SKY = (214, 222, 228)
GREEN = (46, 110, 62)
RED = (178, 44, 36)
BLUE = (38, 74, 148)
GOLD = (212, 168, 60)


class Sheet:
    """A plain RGB pixel buffer with a few drawing helpers."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill(bg)

    def fill(self, c):
        r, g, b = c
        self.buf[:] = bytes((r, g, b)) * (self.w * self.h)

    def dot(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = c

    def block(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def hrule(self, x, y, w, c, t=1):
        self.block(x, y, w, t, c)

    def vrule(self, x, y, h, c, t=1):
        self.block(x, y, t, h, c)

    def frame(self, x, y, w, h, c, t=1):
        self.hrule(x, y, w, c, t)
        self.hrule(x, y + h - t, w, c, t)
        self.vrule(x, y, h, c, t)
        self.vrule(x + w - t, y, h, c, t)

    def line(self, x0, y0, x1, y1, c):
        dx = x1 - x0
        dy = y1 - y0
        n = max(abs(dx), abs(dy), 1)
        for s in range(n + 1):
            self.dot(x0 + round(dx * s / n), y0 + round(dy * s / n), c)

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.dot(xx, yy, c)

    def ring(self, cx, cy, r, c, t=2):
        for a in range(360):
            th = math.radians(a)
            for k in range(t):
                self.dot(cx + round((r + k) * math.cos(th)),
                         cy + round((r + k) * math.sin(th)), c)

    def poly(self, pts, c):
        """Scanline-fill a polygon given as [(x, y), ...]."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for yy in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            for i in range(len(pts)):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % len(pts)]
                if y0 == y1:
                    continue
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.block(int(math.ceil(xs[k])), yy,
                           int(math.floor(xs[k + 1])) - int(math.ceil(xs[k])) + 1,
                           1, c)

    def swirl(self, cx, cy, turns, rmax, c, step=2):
        """A cyclone spiral: radius grows with angle."""
        prev = None
        a = 0.0
        while a <= turns * 360:
            r = rmax * a / (turns * 360)
            th = math.radians(a)
            p = (cx + round(r * math.cos(th)), cy + round(r * math.sin(th)))
            if prev is not None:
                self.line(prev[0], prev[1], p[0], p[1], c)
            prev = p
            a += step


# ------------------------------------------------------------------ font

# A 5x7 bitmap font, drawn up by hand for this page. '#' is ink.
FONT = {
    "A": ("..#..", ".#.#.", "#...#", "#...#", "#####", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".###."),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".###."),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".....", ".####", "#...#", "#...#", ".###.", "....#"),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": (".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."),
    "j": (".....", "...#.", ".....", "..##.", "...#.", "...#.", "##..."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".###.", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#...#", ".###."),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", ".#.#.", "..#..", "..#.."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "&": (".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "$": ("..#..", ".####", "#.#.#", ".###.", "..#.#", "####.", "..#.."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "[": (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    "]": (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
    "•": (".....", "..#..", ".###.", ".###.", ".###.", "..#..", "....."),
}

BLANK = (".....",) * 7


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(sheet, x, y, s, scale, color):
    """Draw left-aligned text; returns the x just past the last glyph."""
    cx = x
    for ch in s:
        glyph = FONT.get(ch, BLANK)
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "#":
                    sheet.block(cx + gx * scale, y + gy * scale,
                                scale, scale, color)
        cx += 6 * scale
    return cx


def draw_centred(sheet, cx, y, s, scale, color):
    return draw_text(sheet, cx - text_width(s, scale) // 2, y, s, scale, color)


def wrap_lines(s, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    per = 6 * scale
    max_chars = max(1, (max_w + scale) // per)
    words = s.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            # A single over-long word is hard-split.
            while len(word) > max_chars:
                lines.append(word[:max_chars])
                word = word[max_chars:]
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(sheet, x, y, s, scale, max_w, color, gap=None):
    """Draw a wrapped paragraph; returns the y just past its last line."""
    if gap is None:
        gap = 7 * scale + 2
    for line in wrap_lines(s, scale, max_w):
        draw_text(sheet, x, y, line, scale, color)
        y += gap
    return y


def kicker(sheet, x, y, s):
    draw_text(sheet, x, y, s, 2, RED)
    return y + 18


# ------------------------------------------------------------------ art

def cyclone_art(sheet, x, y, w, h):
    """Bay of Bengal coast with the storm spiral over it."""
    sheet.frame(x, y, w, h, INK, 2)
    sheet.block(x + 2, y + 2, w - 4, h - 4, SEA)
    # Land mass on the right: the Indian east coast.
    sheet.poly([(x + w - 4, y + 2), (x + w - 4, y + h - 2),
                (x + w - 150, y + h - 2), (x + w - 120, y + h - 90),
                (x + w - 95, y + 130), (x + w - 60, y + 60),
                (x + w - 30, y + 2)], LAND)
    # Coastline.
    sheet.line(x + w - 150, y + h - 2, x + w - 120, y + h - 90, COAST)
    sheet.line(x + w - 120, y + h - 90, x + w - 95, y + 130, COAST)
    sheet.line(x + w - 95, y + 130, x + w - 60, y + 60, COAST)
    sheet.line(x + w - 60, y + 60, x + w - 30, y + 2, COAST)
    # Storm spiral over the sea, just off the coast.
    cx, cy = x + 150, y + 130
    sheet.swirl(cx, cy, 3.2, 105, STORM, step=3)
    sheet.swirl(cx, cy, 3.2, 78, (110, 150, 190), step=3)
    sheet.disc(cx, cy, 13, PAPER)
    sheet.ring(cx, cy, 13, STORM, 2)
    # Wind arrows curling in.
    sheet.line(cx - 150, cy - 60, cx - 120, cy - 40, STORM)
    sheet.line(cx - 120, cy - 40, cx - 95, cy - 30, STORM)
    sheet.line(cx + 150, cy + 55, cx + 120, cy + 38, STORM)
    sheet.line(cx + 120, cy + 38, cx + 98, cy + 28, STORM)
    # Labels.
    draw_text(sheet, x + 12, y + 12, "BAY OF BENGAL", 1, INK)
    draw_text(sheet, x + w - 118, y + h - 52, "ODISHA", 1, INK)
    draw_text(sheet, x + w - 128, y + h - 30, "ANDHRA PRADESH", 1, INK)
    draw_text(sheet, x + 12, y + h - 22, "LANDFALL: GOPALPUR, NOON", 1, INK)


def bars_art(sheet, x, y, w, h):
    """Rising bars: the IPO that broke the record books."""
    sheet.frame(x, y, w, h, INK, 2)
    sheet.block(x + 2, y + 2, w - 4, h - 4, (238, 236, 228))
    base = y + h - 12
    heights = [14, 24, 34, 48, 66]
    bw = 52
    gap = 18
    x0 = x + 22
    for i, hh in enumerate(heights):
        bx = x0 + i * (bw + gap)
        col = GREEN if i < 4 else GOLD
        sheet.block(bx, base - hh, bw, hh, col)
        sheet.frame(bx, base - hh, bw, hh, INK, 1)
    sheet.hrule(x + 12, base, w - 24, INK, 2)
    draw_text(sheet, x + 22, y + 8, "$81.3 BILLION", 2, INK)
    draw_text(sheet, x + 22, y + 26, "SHARES +17% ON DEBUT", 1, SOFT)


def kyiv_art(sheet, x, y, w, h):
    """A Kyiv block at dawn: one building burning, smoke rising."""
    sheet.frame(x, y, w, h, INK, 2)
    sheet.block(x + 2, y + 2, w - 4, h - 4, SKY)
    sheet.disc(x + w - 42, y + 26, 12, EMBER)  # low winter sun
    # Far buildings, kept low so nothing leaves the box.
    sheet.block(x + 18, y + h - 30, 60, 28, STEEL)
    sheet.block(x + 330, y + h - 36, 70, 34, STEEL)
    sheet.block(x + 340, y + h - 36, 8, 8, INK)
    # The struck block, centre, squat so flame and smoke fit inside.
    bx, bw = x + 130, 130
    by = y + h - 34
    sheet.block(bx, by, bw, 32, DARKSTEEL)
    sheet.frame(bx, by, bw, 32, INK, 1)
    for r in range(2):
        for c in range(5):
            wx = bx + 12 + c * 22
            wy = by + 6 + r * 13
            sheet.block(wx, wy, 10, 8, EMBER if (r == 0 and c in (1, 3)) else PAPER)
    # Flames from the roof, apex 20 px above the roofline.
    sheet.poly([(bx + 18, by), (bx + 38, by - 20), (bx + 52, by - 7),
                (bx + 66, by - 22), (bx + 84, by - 6), (bx + 104, by),
                (bx + 84, by - 2), (bx + 60, by - 11), (bx + 38, by - 3)],
               FLAME)
    sheet.poly([(bx + 40, by), (bx + 52, by - 12), (bx + 66, by - 4),
                (bx + 78, by - 10), (bx + 88, by)], EMBER)
    # Two small smoke puffs, still inside the box.
    sheet.disc(bx + 52, by - 28, 7, SMOKE)
    sheet.disc(bx + 78, by - 30, 6, SMOKE)
    draw_text(sheet, x + 12, y + 8, "OBOLONSKYI, KYIV", 1, INK)


def flags_art(sheet, x, y, w, h):
    """Three flags on poles: the United States, China, Russia."""
    sheet.frame(x, y, w, h, INK, 2)
    sheet.block(x + 2, y + 2, w - 4, h - 4, (238, 236, 228))
    poles = [x + 30, x + 120, x + 210]
    # United States: stripes + blue canton.
    px = poles[0]
    for s in range(7):
        sheet.block(px, y + 18 + s * 7, 62, 7,
                    RED if s % 2 == 0 else PAPER)
    sheet.block(px, y + 18, 28, 21, BLUE)
    # China: red field, gold stars.
    px = poles[1]
    sheet.block(px, y + 18, 62, 49, RED)
    sheet.disc(px + 14, y + 32, 5, GOLD)
    sheet.disc(px + 30, y + 24, 3, GOLD)
    sheet.disc(px + 36, y + 32, 3, GOLD)
    sheet.disc(px + 30, y + 40, 3, GOLD)
    # Russia: white, blue, red bands.
    px = poles[2]
    sheet.block(px, y + 18, 62, 16, PAPER)
    sheet.block(px, y + 34, 62, 17, BLUE)
    sheet.block(px, y + 51, 62, 16, RED)
    for px in poles:
        sheet.vrule(px - 3, y + 12, h - 24, INK, 3)
        sheet.disc(px - 2, y + 11, 4, GOLD)
    draw_text(sheet, x + 18, y + h - 20, "SHENZHEN, 19 NOVEMBER", 1, SOFT)


# ----------------------------------------------------------------- page

def build():
    s = Sheet(W, H, PAPER)
    # Outer double border.
    s.frame(12, 12, W - 24, H - 24, INK, 2)
    s.frame(20, 20, W - 40, H - 40, INK, 1)

    # Masthead.
    draw_centred(s, W // 2, 36, "THE WORLD", 12, INK)
    s.hrule(34, 132, W - 68, INK, 2)
    draw_text(s, 34, 140, "No. 324", 2, SOFT)
    draw_centred(s, W // 2, 140, "FRIDAY 20 NOVEMBER 2026", 2, INK)
    draw_text(s, W - 34 - text_width("PRICE: ONE PICTURE", 2), 140,
              "PRICE: ONE PICTURE", 2, SOFT)
    s.hrule(34, 162, W - 68, INK, 3)
    s.hrule(34, 168, W - 68, INK, 1)

    # ---- Lead: Cyclone Akvan -------------------------------------
    ly = 184
    kicker(s, 34, ly, "WEATHER  •  INDIA")
    draw_text(s, 34, ly + 24, "CYCLONE AKVAN", 5, INK)
    draw_text(s, 34, ly + 64, "HITS EAST COAST", 5, INK)
    deck = ("Severe Cyclonic Storm Akvan crossed the Andhra "
            "Pradesh-Odisha coast near Gopalpur at noon, with "
            "winds of 100 kmph. More than 300,000 people were "
            "moved to shelters, 423 rescue teams were deployed "
            "and 69 trains were cancelled.")
    para(s, 34, ly + 116, deck, 2, 560, INK)
    draw_text(s, 34, ly + 236, "WINDS 100 KMPH  •  GUSTS 110  •  LANDFALL NOON",
              2, SOFT)
    cyclone_art(s, 620, ly, 370, 268)

    s.hrule(34, 466, W - 68, INK, 2)

    # ---- Middle row: Anthropic | Kyiv ------------------------------
    my = 482
    # Left: the IPO.
    kicker(s, 34, my, "BUSINESS  •  MARKETS")
    draw_text(s, 34, my + 24, "ANTHROPIC'S $81BN", 4, INK)
    draw_text(s, 34, my + 56, "RECORD IPO", 4, INK)
    bars_art(s, 34, my + 96, 466, 84)
    para(s, 34, my + 192,
         "The AI firm raised $81.3 billion in the largest flotation "
         "on record. Shares rose 17% on their first day.", 2, 466, INK)
    # Right: Kyiv.
    s.vrule(512, my, 224, INK, 1)
    kicker(s, 530, my, "WAR IN UKRAINE")
    draw_text(s, 530, my + 24, "MISSILES HIT KYIV", 4, INK)
    draw_text(s, 530, my + 56, "AGAIN AT DAWN", 4, INK)
    kyiv_art(s, 530, my + 96, 460, 84)
    para(s, 530, my + 192,
         "Missile debris set a building ablaze in Obolonskyi; a "
         "projectile also struck near the Dutch embassy.", 2, 460, INK)

    s.hrule(34, 722, W - 68, INK, 2)

    # ---- Shenzhen band ---------------------------------------------
    sy = 738
    kicker(s, 34, sy, "DIPLOMACY  •  SHENZHEN")
    draw_text(s, 34, sy + 24, "A PEACE DECLARATION", 4, INK)
    draw_text(s, 34, sy + 56, "THAT SKIPS THE WARS", 4, INK)
    para(s, 34, sy + 88,
         "Trump, Xi and Putin signed a four-point declaration saying "
         "a nuclear war must never be fought. It says nothing about "
         "Ukraine or Iran, and sets no arms talks. Trump faces the "
         "press at noon today.", 2, 640, INK)
    flags_art(s, 700, sy, 290, 132)

    s.hrule(34, 890, W - 68, INK, 2)

    # ---- Also today --------------------------------------------------
    ay = 902
    draw_text(s, 34, ay, "ALSO TODAY", 2, RED)
    items = [
        "GTA VI takes $2.36bn on day one, Sensor Tower estimates",
        "Houthi strike damages Riyadh landmark tower",
        "Trump pardons baseball star Pete Rose, posthumously",
        "Nicholls 113* as New Zealand reach 317-6 v India",
    ]
    col_w = 239
    for i, item in enumerate(items):
        x = 34 + i * col_w
        if i:
            s.vrule(x - 8, ay + 2, 58, SOFT, 1)
        yy = ay + 22
        for line in wrap_lines(item, 2, col_w - 18):
            draw_text(s, x, yy, line, 2, INK)
            yy += 15

    # ---- Footer -------------------------------------------------------
    s.hrule(34, 976, W - 68, INK, 1)
    draw_centred(s, W // 2, 986,
                 "Sources: Reuters, IMD, Sensor Tower via Deadline, AP, Xinhua. Drawn by code; no photograph.",
                 1, SOFT)
    return s


# ------------------------------------------------------------------ png

def write_png(sheet, path):
    raw = bytearray()
    for y in range(sheet.h):
        raw.append(0)  # filter: none
        raw += sheet.buf[y * sheet.w * 3:(y + 1) * sheet.w * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", sheet.w, sheet.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(build(), path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
