# SRW OG Translation Knowledge Base

Lessons learned from the evilgouki fan-translation projects, written to be carried forward
to every new game. Copy this file into each new project and update it at the end of each one.

| Project | Platform | Serial | Status | Entries | AI cost |
|---|---|---|---|---|---|
| 2nd Super Robot Wars OG | PS3 / RPCS3 | BLJS10133 | Playable beta (public) | 84,516 | $65.86 (cap $75) |
| Super Robot Taisen OG Gaiden | PS2 / PCSX2 | SLPS-25836 | v0.1 pre-release (public) | 83,389 | $36.47 (cap $60, key ran dry) |
| The Moon Dwellers | PS3 / RPCS3 | BLJS10335 | In progress, see `PLAN.md` | — | — |

How the file is organised:

- **Part A:** applies to any game (process, translation, QA, publishing, privacy).
- **Part B:** applies to any PS3 game on the 2nd OG / Moon Dwellers engine.
- **Part C:** PS2 notes, kept for reference.
- **Part D:** a checklist of problems we have already hit.

Facts that belong to one game (offsets, addresses, string counts) go in that project's
`docs/` and `PLAN.md`, not here.

Source projects (local): `C:\Claude Code Projects\2nd Og translation\` and
`C:\Claude Code Projects\OG Gaiden Translation\`. Their `docs/`, `tools/`, `glossary/` and
the Gaiden handoff (`HANDOFF-OG-Gaiden.md`) hold the full detail behind this file.

---

## Standing decisions (series-wide)

| # | Decision | Set |
|---|---|---|
| D1 | **Name canon:** (1) English of Kingcom's *OG: Original Generations* PS2 patch, (2) our earlier patches' picks, (3) Akurasu wiki, (4) new proposals. Official Bandai Namco Asia English releases are a **reference only**, never canon. | 2nd OG, reaffirmed for Moon Dwellers |
| D2 | **Review model:** AI first pass + automated gates + scripted playtests, shipped as a **beta**. No human line-edit pass is required before release. Name sign-off is optional; unresolved names fall back to the canon order in D1. | Moon Dwellers kickoff |
| D3 | **Distribution (PS3):** a build-from-your-own-dump installer (`Install.bat` → `install.py`). No game data and no xdelta are shipped. | 2nd OG |
| D4 | **Publishing:** the Japanese script never leaves the private repo. The public repo is a separate tree with English-only worksheets; players refill the Japanese from their own disc (`hydrate.py fill`). | Gaiden, adopted series-wide |
| D5 | **Independence:** never reuse text from other fan patches or MTLs. Their issue lists may be used as pitfall maps, and their xdelta files only to locate files and offsets. The OGs patch is the one exception, as the name and style canon. | 2nd OG |
| D6 | **Credit and privacy:** credit the user as **evilgouki** only (see A9). | Global |

---

# Part A: any game

## A1. Process: ten phases, each with a gate

Do not start a phase until the previous phase's gate passes. Most of our redo work came
from skipping ahead.

| # | Phase | Gate |
|---|---|---|
| 1 | **Data in hand:** hash the dump, boot it once, make save states, set up a short-path work folder outside OneDrive. | Hashes recorded in `pristine/SHA256SUMS.txt`. |
| 2 | **Round-trip tools:** for every container and text format, `extract` → `build` without edits. | **Byte-identical output for every file.** |
| 3 | **Text inventory** of every carrier (`textscan.py`: Shift-JIS, UTF-8, UTF-16 BE/LE), *including 1-character strings, printf-style formats and strings packed after a NUL*. | Coverage report; every Japanese run is accounted for as translate, keep, or not-text. |
| 4 | **Make English render:** put test English into one dialogue line, one menu and one battle line; deploy; screenshot. Fix the font, the advance and wrapping. Measure the real box, row and backlog limits. | Screenshots show readable proportional English. **Width and byte budgets written down.** |
| 5 | **Glossary:** extract every name from the data tables into `signoff.tsv` and fill it from the canon sources (D1). | Every recurring name has one English form. |
| 6 | **Pilot:** one chapter through the full pipeline; report its cost. | Pipeline works end to end; cost per character calibrated. |
| 7 | **Full AI pass** by phase: (A) UI and data tables, then (B) story and battle. Retry until the checker passes. | `fitcheck` / `check` reports 0 errors. |
| 8 | **Playtest and fix rounds**, always from a **fresh boot**. | Agreed screens verified. |
| 9 | **Edit pass:** optional under D2. | — |
| 10 | **Release:** installer, README with known issues, public export (D4), privacy grep (A9). | Clean install from scratch reproduces the dev build. |

**Decide these before phase 7, never after:** the byte encoding (1-byte vs 2-byte), line,
box and backlog limits, label width budgets, and the glossary. Every one of them caused a
re-translation in at least one project.

## A2. Repo layout and file conventions

```
README.md  LICENSE  CHANGELOG.md  PLAN.md  KNOWLEDGE-BASE.md
choices.md        numbered decisions (open / suggested / done) needing evilgouki
deviations.md     names where canon sources disagree
docs/             formats-*.md, rendering.md, style-guide.md, playtesting.md
glossary/         signoff.tsv (canon), category TSVs, akurasu_*.tsv, sources.md, gaps.md
tools/            one tool per format, each with extract / build / roundtrip
worksheets/       one JSON per game file
translations/     tm.json, spent.json, batches/, fit_failures.json
textures/         JSON specs for picture text (never hand-edited images)
screenshots/      (gitignored)
```

Keep the work folder outside the repo and outside OneDrive, on a short path
(`%USERPROFILE%\<game>-work\` with `pristine/ dec/ ext/ build/ fonts/ public/`). Windows
MAX_PATH (260 characters) broke deep builds; the installer refuses work paths longer than
80 characters.

**Worksheet shape:** one JSON per game file.

```json
{"file": "...", "format": "LDBI|LOGO|FIXH|BMD|CSB|WTD|ELF|MTI|...",
 "strings": [{"id": 0, "jp": "...", "en": "...", "kind": "...", "keep": false,
              "budget": 0, "refs": []}]}
