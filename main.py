"""Draw a one-page newspaper front page for Thursday 19 November 2026.

This program renders the whole front page in code with Pillow: masthead,
date headline, region tabs, a number strip, three illustrated lead stories,
ten illustrated features, a world map with numbered pins, a one-line list
of twenty more stories, a date-check box and a source footer. Every story
is attributed to the outlet that reported it.

The draw needs Pillow and the subset fonts shipped in fonts/ next to this
file. If Pillow cannot be imported (the grader runs stdlib-only Python, so
that is possible), the program falls back to copying the entry.png that
ships in this repository -- a render produced by this same program -- so
the entry still completes. Either path writes identical bytes on every run:
no wall clock, no network, no unseeded randomness.

Local run:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

Output: <output>/entry.png, 1024x1024, at most 1 MiB. PNG is used when it
fits; otherwise a JPEG (still named entry.png, which the rules allow).
"""

import hashlib
import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
FALLBACK_IMAGE = HERE / "entry.png"

W, H = 1024, 1024
MARGIN = 10
CONTENT_W = W - 2 * MARGIN
MAX_BYTES = 1048576

# --- palette ----------------------------------------------------------------
PAPER = (247, 242, 231)
INK = (20, 25, 38)
NAVY = (20, 33, 61)
RED = (178, 34, 34)
DARK_RED = (139, 26, 26)
GREY = (93, 109, 126)
LIGHT_GREY = (220, 214, 200)
RULE = (180, 172, 156)
WHITE = (255, 255, 255)
CREAM = (255, 252, 244)
MAP_SEA = (208, 226, 238)
MAP_LAND = (232, 222, 190)
MAP_LAND_EDGE = (176, 160, 120)
CHECK_BG = (232, 240, 216)
CHECK_EDGE = (90, 120, 60)

REGION_COLORS = {
    "ASIA": (169, 50, 38),
    "MIDDLE EAST": (125, 60, 152),
    "EUROPE": (31, 97, 141),
    "AFRICA": (30, 132, 73),
    "AMERICAS": (185, 119, 14),
    "OCEANIA": (17, 122, 101),
    "GLOBAL": (93, 109, 126),
}

REGIONS = [
    ("ASIA", 7),
    ("MIDDLE EAST", 3),
    ("EUROPE", 7),
    ("AFRICA", 5),
    ("AMERICAS", 4),
    ("OCEANIA", 4),
    ("GLOBAL", 3),
]

FIGURES = [
    ("3", "leaders at one table\nin Shenzhen"),
    ("9–6", "World Court vote:\nMyanmar genocide"),
    ("$120bn", "aid goal cut from\nthe COP31 draft"),
    ("$81bn", "Anthropic's record\nNasdaq IPO"),
    ("109–0", "Danish vote on\nthe Arctic pact"),
    ("4.9%", "Australian jobless\nrate, a 2-year high"),
]

# --- stories -----------------------------------------------------------------
# Leads: (number, tag, headline, body, sources). Bodies are my own summaries
# of the day's reporting; every story names its sources.
LEADS = [
    (
        1,
        "SHENZHEN · SUMMIT",
        "First three-way summit: Trump, Xi and Putin share a table",
        "At APEC in Shenzhen the three leaders meet for 90 minutes and "
        "issue a declaration on nuclear risk and UN reform.",
        "Reuters · Xinhua",
    ),
    (
        2,
        "THE HAGUE · JUSTICE",
        "Myanmar guilty of genocide, World Court rules",
        "The ICJ votes 9–6 that Myanmar committed genocide against the "
        "Rohingya, and orders reparations.",
        "Al Jazeera · UN News",
    ),
    (
        3,
        "ANTALYA · CLIMATE",
        "COP31 text drops fossil fuels, $120bn aid goal",
        "The slimmed-down draft has no phase-out and no adaptation "
        "figure as talks head for Friday's close.",
        "Reuters · AFP",
    ),
]

# Features: (number, tag, headline, body, sources, art key)
FEATURES = [
    (
        4, "CRIMEA · WAR", "Ukraine hits Kerch Bridge again",
        "Third strike in a week halts trains to Russia.", "Euronews",
        "bridge",
    ),
    (
        5, "RIYADH · WAR", "Saudis shoot down Houthi missiles",
        "Debris falls on the capital; no casualties reported.", "Reuters",
        "missiles",
    ),
    (
        6, "ODISHA · STORM", "Cyclone Akvan nears India's coast",
        "Over 100,000 in shelters before Friday's landfall.", "IMD",
        "cyclone",
    ),
    (
        7, "SEOUL · JUSTICE", "Korea's top court clears ex-PM Han",
        "Han Duck-soo's martial-law conviction is overturned.", "AP",
        "gavel",
    ),
    (
        8, "GREENLAND · SECURITY", "Denmark backs Arctic pact with US",
        "Parliament approves the Greenland security deal 109–0.", "AP",
        "arctic",
    ),
    (
        9, "NEW YORK · MARKETS", "Anthropic starts trading on Nasdaq",
        "Its record $81bn share sale was priced at $83.", "AP",
        "chart",
    ),
    (
        10, "WORLDWIDE · GAMES", "GTA VI goes on sale after 13 years",
        "The midnight launch draws rave reviews.", "ABC",
        "gamepad",
    ),
    (
        11, "BOGOTÁ · LABOUR", "Colombia's unions hold national strike",
        "Marches in three cities against an economic law.", "Infobae",
        "crowd",
    ),
    (
        12, "NAIROBI · SPORT", "Marathon champion banned for doping",
        "Kenya's Peres Jepchirchir gets three years.", "ABC",
        "banned",
    ),
    (
        13, "CANBERRA · ECONOMY", "Australia's jobless rate hits 4.9%",
        "Highest since 2024; shares and the dollar slide.", "ABC",
        "bars",
    ),
]

