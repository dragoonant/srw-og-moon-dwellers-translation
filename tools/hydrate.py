#!/usr/bin/env python3
"""Public worksheets carry English only; the Japanese comes from the player's own disc.

  hydrate.py strip SRC_DIR OUT_DIR   write English-only copies of every worksheet under SRC_DIR
                                     (drops the Japanese fields; used for the public repo)
  hydrate.py fill [--work WORK] [WORKSHEET_DIR]
                                     put the Japanese back: for each English-only worksheet,
                                     extract its source file from WORK/dec (the player's own
                                     decrypted archives), run the format tool's extract, and
                                     copy the Japanese fields across by string id
  hydrate.py check [WORKSHEET_DIR]   report worksheets that still lack their Japanese

Worksheets live at worksheets/<Archive>/<path in archive>.json and worksheets/EBOOT.elf.json,
the layout build.py and extract_all.py use. Entries are matched by "id" (every format tool
numbers its strings the same way on every extract).
"""
import glob
import json
import os
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

SECRET = ("jp", "text", "lines", "raw")
TOOL = {"LDBI": "script.py", "LOGO": "script.py", "FIXH": "fixh.py", "BMD": "battle.py",
        "CSB": "csb.py", "WTD": "wtd.py", "ELF": "eboot_strings.py", "MTI": "mti.py"}


def load(p):
    return json.load(open(p, encoding="utf-8"))


def save(p, ws):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ws, f, ensure_ascii=False, indent=1)


def has_jp(ws):
    return any(any(k in e for k in SECRET) for e in ws.get("strings", []))


def strip(src, out):
    n = 0
    for p in glob.glob(os.path.join(src, "**", "*.json"), recursive=True):
        ws = load(p)
        for e in ws.get("strings", []):
            for k in SECRET:
                e.pop(k, None)
        dst = os.path.join(out, os.path.relpath(p, src))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        save(dst, ws)
        n += 1
    return n


def source_of(work, wroot, p):
    rel = os.path.relpath(p, wroot).replace(os.sep, "/")
    if rel == "EBOOT.elf.json":
        return None, None, os.path.join(work, "pristine", "USRDIR", "EBOOT.elf")
    archive, inner = rel.split("/", 1)
    inner = inner[:-5]                                   # strip .json
    return archive, inner, os.path.join(work, "ext", archive, *inner.split("/"))


def fill(work, wroot):
    import build                                         # for ensure_extracted
    sheets = [p for p in glob.glob(os.path.join(wroot, "**", "*.json"), recursive=True)]
    todo = [(p, load(p)) for p in sheets]
    todo = [(p, ws) for p, ws in todo if not has_jp(ws)]
    by_arc = {}
    for p, ws in todo:
        arc, inner, _ = source_of(work, wroot, p)
        if arc:
            by_arc.setdefault(arc, []).append(inner)
    for arc, inners in by_arc.items():
        build.ensure_extracted(work, arc, inners)
    done = 0
    with tempfile.TemporaryDirectory() as tmp:
        for p, ws in todo:
            fmt = str(ws.get("format", "")).split()[0]
            _, _, src = source_of(work, wroot, p)
            fresh = os.path.join(tmp, "x.json")
            r = subprocess.run([sys.executable, os.path.join(HERE, TOOL[fmt]), "extract", src, fresh],
                               capture_output=True, text=True, encoding="utf-8")
            if r.returncode != 0:
                raise SystemExit("extract failed for %s:\n%s%s" % (src, r.stdout, r.stderr))
            orig = {(e.get("pool"), e["id"]): e for e in load(fresh)["strings"]}   # LOGO ids restart per pool
            for e in ws["strings"]:
                o = orig.get((e.get("pool"), e["id"]))
                if o is None:
                    raise SystemExit("%s: string %s not in your game file (different version?)" % (p, e["id"]))
                for k in SECRET:
                    if k in o:
                        e[k] = o[k]
            save(p, ws)
            done += 1
    print("filled the Japanese into %d worksheet(s)" % done)


def main(argv):
    if len(argv) >= 2 and argv[1] == "strip" and len(argv) == 4:
        print("wrote %d English-only worksheets" % strip(argv[2], argv[3]))
        return 0
    if len(argv) >= 2 and argv[1] in ("fill", "check"):
        work = argv[argv.index("--work") + 1] if "--work" in argv else os.path.join(os.path.expanduser("~"), "srwmd-work")
        pos = [a for i, a in enumerate(argv[2:], 2) if not a.startswith("--") and argv[i - 1] != "--work"]
        wroot = pos[0] if pos else os.path.join(REPO, "worksheets")
        if argv[1] == "check":
            missing = [p for p in glob.glob(os.path.join(wroot, "**", "*.json"), recursive=True) if not has_jp(load(p))]
            print("%d worksheet(s) without Japanese" % len(missing))
            return 1 if missing else 0
        fill(work, wroot)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
