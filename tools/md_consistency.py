#!/usr/bin/env python3
"""Unify English across worksheets after parallel translation.

1. Variant fixes: every "en" gets the replacements in VARIANTS (whole words,
   case-sensitive), e.g. "Leonisis" -> "Leonysis". These are spellings that
   different translators chose before a term was settled.
2. Context fixes: a replacement that applies only when the Japanese contains a
   marker (Axel's 「…これがな」 tic -> "that's how it is").
3. Report: for every canon glossary term found in an entry's Japanese, count
   entries whose English uses a different known rendering (reported only).

Entries with "keep" are never touched. Prints counts per rule.

Usage: md_consistency.py [--dry-run]
"""
import collections
import glob
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

VARIANTS = [
    ("Leonisis", "Leonysis"),
    ("Leonysis Haga", "Leonysis Harga"),
    ("Rato", "Lato"),
    ("Replace weapon", "Replace Weapon"),
    ("Replace parts", "Replace Parts"),
    ("Sick Cylinder", "Thick Cylinder"),
    ("Kashin Ship", "deity ship"),
    ("god-ship", "deity ship"),
    ("Elebe", "Eleve"),
    ("Duban Ogre", "Duban Org"),
    ("Duban Ogue", "Duban Org"),
    ("Arieil Ogre", "Arieil Org"),
    ("Gestirben", "Gestorben"),
    ("Zelanio", "Zeranio"),               # 2nd OG unit name
    ("Type-II", "Type-2"),
    ("Sure Kill", "Honmei Satsu"),
    ("emperor unit", "Emperor Unit"),
    ("Ensign", "Lieutenant"),            # 少尉: 2nd OG uses Lieutenant (270 vs 18)
    ("Darubi", "Dalubi"),
    ("Fairy Cribiar", "Fairy Klibia"),
    ("Fairy Crivia", "Fairy Klibia"),
    ("Fairy Clivia", "Fairy Klibia"),
    ("Altried", "Altolied"),
    ("Yon Jebana", "Yon Gebana"),
    ("Jebana", "Gebana"),
    ("Gayattova Schecca", "Gayattoba Stecca"),
    ("Nicolaus", "Nikolaus"),
    ("Kujuua", "Kujuah"),
    ("Quisud", "Quisude"),
    ("Giran", "Gilan"),
    ("Gillan", "Gilan"),
    ("Courangeux", "Coulange"),
    ("Muruu", "Muru"),
    ("Malm", "Malum"),
    ("Laki", "Raki"),                    # ラキ: 2nd OG TM 50 vs 9
    ("Lakhi", "Raki"),
    ("Race Arcana", "Res Arcana"),       # レース・アルカーナ: 2nd OG TM 16 vs 9
    ("Eiterum", "Eitelum"),
    ("Shuun", "Shune"),                  # シューン: glossary form, the Fury form of Shiun (Tou-Ya / E-Selda Shune)
    ("Eitelm", "Eitelum"),
    ("Zonbolt", "Sombold"),
    ("Stecka", "Stecca"),
    ("Marum", "Malum"),
    ("Isvelga", "Isberga"),
    ("Bolquede", "Borquede"),
    ("Vodue", "Vodyu"),
    ("Borkwede", "Borquede"),
    ("Grignard", "Grineal"),
    ("Clearna", "Cliana"),
    ("Grand Red Fenossa", "Grandred Fenossa"),
    ("Enlightened Brain", "Kaimei Brain"),
    ("Cuastwell", "Coustwell"),
    ("Grove of Eons", "Grove of Timefaring"),
    ("Grove of Time's Journey", "Grove of Timefaring"),
    ("Volquede", "Borquede"),
    ("Zonvolt", "Sombold"),
    ("Vodu", "Vodyu"),                   # ヴォーデュ (ヴォドー is Vodo)
    ("Fulaim", "Fureim"),
    ("Goats", "Gortz"),
    ("Gola Golem", "Golar Golem"),
    ("Alistair Links", "Alistair Lynx"),  # アリスター・リンクス (White Lynx)
    # menu labels win over help-text paraphrases (windowdataMain.wtd, as in 2nd OG)
    ("Quick Save", "Suspend Save"),      # 途中セーブ
    ("Split Attack", "Single Attack"),   # 個別攻撃
    ("Focus Attack", "Focused Attack"),  # 集中攻撃
    ("Support Defend", "Support Defense"),   # 援護防御 (skill and menu name)
]
CONTEXT = [
    # (Japanese marker, English pattern, replacement)
    ("これがな", re.compile(r",? and that's (?:that|a fact)"), ", that's how it is"),
    ("フェアリー部隊", re.compile(r"\bThe Fury\b"), "The Fairy unit"),   # source typo misread as the Fury
    ("二度あることは三度ある", re.compile(r"[Tt]hird time's the charm"), "things come in threes"),
    ("個別攻撃", re.compile(r"\bFocused and Split\b"), "Focused and Single"),
    # 解散 (break up a Twin Unit) is Disband in the command menu (ProgStrData);
    # Separate is 分離 (a combining robot), so the two never share a name
    ("解散", re.compile(r"\bJoin, (?:Split|Separate)\b"), "Join, Disband"),
    ("解散", re.compile(r"\band (?:Split|Separate) forms\b"), "and Disband forms"),
    ("解散", re.compile(r"\bthe Separate unit command\b"), "the Disband unit command"),
    ("ド根性", re.compile(r"\bSuper Guts\b"), "Guts"),          # 2nd OG name (根性 is Vigor)
]