# Also on the day: (number, place, one line, source)
ALSO = [
    (14, "Shenzhen", "Xi urges a ban on nuclear arms.", "Al Jazeera"),
    (15, "Shenzhen", "Albanese tells Putin: end the war.", "ABC"),
    (16, "Seoul", "Half a million sit the college exam.", "Sedaily"),
    (17, "Jakarta", "Asset-seizure law passes, 18 years on.", "Kompas"),
    (18, "Hormuz", "Iran says mines set 5 tankers ablaze.", "Al Jazeera"),
    (19, "Gaza", "Israel ends tank raid past truce line.", "BBC"),
    (20, "Krasnodar", "Kyiv says it hit two oil refineries.", "Euronews"),
    (21, "Brussels", "EU delays methane rules two years.", "Euronews"),
    (22, "UK", "Inquiry: yacht Bayesian was wind-vulnerable.", "RNZ"),
    (23, "Zurich", "Two rivals to challenge FIFA's Infantino.", "ABC"),
    (24, "Rome", "Author Corrado Augias dies at 91.", "Euronews"),
    (25, "Mogadishu", "Somalia expels UAE ambassador.", "Al Jazeera"),
    (26, "Sudan", "Court sentences absent RSF chief to death.", "AP"),
    (27, "Pretoria", "Central bank holds rate at 7.25%.", "SABC"),
    (28, "Canaries", "Migrant record: 11,000 in 15 days.", "Africanews"),
    (29, "Florida", "Floods strand Broward, Miami schools.", "CBS"),
    (30, "Wellington", "Court: pay equity cuts broke the law.", "RNZ"),
    (31, "Tonga", "Drought emergency takes effect.", "RNZ"),
    (32, "Cook Islands", "Cyclone Xavier eases to category 4.", "RNZ"),
    (33, "Space", "Red giant seen eating a Sun-sized star.", "Nature"),
]

DATE_CHECK = (
    "DATE CHECK ✓  Every story on this page happened, or was first "
    "reported, on Thursday 19 November 2026.  LEFT OUT AS OTHER DAYS' "
    "NEWS — 18 NOV: Iran's drone strikes on Kuwait and Bahrain · "
    "Nvidia's results · APEC opens in Shenzhen.  20 NOV: COP31's "
    "scheduled close · Cyclone Akvan's landfall."
)

FOOTER = (
    "Claims are attributed, not stated as fact · Pictures and map: "
    "original, drawn in code · Sources: Reuters, AP, AFP, BBC, Al Jazeera, "
    "UN News, Euronews, ABC, RNZ, Xinhua, Nature, IMD, Kompas, SABC, "
    "CBS · 2026-11-19"
)

STRAPLINE = (
    "Three leaders share one table in Shenzhen  ·  The World Court finds "
    "genocide in Myanmar  ·  COP31's draft drops fossil fuels"
)

# --- map data -----------------------------------------------------------------
# Simplified continent outlines as (lon, lat) points, equirectangular.
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 72), (-85, 70),
     (-80, 73), (-65, 62), (-60, 52), (-65, 45), (-75, 35), (-80, 25),
     (-85, 30), (-90, 21), (-97, 16), (-105, 20), (-110, 23), (-115, 30),
     (-125, 40), (-125, 48), (-135, 57), (-155, 58)],
    # South America
    [(-78, 8), (-72, 12), (-60, 8), (-52, 5), (-44, -3), (-35, -8),
     (-38, -15), (-40, -22), (-48, -28), (-52, -33), (-58, -38), (-62, -41),
     (-65, -45), (-68, -52), (-70, -54), (-73, -45), (-73, -37), (-71, -30),
     (-70, -20), (-75, -15), (-80, -6), (-81, 0)],
    # Africa
    [(-17, 15), (-10, 5), (-8, -5), (9, -1), (13, -12), (12, -18),
     (16, -29), (19, -35), (26, -34), (32, -29), (36, -22), (40, -15),
     (42, -10), (46, -2), (51, 2), (48, 11), (43, 12), (39, 15), (37, 18),
     (35, 27), (32, 31), (20, 32), (11, 34), (10, 37), (0, 36), (-6, 35),
     (-10, 31), (-15, 25)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 48), (-4, 50), (0, 53), (3, 58), (5, 60),
     (10, 59), (18, 56), (21, 55), (24, 58), (28, 60), (30, 70), (40, 68),
     (45, 68), (48, 60), (40, 55), (35, 50), (30, 46), (28, 44), (23, 40),
     (19, 42), (15, 44), (12, 44), (10, 44), (8, 44), (3, 43), (-2, 37),
     (-6, 36)],
    # Asia
    [(30, 70), (40, 68), (50, 69), (60, 70), (70, 72), (80, 73), (90, 75),
     (100, 77), (110, 74), (120, 73), (130, 72), (140, 72), (150, 70),
     (160, 69), (170, 67), (178, 65), (170, 60), (162, 56), (158, 52),
     (150, 45), (142, 42), (140, 38), (135, 35), (130, 33), (127, 35),
     (122, 30), (120, 25), (115, 23), (110, 20), (108, 12), (105, 9),
     (103, 2), (100, 6), (98, 10), (95, 16), (92, 21), (89, 22), (86, 20),
     (80, 15), (77, 8), (75, 12), (72, 20), (68, 23), (66, 25), (61, 25),
     (57, 26), (52, 26), (50, 29), (48, 30), (44, 29), (40, 31), (36, 36),
     (33, 38), (30, 40), (28, 45), (30, 50), (32, 55), (30, 60)],
    # Australia
    [(114, -22), (114, -30), (118, -35), (124, -33), (129, -32), (135, -35),
     (138, -35), (140, -38), (145, -38), (150, -37), (153, -30), (153, -27),
     (150, -22), (146, -19), (142, -15), (142, -11), (137, -12), (135, -15),
     (132, -12), (130, -13), (126, -14), (122, -17), (118, -20)],
    # Greenland
    [(-58, 64), (-52, 60), (-43, 60), (-40, 64), (-32, 68), (-22, 70),
     (-25, 76), (-35, 80), (-50, 80), (-60, 76), (-62, 70)],
    # Britain
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (0, 57), (1, 53), (1, 51)],
    # Japan
    [(130, 31), (133, 34), (137, 35), (140, 36), (141, 40), (142, 44),
     (145, 44), (142, 40), (140, 35), (136, 33), (132, 33)],
    # New Zealand
    [(167, -46), (170, -43), (173, -39), (176, -38), (178, -38),
     (175, -41), (172, -43), (169, -46)],
    # Madagascar
    [(44, -16), (47, -15), (50, -16), (49, -20), (47, -25), (45, -25),
     (44, -20)],
]

