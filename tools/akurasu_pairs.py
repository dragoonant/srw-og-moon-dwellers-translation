#!/usr/bin/env python3
"""Extract Japanese/English name pairs from Akurasu wiki OG2nd pages.

Input: a folder of raw wikitext files saved from
  https://www.akurasu.net/wiki/index.php?title=Super_Robot_Wars/OG2nd/<Page>&action=raw
(file name = page path with "/" as "__" and spaces as "_").
Output: glossary/akurasu_og2nd.tsv with columns page, jp, en.

Rule: in every table row ("| a || b || ..."), the first cell containing
Japanese is the jp name and the nearest cell before it without Japanese is
the en name. Cells with " / " on both sides are split pairwise
("R-1 / R-Wing || Ｒ－１ / Ｒウィング"). Pilot_Spirit lines also carry the
spirit list as "熱血ーHotblood(40)", which yields spirit pairs.

Chart pages (MD Complete_Chart / Flow_Chart) also give stage titles from cells like
"第0話： プロローグ<br>Scenario 0: Prologue".

Usage: akurasu_pairs.py RAW_DIR --out glossary/akurasu_XXX.tsv
       (--out is required, so one game's pairs never overwrite another's)
"""
import csv
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JP = re.compile(r"[぀-ヿ一-鿿０-ｚ]")
SPIRIT = re.compile(r"([぀-ヿ一-鿿]+)\s*[－ー\-]\s*([A-Za-z][A-Za-z' .-]*?)\s*[（(]")


def clean(cell):
    cell = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", cell)   # [[link|text]]
    cell = re.sub(r"'''?|<[^>]+>|\{\{[^}]*\}\}", "", cell)
    return cell.strip().strip("|").strip()


STAGE = re.compile(r"第\s*\d+\s*話[：:]\s*([^<'|]+?)\s*<br\s*/?>\s*(?:Scenario\s*\d+[：:]\s*)?([^<'|]+?)(?:\s+Scenario\s*\d+)?\s*'''")


def pairs_from_page(name, text):
    out = [(m.group(1).strip(), m.group(2).strip()) for m in STAGE.finditer(text)]
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("|-") or line.startswith("|}"):
            continue
        cells = [clean(c) for c in re.split(r"\|\|", line.lstrip("|"))]
        for i, c in enumerate(cells):
            if JP.search(c):
                en = next((cells[j] for j in range(i - 1, -1, -1) if cells[j] and not JP.search(cells[j])), None)
                if en:
                    jps, ens = [x.strip() for x in c.split(" / ")], [x.strip() for x in en.split(" / ")]
                    if len(jps) == len(ens) > 1:
                        out += list(zip(jps, ens))
                    else:
                        out.append((c, en))
                break
        if name == "Pilot_Spirit":
            out += [(m.group(1), m.group(2).strip()) for m in SPIRIT.finditer(line)]
    return out


def main(argv):
    raw = argv[1]
    rows, seen = [], set()
    for f in sorted(os.listdir(raw)):
        if not f.endswith(".txt"):
            continue
        page = f[:-4].split("__")[-1]
        for jp, en in pairs_from_page(page, open(os.path.join(raw, f), encoding="utf-8").read()):
            jp = jp.replace("･", "・")
            if len(en) > 60 or len(jp) > 40:
                continue
            key = (page, jp, en)
            if key not in seen:
                seen.add(key)
                rows.append(key)
    if "--out" not in argv:
        raise SystemExit("usage: akurasu_pairs.py RAW_DIR --out glossary/akurasu_XXX.tsv")
    dst = argv[argv.index("--out") + 1]
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["page", "jp", "en"])
        w.writerows(rows)
    by = {}
    for p, _, _ in rows:
        by[p] = by.get(p, 0) + 1
    print(by)
    print("wrote %d pairs to %s" % (len(rows), dst))


if __name__ == "__main__":
    main(sys.argv)
