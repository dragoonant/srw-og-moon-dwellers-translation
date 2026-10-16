# Rendering English: The Moon Dwellers

Phase 4 results, 2026-10-15. The renderer internals and the patch are in `docs/eboot-renderer.md`.
Screenshots are in `screenshots/` (gitignored).

## What the build does

1. **EBOOT:** `eboot_patch.py` (variant `stub`, 14 words) makes the six FTTF routines always take the proportional path.
2. **Font:** `fttf.py proportional` changes `font.bin`:
   - **Spacing:** ASCII ink moves to the cell's left edge, with advance = ink + 2 px, space = 8 px, and all digits as wide as the widest.
   - **ä / ü:** composed into free cells, white dots with a 1-px outline like the rest of the font.
   - **U+3000:** its remap target (0xA000) keeps a 32 px advance.
   - **No vertical shift.** MD's descenders already line up with the x-height.

## Verified in game (RPCS3, keyboard profile, fresh boot)

| Screen | Result |
|---|---|
| Title, Select-Scenario, Select-Mode, Question dialog | English from the 2nd OG TM renders proportionally; italic menus are fine |
| Opening dialogue (wide box) | Test rows of 389 / 727 / 894 px all fit. About 70 screen px are left after the 894 px row |
| Event dialogue (narrow box, smaller text) | The 894 px row fits with about 12 screen px to spare |
| Mission Objective | Win / loss / SR-point texts render; 「第0話」 is Japanese (EBOOT format string) |
| Map command window | "Spirit" and "Stats" render; 「移動」 is not in the TM yet |
| Untranslated Japanese | Narrow kana and full-width Latin drawn as ASCII (SR, PP, NORMAL); readable |
| Name box | Names such as エ=セルダ show the full-width ＝ as ASCII "=" |

**Width budgets.** `fitcheck.py` derives them from the Japanese: LDBI **832 px**, BMD **800 px**. Both are inside the
measured room (at least about 880 px in the narrow box), so they stay as they are.

## Problems found and fixed

| Problem | Cause | Fix |
|---|---|---|
| q, p, j sat lower than the other letters | The 2nd OG descender drop (+2, base −1) moved them away from the x-height; MD's font already aligns them | `fttf.BASE_DY = 0`, no per-letter drop |
| ä dots were black | MD glyphs are white fill with a black outline; the dot colour came from the first ink pixel, which is outline | Dots use the fill colour with an outline-coloured edge |
| Icon overlapped "Fast" in the key guide ('Advance (+　　Fast)') | U+3000 is on page 0x30, which the remap sends to the narrow page A0 (22 px); the menu reserves icon room with U+3000 | `fttf.keep_ideographic_space` sets 0xA000's advance to 32 |

## Full-translation build (2026-10-15, commit 28ca3ea)

Verified in game after a fresh boot: Select-Scenario, Select-Mode (fully English, with colour tags kept), the question
dialog, prologue dialogue (three-line lines, name box "E-Selda", "Al-Van"), and the **battle quote window** in the
prologue demo battle ("Finger Cleave!", "Lord E-Selda struck first...! / But!", with the second-line indent kept).
Screenshots: `screenshots/full_*.png`.

## Guidance Scenario and picture text (2026-10-16)

Verified in game in the Guidance Scenario (tutorial):
- The **LESSON 1 ~ Movement ~** banner (white italic with a cyan halo, like the original).
- Map **General Commands** (End Phase … Suspend Save, NORMAL / SR Points / Turn Count / Funds) and **unit commands**
  (Move, Air, Spirit, Stats, Join, Wait); the End Phase question dialog.
- The **SUP ATK / SUP DEF** map overlay (exFont01 sprites).
- The **Status** screen (move type and spirit legend in the old build; both are now English sprites:
  `Move [6/ A L – –]`, `Va So Mt Fl …`), **Unit Stats** (stats, Special Skills, terrain table), **MAP DATA**.

Found and fixed from these screens: the terrain headers 空陸海宇, movement types 空陸水地 and active-spirit markers
are exFont01 sprites, not strings; the skill-level "Lv" sprite touched the skill name.

## Prologue playthrough (2026-10-16)

Played Stage 0 "Prologue" to the end in RPCS3: player and enemy phases, pre-battle screen (Offense/Defense, ATK/CTR
badges, Action Settings / Support Settings / Animations: ON / Start Battle), battle quotes, GET RESULT, the boss
dialogue, So-Des defeated and the aftermath scene with Katia and Melua. Unit Stats now reads "Counter Lv8",
terrain Ai/La/Se/Sp, Move "5/ – L – –"; the weapon list is English.

The first attempt crashed at the first enemy phase (RPCS3: illegal opcode 0x000000e0 at 0x407f64): five EBOOT
worksheet entries were instruction bytes taken for one-kanji strings, and their "translation" overwrote code. Fixed
in `eboot_strings.py` (KB item 49).

## Still to check

- **Tutorial summary pages** (`textures/summary_01-15.json`) and the **Summary** panel header: previews only. They
  appear at the end of each lesson; the scripted lesson flow was not completed in RPCS3.
- **New font in game:** the ä/ü outline has not been screenshotted yet (no ä/ü name has come up so far). The key
  guide's icon row renders correctly (pre-battle screen: Confirm / Back / Demo / Spirit / Info).

## Intermission, Library and Stage 1 Space Route (2026-10-16)

Loaded the post-prologue save: Intermission, Options (System Settings, Library menu), Strategy Q&A (topic list and an
answer page), Sound Select, Buy Abilities, the route choice, the Space Route title card ("Stage 1 / White Lynx") and
its objectives, Calvina's Unit Stats, and the Guidance Scenario banner "LESSON 1 / ~ Movement ~" all read correctly.

Fixed from these screens:
- **Terrain table operators.** WTD #601 `  ＋<X=16>＝` draws "+" and "=" between the pilot, unit and final rank
  columns. With the proportional font both landed on column 1, so the letters looked struck through. It is now
  `<X=30>+<X=22>=` and reads "B +A =B". `<X=n>` did not behave like a plain offset (30/22 and 33/25 rendered the same),
  so the spacing is close but not centred. Waived in `fit_waivers.json`.
- Save descriptions say "Stage 00" instead of "Scenario:00" (only new saves; old saves keep their text).
- Three "(Ver. …)" BGM titles now match their base songs.

Not yet seen: the tutorial summary pages. Lesson 1 never advanced in RPCS3 (the Raven reached the point over two turns
and no event fired), so they remain preview-only.

Verified since: the exFont01 sprites after the fix (Unit Stats: Ai/La/Se/Sp, "Counter Lv8", Move "5/ – L – –";
weapon list terrain row) and the **Stage 1 title card** ("Stage 1" / "Soul Saber vs. Compati Kaiser", reached by
playing the prologue through; Stage 1 objectives, Intermission, the route choice and the area-map label "Japan -
Sapporo Outskirts" are English too). A save at the Intermission after the prologue is in RPCS3's save list.
