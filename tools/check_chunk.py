#!/usr/bin/env python3
"""Check in-session translations of exported request files before ingest.

For each rNNNNN.json with an rNNNNN.out.json next to it: every id answered
once; line count within max_lines; each line within the pixel budget
(max_chars_per_line x 17 px, measured with the game's proportional font);
UTF-8 bytes within max_bytes; tags and printf codes as in the Japanese
(keyword tags may appear fewer times); no stray ASCII < >; no Japanese left
outside tags; no full-width Latin or digits.

Usage: check_chunk.py DIR [rNNNNN ...]     (no names: every answered file in DIR)
Exit 1 if any problem; prints one line per problem.
"""
import collections
import glob
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fitcheck  # noqa: E402

JP = re.compile(r"[぀-ヿ一-鿿]")
FW = re.compile(r"[Ａ-Ｚａ-ｚ０-９]")
TAG = re.compile(r"<[^<>]*>")
PRINTF = re.compile(r"%[-+ 0#]*\d*(?:\.\d+)?[sdifuxXc%]")
KEYWORD = re.compile(r"<[^<>/=\d][^<>=]*>")


def split(fmt, s):
    if fmt in ("LDBI", "LOGO", "ELF", "MTI"):     # MTI: "<shown name>@<designer note>"
        return s.split("@")
    if fmt == "BMD":
        return s.split("/")
    return s.split("\n")


def main(argv):
    d = argv[1]
    names = argv[2:] or sorted(os.path.basename(p)[:-9] for p in glob.glob(os.path.join(d, "r*.out.json")))
    font = fitcheck.Font(fitcheck.DEFAULT_FONT)
    bad = 0
    for cid in names:
        req = json.load(open(os.path.join(d, cid + ".json"), encoding="utf-8"))
        fmt = req["format"]
        try:
            out = json.load(open(os.path.join(d, cid + ".out.json"), encoding="utf-8"))["translations"]
        except Exception as ex:  # noqa: BLE001
            print("%s: cannot read answer: %s" % (cid, ex))
            bad += 1
            continue
        got = collections.Counter(int(t["id"]) for t in out)
        en = {int(t["id"]): t["en"] for t in out}
        for it in req["items"]:
            i, jp = it["id"], it["jp"]
            p = lambda msg: print("%s #%d: %s | %r" % (cid, i, msg, en.get(i, "")[:90]))
            if got[i] != 1:
                p("answered %d times" % got[i])
                bad += 1
                continue
            s = en[i]
            if not s.strip():
                p("empty")
                bad += 1
                continue
            lines = split(fmt, s)
            if len(lines) > it["max_lines"]:
                p("%d lines > %d" % (len(lines), it["max_lines"]))
                bad += 1
            limit = it["max_chars_per_line"] * 17
            for ln in lines:
                # formatting tags (<W=..>, </W>, <C=..>) draw nothing; a keyword tag
                # shows its inner text, so measure that without the brackets
                shown = re.sub(r"<([^<>=/]+)>", r"\1", ln)
                w = font.width(TAG.sub("", shown).lstrip("　"))
                if w > limit:
                    p("line %dpx > %dpx: %r" % (w, limit, ln[:60]))
                    bad += 1
            if fmt == "MTI" and len(s.encode("utf-8")) > 63:
                p("%d bytes > 63 (MTI name field)" % len(s.encode("utf-8")))
                bad += 1
            if "max_bytes" in it and len(s.encode("utf-8")) > it["max_bytes"]:
                p("%d bytes > %d" % (len(s.encode("utf-8")), it["max_bytes"]))
                bad += 1
            jt, et = collections.Counter(TAG.findall(jp)), collections.Counter(TAG.findall(s))
            fmt_j = collections.Counter(t for t in jt.elements() if not KEYWORD.fullmatch(t))
            fmt_e = collections.Counter(t for t in et.elements() if not KEYWORD.fullmatch(t))
            if fmt_j != fmt_e:
                p("format tags differ: %s vs %s" % (sorted(fmt_j.elements()), sorted(fmt_e.elements())))
                bad += 1
            if sum(1 for t in et.elements() if KEYWORD.fullmatch(t)) > sum(1 for t in jt.elements() if KEYWORD.fullmatch(t)):
                p("more keyword tags than the Japanese")
                bad += 1
            if PRINTF.findall(jp) != PRINTF.findall(s):
                p("printf codes differ: %s vs %s" % (PRINTF.findall(jp), PRINTF.findall(s)))
                bad += 1
            bare = TAG.sub("", s)
            if "<" in bare or ">" in bare:
                p("stray < or >")
                bad += 1
            if JP.search(bare):
                p("Japanese left in the English")
                bad += 1
            if FW.search(bare):
                p("full-width Latin/digits")
                bad += 1
    print("%d problem(s) in %d file(s)" % (bad, len(names)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
