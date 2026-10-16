#!/usr/bin/env python3
"""Find the 2nd OG renderer patch sites in another build of the engine.

For each site in eboot_patch.ADVANCE / FLAG, takes a window of instruction
words around it in the reference ELF (2nd OG) and slides it over the
target ELF's executable segment. Words are compared with register fields
masked out (PPC: bits 6-20 hold rD/rA/rB), so a recompiled function that
only renumbered registers still matches. Prints the best candidates with
their score and a disassembly of the target around the site.

Usage: find_sites.py REF.elf TARGET.elf [--window 24] [--top 3]
"""
import os
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import eboot_patch  # noqa: E402

try:
    import capstone
    CS = capstone.Cs(capstone.CS_ARCH_PPC, capstone.CS_MODE_64 | capstone.CS_MODE_BIG_ENDIAN)
except ImportError:  # disassembly is optional
    CS = None


def exec_seg(elf):
    for va, off, sz, flags in eboot_patch.load_segments(elf):
        if flags & 1:
            return va, off, sz
    raise SystemExit("no executable segment")


def words(elf, off, n):
    return list(struct.unpack_from(">%dI" % n, elf, off))


def mask(w):
    return w & 0xFC00F801 if (w >> 26) in (31, 63, 59) else w & 0xFC000000 | (w & 0xFFFF)


def dis(elf, off, va, n):
    if not CS:
        return
    for ins in CS.disasm(bytes(elf[off:off + 4 * n]), va):
        print("      %08X  %s %s" % (ins.address, ins.mnemonic, ins.op_str))


def main(argv):
    ref = open(argv[1], "rb").read()
    tgt = open(argv[2], "rb").read()
    opt = lambda k, d: int(argv[argv.index(k) + 1]) if k in argv else d
    win, top = opt("--window", 24), opt("--top", 3)
    rva, roff, _ = exec_seg(ref)
    tva, toff, tsz = exec_seg(tgt)
    tw = words(tgt, toff, tsz // 4)
    twm = [mask(w) for w in tw]
    for name, sites in (("ADVANCE", eboot_patch.ADVANCE), ("FLAG", eboot_patch.FLAG)):
        print("==", name)
        for va, old, new, desc in sites:
            ro = roff + (va - rva)
            ctx = words(ref, ro - 4 * win, 2 * win + 1)
            ctxm = [mask(w) for w in ctx]
            # anchor on rare exact words to keep this fast: try every target pos
            # whose masked word equals the masked site word
            best = []
            key = ctxm[win]
            for i, w in enumerate(twm):
                if w != key or i < win or i + win >= len(twm):
                    continue
                score = sum(1 for k in range(2 * win + 1) if twm[i - win + k] == ctxm[k])
                exact = sum(1 for k in range(2 * win + 1) if tw[i - win + k] == ctx[k])
                best.append((score, exact, i))
            best.sort(reverse=True)
            print("  %08X %08X %s" % (va, old, desc[:60]))
            for score, exact, i in best[:top]:
                print("     -> %08X  word %08X  masked %d/%d exact %d"
                      % (tva + 4 * i, tw[i], score, 2 * win + 1, exact))
            if best and "--dis" in argv:
                i = best[0][2]
                dis(tgt, toff + 4 * (i - 3), tva + 4 * (i - 3), 7)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
