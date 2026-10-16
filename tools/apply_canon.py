#!/usr/bin/env python3
"""Force glossary canon onto names: every not-kept "name" entry whose whole
Japanese text is a canon key gets the canon English (the glossary is
authoritative; TM or AI English for a name is only a proposal).

Covers FIXH table names (pilot, unit, weapon, keyword ... fields) and the
speaker labels of the talk and stage scripts. Entries get "en_src": "canon".

Usage: apply_canon.py [--dry-run]
"""
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fitcheck  # noqa: E402


def jp_of(e):
    return e.get("jp") or e.get("text") or "\n".join(e.get("lines", []))


def main(argv):
    dry = "--dry-run" in argv
    canon = {jp: en for jp, en, _ in fitcheck.load_glossary()}
    total = 0
    pats = ["worksheets/Logic/Dat/FixedData/*.json", "worksheets/Logic/Dat/logic/talk/*.json",
            "worksheets/Logic/Dat/logic/*.json"]
    for pat in pats:
        for path in glob.glob(os.path.join(REPO, pat)):
            ws = json.load(open(path, encoding="utf-8"))
            changed = 0
            for e in ws["strings"]:
                if e.get("keep") or e.get("kind") != "name":
                    continue
                en = canon.get(jp_of(e).strip())
                if en and e.get("en") != en:
                    e["en"], e["en_src"] = en, "canon"
                    changed += 1
            if changed:
                total += changed
                if not dry:
                    with open(path, "w", encoding="utf-8", newline="\n") as f:
                        json.dump(ws, f, ensure_ascii=False, indent=1)
    print("%s %d names from canon" % ("would set" if dry else "set", total))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
