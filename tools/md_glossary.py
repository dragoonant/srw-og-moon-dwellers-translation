#!/usr/bin/env python3
"""Build glossary/md_names.tsv: every proper name in The Moon Dwellers with one English form.

Names come from the FIXH tables (pilot names and full names, units, weapons,
keywords, abilities, skills, parts, spirits, stage titles) and from the
speaker labels of the talk scripts. Each name is resolved in canon order
(KNOWLEDGE-BASE D1):

  1. our earlier picks: the worksheet English that came from the 2nd OG TM
     (en_src "tm"), then glossary/signoff.tsv and the category TSVs
  2. OG Gaiden picks: glossary/ogg_proposals.tsv, ogg_terms.tsv, ogg_short_names.tsv
  3. Akurasu: glossary/akurasu_ogmd.tsv, then akurasu_og2nd.tsv / akurasu_ogg.tsv
  4. glossary/md_proposals.tsv (our proposals; English from the official MD release is a
     reference only)
  5. left empty

Matching normalises NFKC, dashes, middle dots, '=' and spaces. Pilot short
names also match the first part of a full name (キョウスケ <- キョウスケ・ナンブ).
Akurasu's Japanese has typos (コンバチカイサー), so a near match (edit distance
1 on names of 6+ characters) is accepted from Akurasu only and marked "near".

glossary/md_fixed.tsv overrides every tier (deliberate corrections, e.g. an Akurasu
mistranslation). Rows already in md_names.tsv with source "proposal" or "fixed"
are kept as they are, so hand edits survive a rebuild.

Usage: md_glossary.py [--stats]
"""
import csv
import glob
import json
import os
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
G = os.path.join(REPO, "glossary")
FIX = os.path.join(REPO, "worksheets", "Logic", "Dat", "FixedData")
OUT = os.path.join(G, "md_names.tsv")

FIELDS = {  # table -> {field label: category}
    "PilotData": {"name": "pilot", "fullname_1": "pilot", "fullname_2": "pilot"},
    "UnitData": {"name": "unit"},
    "WeaponData": {"name": "weapon"},
    "KeyWordData": {"name": "keyword", "name_b": "keyword", "name_c": "keyword"},
    "AbilityData": {"name": "ability", "name_b": "ability"},
    "SkillData": {"name": "skill"},
    "PartsData": {"name": "part"},
    "SpiritData": {"name": "spirit"},
    "StageData": {"title": "stage"},
}


def norm(s):
    s = unicodedata.normalize("NFKC", s)
    for d in "‐‑‒–—―－":
        s = s.replace(d, "-")
    for d in "・･=＝ 　":
        s = s.replace(d, "")
    return s


def is_kana(c):
    return "぀" <= c <= "ヿ"


def near(a, b):
    """One kana substituted, added or dropped (Akurasu typos such as バ/パ, サ/ザ).
    A differing Latin letter or digit is a different name (クラウドＳ vs クラウドＨ)."""
    if abs(len(a) - len(b)) > 1 or min(len(a), len(b)) < 6:
        return False
    if len(a) == len(b):
        diff = [(x, y) for x, y in zip(a, b) if x != y]
        return len(diff) == 1 and is_kana(diff[0][0]) and is_kana(diff[0][1])
    if len(a) > len(b):
        a, b = b, a
    return any(a == b[:i] + b[i + 1:] and is_kana(b[i]) for i in range(len(b)))


def read_tsv(name, jp_col="jp", en_col="en"):
    p = os.path.join(G, name)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return [(r.get(jp_col) or "", r.get(en_col) or "") for r in csv.DictReader(f, delimiter="\t")]


def jp_of(e):
    return e.get("jp") or e.get("text") or "\n".join(e.get("lines", []))


