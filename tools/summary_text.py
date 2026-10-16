#!/usr/bin/env python3
"""Repaint a text-heavy picture page (e.g. the tutorial summaries in
Logic/Dat/logic/Resource/summary/Img/@Ja/@ps3/guidance_NN.dds) in English.

These pages are transparent 32-bit DDS sheets: outlined text in a rounded
gothic over a faint dark backing, with some screenshots and icons. The tool
keeps the listed picture areas, clears everything else back to the backing,
and lays out word-wrapped English blocks.

Spec (textures/<name>.json, "tool": "summary_text.py"):
  {"texture": "...guidance_01.dds", "font": "seguisb.ttf", "size": 22, "lh": 25,
   "keep":  [[x0,y0,x1,y1], ...],          # pictures copied back unchanged
   "icons": {"ex": [x0,y0,x1,y1], ...},     # cut from the original for {i:ex}
   "blocks": [{"x": 5, "y": 4, "w": 950, "text": "● {o|SR Points} are ...",
               "size": 21, "h": 75}]}       # h: shrink the font until it fits

Text markup: {o|..} orange, {r|..} red, {b|..} blue, {g|..} green, {y|..}
yellow; a capital letter ({G|..}) draws it in italics; {i:NAME} is an
inline icon. A block starting with
"● " gets a round bullet and a hanging indent, "• " a small bullet; "\\n"
forces a line break. Boxes are exclusive [x0, y0, x1, y1).

Usage: summary_text.py SPEC ORIGINAL.dds OUT.dds [--preview OUT.png]
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from texture_text import load_dds, save_dds  # noqa: E402

FONT_DIR = r"C:\Windows\Fonts"
COLOURS = {"": (255, 255, 255), "o": (255, 128, 0), "r": (255, 0, 0), "b": (0, 106, 255),
           "g": (0, 255, 0), "y": (255, 204, 0)}
OUTLINE = (12, 14, 24)
BACKING = (20, 22, 35, 11)
ITALIC = 0.2


def tokens(text):
    """Split markup into (kind, value, style) tokens: words, spaces, breaks, icons."""
    out = []
    for m in re.finditer(r"\{([orbgyORBGY])\|([^}]*)\}|\{i:(\w+)\}|([^{]+)", text):
        if m.group(3):
            out.append(("icon", m.group(3), ""))
            continue
        style, s = (m.group(1), m.group(2)) if m.group(1) else ("", m.group(4))
        for part in re.split(r"(\n| )", s):
            if part == "\n":
                out.append(("br", "", style))
            elif part == " ":
                out.append(("sp", " ", style))
            elif part:
                out.append(("word", part, style))
    return out


def layout(toks, font, icons, width, indent):
    """Greedy word wrap. Returns lines of (x, kind, value, style) items."""
    lines, cur, x = [], [], indent
    def adv(kind, val):
        return icons[val].width + 2 if kind == "icon" else font.getlength(val)
    for kind, val, style in toks:
        if kind == "br":
            lines.append(cur)
            cur, x = [], indent
            continue
        w = adv(kind, val)
        if kind == "sp":
            if cur:
                cur.append((x, kind, val, style))
                x += w
            continue
        if x + w > width and cur:
            while cur and cur[-1][1] == "sp":
                cur.pop()
            lines.append(cur)
            cur, x = [], indent
        cur.append((x, kind, val, style))
        x += w
    lines.append(cur)
    return lines


def line_width(line, font, icons):
    if not line:
        return 0
    x, kind, val, _ = line[-1]
    return x + (icons[val].width if kind == "icon" else font.getlength(val))


def draw_text(im, xy, s, font, colour, italic):
    if not italic:
        ImageDraw.Draw(im).text(xy, s, font=font, fill=colour + (255,), stroke_width=1,
                                stroke_fill=OUTLINE + (255,))
        return
    l, t, r, b = font.getbbox(s, stroke_width=1)
    h = b + 4
    w = int(r + 4 + h * ITALIC)
    tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((2, 0), s, font=font, fill=colour + (255,), stroke_width=1,
                              stroke_fill=OUTLINE + (255,))
    tile = tile.transform((w, h), Image.AFFINE, (1, ITALIC, -ITALIC * h, 0, 1, 0), Image.BICUBIC)
    im.alpha_composite(tile, (int(xy[0]) - 2, int(xy[1])))


def bullet(im, x, y, font, small):
    """Draw a round bullet centred on the cap height of the first line."""
    d = ImageDraw.Draw(im)
    size = font.size
    t, b = font.getbbox("H")[1::2]
    cy = y + (t + b) / 2.0
    if small:
        r = max(2.0, size / 7.0)
        cx = x + 8
    else:
        r = size * 0.4
        cx = x + r + 1
    d.ellipse((cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1), fill=OUTLINE + (255,))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 255))


def render_block(im, blk, spec, font_path, icons):
    size = blk.get("size", spec.get("size", 22))
    text = blk["text"]
    kind = "big" if text.startswith("● ") else "small" if text.startswith("• ") else None
    if kind:
        text = text[2:]
    toks = tokens(text)
    while True:
        font = ImageFont.truetype(font_path, size)
        lh = blk.get("lh", round(size * spec.get("lh", 25) / spec.get("size", 22)))
        indent = {"big": round(size * 1.15), "small": 18, None: 0}[kind]
        lines = layout(toks, font, icons, blk.get("w", im.width - 8 - blk["x"]), indent)
        if "h" not in blk or len(lines) * lh <= blk["h"] or size <= 14:
            break
        size -= 1
    x0, y0 = blk["x"], blk["y"]
    if kind:
        bullet(im, x0, y0, font, kind == "small")
    for n, line in enumerate(lines):
        y = y0 + n * lh
        for x, k, val, style in line:
            if k == "icon":
                ic = icons[val]
                im.alpha_composite(ic, (int(x0 + x), int(y + (lh - ic.height) / 2 + 1)))
            else:
                draw_text(im, (x0 + x, y), val, font, COLOURS[style.lower()], style.isupper())
    return len(lines), size


def apply(spec_path, src, dst, preview=None):
    spec = json.load(open(spec_path, encoding="utf-8"))
    header, orig, tail = load_dds(src)
    font_path = os.path.join(FONT_DIR, spec.get("font", "seguisb.ttf"))
    icons = {k: orig.crop(tuple(b)) for k, b in spec.get("icons", {}).items()}
    im = Image.new("RGBA", orig.size, BACKING)
    for b in spec.get("keep", []):
        im.paste(orig.crop(tuple(b)), (b[0], b[1]))
    report = []
    for blk in spec["blocks"]:
        report.append(render_block(im, blk, spec, font_path, icons))
    save_dds(dst, header, im, tail)
    if preview:
        bg = Image.new("RGBA", im.size, (40, 40, 60, 255))
        bg.alpha_composite(im)
        bg.convert("RGB").save(preview)
    return report


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    prev = argv[argv.index("--preview") + 1] if "--preview" in argv else None
    rep = apply(argv[1], argv[2], argv[3], prev)
    print("laid out %d block(s) -> %s  (lines/size: %s)" % (len(rep), argv[3],
          " ".join("%d/%d" % r for r in rep)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