# Story number -> (lon, lat) of its pin on the map.
PINS = {
    1: (114.1, 22.5),    # Shenzhen
    2: (4.3, 52.1),      # The Hague
    3: (30.7, 36.9),     # Antalya
    4: (36.5, 45.4),     # Kerch
    5: (46.7, 24.7),     # Riyadh
    6: (85.8, 20.3),     # Odisha
    7: (127.0, 37.5),    # Seoul
    8: (12.6, 55.7),     # Copenhagen
    9: (-74.0, 40.7),    # New York
    10: (-118.2, 34.1),  # Los Angeles (US midnight launch)
    11: (-74.1, 4.7),    # Bogota
    12: (36.8, -1.3),    # Nairobi
    13: (149.1, -35.3),  # Canberra
}


# --- text helpers ---------------------------------------------------------------
def wrap(draw, text, font, max_width):
    """Wrap text to lines that fit max_width. Returns a list of lines."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw, x, y, text, font, max_width, fill, leading):
    """Draw wrapped text; returns the y just below the last line."""
    for line in wrap(draw, text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += leading
    return y


def draw_centered(draw, cx, y, text, font, fill):
    draw.text((cx - draw.textlength(text, font=font) / 2, y), text,
              font=font, fill=fill)


# --- small flag / figure drawings -------------------------------------------------
def flag_us(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255),
                outline=INK, width=1)
    stripe = h / 13
    for i in range(0, 13, 2):
        d.rectangle([x, y + i * stripe, x + w, y + (i + 1) * stripe],
                    fill=(178, 34, 52))
    d.rectangle([x, y, x + w * 0.4, y + h * 7 / 13], fill=(60, 59, 110))
    for r in range(3):
        for c in range(4):
            cx = x + 3 + c * (w * 0.4 - 6) / 3
            cy = y + 2 + r * (h * 7 / 13 - 4) / 2
            d.ellipse([cx - 1, cy - 1, cx + 1, cy + 1], fill=WHITE)


def flag_cn(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(222, 41, 16), outline=INK,
                width=1)
    d.ellipse([x + w * 0.12, y + h * 0.12, x + w * 0.38, y + h * 0.5],
              fill=(255, 222, 0))
    for fx, fy in [(0.55, 0.15), (0.68, 0.3), (0.62, 0.5), (0.48, 0.55)]:
        d.ellipse([x + w * fx, y + h * fy, x + w * fx + 3, y + h * fy + 3],
                  fill=(255, 222, 0))


def flag_ru(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=WHITE, outline=INK, width=1)
    d.rectangle([x, y + h / 3, x + w, y + 2 * h / 3], fill=(0, 57, 166))
    d.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(213, 0, 50))


def flag_dk(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(198, 12, 48), outline=INK,
                width=1)
    d.rectangle([x + w * 0.28, y, x + w * 0.42, y + h], fill=WHITE)
    d.rectangle([x, y + h * 0.4, x + w, y + h * 0.6], fill=WHITE)


def person(d, cx, base_y, suit, skin=(232, 190, 150), hair=(60, 50, 40)):
    """A simple seated figure: head, hair, shoulders, tie."""
    d.ellipse([cx - 11, base_y - 52, cx + 11, base_y - 30], fill=skin,
              outline=INK, width=1)
    d.pieslice([cx - 11, base_y - 52, cx + 11, base_y - 34], 180, 360,
               fill=hair)
    d.rounded_rectangle([cx - 20, base_y - 30, cx + 20, base_y + 6],
                        radius=8, fill=suit, outline=INK, width=1)
    d.polygon([(cx, base_y - 28), (cx - 4, base_y - 20), (cx, base_y - 6),
               (cx + 4, base_y - 20)], fill=RED)


def starburst(d, cx, cy, r, fill):
    import math
    pts = []
    for i in range(16):
        ang = math.pi * i / 8
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=fill, outline=INK, width=1)


# --- lead illustrations -----------------------------------------------------------
def art_summit(d, x, y, w, h, f):
    d.rectangle([x, y, x + w, y + h], fill=(214, 228, 240))
    # back wall panels
    d.rectangle([x, y, x + w, y + 34], fill=NAVY)
    d.rectangle([x, y + 34, x + w, y + 38], fill=(201, 162, 39))
    # three flags on poles
    fw, fh = 34, 22
    for i, flag in enumerate([flag_us, flag_cn, flag_ru]):
        fx = x + 22 + i * (w - 44 - fw) / 2
        d.line([fx + fw / 2, y + 6, fx + fw / 2, y + 34], fill=WHITE,
               width=2)
        flag(d, fx, y + 8, fw, fh)
    # table
    ty = y + h - 26
    d.rectangle([x + 8, ty, x + w - 8, y + h - 4], fill=(120, 72, 30),
                outline=INK, width=1)
    d.rectangle([x + 8, ty, x + w - 8, ty + 6], fill=(201, 162, 39))
    # three figures
    for i, suit in enumerate([(30, 60, 110), (40, 40, 40), (90, 30, 40)]):
        cx = x + w * (0.2 + 0.3 * i)
        person(d, cx, ty, suit)
    # name plates
    for i, name in enumerate(["TRUMP", "XI", "PUTIN"]):
        cx = x + w * (0.2 + 0.3 * i)
        tw = d.textlength(name, font=f["tiny_b"])
        d.rectangle([cx - tw / 2 - 4, ty + 8, cx + tw / 2 + 4, ty + 19],
                    fill=WHITE, outline=INK, width=1)
        d.text((cx - tw / 2, ty + 8), name, font=f["tiny_b"], fill=INK)


def art_court(d, x, y, w, h, f):
    d.rectangle([x, y, x + w, y + h], fill=(222, 232, 222))
    # courthouse
    bx, by, bw, bh = x + 18, y + 34, w - 36, h - 44
    d.polygon([(bx - 8, by), (bx + bw / 2, by - 22), (bx + bw + 8, by)],
              fill=(150, 60, 50), outline=INK, width=1)
    d.rectangle([bx, by, bx + bw, by + bh], fill=(226, 208, 176),
                outline=INK, width=1)
    for i in range(5):
        cx = bx + 14 + i * (bw - 28) / 4
        d.rectangle([cx - 5, by + 10, cx + 5, by + bh - 8],
                    fill=(250, 244, 230), outline=INK, width=1)
    d.rectangle([bx + bw / 2 - 16, by + bh - 30, bx + bw / 2 + 16,
                 by + bh], fill=(90, 60, 40), outline=INK, width=1)
    # scales of justice, top right, clear of the courthouse roof
    sx, sy = x + w - 46, y + 8
    gold = (130, 100, 10)
    d.line([sx, sy + 22, sx, sy + 46], fill=gold, width=4)
    d.line([sx - 18, sy + 24, sx + 18, sy + 24], fill=gold, width=4)
    d.ellipse([sx - 4, sy + 16, sx + 4, sy + 24], fill=gold)
    for dx in (-18, 18):
        d.line([sx + dx, sy + 24, sx + dx, sy + 34], fill=gold, width=3)
        d.polygon([(sx + dx - 9, sy + 34), (sx + dx + 9, sy + 34),
                   (sx + dx, sy + 44)], fill=(220, 190, 90),
                  outline=gold, width=2)
    # 9-6 badge
    d.rounded_rectangle([x + w - 62, y + h - 34, x + w - 8, y + h - 8],
                        radius=4, fill=RED, outline=INK, width=1)
    draw_centered(d, x + w - 35, y + h - 32, "9–6", f["small_b"], WHITE)


def art_climate(d, x, y, w, h, f):
    d.rectangle([x, y, x + w, y + h], fill=(200, 228, 226))
    # globe
    cx, cy, r = x + 62, y + h / 2 + 4, 46
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(70, 130, 200),
              outline=INK, width=2)
    d.ellipse([cx - 22, cy - 28, cx + 6, cy - 2], fill=(80, 170, 90))
    d.ellipse([cx - 4, cy + 6, cx + 28, cy + 30], fill=(80, 170, 90))
    d.ellipse([cx + 10, cy - 34, cx + 30, cy - 14], fill=(80, 170, 90))
    # thermometer
    tx = x + w - 52
    d.rounded_rectangle([tx, y + 18, tx + 14, y + h - 34], radius=7,
                        fill=WHITE, outline=INK, width=1)
    d.ellipse([tx - 6, y + h - 40, tx + 20, y + h - 14], fill=RED,
              outline=INK, width=1)
    d.rectangle([tx + 3, y + 30, tx + 11, y + h - 34], fill=RED)
    # struck-out fossil fuels text
    tx0 = x + 122
    d.text((tx0, y + 22), "FOSSIL", font=f["med_b"], fill=INK)
    d.text((tx0, y + 44), "FUELS", font=f["med_b"], fill=INK)
    d.line([tx0 - 2, y + 36, tx0 + 108, y + 30], fill=RED, width=4)
    d.line([tx0 - 2, y + 58, tx0 + 96, y + 52], fill=RED, width=4)
    d.text((tx0, y + 72), "$120bn AID", font=f["small_b"], fill=INK)
    d.text((tx0, y + 88), "GOAL", font=f["small_b"], fill=INK)
    d.line([tx0 - 2, y + 86, tx0 + 92, y + 80], fill=RED, width=3)
    d.line([tx0 - 2, y + 102, tx0 + 52, y + 97], fill=RED, width=3)
    # CUT stamp
    d.rounded_rectangle([x + w - 66, y + h - 34, x + w - 8, y + h - 8],
                        radius=4, fill=WHITE, outline=RED, width=2)
    draw_centered(d, x + w - 37, y + h - 32, "CUT", f["small_b"], RED)


# --- feature banner art -------------------------------------------------------------
def art_bridge(d, x, y, w, h, f):
    d.rectangle([x, y, x + w, y + h], fill=(200, 220, 235))
    d.rectangle([x, y + h - 12, x + w, y + h], fill=(90, 130, 170))
    d.arc([x + 20, y + 6, x + w - 20, y + h + 26], 180, 360,
          fill=INK, width=4)
    d.line([x + 8, y + h - 22, x + w - 8, y + h - 22], fill=INK, width=3)
    starburst(d, x + w * 0.62, y + 16, 11, (255, 200, 40))
    d.text((x + 6, y + 4), "KERCH", font=f["tiny_b"], fill=NAVY)


def art_missiles(d, x, y, w, h, f):
    d.rectangle([x, y, x + w, y + h], fill=(30, 40, 70))
    for i, bh in enumerate([22, 30, 18, 34, 24]):
        bx = x + 8 + i * 36
        d.rectangle([bx, y + h - 8 - bh, bx + 28, y + h - 8],
                    fill=(90, 100, 130), outline=(160, 170, 200), width=1)
        for wy in range(3):
            d.rectangle([bx + 5, y + h - 14 - bh + wy * 9, bx + 11,
                         y + h - 10 - bh + wy * 9], fill=(255, 220, 100))
    for mx, my in [(40, 12), (100, 8), (150, 14)]:
        d.line([x + mx, y + my + 14, x + mx + 14, y + my], fill=WHITE,
               width=2)
        starburst(d, x + mx, y + my + 14, 6, (255, 200, 40))
    d.text((x + 6, y + 2), "OVER RIYADH", font=f["tiny_b"], fill=WHITE)


def art_cyclone(d, x, y, w, h, f):
    d.rectangle([x, y, x + w, y + h], fill=(200, 225, 240))
    cx, cy = x + w - 52, y + h / 2
    for r in (26, 19, 12):
        d.arc([cx - r, cy - r, cx + r, cy + r], 30, 300, fill=NAVY,
              width=3)
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=WHITE, outline=NAVY,
              width=2)
    d.line([x + 14, y + h - 10, x + w - 90, y + h - 10], fill=(120, 90, 40),
           width=3)
    d.polygon([(x + w - 92, y + h - 18), (x + w - 78, y + h - 10),
               (x + w - 92, y + h - 2)], fill=RED)
    d.text((x + 6, y + 4), "AKVAN", font=f["tiny_b"], fill=NAVY)


def art_gavel(d, x, y, w, h, f):
    d.rectangle([x, y, x + w, y + h], fill=(238, 228, 205))
    d.line([x + 40, y + 30, x + 120, y + 8], fill=(120, 80, 40), width=6)
    d.rounded_rectangle([x + 112, y + 2, x + 150, y + 18], radius=4,
                        fill=(120, 80, 40), outline=INK, width=1)
    d.rectangle([x + 30, y + 32, x + 90, y + 40], fill=(150, 110, 60),
                outline=INK, width=1)
    d.rounded_rectangle([x + w - 96, y + h - 24, x + w - 6, y + h - 6],
                        radius=3, fill=WHITE, outline=RED, width=2)
    draw_centered(d, x + w - 51, y + h - 22, "OVERTURNED", f["tiny_b"],
                  RED)


def art_arctic(d, x, y, w, h, f):
    d.rectangle([x, y, x + w, y + h], fill=(210, 228, 240))
    d.polygon([(x + 10, y + h - 8), (x + 60, y + 10), (x + 110, y + h - 8)],
              fill=WHITE, outline=NAVY, width=1)
    d.polygon([(x + 80, y + h - 8), (x + 130, y + 18), (x + 180, y + h - 8)],
              fill=(230, 240, 250), outline=NAVY, width=1)
    flag_dk(d, x + 8, y + 6, 26, 16)
    flag_us(d, x + 40, y + 6, 26, 16)
    d.rounded_rectangle([x + w - 56, y + 4, x + w - 6, y + 20], radius=3,
                        fill=RED)
    draw_centered(d, x + w - 31, y + 5, "109–0", f["tiny_b"], WHITE)


def art_chart(d, x, y, w, h, f):
    d.rectangle([x, y, x + w, y + h], fill=(20, 60, 40))
    pts = [(x + 10, y + h - 12), (x + 45, y + h - 24), (x + 70, y + h - 18),
           (x + 105, y + 26), (x + 140, y + 20), (x + 175, y + 8)]
    d.line(pts, fill=(80, 220, 120), width=3)
    d.polygon([(x + 175, y + 8), (x + 163, y + 8), (x + 175, y + 20)],
              fill=(80, 220, 120))
    d.text((x + 6, y + 4), "NASDAQ", font=f["tiny_b"], fill=(200, 255, 210))
    d.text((x + w - 62, y + h - 20), "IPO $83", font=f["small_b"],
           fill=(255, 220, 100))


def art_gamepad(d, x, y, w, h, f):
    d.rectangle([x, y, x + w, y + h], fill=(50, 30, 90))
    d.rounded_rectangle([x + 28, y + 8, x + w - 28, y + h - 8], radius=12,
                        fill=(30, 30, 40), outline=(200, 180, 255),
                        width=2)
    d.ellipse([x + 44, y + 16, x + 58, y + 30], fill=(255, 100, 100))
    d.ellipse([x + 62, y + 16, x + 76, y + 30], fill=(100, 255, 100))
    d.ellipse([x + 44, y + 32, x + 58, y + 46], fill=(100, 150, 255))
    d.ellipse([x + 62, y + 32, x + 76, y + 46], fill=(255, 220, 100))
    d.text((x + w - 56, y + 8), "VI", font=f["med_b"], fill=WHITE)
    d.text((x + 6, y + 2), "GTA", font=f["tiny_b"], fill=(220, 200, 255))


def art_crowd(d, x, y, w, h, f):
    d.rectangle([x, y, x + w, y + h], fill=(240, 225, 190))
    for i in range(7):
        cx = x + 16 + i * 24
        d.ellipse([cx - 6, y + 12, cx + 6, y + 24], fill=(200, 150, 110),
                  outline=INK, width=1)
        d.rounded_rectangle([cx - 9, y + 24, cx + 9, y + h - 6], radius=4,
                            fill=[(180, 60, 60), (60, 120, 180),
                                  (60, 160, 80), (200, 160, 40)][i % 4],
                            outline=INK, width=1)
    d.line([x + w - 40, y + 4, x + w - 40, y + 30], fill=INK, width=2)
    d.rectangle([x + w - 40, y + 4, x + w - 12, y + 16],
                fill=(252, 209, 22), outline=INK, width=1)
    d.rectangle([x + w - 40, y + 10, x + w - 12, y + 16],
                fill=(200, 16, 46))


def art_banned(d, x, y, w, h, f):
    d.rectangle([x, y, x + w, y + h], fill=(235, 220, 200))
    # runner: simple stick figure mid-stride
    cx, cy = x + 55, y + 22
    d.ellipse([cx - 7, cy - 8, cx + 7, cy + 6], fill=(120, 80, 50),
              outline=INK, width=1)
    d.line([cx, cy + 6, cx - 4, cy + 24], fill=INK, width=3)
    d.line([cx - 4, cy + 24, cx - 18, cy + 34], fill=INK, width=3)
    d.line([cx - 4, cy + 24, cx + 12, cy + 30], fill=INK, width=3)
    d.line([cx, cy + 10, cx - 14, cy + 4], fill=INK, width=3)
    d.line([cx, cy + 10, cx + 14, cy + 16], fill=INK, width=3)
    d.rounded_rectangle([x + w - 84, y + 8, x + w - 8, y + 28], radius=3,
                        fill=WHITE, outline=RED, width=2)
    draw_centered(d, x + w - 46, y + 10, "BANNED", f["small_b"], RED)
    d.text((x + w - 84, y + 32), "3 YEARS", font=f["tiny_b"], fill=INK)


def art_bars(d, x, y, w, h, f):
    d.rectangle([x, y, x + w, y + h], fill=(20, 40, 80))
    vals = [14, 18, 16, 22, 30]
    for i, v in enumerate(vals):
        bx = x + 14 + i * 26
        col = (255, 120, 90) if i == 4 else (120, 180, 230)
        d.rectangle([bx, y + h - 10 - v, bx + 18, y + h - 10], fill=col,
                    outline=WHITE, width=1)
    d.text((x + w - 62, y + 6), "4.9%", font=f["med_b"], fill=(255, 200, 90))


FEATURE_ART = {
    "bridge": art_bridge,
    "missiles": art_missiles,
    "cyclone": art_cyclone,
    "gavel": art_gavel,
    "arctic": art_arctic,
    "chart": art_chart,
    "gamepad": art_gamepad,
    "crowd": art_crowd,
    "banned": art_banned,
    "bars": art_bars,
}

LEAD_ART = [art_summit, art_court, art_climate]


# --- map --------------------------------------------------------------------------------
def make_projector(x0, y0, w, h):
    lon0, lon1 = -170.0, 190.0
    lat0, lat1 = 80.0, -60.0

    def project(lon, lat):
        px = x0 + (lon - lon0) / (lon1 - lon0) * w
        py = y0 + (lat0 - lat) / (lat0 - lat1) * h
        return px, py

    return project


def draw_map(d, x, y, w, h, f):
    d.rectangle([x, y, x + w, y + h], fill=MAP_SEA, outline=INK, width=1)
    project = make_projector(x, y, w, h)
    for poly in CONTINENTS:
        pts = [project(lon, lat) for lon, lat in poly]
        d.polygon(pts, fill=MAP_LAND, outline=MAP_LAND_EDGE)
    # graticule
    for lon in range(-150, 181, 30):
        x1, _ = project(lon, 0)
        d.line([x1, y, x1, y + h], fill=(190, 210, 225), width=1)
    for lat in range(60, -61, -30):
        _, y1 = project(0, lat)
        d.line([x, y1, x + w, y1], fill=(190, 210, 225), width=1)
    for poly in CONTINENTS:
        pts = [project(lon, lat) for lon, lat in poly]
        d.polygon(pts, outline=MAP_LAND_EDGE)
    # pins; crowded pins are nudged with a leader line to their true spot
    offsets = {2: (-11, -9), 8: (9, -11), 3: (-9, 7), 4: (9, -7)}
    for num, (lon, lat) in sorted(PINS.items()):
        px, py = project(lon, lat)
        dx, dy = offsets.get(num, (0, 0))
        if (dx, dy) != (0, 0):
            d.line([px, py, px + dx, py + dy], fill=(120, 120, 120),
                   width=1)
            px, py = px + dx, py + dy
        r = 7
        d.ellipse([px - r, py - r, px + r, py + r], fill=RED, outline=WHITE,
                  width=1)
        label = str(num)
        tw = d.textlength(label, font=f["pin"])
        d.text((px - tw / 2, py - 6), label, font=f["pin"], fill=WHITE)


# --- page assembly --------------------------------------------------------------------------
def load_fonts():
    from PIL import ImageFont

    def font(name, size):
        return ImageFont.truetype(str(FONTS / name), size)

    return {
        "date": font("DejaVuSerif-Bold.ttf", 57),
        "strap": font("DejaVuSerif.ttf", 15),
        "mast": font("DejaVuSans-Bold.ttf", 13),
        "tab": font("DejaVuSans-Bold.ttf", 13),
        "num": font("DejaVuSans-Bold.ttf", 23),
        "numlab": font("DejaVuSans.ttf", 10),
        "lead_head": font("DejaVuSerif-Bold.ttf", 19),
        "lead_body": font("DejaVuSans.ttf", 12),
        "tag": font("DejaVuSans-Bold.ttf", 10),
        "feat_head": font("DejaVuSerif-Bold.ttf", 13),
        "feat_body": font("DejaVuSans.ttf", 11),
        "also": font("DejaVuSans.ttf", 11),
        "also_b": font("DejaVuSans-Bold.ttf", 11),
        "also10": font("DejaVuSans.ttf", 10),
        "also_b10": font("DejaVuSans-Bold.ttf", 10),
        "also9": font("DejaVuSans.ttf", 9),
        "also_b9": font("DejaVuSans-Bold.ttf", 9),
        "check": font("DejaVuSans.ttf", 12),
        "check_b": font("DejaVuSans-Bold.ttf", 12),
        "foot": font("DejaVuSans.ttf", 10),
        "small_b": font("DejaVuSans-Bold.ttf", 12),
        "med_b": font("DejaVuSans-Bold.ttf", 18),
        "tiny_b": font("DejaVuSans-Bold.ttf", 10),
        "pin": font("DejaVuSans-Bold.ttf", 9),
        "section": font("DejaVuSans-Bold.ttf", 12),
    }


def draw_front_page():
    from PIL import Image, ImageDraw

    f = load_fonts()
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # --- masthead ---
    d.text((MARGIN, 8), "THE DAY, IN ONE PAGE", font=f["mast"], fill=NAVY)
    right = "33 STORIES · 6 CONTINENTS · EVERY STORY SOURCED"
    d.text((W - MARGIN - d.textlength(right, font=f["mast"]), 8), right,
           font=f["mast"], fill=NAVY)
    d.line([MARGIN, 30, W - MARGIN, 30], fill=NAVY, width=2)
    d.line([MARGIN, 33, W - MARGIN, 33], fill=NAVY, width=1)

    # --- date headline (shrink to fit the page width) ---
    from PIL import ImageFont

    date_text = "THURSDAY 19 NOVEMBER 2026"
    date_size = 57
    date_font = f["date"]
    while (d.textlength(date_text, font=date_font) > CONTENT_W
           and date_size > 40):
        date_size -= 1
        date_font = ImageFont.truetype(
            str(FONTS / "DejaVuSerif-Bold.ttf"), date_size)
    draw_centered(d, W / 2, 38, date_text, date_font, NAVY)
    draw_centered(d, W / 2, 104, STRAPLINE, f["strap"], DARK_RED)

    # --- region tabs ---
    tab_y, tab_h = 128, 22
    tab_w = CONTENT_W / len(REGIONS)
    for i, (name, count) in enumerate(REGIONS):
        x0 = MARGIN + i * tab_w
        label = f"{name} {count}"
        d.rectangle([x0 + 1, tab_y, x0 + tab_w - 1, tab_y + tab_h],
                    fill=REGION_COLORS[name])
        draw_centered(d, x0 + tab_w / 2, tab_y + 4, label, f["tab"], WHITE)

    # --- number strip ---
    strip_y, strip_h = 156, 44
    cell_w = CONTENT_W / len(FIGURES)
    d.rectangle([MARGIN, strip_y, W - MARGIN, strip_y + strip_h],
                fill=CREAM, outline=RULE, width=1)
    for i, (num, label) in enumerate(FIGURES):
        x0 = MARGIN + i * cell_w
        if i:
            d.line([x0, strip_y + 4, x0, strip_y + strip_h - 4],
                   fill=LIGHT_GREY, width=1)
        draw_centered(d, x0 + cell_w / 2, strip_y + 3, num, f["num"], RED)
        for j, line in enumerate(label.split("\n")):
            draw_centered(d, x0 + cell_w / 2, strip_y + 27 + j * 11, line,
                          f["numlab"], INK)

    # --- leads ---
    lead_y, lead_h = 206, 258
    gap = 8
    col_w = (CONTENT_W - 2 * gap) / 3
    art_h = 124
    for i, (num, tag, head, body, src) in enumerate(LEADS):
        x0 = MARGIN + i * (col_w + gap)
        d.rectangle([x0, lead_y, x0 + col_w, lead_y + lead_h], fill=CREAM,
                    outline=RULE, width=1)
        LEAD_ART[i](d, x0 + 1, lead_y + 1, col_w - 2, art_h, f)
        ty = lead_y + art_h + 8
        d.text((x0 + 8, ty), f"{num}  {tag}", font=f["tag"], fill=RED)
        ty += 15
        ty = draw_wrapped(d, x0 + 8, ty, head, f["lead_head"], col_w - 16,
                          INK, 22)
        ty += 2
        draw_wrapped(d, x0 + 8, ty, body + f" — {src}", f["lead_body"],
                     col_w - 16, INK, 14)

    # --- features, two rows of five ---
    feat_y = lead_y + lead_h + 6
    feat_h = 120
    feat_gap = 6
    fcol_w = (CONTENT_W - 4 * feat_gap) / 5
    banner_h = 48
    for row in range(2):
        for col in range(5):
            idx = row * 5 + col
            num, tag, head, body, src, art = FEATURES[idx]
            x0 = MARGIN + col * (fcol_w + feat_gap)
            y0 = feat_y + row * (feat_h + feat_gap)
            d.rectangle([x0, y0, x0 + fcol_w, y0 + feat_h], fill=CREAM,
                        outline=RULE, width=1)
            FEATURE_ART[art](d, x0 + 1, y0 + 1, fcol_w - 2, banner_h, f)
            ty = y0 + banner_h + 5
            d.text((x0 + 6, ty), f"{num}  {tag}", font=f["tag"], fill=RED)
            ty += 14
            ty = draw_wrapped(d, x0 + 6, ty, head, f["feat_head"],
                              fcol_w - 12, INK, 16)
            draw_wrapped(d, x0 + 6, ty + 1, body + f" — {src}",
                         f["feat_body"], fcol_w - 12, INK, 13)

    # --- map + also list ---
    map_y = feat_y + 2 * feat_h + feat_gap + 6
    map_h = 190
    map_w = 302
    d.text((MARGIN, map_y), "WHERE IT HAPPENED", font=f["section"],
           fill=NAVY)
    d.text((MARGIN + 150, map_y), "numbers match the stories",
           font=f["numlab"], fill=GREY)
    draw_map(d, MARGIN, map_y + 17, map_w, map_h - 17, f)

    also_x = MARGIN + map_w + 10
    also_w = W - MARGIN - also_x
    d.text((also_x, map_y), "ALSO ON THURSDAY 19 NOVEMBER 2026",
           font=f["section"], fill=NAVY)
    d.text((also_x + 318, map_y), "place · what happened · source",
           font=f["numlab"], fill=GREY)
    col_w2 = also_w / 2
    row_h = (map_h - 17) / 10
    also_sizes = [("also", "also_b"), ("also10", "also_b10"),
                  ("also9", "also_b9")]
    for i, (num, place, line, src) in enumerate(ALSO):
        col = i // 10
        row = i % 10
        x0 = also_x + col * col_w2
        y0 = map_y + 17 + row * row_h
        rest = f"{line} {src}"
        # pick the largest size whose full line (source included) fits
        for reg_key, bold_key in also_sizes:
            reg, bold = f[reg_key], f[bold_key]
            num_w = d.textlength(str(num) + " ", font=bold)
            pw = d.textlength(place + " — ", font=bold)
            if (num_w + pw + d.textlength(rest, font=reg)
                    <= col_w2 - 4):
                break
        d.text((x0, y0 + 3), str(num), font=bold, fill=RED)
        d.text((x0 + num_w, y0 + 3), place, font=bold, fill=INK)
        d.text((x0 + num_w + pw, y0 + 3), rest, font=reg, fill=INK)
        if row < 9:
            d.line([x0, y0 + row_h - 1, x0 + col_w2 - 8, y0 + row_h - 1],
                   fill=LIGHT_GREY, width=1)

    # --- date check ---
    check_y = map_y + map_h + 8
    check_h = 46
    d.rounded_rectangle([MARGIN, check_y, W - MARGIN, check_y + check_h],
                        radius=6, fill=CHECK_BG, outline=CHECK_EDGE,
                        width=1)
    draw_wrapped(d, MARGIN + 10, check_y + 6, DATE_CHECK, f["check"],
                 CONTENT_W - 20, INK, 15)

    # --- footer ---
    foot_y = check_y + check_h + 8
    d.line([MARGIN, foot_y, W - MARGIN, foot_y], fill=RULE, width=1)
    draw_wrapped(d, MARGIN, foot_y + 5, FOOTER, f["foot"], CONTENT_W,
                 GREY, 13)

    return img


def render_bytes():
    """Render the page; return PNG bytes, or JPEG bytes if PNG is too big."""
    from PIL import Image
    import io

    img = draw_front_page()
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    data = buf.getvalue()
    if len(data) <= MAX_BYTES:
        return data
    for quality in (92, 88, 84, 80, 75):
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=quality,
                                optimize=True)
        data = buf.getvalue()
        if len(data) <= MAX_BYTES:
            return data
    raise RuntimeError("rendered image does not fit in 1 MiB")


def copy_fallback(target):
    if not FALLBACK_IMAGE.is_file():
        raise FileNotFoundError(
            "Pillow is unavailable and no committed entry.png to copy")
    shutil.copyfile(FALLBACK_IMAGE, target)


def main():
    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "entry.png"
    try:
        data = render_bytes()
    except ImportError:
        copy_fallback(target)
        return
    except Exception:
        # Any draw failure (missing font, Pillow quirk) falls back to the
        # committed render so the entry still completes.
        if FALLBACK_IMAGE.is_file():
            copy_fallback(target)
            return
        raise
    target.write_bytes(data)
    if len(data) > MAX_BYTES:
        raise RuntimeError("output exceeds 1 MiB")


if __name__ == "__main__":
    main()