```

- `format` selects the build tool.
- `kind` and `keep` come from `classify.py`. **Re-run `classify.py` after any extractor change.**
- `en_raw` is an escape hatch that writes exact bytes.

Every format tool exposes `extract`, `build` and `roundtrip` (plus `info`, `dump`, and
`selftest` where useful). One `build.py --only <steps> --check-only` drives them all.

## A3. Engine text rules to check on every new game

Check each of these against the new game's engine; every one has bitten us.

- **Engine keys stay Japanese.** Speaker and event keys like `[ＤＭ]-name` and `[１]-001`, file
  labels, and `エラー` placeholders. Translating them *skipped interludes and silenced stage
  music*. Short pool words (ゲームオーバー, 非表示, 移動, 実戦) stay `keep` until a test shows they are displayed.
- **`<` and `>` are tag delimiters.** Never emit stray ASCII angle brackets; an unknown tag
  letter can end the line. Formatting tags must match the Japanese exactly.
- **Keyword tags** such as `<イスルギ重工>` → `<Isurugi Heavy Industries>`: the English goes
  *inside* the tag, matches the dictionary entry, and appears **no more often** than in the
  Japanese (`keyword_tags.py`).
- **printf codes** (`%d %s %02d`) stay in the same order.
- **Placeholder characters:** in Gaiden, ASCII `?` was the number placeholder and printed "0".
  Write `？` unless the Japanese uses ASCII.
- **Colour codes** (`#NN…##`, `<C=…>`) are kept exactly, and the measure routine must skip them.
- **Line-break markers differ by format** (`@`+U+3000, `/`+U+3000, real `\n`). The checker
  must split on the right marker per format. It once split CSB/WTD on `@`, and the
  intro crawl merged into one line.
- **The engine does not wrap** (PS3), or wraps only some windows (PS2 battle). Know which.
- **Speaker attribution** comes from the command records, never from pool order.
- **Shared strings:** one Japanese string shared by many speakers gets one English rendering.
  Keep shared battle lines gender- and speaker-neutral.
- **Fake strings:** code bytes can decode as valid Shift-JIS or UTF-8 (junk like 聁 蒁).
  Translating them overwrote code and hung the game. Filter for plausibility and mark
  suspicious hits `keep`.

## A4. Rendering and font: what to look for

- Expect a **fixed-width Latin mode** and patch it to proportional advances. **Always patch the
  draw and measure routines together**, or centring and wrapping break.
- Patch by asserting every original instruction word before writing. Find the patch sites
  in a new build by **byte-pattern search of the known instruction words**.
- **Code caves:** prove them unreferenced against `jal`, **`j` tail calls**, branches, stored
  pointers, `lis/addi` or `lui/addiu` pairs and a RAM dump, then play past the first map load.
  (Gaiden: `acosf` looked dead but was reached by `j` and froze the first map.) Prefer
  rewriting existing instructions in place over using a cave.
- **Generate font changes at build time** from the pristine font, never hand-edited:
  - Move ink to the cell's left edge.
  - Advance = ink width + **2 px** (1 px looked tight).
  - Space ≈ 8 px.
  - Digits share the widest digit's advance.
- **Descenders:** check g/j/p/q/y early; both games needed a baseline fix.
- **Accented letters** (ü ä ö é) are often missing: compose them into spare cells and map
  them in the text encoder.
- The checker must measure with the **same advance table the build writes**, so the checker
  and the screen agree.

## A5. Width and byte budgets

- **Dialogue:** at most 3 lines; per-line pixel budget = **99.5th percentile of Japanese line
  widths** for that format (2nd OG: LDBI 832 px, BMD 704 px).
