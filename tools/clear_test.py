#!/usr/bin/env python3
"""Remove render-test English (entries tagged "en_src": "test") from the worksheets.

Usage: clear_test.py [WORKSHEET_DIR]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "worksheets")
n = files = 0
for dp, _, fs in os.walk(root):
    for fn in fs:
        if not fn.endswith(".json"):
            continue
        p = os.path.join(dp, fn)
        ws = json.load(open(p, encoding="utf-8"))
        k = 0
        for e in ws.get("strings", []):
            if e.get("en_src") == "test":
                e["en"] = ""
                del e["en_src"]
                k += 1
        if k:
            n += k
            files += 1
            with open(p, "w", encoding="utf-8", newline="\n") as out:
                json.dump(ws, out, ensure_ascii=False, indent=1)
print("cleared %d test entries in %d worksheets" % (n, files))
