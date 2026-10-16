#!/usr/bin/env python3
"""Patch the decrypted EBOOT.elf so text uses the font's per-glyph advance.

Usage:
  eboot_patch.py IN.elf OUT.elf [--variant stub|stub-global]

IN is never modified. Every site is checked against the original instruction
word before anything is written; any mismatch aborts without writing OUT.

The Moon Dwellers (BLJS10335) renderer (see docs/eboot-renderer.md) has the
same two layout modes as 2nd OG: fixed (each glyph centred in a size_w cell,
pen += size_w) and proportional (pen += scale * entry.advance, plus the FTTF
page remap). The mode byte moved to font+0xF4 (2nd OG: +0xD4), and every
check is now "proportional if stub() != 0 or font+0xF4 != 0", where the stub
at 0x0034CA78 is `li r3,0; blr`: a localisation hook the Japanese build leaves
off. It is called 14 times in the six FTTF routines (2 draw, 4 measure) and 24
times elsewhere.

Variants:
  stub (default)  Replace the 14 renderer calls `bl 0x34CA78` with `li r3,1`.
                  The renderer always takes the developers' own proportional
                  path; the 24 other callers are untouched. The page remap
                  applies, so full-width ASCII forms draw as proportional ASCII
                  and leftover kana use the narrow page.
  stub-global     Patch the stub itself to `li r3,1` (1 word). Also changes
                  the 24 non-renderer callers; for experiments only.

The 2nd OG patch (16 words at 0x00A11E60..0x00A16E94) does not apply: the
routines were recompiled. See docs/2nd-og/eboot-renderer.md for it.
"""
import argparse
import os
import struct
import sys

NOP = 0x60000000

# (virtual address, original word, new word, description)
LI_R3_1 = 0x38600001
STUB = [
    (0x00B7A498, 0x4B7D25E1, LI_R3_1, "draw A 0xB7A198: loop select (stub||mode -> proportional loop)"),
    (0x00B7B8D4, 0x4B7D11A5, LI_R3_1, "draw A 0xB7A198: squeeze setup (stub||mode -> proportional scale)"),
    (0x00B7CC7C, 0x4B7CFDFD, LI_R3_1, "draw B 0xB7C980: loop select"),
    (0x00B7E0A8, 0x4B7CE9D1, LI_R3_1, "draw B 0xB7C980: squeeze setup"),
    (0x00B7F264, 0x4B7CD815, LI_R3_1, "measure 0xB7F158: remap select"),
    (0x00B7F434, 0x4B7CD645, LI_R3_1, "measure 0xB7F158: advance select"),
    (0x00B7F5D4, 0x4B7CD4A5, LI_R3_1, "measure 0xB7F4D0: remap select"),
    (0x00B7F618, 0x4B7CD461, LI_R3_1, "measure 0xB7F4D0: advance select"),
    (0x00B7F8EC, 0x4B7CD18D, LI_R3_1, "measure 0xB7F808: select 1"),
    (0x00B7F980, 0x4B7CD0F9, LI_R3_1, "measure 0xB7F808: select 2"),
    (0x00B7FB90, 0x4B7CCEE9, LI_R3_1, "measure 0xB7F808: select 3"),
    (0x00B7FCF4, 0x4B7CCD85, LI_R3_1, "measure 0xB7FC20: select 1"),
    (0x00B7FD8C, 0x4B7CCCED, LI_R3_1, "measure 0xB7FC20: select 2"),
    (0x00B7FF98, 0x4B7CCAE1, LI_R3_1, "measure 0xB7FC20: select 3"),
]

STUB_GLOBAL = [
    (0x0034CA78, 0x38600000, LI_R3_1, "localisation stub: li r3,0 -> li r3,1 (all 38 callers)"),
]

VARIANTS = {"stub": STUB, "stub-global": STUB_GLOBAL}


def load_segments(elf):
    if elf[:4] != b"\x7fELF" or elf[4] != 2 or elf[5] != 2:
        raise SystemExit("error: not a big-endian ELF64 file")
    phoff = struct.unpack_from(">Q", elf, 0x20)[0]
    phentsize, phnum = struct.unpack_from(">HH", elf, 0x36)
    segs = []
    for i in range(phnum):
        p = phoff + i * phentsize
        p_type, p_flags = struct.unpack_from(">II", elf, p)
        p_offset, p_vaddr, _paddr, p_filesz = struct.unpack_from(">QQQQ", elf, p + 8)
        if p_type == 1 and p_filesz:
            segs.append((p_vaddr, p_offset, p_filesz, p_flags))
    return segs


def va_to_offset(segs, va):
    for vaddr, offset, filesz, flags in segs:
        if vaddr <= va and va + 4 <= vaddr + filesz:
            if not flags & 1:
                raise SystemExit("error: 0x%08X is not in an executable segment" % va)
            return offset + (va - vaddr)
    raise SystemExit("error: 0x%08X is not inside any PT_LOAD segment" % va)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inp", metavar="IN")
    ap.add_argument("out", metavar="OUT")
    ap.add_argument("--variant", choices=sorted(VARIANTS), default="stub")
    args = ap.parse_args()

    if os.path.abspath(args.inp) == os.path.abspath(args.out):
        raise SystemExit("error: OUT must differ from IN (IN is never modified)")

    with open(args.inp, "rb") as f:
        elf = bytearray(f.read())
    segs = load_segments(elf)
    patches = VARIANTS[args.variant]

    # Check every site first; write nothing unless all match.
    plan = []
    bad = 0
    for va, old, new, desc in patches:
        off = va_to_offset(segs, va)
        cur = struct.unpack_from(">I", elf, off)[0]
        if cur != old:
            state = "already patched" if cur == new else "unexpected"
            print("MISMATCH va 0x%08X off 0x%06X: found %08X, expected %08X (%s)"
                  % (va, off, cur, old, state), file=sys.stderr)
            bad += 1
        plan.append((va, off, old, new, desc))
    if bad:
        raise SystemExit("error: %d site(s) did not match the original EBOOT; nothing written" % bad)

    for va, off, old, new, desc in plan:
        struct.pack_into(">I", elf, off, new)
        print("va 0x%08X  off 0x%06X  %08X -> %08X  %s" % (va, off, old, new, desc))

    with open(args.out, "wb") as f:
        f.write(elf)
    print("%s: %d word(s) patched (variant %s) -> %s"
          % (os.path.basename(args.inp), len(plan), args.variant, args.out))


if __name__ == "__main__":
    main()