- **Short labels** (Japanese ≤ 320 px): **2.2× the Japanese width, minimum 160 px**. Holding
  labels to the Japanese width produced "Atk", "Spr", "Abl" and cost a 2,559-entry redo.
- **Menus and windows:** compute real room from the layout geometry (`wtd_fit.py`) *before*
  the full pass. Fix order: reword → shrink that element's font cell (`font_px`) → abbreviate.
- **One-line names stay one line.** Retries had split names over two lines.
- **In-place strings** (executable): budget = original byte length / slot. Over-budget →
  keep the Japanese, log it to `ui_over_budget.json`, re-translate shorter. Never abort the
  whole build for one string.
- **Files that must not grow:** if a file loads into a fixed buffer, gate its size in the
  build (Gaiden SHARED/IM grew and crashed at boot). Tools for staying in size: tail-merge
  strings, reuse dead slots, wrap descriptions at 0.9× the Japanese width.
- **Pool offset width:** u16 offsets cap a pool at 65,535 bytes; the build must refuse, not wrap.
- **Backlog / history:** it may copy fewer bytes per row than the live window (Gaiden: 64).
  This was the competitor patch's crash bug, so measure it in phase 4.

## A6. AI translation pass (`translate_batch.py`)

**Setup**
- Anthropic **Message Batches API**, default model `claude-opus-5-5`, effort `medium`.
  Requests of **80 entries**, `max_tokens` 32000.
- Key from the `ANTHROPIC_API_KEY` env var (or HKCU registry). **Never stored in the repo**;
  `*_key.txt` is gitignored. Check the key has credit before a big batch (Gaiden ran dry).
- **System prompt** = game intro + `docs/style-guide.md` + per-kind working rules, cached with
  `cache_control: ephemeral`.
- **User payload** (JSON):
  - `file`, `format`, `line_break_marker`
  - `glossary`: only the terms in this chunk, longest first
  - `keyword_tags_display_as`
  - `previous_lines_for_context`: 6–8 lines
  - `items[]` = {`id`, `jp`, `kind`, `speaker`, `max_lines`, `max_chars_per_line`, `max_bytes`, `previous_attempt`}
  - `reference_names` (names only)
- **Structured output:** JSON schema `{"translations":[{"id","en"}]}`; every id must come back
  exactly once.

**Translation memory**
- `translations/tm.json`, keyed `FORMAT\tjp`. Identical Japanese is translated once and
  pre-filled. Battle quotes are very repetitive, so this saves most of their cost.
- Carry the previous games' TMs forward (2nd OG `tm.json` 56k entries; Gaiden `tm_ogg.json`).
  They share most of the cast.

**Spend control**
- `submit --dry-run` estimates the cost from a per-character rate calibrated on the pilot.
- Submit refuses if *spent + 1.3 × estimate > cap*. Every batch's actual cost goes into `spent.json`.
- **evilgouki approves the cap in advance** (recorded in `choices.md`); report the pilot cost first.
- Rough cost: **$0.45–0.80 per 1,000 entries** with a carried-over TM.
- Before any unattended or overnight job, run `--dry-run` **and a one-chunk real batch**. An
  overnight poller once died on one broken line.

**Check → retry loop**
- The checker runs the same gates as the build and writes `fit_failures.json`.
- `retry` clears the failing English, stores `retry_note` = failed English + reason, drops the
  TM entry, and resubmits.
- Two or three rounds reach 0 errors. Budget about 10–15% of the spend for retries.

**Order:** pilot chapter → names (forced to canon) → UI/data → descriptions/help → story →
battle → retries → targeted redos.

## A7. Glossary and canon

- **`glossary/signoff.tsv`** is the canon (columns: `category jp en match glossary_jp ogs
  ogs_count akurasu notes signed`). Category TSVs (pilots, units, attacks, skills, spirits,
  parts, factions, terrain) are consulted only for terms missing from signoff.
- **Build it from the data tables before the full pass.** A unit missing from the glossary
  came out in **five spellings** (Altalion).
- **OGs English:** `xdelta_added.py` recovers about 140,000 English strings straight from Kingcom's
  `ogs.xdelta` (VCDIFF ADD/RUN data, LZMA secondary compression) without the source disc.
  `ogs_compare.py` matches names against it.
- **Akurasu:** save raw wikitext (`index.php?title=…&action=raw`) and parse it with `akurasu_pairs.py`.
  romhacking.net and GameFAQs are behind Cloudflare and unreachable; list every URL in `sources.md`.
- `names_signoff.py` normalises with NFKC, unifies dashes and middle dots, and matches first names.
- **Enforcement:**
  - `apply_canon.py` forces canon English onto every table name; AI output for names is only a proposal.
  - `fitcheck` errors on known-wrong variants. Longest term wins (ド根性 Guts vs 根性 Vigor).
  - Katakana names must stand alone (ライ ≠ サテライト).
  - Spirit and skill names are enforced in menus and help, not in dialogue.
  - `consistency.py` reports English drift; one pass fixed 173 cases.
