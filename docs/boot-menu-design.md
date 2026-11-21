# Boot menu: design

A replacement system ROM (27256) that adds a **boot menu** to the Laser 128 family. Hold **B** at power-on or
Ctrl-Reset, let go, and choose where to boot. It's mainly for booting the **external 5.25" drive** (a
FloppyEmu or a second drive), which the stock firmware can't boot from, and for any card in slot 5 or 7.
Without B the machine starts exactly as before.

How the design was arrived at, and the evidence behind each decision, is in `boot-menu-research.md`. Build and
usage details are in `software/bootmenu/README.md`.

## Supported ROMs and status
| ROM | Machine | Image (`roms/bootmenu/`) | CRC32 | Hardware status |
|---|---|---|---|---|
| 2.7 | original Laser 128 | `Laser128_2.7_bootmenu.bin` | `9866b5bc` | **tested**, S/N 59554 |
| 2.9 | original Laser 128 | `Laser128_2.9_bootmenu.bin` | `1d5b5452` | **tested**, S/N 59554 |
| 3.0 | original Laser 128 | `Laser128_3.0_bootmenu.bin` | `b7842da4` | **tested**, S/N 59554 |
| 4.1, 4.2, 4.3, 4.5 | New Laser 128 / early 128EX | `Laser128_4.x_bootmenu.bin` | see `CHECKSUMS.txt` | model only |
| 6.0 | 128EX, New Laser 128 | `Laser128_6.0_bootmenu.bin` | `4fb06d29` | **tested**, 128EX S/N 1002869 and New Laser 128 S/N 151202 |
| 6.1 | 128EX/2 | `Laser128_6.1_bootmenu.bin` | `2ebc06db` | **tested**, owner's EX/2 |

Not covered: VTech's 1986 ROMs (860801, 860915) and 3.3/3.5. The cold-start banner gains an **X** ("…Version
3.0X") to mark the modified firmware.

## What the user sees
```
        LASER 128 BOOT MENU
        ROM 6.0X

      1  INTERNAL DRIVE
      2  EXTERNAL DRIVE (DRIVE 2)
      B  APPLESOFT BASIC
      M  MONITOR
      5  SLOT 5 (RAM DISK OR CARD)      shown only if slot 5's ROM has the boot signature
      7  SLOT 7 (3.5 INCH OR CARD)      shown only if slot 7's ROM has the boot signature

   HOLD B DURING RESET FOR THIS MENU
```
| Key | Action |
|---|---|
| 1 | normal slot 6 boot (internal drive) |
| 2 | slot 6 boot from **drive 2** (external port); a ProDOS disk stays on drive 2 |
| 5, 7 | start that slot's firmware, as the ROM's own autostart does (`$00/$01 = $Cn00`, `JMP ($0000)`) |
| B | Applesoft (after INIT, SETVID, SETKBD) |
| M | monitor (`$FF69`) |

Slot labels by ROM:
- **2.7–3.0:** "5  SLOT 5 CARD", "7  SLOT 7 CARD";
- **4.x:** "5  SLOT 5 (RAM DISK OR CARD)", "7  SLOT 7";
- **6.0:** as in the screen above;
- **6.1:** "5  SLOT 5 (RAM DISK OR CARD)", "7  SLOT 7 (3.5 INCH DRIVE)".

The firmware can't read the INT/EXT switches, so the labels cover both cases.

The machine's own reset keys are unchanged on every ROM:
- **2.7–3.0:** P (port configuration), M (monitor);
- **4.x, 6.x:** P/0 (control panel), M/Return (monitor), 1/2/3 (speed), space.

## Architecture (all ROMs)
1. **Key hook.** In the reset-key check, B (`$02` after `AND #$1F`) clears the power-up bytes `$03F3/$03F4`.
   That forces the full cold-start path, also after Ctrl-Reset.
2. **Cold-start hook.** Near the end of the cold start, if B is still held, select the menu's `$C800` bank
   and jump to the copier. Otherwise carry on exactly as the stock ROM does. So every menu choice starts from a
   fully initialised machine.
3. **Copier.** It runs in the `$C800` window, copies the menu body to RAM at `$1000`, and jumps to it. The
   menu then never depends on which `$C800` bank is selected, and choices can freely touch slot ROMs.
4. **Menu body** (`software/bootmenu/menu.s`, one source for all ROMs). It writes text page 1 directly and
   reads the keyboard directly, with no firmware I/O until a choice is made.
   - **It waits for B to be released** before reading a choice.
   - **5 and 7:** it offers them only if `$Cn01=$20`, `$Cn03=$00`, `$Cn05=$03`. When one is chosen, it waits
     for that key to be released before starting the card. (Some cards poll the keyboard as they start and
     take a held digit as their own command.)
5. **Drive-2 boot.** The body includes a **RAM copy of the ROM's own slot 6 boot page**, page-aligned so its
   timing matches the ROM. It's relocated by `build.py`'s `boot_copy()`:
   - `$C0EA` → `$C0EB` (drive 2);
   - the `$CFFF` window release → `$C600` (keep the slot 6 helper bank selected);
   - own-page references → the copy;
   - the final `JMP $0801` → **FIXUP**.
6. **FIXUP.** If sector 0 is a ProDOS boot block (`38 B0 03 …` with `STX $43` at `$0807`), it sets `$43 =
   $E0` (slot 6, drive 2) and turns the `STX $43` into `NOP`s. ProDOS then loads and stays on drive 2. Any
   other boot sector is left alone.

