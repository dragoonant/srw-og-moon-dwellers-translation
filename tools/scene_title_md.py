#!/usr/bin/env python3
"""Repaint The Moon Dwellers' stage-title cards (Common/Dat/SceneTitle/Dds/@Ja) in English.

Moon Dwellers uses a different card format from 2nd OG (tools/scene_title.py). Both kinds are
uncompressed 32-bit BGRA DDS strips of 6 frames, white text on transparent:

  st_NNN.dds  1280 x 1152 = 6 frames of 1280 x 192, the stage title (Japanese glyphs about
              69 px tall, centred on (640, 95.5))
  sn_NNN.dds   352 x  480 = 6 frames of  352 x  80, "第 N 話" (about 43 px tall, centred on
              (175.5, 39.5))

Frame recipes, fitted against the originals (st_001, st_030, sn_001, sn_020) with the solid
frame as input (A = solid alpha, ring = A - MinFilter5(A)):
  f1  coarse mosaic:  A downscaled by k1 (box), upscaled nearest, Gaussian blur 4, x0.62
  f2  fine mosaic:    A downscaled by k2 (box), upscaled bilinear, Gaussian blur 4, x0.70
  f3  scan glitch:    A x vertical stripe mask (deterministic per stage)
  f4  solid white text
  f5  faded:          0.16 A + 0.20 ring
  f6  outline:        0.14 A + 0.38 ring
(k1, k2) = (24, 8) for st and (8, 6) for sn.

NNN is the stage id (byte 0 of the StageData record), as in 2nd OG. Number cards read
"Stage N" ("Final Stage" for 999), matching the game's menus.

Usage:
  scene_title_md.py render ORIG_DIR OUT_DIR STAGEDATA_JSON [--font FONT.ttf]
  scene_title_md.py preview STRIP.dds OUT.png
"""
import glob
import json
import os
import random
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from texture_text import load_dds, save_dds  # noqa: E402

FONT = r"C:\Windows\Fonts\arialbd.ttf"
KINDS = {
    "st": dict(size=(1280, 1152), fh=192, cap=50, centre=(640.0, 95.5), max_w=1120, k1=24, k2=8),
    "sn": dict(size=(352, 480), fh=80, cap=31, centre=(175.5, 39.5), max_w=330, k1=8, k2=6),
}


def load_titles(json_path, dat_path):
    d = json.load(open(json_path, encoding="utf-8"))
    raw = open(dat_path, "rb").read()
    data = next(s for s in d["sections"] if s["magic"] == "DATA")
    rec_size = d["records"]["size"]
    en = {}
    for e in d["strings"]:
        for r in e.get("refs", []):
            m = re.fullmatch(r"rec(\d+)\.title", r)
            if m and e.get("en"):
                en[int(m.group(1))] = e["en"]
    titles = {}
    for i in range(data["count"]):
        sid = raw[data["payload_offset"] + rec_size * i]
        if i in en and sid not in titles:
            titles[sid] = en[i]
    return titles


def fit_font(text, font_path, cap, max_w):
    size = cap
    while True:
        f = ImageFont.truetype(font_path, size + 1)
        l, t, r, b = f.getbbox("H")
        if b - t > cap:
            break
        size += 1
    font = ImageFont.truetype(font_path, size)
    while size > 8 and (lambda bb: bb[2] - bb[0])(font.getbbox(text)) > max_w:
        size -= 1
        font = ImageFont.truetype(font_path, size)
    return font


def text_alpha(text, font, w, fh, centre):
    l, t, r, b = font.getbbox("H")
    baseline = centre[1] + (b - t) / 2.0
    l, t, r, b = font.getbbox(text, anchor="ls")
    x = centre[0] - (l + r) / 2.0
    im = Image.new("L", (w, fh), 0)
    ImageDraw.Draw(im).text((x, baseline), text, font=font, fill=255, anchor="ls")
    return im