- `deviations.md` lists canon conflicts. Under D2 the OGs form ships unless evilgouki picks otherwise.
- **Established series picks:**
  - Names: OGs short vowels (Kyosuke, Ryusei, Kota, Shu) and umlauts (Lüne, Sänger, Rätsel, Wildwürger).
  - Kai/Shiki become "Custom" / "Type" (Hiryu Custom, Grungust Type 0).
  - OGs Spirit Commands: Valor, Flash, Persist, Wall, Bullseye, Pierce, Gain, Spirit, Vigor, Mettle, Hope.
  - クライウルブズ = Cry Wolves.

## A8. Style guide (summary of `docs/style-guide.md`)

**Names and register**
- No honorifics except "Rishu-sensei". Ranks spelled out ("Lieutenant", never "Lt.").
- Given name first.
- Contraction-heavy natural register, with per-character voice notes.
- Leave gender unspecified where the Japanese does.

**Dialogue punctuation**
- No quote marks on spoken lines (the name box shows the speaker; where there is no name box, use `Name: line`).
- Thoughts in (parentheses). `???` for ？？？.
- `...` for an ellipsis, `--` for a dash, at most `!!`.
- Plain half-width ASCII; the build converts quotes and dashes. No full-width Latin and no leftover 「」『』（）.
- Dialogue is written as one paragraph; the build wraps by pixels.

**Names of units, attacks and UI**
- Units in Title Case with model codes (R-1, MP Gespenst Mk-II).
- Attacks in Title Case. Translate Japanese-word attack names unless canon keeps the romaji (Shishioh Blade).
- Menus in Title Case, banners in ALL CAPS. Stat abbreviations Mob/Mel/Skl/Rng/Def/Acc/Eva.
- Every forced wording (to fit a box) goes in `choices.md`.

## A9. Privacy and publishing (hard rules)

**Privacy**
- **Never** put the real name, Windows username, Gmail or `C:\Users\<name>` path in anything public:
  repo files, comments, commit messages, PRs, artifacts, glossary notes, tool defaults.
- Credit **evilgouki**.
- Tool defaults use `os.path.expanduser("~")` or `%USERPROFILE%`.
- The commit email is the GitHub no-reply address.
- **Grep every change before committing.** 2nd OG's history had to be rewritten with git-filter-repo.

**What goes in git**
- No game data in git. Ignore `*.iso *.7z *.bin *.BIN *.elf *.psarc *.sdat *.xdelta *.ppf EBOOT.* screenshots/ *_key.txt work/ build/`.
- **Watch for over-broad patterns:** `EBOOT.*` hid `worksheets/EBOOT.elf.json` and the
  GitHub build shipped Japanese menus. Add negations (`!worksheets/EBOOT.elf.json`) and check
  `git status --ignored` before release.

**Public repo (D4)**
- The local repo (with the Japanese) is **never pushed**.
- `export_public.py OUT` copies README / LICENSE / CHANGELOG / .gitignore / docs / tools / glossary / textures / data.
  It writes English-only worksheets via `hydrate.py strip`. AI batch dumps and internal notes are excluded.
- Players and builders refill the Japanese with `hydrate.py fill`; verify 0 mismatches.

**Licence and README**
- LICENSE: MIT, "Copyright (c) 2026 evilgouki", for tools and docs only; game content is excluded.
- Ship the font licence (e.g. Fira Sans OFL).
- Credits: "evilgouki, with tools and the first-pass translation by Claude (Anthropic)". Credit
  OGs and Akurasu. Bandai Namco owns the game: buy it.
- README skeleton:
  - Status
  - What you need
  - Installing / Updating / Uninstalling
  - Options
  - Troubleshooting
  - Design choices (incl. AI disclosure)
  - Known issues
  - Reporting problems (screenshot + scenario number)
  - Contributors
  - Credits
  - Licence

## A10. Working with evilgouki (session rules)

**Ask first:** pushing to GitHub, history rewrites, deleting folders, spending past the cap,
and decisions only evilgouki can make (names, font, picture-text wording).
- evilgouki merges PRs.
- **Warn before launching the emulator**; a game window that pops up mid-task gets closed.

**Standing approval:** downloading tools from official sources, and opening or closing the
emulator after warning.

**How to ask:** batch questions with AskUserQuestion. Keep `choices.md`, `PLAN.md` and memory
current, because sessions and API keys change.

**Division of labour:** evilgouki supplies the dump, firmware / EBOOT decrypt, playtests and
picks. Claude does reverse engineering, tools, glossary, translation, builds, QA and packaging.

Report outcomes exactly; say what was not verified.

## A11. Emulator testing (general)

- **Verify from a fresh boot, never from an old save state.** A state carries the old text in
  RAM. Gaiden's texture step wiped all story text and save-state tests hid it. Add a build gate
  that every story file survives to the final image.