## Per-ROM implementation
### Original board (2.7, 2.9, 3.0): `patch()` in `build.py`
Patch sites are located by byte pattern.

| Item | Where | Notes |
|---|---|---|
| Key hook | key check `CMP #$10 / BEQ` (`$F9C0`; `$F9C3` in 3.0) → `JMP KEYX` | KEYX (20 bytes) at `$FAF5`: P as before, B as above, then the M check |
| Cold-start hook | slot 7 card test `LDA $C701` (`$F9F4`; `$F9F7`) → `JMP BOOTSEL` | BOOTSEL (32 bytes) at `$FEE9`: with B, reads `$CFFF`, `$C600`, `$C200` and jumps to `$C800`; otherwise does the `LDA $C701` and continues |
| Menu bank | chip `$7800`, empty in all three ROMs | copier at `$C800`, body at `$C900–$CEFF` (1,024 bytes; drive-2 page at `$1300`) |
| Banner | "LASER 128  ROM Version 2.7" → "LASER 128 ROM Version 2.7X" | 3.0 keeps its spacing and uses its trailing space |

On this board `$CFFF`, `$C600`, `$C200` selects chip `$7800` (`free-space.md`).

### New-board ROMs (4.1–4.5, 6.0, 6.1): `patch_new()` with per-ROM profiles (`NEW` in `build.py`)
These ROMs share one reset-code shape:
- a key-table search, then `JSR keyfn`;
- the cold start's `JSR banner`, a routine that prints the banner and **waits for the key to be released**.

The hooks replace those two `JSR`s. The build reads the original targets from the ROM.

| Item | 4.1 / 4.2 / 4.3 / 4.5 | 6.0 | 6.1 |
|---|---|---|---|
| Key hook | `$F9BB JSR keyfn` → KEYB | `$F9BB JSR $FA17` → KEYB | `$F9C1 JSR $FA28` → KEYB |
| keyfn | `$FA07` / `$FA29` / `$FA29` / `$FA29` | `$FA17` | `$FA28` |
| Cold hook | `$F9CE JSR banner` → BOOTSEL | `$F9CE JSR $CE7C` → BOOTSEL | `$F9D1 JSR $CEB5` → BOOTSEL |
| banner | `$CE35` / `$CE7A` / `$CE7C` / `$CE7C` | `$CE7C` | `$CEB5` |
| KEYB (13 bytes) | `$F75B` | `$F758` | `$F758` |
| BOOTSEL (20) / stub | `$F1AB` / `$F209` | same | same; plus INIT7 (15) at `$F379` |
| Menu bank space | chip `$78A0–$7CFF` | chip `$791F–$7CFF` | chip `$791F–$7CFF` |
| Spare bytes | 280 | 134 | 136 |

- **BOOTSEL** tests for B *before* the banner routine's release wait. With B, the stub:
  1. calls the banner routine itself;
  2. drops BOOTSEL's return address;
  3. does the cold start's next step (`STA $C006`);
  4. on 6.1 only, calls INIT7, which repeats the cold start's 3.5" controller init (`BIT $CFFF`, `BIT $C700`,
     `STZ $CABC`, `$C71A` with X=3, Y=`$14`);
  5. reads `$CFFF`, `$C600` (chip `$7800`, the slot 6 helper bank, on these boards) and jumps to the copier.

  Without B, it tail-calls the banner routine and the stock cold start continues.
- **Menu bank:** the free tail of chip `$7800`, after the ROM's own slot 6 helpers. The copier comes first,
  then the body: the drive-2 page (runs at `$1000`), then `menu.s` (at `$1100`).
- **Banner:** the "X" fits in the existing length ("LASER 128 ROM Version 6.0X", "LASER 128EX/2 ROM Version
  6.1X").

## Verification
`python3 software/bootmenu/build.py` builds all nine images. For each one it:
- checks that only the intended bytes changed;
- runs the 65C02 model (`software/sim65.py`) through:
  - the reset keys;
  - the cold-start hook, with and without B (on new-board ROMs the banner routine releases the key, as the real
    one does);
  - the copier and menu screen, with and without slot 5/7 firmware;
  - every choice down to its final jump;
  - the release wait before a card starts;
  - the drive-2 page byte for byte, and FIXUP on ProDOS and non-ProDOS boot sectors.

Hardware testing then covers what the model can't.

## Limitations
- **DOS 3.3 from drive 2:** its first stage loads from drive 2, then DOS's own disk code switches to drive 1.
  Fixing that needs a patch to DOS, not the ROM. Seen on both the original board and the 128EX.
- **SmartPort devices:** 6.0 and 6.1 have no SmartPort bus support (`models-and-versions.md`), so options 5 and
  7 boot only what the firmware supports: the RAM disk, plain 3.5" drives, and cards. 4.2/4.5 reportedly
  support a directly connected SmartPort device in slot 7 (untested here).
- **Which slot is external:**
  - original Laser 128: slot 7;
  - 128EX without the expansion box: slot 7 (port 7 on EXT);
  - 128EX through the expansion box: slot 5 as well (port 5 on EXT);
  - EX/2: slot 5.
- **EX/2 slots:**
  - **Slot 5:** port 5 INT gives `/RAM5`, EXT gives the expansion card, so the menu never offers both in one
    session.
  - **Slot 7:** there's no port 7 switch, so slot 7 is always the internal 3.5" firmware. It drives a 3.5"
    drive on the drive port.
