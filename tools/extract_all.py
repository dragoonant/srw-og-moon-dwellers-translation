#!/usr/bin/env python3
"""Write a worksheet for every text carrier in the extracted archives + EBOOT.

Walks WORK/ext/<Archive>/ and runs the matching tool's `extract` into
REPO/worksheets/<Archive>/<path inside archive>.json (the layout build.py
reads). Existing worksheets are left alone unless --force, so translations
are never overwritten.

Skipped on purpose:
  Logic/Dat/logic/old_20151105/   developer leftovers, referenced by nothing
                                  (not in the EBOOT, not in any table)

Usage: extract_all.py [--work WORK] [--force] [--only Logic,EBOOT]
"""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PY = sys.executable
SKIP_DIRS = ("Dat/logic/old_20151105",)


def tool_for(rel, data4):
    low = rel.lower()
    if low.endswith(".bmd"):
        return "battle.py"
    if low.endswith(".csb"):
        return "csb.py"
    if low.endswith(".wtd"):
        return "wtd.py"
    if low.endswith(".mti"):
        return "mti.py"
    if "/fixeddata/" in low and low.endswith(".dat"):
        return "fixh.py"
    if low.endswith(".bin") and data4 in (b"LOGO", b"LDBI"):
        return "script.py"
    return None


def main(argv):
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
    work = opt("--work", os.path.join(os.path.expanduser("~"), "srwmd-work"))
    only = opt("--only", "")
    only = set(only.split(",")) if only else None
    force = "--force" in argv
    jobs = []
    for arc in ("Logic", "Common", "General2d", "General3d", "Battle"):
        if only and arc not in only:
            continue
        root = os.path.join(work, "ext", arc)
        for dp, _, files in os.walk(root):
            for fn in files:
                full = os.path.join(dp, fn)
                rel = os.path.relpath(full, root).replace(os.sep, "/")
                if any(rel.startswith(s) for s in SKIP_DIRS):
                    continue
                with open(full, "rb") as fh:
                    head = fh.read(4)
                tool = tool_for(rel, head)
                if tool:
                    out = os.path.join(REPO, "worksheets", arc, rel + ".json")
                    jobs.append((tool, full, out))
    if not only or "EBOOT" in only:
        jobs.append(("eboot_strings.py", os.path.join(work, "pristine", "USRDIR", "EBOOT.elf"),
                     os.path.join(REPO, "worksheets", "EBOOT.elf.json")))
    done = skipped = failed = 0
    for tool, src, out in jobs:
        if os.path.exists(out) and not force:
            skipped += 1
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        r = subprocess.run([PY, os.path.join(HERE, tool), "extract", src, out],
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0 or not os.path.exists(out):
            failed += 1
            print("FAIL %s %s: %s" % (tool, src, (r.stderr or r.stdout).strip()[-300:]))
        else:
            done += 1
    print("%d worksheets written, %d already present (kept), %d failed" % (done, skipped, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
