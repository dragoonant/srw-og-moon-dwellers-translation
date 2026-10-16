#!/usr/bin/env python3
"""Fill empty "en" fields from the translation memory (exact FORMAT\\tjp hits).

Only entries that are not kept and have no English yet are touched, so
running it again is harmless. Each filled entry gets "en_src": "tm" so later
passes can tell TM English from new AI English.

Usage: tm_prefill.py [--tm translations/tm.json] [--dry-run] [WORKSHEET_DIR]
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def jp_of(e):
    if "jp" in e:
        return e["jp"]
    if "text" in e:
        return e["text"]
    return "\n".join(e.get("lines", []))


def main(argv):
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
    tm = json.load(open(opt("--tm", os.path.join(REPO, "translations", "tm.json")), encoding="utf-8"))
    dry = "--dry-run" in argv
    pos = [a for i, a in enumerate(argv[1:], 1) if not a.startswith("--") and argv[i - 1] != "--tm"]
    root = pos[0] if pos else os.path.join(REPO, "worksheets")
    filled = files = 0
    for dp, _, fs in os.walk(root):
        for fn in fs:
            if not fn.endswith(".json"):
                continue
            p = os.path.join(dp, fn)
            ws = json.load(open(p, encoding="utf-8"))
            fmt = str(ws.get("format", "")).split()[0]
            n = 0
            for e in ws.get("strings", []):
                if e.get("keep") or e.get("en"):
                    continue
                en = tm.get(fmt + "\t" + jp_of(e))
                if en:
                    e["en"], e["en_src"] = en, "tm"
                    n += 1
            if n:
                filled += n
                files += 1
                if not dry:
                    with open(p, "w", encoding="utf-8", newline="\n") as out:
                        json.dump(ws, out, ensure_ascii=False, indent=1)
    print("%s %d entries in %d worksheets from the TM" % ("would fill" if dry else "filled", filled, files))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
