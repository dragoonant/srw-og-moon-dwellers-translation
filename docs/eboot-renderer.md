# EBOOT text renderer: The Moon Dwellers (BLJS10335)

Decrypted `EBOOT.elf`: SHA-1 `cec06905…`, 15,722,648 bytes. Big-endian ELF64, 32-bit pointers.
Disassembly is from capstone (`tools/re/find_sites.py` and the listing script in this doc's history).
The 2nd OG notes are in `docs/2nd-og/eboot-renderer.md`. The engine is the same, but every routine was recompiled, so
**no 2nd OG address or patch word applies.**

## How the routines were found

The six FTTF readers are the only instructions in `.text` that read the page-remap table at FTTF+0x454
(`lhz rX,0x454(rY)`). Searching for that gives exactly six hits in each game.

| Routine | MD entry | MD remap read | 2nd OG entry |
|---|---|---|---|
| draw A (tagged text) | `0x00B7A198` (size 0x27E8) | 0xB7A510 | 0x00A123F0 |
| draw B (plain text) | `0x00B7C980` (size 0x27D8) | 0xB7CCE8 | 0x00A149E4 |
| measure | `0x00B7F158` | 0xB7F2E4 | one of 0xA11CB8 / 0xA16F94 (skips U+0020..0080) |
| measure | `0x00B7F4D0` | 0xB7F690 | |
| measure | `0x00B7F808` | 0xB7F9D4 | |
| measure | `0x00B7FC20` | 0xB7FDE0 | |

The FTTF magic check (`lis rX,0x4654`) is at 0x002400A4 in the font loader.

## Font object: field offsets moved

| Field | 2nd OG | MD |
|---|---|---|
| FTTF header pointer | +0x10 | **+0x18** |
| size_w (glyph quad width, float) | +0x2C | **+0x48** |
| size_h | +0x30 | +0x4C |
| layout mode byte (0 fixed, 1 proportional) | +0xD4 | **+0xF4** |

`scale = size_w / hdr->cell_w`, the same as in 2nd OG (for example `fdivs f30,f13,f0` at 0xB7F1B4).

## The localisation hook

```
0x0034CA78:  li r3,0
0x0034CA7C:  blr
```

Every layout decision in the six routines is now:

```c
if (stub_0034CA78() != 0 || font->mode /*+0xF4*/ != 0)  proportional (+ page remap)
else                                                    fixed (centred, pen += size_w)
```

There are 14 such calls in the renderer (two per draw routine for the loop and the squeeze setup; two or three per measure
routine for the remap and the advance). There are 24 more callers outside the renderer
(0x10F9F8, 0x23E068, 0x32DC78…0x32E830, 0x330BB4, 0x7A2C88, 0x7A3F88), not yet examined.
In the Japanese build the stub always returns 0. It is very likely what an overseas build switches on.

## Patch (`tools/eboot_patch.py`, default variant `stub`)

Replace each of the 14 renderer calls `bl 0x34CA78` with `li r3,1` (`38600001`). The renderer then always takes the
developers' own proportional path:

- **pen += scale × entry.advance**, glyphs left-aligned; `fttf.py proportional` writes the advances.
- **Page remap** from font.bin: U+30xx kana use the narrow page A0, and U+FF01..FF5E full-width forms draw as
  ASCII glyphs (+0x20). Full-width digits or letters left in English text therefore draw as proportional ASCII.
- **The 24 non-renderer callers are untouched.** Variant `stub-global` patches the stub itself instead; it is for experiments only.

| VA | Original | Routine |
|---|---|---|
| 0x00B7A498 | 4B7D25E1 | draw A: loop select |
| 0x00B7B8D4 | 4B7D11A5 | draw A: squeeze setup |
| 0x00B7CC7C | 4B7CFDFD | draw B: loop select |
| 0x00B7E0A8 | 4B7CE9D1 | draw B: squeeze setup |
| 0x00B7F264 / 0x00B7F434 | 4B7CD815 / 4B7CD645 | measure 0xB7F158 |
| 0x00B7F5D4 / 0x00B7F618 | 4B7CD4A5 / 4B7CD461 | measure 0xB7F4D0 |
| 0x00B7F8EC / 0x00B7F980 / 0x00B7FB90 | 4B7CD18D / 4B7CD0F9 / 4B7CCEE9 | measure 0xB7F808 |
| 0x00B7FCF4 / 0x00B7FD8C / 0x00B7FF98 | 4B7CCD85 / 4B7CCCED / 4B7CCAE1 | measure 0xB7FC20 |

The `nop` after each `bl` is the TOC-restore slot and stays a nop. `r3` is the call's return register, so
`li r3,1` is exactly "the stub returned 1".

## To verify in game

1. Dialogue, menus and battle text advance proportionally, and descenders and ä/ü draw correctly.
2. Centred and right-aligned UI text still lines up (the measure routines use the same path).
3. Japanese text left untranslated looks acceptable with narrow kana.
4. The 2nd OG open point still applies: code that positions text by character index × fixed width
   (a marquee or scroll in 2nd OG at 0x00063060) has not yet been located in MD.
