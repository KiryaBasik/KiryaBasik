"""Text -> SVG path data using real font outlines, so GitHub renders the exact font."""
import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
FAMILIES = {"cormorant": "cormorant-garamond", "montserrat": "montserrat", "mono": "jetbrains-mono"}
_cache = {}


def _font(family, subset, weight):
    key = (family, subset, weight)
    if key not in _cache:
        _cache[key] = TTFont(os.path.join(FONT_DIR, f"{FAMILIES[family]}-{subset}-{weight}-normal.woff"))
    return _cache[key]


def _pick(family, weight, ch):
    for subset in ("latin", "cyrillic"):
        f = _font(family, subset, weight)
        if ord(ch) in f.getBestCmap():
            return f
    return _font(family, "latin", weight)


def _num(v):
    return ("%.1f" % v).rstrip("0").rstrip(".")


def measure(text, family="cormorant", weight=600, size=48, spacing=0):
    return text_path(text, family, weight, size, 0, 0, spacing)[1]


def text_path(text, family="cormorant", weight=600, size=48, x=0, y=0, spacing=0, anchor="start"):
    """Return (path d, width). spacing = extra px between letters."""
    glyphs, width = [], 0.0
    for i, ch in enumerate(text):
        f = _pick(family, weight, ch)
        s = size / f["head"].unitsPerEm
        gname = f.getBestCmap().get(ord(ch))
        adv = f["hmtx"][gname][0] * s if gname else size * 0.3
        glyphs.append((f, gname, width, s))
        width += adv + (spacing if i < len(text) - 1 else 0)
    ox = x - (width if anchor == "end" else width / 2 if anchor == "middle" else 0)
    parts = []
    for f, gname, gx, s in glyphs:
        if not gname:
            continue
        gs = f.getGlyphSet()
        pen = SVGPathPen(gs, ntos=_num)
        gs[gname].draw(TransformPen(pen, (s, 0, 0, -s, ox + gx, y)))
        d = pen.getCommands()
        if d:
            parts.append(d)
    return " ".join(parts), width