def game_names():
    names = {}   # jp -> {"cat": set, "tm": en or "", "count": n}
    for table, fields in FIELDS.items():
        ws = json.load(open(os.path.join(FIX, table + ".dat.json"), encoding="utf-8"))
        for e in ws["strings"]:
            if e.get("keep"):
                continue
            labels = {r.split(".", 1)[1] for r in e.get("refs", [])}
            cats = {fields[l] for l in labels if l in fields}
            jp = jp_of(e).strip()
            if not cats or not jp or jp.startswith("ダミー") or set(jp) <= set("－？-?ー"):
                continue
            d = names.setdefault(jp, {"cat": set(), "tm": "", "count": 0})
            d["cat"] |= cats
            d["count"] += 1
            if e.get("en") and e.get("en_src") == "tm":
                d["tm"] = e["en"]
    for p in glob.glob(os.path.join(REPO, "worksheets", "Logic", "Dat", "logic", "talk", "*.json")):
        for e in json.load(open(p, encoding="utf-8"))["strings"]:
            if e.get("kind") != "name" or e.get("keep"):
                continue
            jp = e["jp"].strip()
            if "　" in jp:          # "ハガネ　ブリッジ": a place label, not a name
                continue
            d = names.setdefault(jp, {"cat": set(), "tm": "", "count": 0})
            d["cat"].add("speaker")
            d["count"] += 1
            if e.get("en") and e.get("en_src") == "tm":
                d["tm"] = d["tm"] or e["en"]
    return names


def index(pairs):
    exact, first = {}, {}
    for jp, en in pairs:
        if not jp or not en:
            continue
        exact.setdefault(norm(jp), en)
        parts = jp.replace("･", "・").split("・")
        if len(parts) > 1:
            first.setdefault(norm(parts[0]), en.split()[0])
    return exact, first


def main(argv):
    names = game_names()
    keep = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if r["en"] and r["source"] in ("proposal", "fixed"):
                    keep[r["jp"]] = r
    tiers = [
        ("2og", read_tsv("signoff.tsv") + sum((read_tsv(t) for t in
            ("pilots.tsv", "units.tsv", "attacks.tsv", "skills.tsv", "spirits.tsv", "parts.tsv", "factions.tsv")), [])),
        ("ogg", read_tsv("ogg_proposals.tsv") + read_tsv("ogg_terms.tsv") + read_tsv("ogg_short_names.tsv")),
        ("akurasu-md", read_tsv("akurasu_ogmd.tsv")),
        ("akurasu", read_tsv("akurasu_og2nd.tsv") + read_tsv("akurasu_ogg.tsv")),
        ("proposal", read_tsv("md_proposals.tsv")),     # our own proposals, last
    ]
    idx = [(name, *index(pairs)) for name, pairs in tiers]
    # Deliberate corrections beat every source (glossary/md_fixed.tsv).
    for jp, en in read_tsv("md_fixed.tsv"):
        if jp and en:
            keep[jp] = {"en": en, "source": "fixed", "alt": "", "notes": "md_fixed.tsv"}
    rows = []
    for jp, d in sorted(names.items(), key=lambda kv: (sorted(kv[1]["cat"])[0], kv[0])):
        cat = ",".join(sorted(d["cat"]))
        if jp in keep:
            r = keep[jp]
            rows.append([cat, jp, r["en"], r["source"], r.get("alt", ""), r.get("notes", "")])
            continue
        k = norm(jp)
        found = []
        if d["tm"]:
            found.append(("2og-tm", d["tm"]))
        for name, exact, first in idx:
            if k in exact:
                found.append((name, exact[k]))
            elif ("pilot" in d["cat"] or "speaker" in d["cat"]) and k in first:
                found.append((name + "-first", first[k]))
            elif name.startswith("akurasu"):
                hit = next((en for j, en in exact.items() if near(k, j)), None)
                if hit:
                    found.append((name + "-near", hit))
        en, src = (found[0][1], found[0][0]) if found else ("", "")
        alts = sorted({f"{s}:{e}" for s, e in found[1:] if e != en})
        rows.append([cat, jp, en, src, " | ".join(alts), "x%d" % d["count"]])
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["category", "jp", "en", "source", "alt", "notes"])
        w.writerows(rows)
    by = {}
    for r in rows:
        c = r[0].split(",")[0]
        t = by.setdefault(c, [0, 0])
        t[0] += 1
        t[1] += bool(r[2])
    for c, (n, h) in sorted(by.items()):
        print("%-8s %4d names, %4d resolved, %4d open" % (c, n, h, n - h))
    print("total %d names, %d open; wrote %s" % (len(rows), sum(1 for r in rows if not r[2]), OUT))


if __name__ == "__main__":
    main(sys.argv)
