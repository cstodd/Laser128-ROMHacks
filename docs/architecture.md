# Architecture overview

How the hardware, the ROM and this repository fit together. Details live in the topic docs linked below.

## 1. The machines
| Model | ROM versions | `$C800` bank decoding | Notable hardware |
|---|---|---|---|
| Original Laser 128 (1986–87) | VTech 860801/860915, 2.7, 2.9, 3.0 | original rule | Quad Hi-Res (`$C023–$C027`), VT27-0430-0 video ROM; slot 7 card connector |
| New Laser 128 | 3.3, 3.5, then 4.x (and later 6.0 fits) | EX rule (assumed for 3.3/3.5) | redesigned gate array; port 5/7 INT/EXT switches; expansion RAM header (4.x+) |
| 128EX | 4.x, 6.0 | EX rule (measured) | 1 / 2.3 / 3.6 MHz (`$C074`); 64K shadow video RAM; UDC 3.5" controller |
| 128EX/2 | 6.1 | EX rule (in effect) | MSM6242 clock card at `$C078`; battery-backed settings; MIDI; port 5 switch only |

Version boundaries and model notes: `models-and-versions.md`.

## 2. The 32K system ROM (27256)
| Chip | Seen at | Contents |
|---|---|---|
| `$0000–$3FFF` | `$C000–$FFFF` main bank | monitor, Applesoft, reset code; `$0800` = C3's `$C800` code |
| `$4000–$47FF` | `$C100–$C7FF` (slot ROM) | the real slot firmware; slot 6 boot at chip `$4600` |
| `$4800–$7FFF` | `$C800–$CFFF`, 2K at a time | banks selected by touching slot pages |

**Bank selection:** reading `$CFFF` releases the window. Touching `$Cnxx` sets latches, which are held until
`$CFFF`. The rules differ by board:
- **Original board:** C1 → `$4800`, C2 → `$5800`, C6 → `$6800`, C2+C6 → `$7800`, C3 → `$0800`.
- **128EX / New 128:** C5 → `$5000`, C6 → `$7800`, C5+C6 → `$7000`. Slot 7's window is 1K of buffer RAM plus a
  1K ROM slice paged by `$C0ED` bits 4–6 (chip `$6000–$7FFF`).

Full tables and free space: `free-space.md`. Evidence: `free-space-research.md`.

## 3. The boot menu (the main deliverable)
Hold B at reset to choose: 1 internal drive, 2 external drive 2, 5 / 7 slot firmware or cards, B BASIC, M
monitor. It works like this:
1. **Key hook:** B forces a cold start.
2. **Cold-start hook:** if B is still held, select the menu's `$C800` bank.
3. **Copier:** moves the menu to RAM at `$1000`.
4. **The menu runs from RAM.** Option 2 runs a relocated copy of the ROM's own slot 6 boot page with drive 2
   selected, plus FIXUP so ProDOS stays on drive 2.

There are two patch families:
- **Original board** (`patch()`): menu in empty chip `$7800`; hooks found by byte pattern.
- **New-board ROMs** (`patch_new()` with per-ROM profiles): hooks replace `JSR keyfn` and `JSR banner` (the
  routine that waits for key release); the menu goes in the free tail of chip `$7800`.

Design: `boot-menu-design.md`. Findings and test record: `boot-menu-research.md`.

## 4. Repository layout
| Path | Role |
|---|---|
| `roms/` | stock ROM dumps (`SHA256SUMS`); `bootmenu/` released images + `CHECKSUMS.txt`; `test/` the bank-marker ROM |
| `software/asm65.py` | small 65C02 assembler: `assemble(src, org)` → `(bytes, symbols)` |
| `software/sim65.py` | 65C02 model: `Sim(code, org, keys)`, `.run(start, stop, limit)`, `.io` log; subclassed per test |
| `software/mkdisk.py`, `prodisk.py` | ProDOS image builder; bootable tool disks with ProDOS 2.4 (`software/prodos/`) |
| `software/bootmenu/` | `menu.s` (shared menu), `copier.s` (original board), `build.py` (patch, check, write images) |
| `software/banktest/`, `banktest2/` | hardware test programs for `$C800` bank selection (bootable disks in `dist/`) |
| `software/carddump/` | monitor routines to save a card's slot ROM to disk |
| `tools/` | disassembler, free-space survey, bank checksums, soft-switch and string scans |
| `docs/` | topic docs (design / research pairs), progress, building, `ref/` manuals, photos and articles |

## 5. Key facts worth remembering
- The 4.x/6.x cold start **waits for the key to be released** in its banner routine. Check keys before it.
- **ProDOS re-reads its boot unit** through the ROM's sector routine (X = `$60`). FIXUP patches `$43` / `STX $43`.
- **Some cards poll the keyboard** at start (CoGS: digits = boot choice). Start them only after the key is released.
- **6.x has no SmartPort bus support** (4.2/4.5 reportedly do, in slot 7). UniDisk 3.5 isn't supported on 6.x.
- **The port 5 firmware keeps a valid `/RAM5` across power-off.** It checks the volume directory on the card and
  doesn't rely on screen holes.
- **EX/2 settings** are 24 bytes plus a checksum at `$C8B8–$C8D0` in slot 7's buffer RAM, which is
  battery-backed on the EX/2. Its 6.1 ROM hooks ProDOS's clock vector by itself (`$BF06` → `JMP $C718`).