def mosaic(a, k, resample, gain):
    w, h = a.size
    m = a.resize((max(1, w // k), max(1, h // k)), Image.BOX).resize((w, h), resample)
    m = m.filter(ImageFilter.GaussianBlur(4))
    return m.point(lambda v: min(255, int(v * gain + 0.5)))


def stripes(w, fh, seed):
    rnd = random.Random(seed)
    row = np.zeros(w)
    x = 0
    while x < w:
        n = rnd.randint(4, 24)
        row[x:x + n] = rnd.choice((0.25, 0.6, 0.85, 1.0, 1.0))
        x += n
    return np.tile(row, (fh, 1))


def build_strip(kind, text, font_path, seed, size=None):
    spec = dict(KINDS[kind])
    if size and size != spec["size"]:        # a few st cards are 1120 px wide: centre on that
        spec.update(size=size, centre=(size[0] / 2.0, spec["centre"][1]),
                    max_w=spec["max_w"] - (spec["size"][0] - size[0]))
    w, fh = spec["size"][0], spec["fh"]
    font = fit_font(text, font_path, spec["cap"], spec["max_w"])
    a = text_alpha(text, font, w, fh, spec["centre"])
    A = np.asarray(a, dtype=float)
    ring = A - np.asarray(a.filter(ImageFilter.MinFilter(5)), dtype=float)
    frames = [
        mosaic(a, spec["k1"], Image.NEAREST, 0.62),
        mosaic(a, spec["k2"], Image.BILINEAR, 0.70),
        Image.fromarray(np.clip(A * stripes(w, fh, seed), 0, 255).astype(np.uint8)),
        a,
        Image.fromarray(np.clip(0.16 * A + 0.20 * ring, 0, 255).astype(np.uint8)),
        Image.fromarray(np.clip(0.14 * A + 0.38 * ring, 0, 255).astype(np.uint8)),
    ]
    strip = Image.new("RGBA", spec["size"], (255, 255, 255, 0))
    for i, al in enumerate(frames):
        fr = Image.new("RGBA", (w, fh), (255, 255, 255, 0))
        fr.putalpha(al)
        strip.paste(fr, (0, i * fh))
    return strip, font.size


def render(orig_dir, out_dir, json_path, font_path=FONT):
    dat = os.path.normpath(os.path.join(orig_dir, "..", "..", "..", "Logic", "Dat", "FixedData",
                                        "StageData.dat"))
    if not os.path.exists(dat):
        dat = json_path[:-5]
    titles = load_titles(json_path, dat)
    done, skipped = 0, []
    for p in sorted(glob.glob(os.path.join(orig_dir, "**", "s[tn]_[0-9][0-9][0-9].dds"), recursive=True)):
        rel = os.path.relpath(p, orig_dir)
        base = os.path.basename(p)
        kind, sid = base[:2], int(base[3:6])
        hdr, im, tail = load_dds(p)
        if im.size[1] != KINDS[kind]["size"][1]:
            skipped.append((rel, "size %dx%d" % im.size))
            continue
        if kind == "st":
            text = titles.get(sid)
            if not text:
                skipped.append((rel, "stage %d has no English title" % sid))
                continue
        else:
            text = "Final Stage" if sid == 999 else "Stage %d" % sid
        strip, size = build_strip(kind, text, font_path, seed=sid * 7 + (kind == "sn"), size=im.size)
        dst = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        save_dds(dst, hdr, strip, tail)
        done += 1
    print("rendered %d title strips" % done)
    for r, why in skipped:
        print("  skipped %s: %s" % (r, why))


def preview(dds_path, out_png):
    _, im, _ = load_dds(dds_path)
    bg = Image.new("RGBA", im.size, (40, 40, 60, 255))
    bg.alpha_composite(im)
    bg.convert("RGB").save(out_png)


def main(argv):
    if len(argv) >= 4 and argv[0] == "render":
        font = argv[argv.index("--font") + 1] if "--font" in argv else FONT
        render(argv[1], argv[2], argv[3], font)
    elif len(argv) == 3 and argv[0] == "preview":
        preview(argv[1], argv[2])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