def main(argv):
    dry = "--dry-run" in argv
    counts = collections.Counter()
    for path in glob.glob(os.path.join(REPO, "worksheets", "**", "*.json"), recursive=True):
        ws = json.load(open(path, encoding="utf-8"))
        dirty = False
        for e in ws["strings"]:
            en = e.get("en")
            if e.get("keep") or not en:
                continue
            new = en
            for a, b in VARIANTS:
                rx = re.compile(r"(?<![A-Za-z])%s(?![a-z])" % re.escape(a))
                new, n = rx.subn(b, new)
                if n:
                    counts[a] += n
            if ws.get("format") in ("LDBI", "LOGO", "BMD", "ELF"):
                # keyword tags copied from wrapped dictionary names: one line inside <...>
                fixed = re.sub(r"<[^<>=]*\n[^<>=]*>", lambda m: " ".join(m.group(0).split()), new)
                if fixed != new:
                    counts["tag-newline"] += 1
                    new = fixed
            jp = e.get("jp") or e.get("text") or "\n".join(e.get("lines", []))
            # 「！　…」 startle mark: a bare "!" opening an English line reads as a
            # typo; write it "...!" (style guide, "Startle marks")
            fixed = re.sub(r"^([!?]+)[ 　]+(?=\S)", r"...\1 ", new)
            if fixed != new:
                counts["startle"] += 1
                new = fixed
            for mark, rx, b in CONTEXT:
                if mark in jp:
                    new, n = rx.subn(b, new)
                    if n:
                        counts["ctx:" + mark] += n
            if new != en:
                e["en"] = new
                dirty = True
        if dirty and not dry:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(ws, f, ensure_ascii=False, indent=1)
    # keep the translation memory in step
    tmp = os.path.join(REPO, "translations", "tm.json")
    if os.path.exists(tmp) and not dry:
        tm = json.load(open(tmp, encoding="utf-8"))
        for k, v in tm.items():
            for a, b in VARIANTS:
                v = re.sub(r"(?<![A-Za-z])%s(?![a-z])" % re.escape(a), b, v)
            tm[k] = v
        json.dump(tm, open(tmp, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=0)
    for k, n in counts.most_common():
        print("%-20s %6d" % (k, n))
    print("%s %d replacements" % ("would make" if dry else "made", sum(counts.values())))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
