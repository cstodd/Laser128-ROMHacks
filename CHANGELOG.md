# Changelog

Newest first. Add an entry at least every couple of hours of work, and at the end of each session (see `CLAUDE.md`).
Hardware results name the machine and the image CRC32.

## 2026-11-25
- Added session-handoff docs: `CLAUDE.md` (start-here and rules), `docs/architecture.md`, `docs/building.md`,
  `docs/progress.md` and this changelog.
- Checked that all three builds (boot menu, BANKTEST, BANKTEST2) reproduce the committed outputs byte for byte.

## 2026-11-21
- **Docs restructured:**
  - `boot-menu.md` split into `boot-menu-design.md` (definitive) and `boot-menu-research.md` (findings with
    evidence, test record);
  - `free-space.md` rewritten as the definitive layout and bank-select reference, with the evidence in
    `free-space-research.md`.
- **Hardware:** 6.1X (`2ebc06db`) passed on the owner's EX/2. All choices work. Slot 5 is `/RAM5` or the card,
  never both; slot 7 is always the internal 3.5" firmware.
- **EX/2, traced in ROM 6.1:**
  - settings are 24 bytes plus a checksum at `$C8B8–$C8D0` in slot 7's buffer RAM;
  - the clock is MSM6242-style at `$C078`;
  - the firmware hooks ProDOS's clock vector (`$BF06` → `JMP $C718`), so no driver file is needed.

  New doc: `ex2-settings-and-clock.md`.
- **EX/2 clock card**, from the owner's photo: OKI M6242, 74HCT10, 74HCT74 ×2, CD74HCT04, HD74LS27, battery
  switchover, no RAM. So the settings RAM is on the motherboard.
- **Survey** of possible undocumented features in 4.x–6.1, with probe candidates. The 128EX's extra 64K is
  recorded as most likely shadow video RAM, not user-accessible, with the reason: interleaved RAM would need
  about 7.2 MHz cycles.

## 2026-11-20
- **Boot menu, new boards:**
  - **6.0X:** the first image (`1aec2386`) checked B after the banner's key-release wait, so it never saw it. The
    fix hooks `$F9CE`.
  - **CoGS:** the card read a held 7 as its own choice, so the menu now waits for 5/7 to be released.
  - **Current 6.0X (`4fb06d29`):** tested on the 128EX (S/N 1002869) and the New Laser 128 (S/N 151202).
  - **New images** for 4.1–4.5 and 6.1, from one generalized `patch_new()` with per-ROM profiles.
- **Boot menu, original board:**
  - a slot 5 option, and generic slot labels;
  - 2.7X (`9866b5bc`), 2.9X (`1d5b5452`) and 3.0X (`b7842da4`) regression-tested on S/N 59554;
  - slot 5 boots a card through an expansion box replica;
  - DOS 3.3 from drive 2 switches to drive 1, on both boards (needs a DOS patch).
- **128EX bank map:**
  - BANKTEST2 and BANKTEST2X results;
  - slot 7's window is 1K buffer RAM plus a 1K ROM slice paged by `$C0ED` bits 4–6;
  - all eight values were confirmed with port 7 on INT. Earlier `$50`–`$70` reads were on EXT.
- **EX/2:**
  - no SmartPort bus devices in slot 5 or 7 (STATUS calls);
  - BMOW's UDC article archived, with its findings (SmartPort in 4.2/4.5, not 6.x);
  - the 1989 manual excludes the UniDisk 3.5;
  - reset keys are the same as 6.0.
- **CARDDUMP** monitor routines (kept, made generic). The CoGS investigation notes and ROM dump were later
  dropped.
- **Recorded:** the New Laser 128 (S/N 151202, owner-installed 6.0, port switches, RAM header) and the 128EX's
  S/N.

## 2026-11-19
- Started the repo: ROM collection (VTech 860801/860915, 2.9–6.1), disassembler, free-space survey, version
  boundaries per model.
- Added ROM 2.7 dumped from S/N 59554.
- BANKTEST and BANKTEST2 (bootable ProDOS 2.4 disks via `prodisk.py`), and a bank-marker test ROM. Result: the
  original board's select rule, with chip `$7800` reachable by `$CFFF`, `$C600`, `$C200`.
- **Boot menu for 2.7/2.9/3.0:** B at reset; external drive boot with a relocated slot 6 boot page; FIXUP keeps
  ProDOS on drive 2. Tested on 3.0X (S/N 59554), and Quad Hi-Res still works.
- Added the 1989 User's Guide, Laser's 1988 EX/2 ad, and notes on models, ports, switches, MIDI and the EX's
  video RAM.