- **Send input to the emulator window directly**, not as global key events (keys once
  landed in Windows Search). Send arrows as **extended keys** or they read as numpad.
- **Use the emulator's own screenshot hotkey.** Desktop/GDI capture of a Vulkan window
  returns stale or black frames (about 40 minutes lost to false "stalls").
- Wait for a reference screen before pressing; keys sent during loads and movies are lost.
  Movies screenshot black, which gives false "hang" reports.
- **Switch to a keyboard pad profile only for the test, and always restore it.**
- **Protect evilgouki's own sessions:**
  - Check `tasklist` for a running instance.
  - Snapshot the save-state directory listing at test start and move only new files (a time-based cleanup once moved the user's states).
  - Back up the emulator config first.
  - A running emulator locks the built image.

---

# Part B: PS3 engine (2nd OG / Moon Dwellers family)

Detail: `2nd Og translation\docs\` (`eboot-renderer.md`, `formats-bmd.md`, `formats-csb-wtd.md`,
`formats-fixh.md`, `rendering.md`) and the tool docstrings.

## B1. Disc layout

`PS3_GAME/USRDIR/EBOOT.BIN` (encrypted SELF) and `PSARC/`:

- `{Battle,Common,General2d,General3d,Logic}.psarc.sdat`
- plain `Movie.psarc` and `Sound.psarc`
- `PsarcList.bin` (`PSAL`)

**Setup**
- Extract the ISO to `RPCS3\dev_hdd0\disc\<SERIAL>\`; RPCS3 does not need an ISO.
- Firmware: `rpcs3.exe --installfw`. Keep RPCS3 portable in `%USERPROFILE%\RPCS3`, outside OneDrive.
- **Decrypt the EBOOT** with `rpcs3.exe --decrypt EBOOT.BIN`, which writes `EBOOT.elf` (needs the user's firmware).
- RPCS3 boots the plain ELF copied back as `EBOOT.BIN`; no fake SELF is needed.

## B2. Containers

**SDAT** (`sdat.py info|verify|decrypt|encrypt TEMPLATE IN OUT`)
- Licence-free NPDRM EDATA: `NPD\0` v4, flags `0x0100003C`, block size 0x4000.
- Per-block HMAC with a random mask. RPCS3 checks only the block HMACs; the tool also
  recomputes the CMACs and copies the ECDSA signatures from the template.
- **Encrypted builds differ every time** (random masks), so compare builds after decryption.

**PSARC v1.4** (`psarc.py list|extract|pack|check`)
- zlib blocks of 64 KB, each an independent stream at level 9 (stored raw if no gain).
- 30-byte TOC entries; entry 0 is the manifest; identical files share block runs.
- Repack is byte-identical with Python zlib.
- `pack` falls back to the template for files not in INDIR, so **extract only the files you
  patch** (the work folder went from about 25 GB to about 13 GB).

## B3. Text carriers

All of these are **big-endian, UTF-8**, NUL-terminated, with full-width punctuation.

| Format | Where | Key facts |
|---|---|---|
| **LDBI** talk scripts | `Logic/.../talk/ls*.bin` | String pool + absolute u32 offset table, both padded to 128 B (a full extra block if already aligned). 132-byte dialogue command records give speaker/text indices. Strings can change length freely. Break `@`+U+3000. |
| **LOGO** stage scripts | `Logic/.../scr*.bin` | Ten (count, offset) pairs. Fill 0xAD then `ADDEADDE`; some files have garbage fill → keep original fill if the layout is unchanged. |
| **FIXH** data tables | `Logic/Dat/FixedData/*.dat` | DOFS/DATA/SOFS/STRI. Always map id via DOFS (not id order). STRI per-line {char count in code points, byte offset}. DATA verbatim; **string count must not change**. `FIELD_MAP` (which field is which string) is per game, by hand. Developer-comment fields are never shown. |
| **BMD** battle quotes | `Battle/.../Message/NNN.bmd` (2nd OG) or `Message/@Ja/NNNN_ja.bmd` (MD) | **v0x0100** (2nd OG): 16-byte entries and lines, u16 pool offsets → pool ≤ 65,535 B. **v0x0300** (MD): 20-byte entries and lines, u32 offsets, 0xFFFFFFFF = none (voice-only lines have no text). Shared texts. Break `/`+U+3000. Many stub files. |
| **CSB** tables | Q&A, recaps, staff roll, telops, chart | **Absolute file offsets everywhere**, all regenerated. Garbage pad bytes in some files. Real `\n` breaks. |
| **WTD** windows/menus | `General2d/.../windowdataMain.wtd` etc. | Inline u32 length + string + pad; the only length-dependent field is each element's own SIZE. Part records give x/y, glyph cell w/h (per-element font size), alignment. `wtd.py geometry` → `wtd_fit.py` overflow finder. |
| **MTI** terrain | `General3d/.../landinfo.mti` | 84-byte records, char[64] `name@designer-note`; **≤ 63 bytes**. |
| **EBOOT strings** | data segment of `EBOOT.elf` | Referenced by 32-bit BE VAs / `lis+addi`. Replaced **in place**, budget = original length. Relocation not built yet (spare space after PT_LOAD[0] exists). |
| **Fonts** | `Common/Dat/Font/font.bin`, `exFont01..05.bin` | FTTF, below. |
| **Picture text** | `exFont01` sprites, `tex_06.dds`, `cosl.dds`, `SceneTitle/st_/sn_NNN.dds` | Repainted from JSON specs (B6). |

Not text: `Battle/.../Anime/Csv/*U8.csv`, `*.utd`.

## B4. Renderer and font

- **FTTF:**
  - 32×32 cells, page table at 0x54 (256 × u32 by codepoint>>8).
  - 4-byte glyph entries {0, advance, column, row}.
  - DXT5 texture in raster block order (exFont01 is ARGB8).
  - BMP-only UTF-8 decode, inlined in each routine.
- **Fixed-width trap:**
  - Byte font+0xD4 selects fixed (0, the default) or proportional (1). Fixed mode advances
    32 px and centres each glyph, so only about 30 characters fit per line.
  - **Fix (2nd OG):** rewrite 16 instruction words across 2 draw and 4 measure routines so the
    fixed mode steps `scale × entry.advance` and stops centring (`eboot_patch.py --variant advance`).
  - The `flag` variant (forcing proportional mode) also turns on the page remap, which sends
    kana to a narrow page and makes full-width Ａ render as ASCII. Rejected.
- **New build = new addresses.** Search the decrypted ELF for the original words (e.g.
  `7F692050`, `ECDB307A`, `C39F002C`, `EF8D0732`, `EFDE002A`, `EFDE302A`, `419E0084`) and for
  the FTTF magic check `lis 0x4654 / ori 0x5446`. Re-derive the sites and the TOC (r2).
- **Open risk:** a routine that positions marquee text by *character index × fixed width*.
- **Reverse-engineering tools:** capstone, plus Ghidra headless with language `PowerPC:BE:64:A2ALT-32addr`
  and r2 fixed. **Commit useful RE scripts to the repo**; 2nd OG's were lost in the scratchpad.
  Ghidra's Java can raise a Windows Firewall prompt that steals focus.

## B5. Deploy and integrity checks (`deploy.py install|rollback|status`)

- On first boot the game copies the sdat files to `dev_hdd0/game/<SERIAL>/USRDIR/PSARC`.
- **On every boot it compares SIZE + MTIME** of the disc and installed copies, not their contents.
  A mismatch shows 「ゲームデータが壊れています」 ("game data is corrupted").
- **It also checks `dev_hdd0/game/<SERIAL>/ICON0.PNG`'s mtime**, which the game stamped with
  Common.psarc.sdat's mtime in whole seconds.
- **Fast deploy:**
  1. Copy each archive to both places with one identical mtime (`os.utime` with ns).
  2. Re-stamp ICON0.PNG.
  3. The 10-minute reinstall is avoided. An EBOOT-only change needs no data copy.
- **Warn if an update EBOOT exists** in `dev_hdd0/game/<SERIAL>/USRDIR`, because RPCS3 runs it instead.

## B6. Picture text

- JSON specs per texture, rendered from pristine at build time. Per item:
  - box, en, font, style (fill / outline / glow / shadow), italic shear, squeeze
  - `inpaint` fill (OpenCV Telea)
  - content-hash keys for same-named textures
- **Every sprite stays inside its original UV box**; abbreviations are forced (ATK, SUP DEF, CTR, CMB…).
  Log each one in `choices.md`.
- Multi-sprite words (インターミッション = two sprites): put the whole word in the first sprite and
  blank the second. The game may tint white titles.
- Stage title cards (`st_NNN` 12 frames, `sn_NNN` 7 frames) are re-rendered from the StageData
  worksheet, recovering the noise masks from the originals. NNN = stage id, not record index.
- The build uses Windows fonts (Bahnschrift), so the build is Windows-only.
- Text-heavy pages (tutorial summaries): `summary_text.py` lays out word-wrapped blocks with colour markup and
  inline icons cut from the original, and keeps the screenshot areas. Opaque title bars: `exfont_text.py` with
  `inner` (refill each row from its left edge) and `align: left`.
- Sprite sheets hide single-kanji sprites the game draws as text-like labels (MD exFont01: terrain headers
  空陸海宇, movement types 空陸水地, 21 active-spirit markers). They are not strings anywhere, so a string search
  never finds them: when a screen shows kanji that no worksheet has, look in the sprite sheets. Two-letter
  abbreviations from the in-game spirit names; `shrink` keeps gaps between sprites drawn side by side.
- Typically left in Japanese: the legal notice and logos.

## B7. RPCS3 driving (`rpcs3_input.ps1`)

- **Screenshots:** send **F12** to the window whose title starts "FPS:". Shots land in
  `RPCS3\screenshots\<SERIAL>\`.
- **Input:**
  - Keyboard map: X = Cross, C = Circle, Z = Square, V = Triangle, Return = Start, Space = Select, arrows = D-pad.
  - The game confirms with **Circle**; system dialogs use Cross.
  - Use user32 `keybd_event` (SendKeys does nothing). Arrows as extended keys.
- **Focus:** RPCS3 pauses on focus loss; hold Start about 2 s to resume (on the map, that opens the overview).
- **Pad profile:** evilgouki plays with XInput (`input_configs/global/Default.yml`). For tests switch
  `active_input_configurations.yml` to the `Keyboard` profile, restart RPCS3, and **switch back after**.
- Run the script from the PowerShell tool; Bash `powershell -File` is blocked by execution policy.

## B8. Player installer (`install.py`)

1. Check for pycryptodome and pillow; offer `pip install --user`.
2. Find RPCS3, then the game via `config/games.yml`. Refuse an ISO: the game must be extracted first.
3. Verify the size and SHA-1 of the original EBOOT and sdat files, back them up to `WORK/pristine`, and check free space.
4. Run `rpcs3 --decrypt` (with a timeout) and verify the ELF hash. Decrypt the archives.
5. Run `build.py`, then `deploy.py install --disc`.
6. Warn about update EBOOTs.

- Limits: work path ≤ 80 characters; Windows only. Options: `--build-only`, `--no-verify`, `--yes`, `--uninstall`.
- Verified on 2nd OG: a from-scratch install reproduced the dev build byte-identically (after decryption).

---

# Part C: PS2 notes (OG Gaiden), kept for reference

Detail: `OG Gaiden Translation\HANDOFF-OG-Gaiden.md`, `docs/formats.md`, `docs/rendering.md`.

**Containers and text**
- ISO9660 replaced in place at the same LBA (`iso_tool.py write`), which keeps the xdelta small.
- LICE nested containers (`lice.py`). Shift-JIS little-endian text.
- MIPS VWF hook written with hand-encoded instructions, every original word asserted.
- **Pair-alignment rule:** the engine's scanners read 1 byte for `@ < > #` and 2 bytes otherwise.
  Every special character must sit at an even offset; `align_pairs` widens an ASCII character to its full-width twin to fix it.
- 1-byte ASCII storage via a hook that converts to full-width just before drawing. It halved the
  byte cost, which the backlog's 64-byte rows needed.

**Fonts and pictures**
- 4-bit 18×18 font repainted from Fira Sans (OFL).
- Spare kanji cells repurposed as icons and 2-letter spirit tiles.
- P2IG textures with CSM1 palette order and GS swizzles.

**PCSX2 testing**
- PINE (slot 28011) for live RAM read/write, `knockout`, and caller logging.
- `pcsx2_input.py` posts WM_KEYDOWN to the window; F8 screenshots.
- Swap the `[Pad1]` section only while PCSX2 is closed.

**Distribution:** xdelta against the redump ISO.

---

# Part D: problems already hit, as a checklist

| # | Problem | Prevention |
|---|---|---|
| 1 | Fixed-width Latin, about 30 characters per line | Phase 4 render test; patch draw + measure together |
| 2 | Descenders float or clip | Check g/j/p/q/y in the first screenshot |
| 3 | Missing ü/ä/é | Compose into spare cells; map in the encoder |
| 4 | Labels abbreviated ("Atk") | 2.2× / min 160 px budget for short labels |
| 5 | Menu overflow | Geometry-based room (`wtd_fit`) before the full pass |
| 6 | Five spellings of one unit | Complete glossary before the full pass |
| 7 | Keyword tags translated outside or repeated | Prompt rule + checker + `keyword_tags.py` |
| 8 | Leftover 「」 in 139 lines | Prompt rule + checker warning |
| 9 | Retries split one-line names | Checker rule |
| 10 | Wrong line-break marker in checker | Per-format break marker |
| 11 | Engine keys translated → skipped scenes, no music | `classify` keeps keys; test interludes |
| 12 | Code-cave freeze (tail call) | Full reference check + play past the first map |
| 13 | Fake code-strings translated → hang | Plausibility filter; keep suspicious |
| 14 | Missed 1-character / format / packed strings | Include them in the phase 3 inventory |
| 15 | File grew past its buffer → boot crash | Size gate in the build |
| 16 | A later build step wiped earlier output | "Text survives" gate; fresh-boot tests |
| 17 | Over-budget in-place string aborted the build | Keep the Japanese + log + shorten |
| 18 | "Game data corrupted" (mtime, ICON0) | `deploy.py` fast path |
| 19 | Stale or black screenshots | Emulator hotkey only |
| 20 | Keys went to another app or the numpad | Window-posted input, extended arrows |
| 21 | User's save states moved / pad left on keyboard | Snapshot listing; always restore the profile |
| 22 | `.gitignore` hid a needed worksheet | Negation rules; `git status --ignored` |
| 23 | Real name / home path in the public repo | Grep before commit; evilgouki only |
| 24 | MAX_PATH build failures | Short work path; installer limit |
| 25 | Overnight batch died | Dry run + one-chunk batch first |
| 26 | API key ran out mid-project | Check credit; set the cap with headroom |
| 27 | RE scripts lost in the scratchpad | Commit them under `tools/re/` |
| 28 | Builds compared encrypted (random masks) | Compare after decryption |
| 29 | Canon picks never made (50 rows, both games) | Under D2: ship the OGs form, list it in Known issues |
| 30 | A sequel bumps a format version (MD BMD 0x0300) or record layout (MD FIXH) | Round-trip every format on the new game; never assume the field maps carry over |
| 31 | The font lacks glyphs the previous game had (MD: no ä) | The font tool composes any missing umlaut; preview after generating |
| 32 | Field maps derived per game: an unreferenced FIXH string is usually dead, but some tables are read by index from code (MD ProgStrData) | `fixh_fields.py` to derive the map; read each table's orphans before keeping them; `ORPHANS_DISPLAYED` for exceptions |
| 33 | Data tables the game never loads still get translated | Check the EBOOT's file-name list; `UNUSED_TABLES` |
| 34 | A recompiled EBOOT shares no patch words with the last game | Anchor on unique operands (FTTF remap reads `lhz …,0x454`), not instruction windows; MD also had a `li r3,0` localisation stub gating proportional mode |
| 35 | The page remap narrows U+3000, which menus use to reserve icon room | Give the remap target of U+3000 the full-width advance |
| 36 | Font fixes tuned for one game's font break another (descender drop, dot colour) | Measure the ink rows and colours of the new font; outlined fonts need outlined composed glyphs |
| 38 | A pairs extractor with a fixed output path overwrote the previous game's Akurasu TSV | Tools that write glossary files take an explicit `--out`; restore from git |
| 39 | Akurasu stage titles and names have mistranslations and typos (Gaia Sabers for 護剣, バ/パ) | A near-match only on kana differences; an override file (`md_fixed.tsv`) beats every source |
| 40 | The glossary loader treated every TSV in `glossary/` as canon, in arbitrary order | One authoritative per-game names file first, then the previous canon; reference TSVs excluded |
| 41 | In-session translation with parallel subagents (no API): names not in a chunk's glossary drift between translators (Darubi/Dalubi, Shune/Shuun, 5 spellings of Fairy's surname) | A live brief with a settled-terms table, updated as reports come in; a variant-fix tool (`md_consistency.py`) after ingest; prefer the previous game's TM form |
| 42 | Parallel subagents overwrote each other's helper scripts in a shared scratch folder | A per-agent work folder rule in the brief; validate every answer file against its own request ids before ingest |
| 43 | The per-chunk checker stripped keyword tags before measuring, but their text is displayed | Measure keyword tag text (without brackets); only formatting tags draw nothing |
| 44 | Dictionary names wrapped with `\n` leaked into keyword tags in dialogue | Tag display text is one line (`" ".join(en.split())`) in the exporter, the checker and `keyword_tags.py` |
| 45 | A glossary proposal can be plain wrong (a proverb's sense, a name that contradicts the previous game) | Translators' reports are a review channel; fix through `md_fixed.tsv` plus a context rule |
| 37 | Movies and white fades screenshot as blank; Start only advances one line | Press through and re-shoot; MD skips dialogue with R1+Start (`rpcs3_input.ps1` supports chords) |
| 46 | Whole paragraphs baked into pictures (MD tutorial summaries: 15 pages) | Check whether the sheet is transparent; if so lay out wrapped English (`summary_text.py`), keeping the screenshots and cutting inline icons from the original |
| 47 | Help text and tutorial dialogue paraphrase command names (Quick Save, Split Attack) that the menu labels spell differently | The menu label wins; add the label as a `md_consistency.py` variant |
| 49 | **Crash at the first enemy phase:** the EBOOT string scanner took 5 runs of instruction bytes for one-kanji strings; their "translation" (`*`) overwrote code (illegal opcode in RPCS3) | `eboot_strings.py` marks hits inside executable sections (from the section headers; the first PT_LOAD mixes code and rodata) as keep, and `build` refuses to write inside code. After any EBOOT build, diff the code range: only the renderer patch words may differ |
| 48 | A Python patch passed through a shell heredoc turned `"\b"` into a backspace inside a regex, so the rule silently matched nothing | Patch with the Edit tool or a script file; test every new rule against a known string |

---

## Updating this file

At the end of each project (or major milestone):

1. Add new problems to Part D.
2. Move anything that turned out game-specific into that project's `docs/`.
3. Update the project table at the top.
4. Copy the file to the next project.
