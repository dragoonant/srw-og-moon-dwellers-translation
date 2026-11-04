# Changelog

## v0.1 (beta, unreleased)

- All 77,271 translatable strings in English: story, battle quotes, data tables, menus, EBOOT messages, terrain names.
- Proportional font: a 14-word EBOOT patch at the localisation-hook calls; ä and ü drawn into the font; full-width
  spaces keep their width.
- Name glossary: 1,451 names with one English form each (`glossary/md_names.tsv`).
- Installer that builds from your own dump (`Install.bat` / `install.py`), with an uninstaller.
- Picture text in English: stage title cards, battle HUD labels, map badges, backlog and combine sprites, tutorial
  banners and the 15 tutorial summary pages.
- Help text and tutorial dialogue use the menu's command names (Suspend Save, Single Attack, Focused Attack, Separate).
- Fixed a crash when the first enemy phase began: the EBOOT patch no longer writes inside game code.
- Consistency: 解散 is Disband, ド根性 is Guts, Support Defense, a space before skill levels (Counter Lv8), startle
  marks written "...!", Alistair Lynx; voice-actor names romanised.
- Installer: fixed "No module named 'Crypto'" when pip installed pycryptodome/pillow per user (the tools ran with
  `python -I`, which skips the user site-packages).
- Known gaps: the screenshots inside the tutorial summary pages still show the Japanese interface; no human edit pass yet.
