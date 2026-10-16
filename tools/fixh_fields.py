#!/usr/bin/env python3
"""Find which record fields of a FIXH table hold string indices.

Used to re-derive fixh.FIELD_MAP for a new game. For every (offset, width)
in the record (u8 and big-endian u16), the values across all records are
read. A field is a candidate when most records hold an in-range value and
the values hit many distinct strings. A greedy cover then picks the
fields that explain the most strings, and the output shows sample strings
per field so a human can label it.

Usage:
  fixh_fields.py FILE.dat [--min-hits N] [--samples N]
  fixh_fields.py DIR                       (every .dat, summary only)
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixh  # noqa: E402


def candidates(f, min_hits):
    n = len(f.strings)
    rs = f.record_size
    ids = [f.record_id(ri) for ri in range(len(f.records))]
    out = []
    for w in (2, 1):
        for off in range(0, rs - w + 1):
            vals = [fixh.read_field(r, off, w) for r in f.records]
            # skip the record id itself (offset 0 in DOFS tables, or a running count)
            same = sum(1 for ri, v in enumerate(vals) if v == ids[ri] or v == ri)
            if off == 0 and same > 0.9 * len(vals):
                continue
            inr = [v for v in vals if v < n]
            hits = set(inr)
            if len(hits) < min_hits or len(inr) < 0.5 * len(vals):
                continue
            # an index field rarely points at string 0 in every record
            if hits == {0}:
                continue
            out.append((off, w, hits, len(inr) / len(vals)))
    return out


def cover(f, cands):
    n = len(f.strings)
    nonempty = {i for i, s in enumerate(f.strings) if any(l for l in s)}
    left = set(nonempty)
    picked = []
    while left:
        best = max(cands, key=lambda c: (len(c[2] & left), c[1]), default=None)
        if not best or len(best[2] & left) < 2:
            break
        picked.append(best)
        left -= best[2]
        cands = [c for c in cands if c is not best and not (c[0] == best[0])]
    return picked, left, nonempty


def report(path, min_hits=2, samples=4, quiet=False):
    f = fixh.FixhFile(open(path, "rb").read(), path)
    n = len(f.strings)
    if not n or not f.records:
        if not quiet:
            print("%s: %d strings, %d records - nothing to map" % (f.stem, n, len(f.records)))
        return
    picked, left, nonempty = cover(f, candidates(f, min_hits))
    old = fixh.FIELD_MAP.get(f.stem, [])
    oldhits = set()
    for off, w, _, _ in old:
        if off + w <= f.record_size:
            oldhits |= {fixh.read_field(r, off, w) for r in f.records} & nonempty
    print("%-26s %4d strings (%d non-empty), %4d records x %3d B; current map covers %d; "
          "derived %s covers %d, %d left"
          % (f.stem, n, len(nonempty), len(f.records), f.record_size, len(oldhits),
             [(o, w) for o, w, _, _ in picked], len(nonempty) - len(left), len(left)))
    if quiet:
        return
    for off, w, hits, frac in picked:
        ex = [ " / ".join(f.strings[i])[:40] for i in sorted(hits)[:samples]]
        print("   +0x%03x u%d  %4d strings, %3.0f%% of records in range: %s"
              % (off, 8 * w, len(hits), 100 * frac, " | ".join(ex)))
    if left:
        print("   unexplained:", " | ".join(" / ".join(f.strings[i])[:30] for i in sorted(left)[:samples]))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    opt = lambda k, d: int(argv[argv.index(k) + 1]) if k in argv else d
    p = argv[1]
    if os.path.isdir(p):
        for fn in sorted(os.listdir(p)):
            if fn.endswith(".dat"):
                report(os.path.join(p, fn), quiet=True)
    else:
        report(p, opt("--min-hits", 2), opt("--samples", 4))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
