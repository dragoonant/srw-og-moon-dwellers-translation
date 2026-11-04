# Super Robot Wars OG: The Moon Dwellers: English Translation (PS3, BLJS10335)

An English translation patch for *Super Robot Taisen OG: The Moon Dwellers* (PlayStation 3, Japan, BLJS10335).
It is played in the [RPCS3](https://rpcs3.net) emulator.

The patch follows our *2nd Super Robot Wars OG* translation, so the two games read the same. Names and terms come
from the *Super Robot Wars OG: Original Generations* PS2 fan patch and our 2nd OG picks. The game's text renderer is
patched to use a proportional font, so English reads like English.

> **Status: beta.** All 77,271 translatable strings have English.
>
> **How it was translated:** with Claude (Anthropic), scene by scene, with the speaker names, the glossary, the style
> guide and each line's pixel budget. Every line was then checked automatically: control codes kept, line widths
> respected, glossary names used.
>
> **No human edit pass has been done yet.** Expect some stiff or slightly-off lines, and some Japanese left in
> pictures (see [Known issues](#known-issues)). Bug reports are welcome.

## What you need

- **Your own copy of the game**, unpacked into a folder (not an ISO file). This repo contains no game data: the
  installer builds the patch from your copy.
- **RPCS3**, with the PS3 firmware installed and the game booting in Japanese.
- **Windows 10 or 11.**
- **Python 3.10 or newer** from [python.org](https://www.python.org/downloads/). Tick **Add python.exe to PATH** in
  the Python installer.
- About **13 GB** of free disk space for the installer's work folder.

Real PS3 hardware and the PS4 version are not supported.

## Installing

1. **Download the patch.** On this page click **Code → Download ZIP**, and unzip it anywhere.
2. **Make sure the game is unpacked.** RPCS3 should list it from a folder like `RPCS3\dev_hdd0\disc\BLJS10335\`,
   with `PS3_GAME` inside. If you only have an ISO, open it with [7-Zip](https://www.7-zip.org/) and extract
   everything into that folder. 7-Zip may report a "Headers Error" on this disc; that is harmless. Then boot the game
   once in RPCS3 and let it install its data.
3. **Double-click `Install.bat`.** It finds RPCS3 and the game by itself (or asks where they are), and offers to
   install the two Python packages it needs. The first run takes about 20 minutes. When it says **Done**, start the
   game in RPCS3: it is in English.

On the game's install prompt, **Cross** confirms. In the game's own menus, **Circle** confirms.

What the installer does:

1. Checks that your files are the original Japanese release and backs them up in a work folder (`srwmd-work` in your
   user folder).
2. Decrypts the game's EBOOT with your own RPCS3 and firmware.
3. Unpacks the game archives and builds the English files.
4. Copies them into your game, with the file dates the game checks on every boot.

Your game is changed only in the last step, and the backup lets you undo it.

### Updating

Download the new version, unzip it, and double-click `Install.bat` again. It reuses the work folder.

### Uninstalling

Double-click `Uninstall.bat`. It puts every original file back from the backup. You can then delete `srwmd-work`.

### Options

```bash
python install.py --rpcs3 "D:\Emulators\RPCS3" --game "D:\Games\BLJS10335" --work "D:\srwmd-work"
```

- `--rpcs3`: the folder that holds `rpcs3.exe`
- `--game`: the folder that holds `PS3_GAME`
- `--work`: where the backup and build files go
- `--uninstall`: restore the original files

### Troubleshooting

- **"is not the original file from the Japanese release"**: another patch was applied, or the dump differs. Restore
  the original files (or dump the disc again) and run the installer again.
- **"ModuleNotFoundError: No module named 'Crypto'"** (or **'PIL'**): download the patch again. Copies from before
  this fix could not find Python packages that pip had installed for your user account only. If the error still
  comes up, open a Command Prompt with **Run as administrator**, run `py -m pip install pycryptodome pillow`, and
  then run `Install.bat` again.
- **"RPCS3 could not decrypt the EBOOT"**: install the PS3 firmware in RPCS3 (**File → Install Firmware**) and check
  that the game boots.
- **The game says its data is corrupted (「ゲームデータが壊れています」)**: run `Install.bat` again. If that does not
  help, run `python tools\deploy.py install "%USERPROFILE%\srwmd-work\build" --reinstall`, boot the game, and let it
  reinstall its data.

## Design choices

- **An independent translation.** It reuses no text from other Moon Dwellers projects. The official Bandai Namco Asia
  English release (PS4) was not used as a source. Every file format was worked out from the game; see [`docs/`](docs/).
- **Names: our 2nd OG picks and the OGs patch first**, then the Akurasu wiki, then our own proposals for the many
  characters new to OG. These include the Fury from SRW J (Touya, Calvina, Al-Van), Gadisword, Endless Frontier
  (Haken, Aschen) and the Compati Hero cast. Every name has one English form: [`glossary/md_names.tsv`](glossary/md_names.tsv).
- **Spelling and naming conventions:**
  - Short vowels and umlauts, as in OGs: Kyosuke, Ryusei, Lüne, Sänger, Rätsel. The font had no ä or ü, so we drew them.
  - "Custom" and "Type" instead of Kai and Shiki.
  - OGs Spirit Command names.
- **Dialogue style:**
  - No honorifics, except "Rishu-sensei". Ranks are written in full.
  - No quote marks on spoken lines; thoughts go in (parentheses).
  - Fury titles are rendered as Lord or Lady.
  - The full rules are in [`docs/style-guide.md`](docs/style-guide.md).
- **A proportional font.** The game draws Latin letters in fixed 32-pixel boxes. The patch makes the six FTTF text
  routines use the developers' own proportional mode: 14 instructions in the EBOOT, at the calls to a localisation
  hook that the Japanese build leaves switched off. See [`docs/eboot-renderer.md`](docs/eboot-renderer.md).
- **Fitting English into Japanese-sized boxes.** The game never wraps text. Every line is measured in pixels: 832 px
  per line for story dialogue, 800 px for battle quotes, and each menu label against its own field.

## Known issues

- **No human edit pass yet.** Some lines read stiffly. Some names new to OG are our proposals and may change.
- **Pictures:** stage title cards, battle HUD labels, map badges and the tutorial pages are repainted in English. The
  screenshots inside the tutorial pages still show the Japanese interface, and logos stay as they are. Not every
  repainted picture has been seen in game yet.
- **Not yet confirmed in game:** a few long names in the dictionary list and weapon list.
  These are listed in `translations/fit_waivers.json`.
- **Only the prologue and the start of Stage 1 have been played in RPCS3.** Routes, endings and the library are
  checked only by the tools so far.

## Reporting problems

Open an issue with a screenshot (F12 in RPCS3) and roughly where you were (the scenario number and what was
happening). For text problems, quote the line.

## For contributors

- `worksheets/` holds the translation: one JSON per game file, with the Japanese, the English and each string's budget.
  Edit `en`, then run `python tools\fitcheck.py` and `python install.py`.
- `tools/` holds the Python tools; each script explains its usage at the top.
- `KNOWLEDGE-BASE.md` collects what we learned across the OG translation projects.

## Credits

- Translation project: evilgouki, with tools and the translation by Claude (Anthropic).
- Naming follows the *OG: Original Generations* PS2 fan translation and our 2nd OG patch, checked against the Akurasu
  SRW wiki.
- *Super Robot Wars* belongs to Bandai Namco Entertainment. This is an unofficial fan project. Please buy the game.

## Licence

The installer, tools and documentation are under the [MIT licence](LICENSE). The game and its contents are not ours and
are not included.
