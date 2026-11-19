# Boot menu for the original Laser 128 (ROM 2.7, 2.9, 3.0)

**Hold B while powering on, or while pressing Ctrl-Reset, and keep holding it until the menu appears:**
```
        LASER 128 BOOT MENU
        ROM 2.7 + BOOT MENU

      1  INTERNAL DRIVE
      2  EXTERNAL DRIVE (DRIVE 2)
      7  SLOT 7 CARD            (only if a card answers in slot 7)
      B  APPLESOFT BASIC
      M  MONITOR

   HOLD B DURING RESET FOR THIS MENU
```
Without B the machine starts exactly as before; the existing **P** (port configuration) and **M** (monitor) reset
keys still work.

Images (27256 / 27C256): `roms/bootmenu/Laser128_2.7_bootmenu.bin`, `…_2.9_…`, `…_3.0_…`. Checksums in
`roms/bootmenu/CHECKSUMS.txt`. **Original board only:** the menu lives in a `$C800` bank selected the way the
original board decodes it (`docs/free-space.md`).

## How it works
- **Reset key check** (`$F9C0`; `$F9C3` in 3.0): the `CMP #$10 / BEQ` for P becomes `JMP $FAF5`. The 20 bytes
  there handle P as before, and for **B** clear `$03F3`/`$03F4` so the reset takes the full cold-start path
  (also after Ctrl-Reset), then continue with the M check.
- **End of cold start** (`$F9F4`; `$F9F7` in 3.0): the slot 7 card test's `LDA $C701` becomes `JMP $FEE9`. If B
  is still held (`$C010` bit 7 and the last key = B), the stub reads `$CFFF`, `$C600`, `$C200` to select chip
  `$7800` and jumps to `$C800`; otherwise it does the `LDA $C701` and carries on. So every choice starts from a
  fully initialised machine.
- **Chip `$7800`** (empty in all three ROMs): a copier at `$C800` moves the menu (`menu.s`) to `$1000–$15FF` and
  runs it from RAM. The menu writes to the text screen and reads the keyboard directly, so nothing depends on
  which `$C800` bank is selected.
- **Choices:** 1 → `JMP $C600`. B and M call INIT, SETVID and SETKBD, then `$E000` (Applesoft) / `$FF69`
  (monitor). 7 → the ROM's own slot 7 start (`$00/$01 = $C700`, `JMP $C700`).
- **External drive:**
  - **2.7** has an unused drive-2 entry in its own boot code (`$C60D`: `ORA $C0EB`, skipped by a `BRA` from the
    normal path; also in VTech's 860801/860915 firmware). The menu uses it.
  - **2.9 / 3.0** rewrote the boot code without it, so the menu runs a RAM copy of the slot 6 boot page at
    `$1200` (page-aligned, so branch timing matches the ROM) with `$C0EA → $C0EB` (drive 2), the window release
    `$CFFF → $C600` (keep the slot 6 helper bank selected) and its three `JSR $C683` relocated.

## What to test (with a FloppyEmu or a second drive on the external port)
1. Normal power-on and Ctrl-Reset without B: unchanged behaviour (boots / BASIC prompt).
2. P and M at reset still work.
3. B at power-on and B at Ctrl-Reset: menu appears.
4. 1, B, M, and 7 with/without a slot 7 card.
5. **2 with different disks**:
   - Loaders that read through the boot ROM's sector routine (many single-load games) should run from drive 2.
   - **DOS 3.3 and ProDOS** use their own drivers after the first stage and may switch to **drive 1**. Note what
     each does; that tells us whether a fuller fix is worth it.

## Build
`python3 build.py` patches each ROM by byte pattern, checks that only the two hooks, the two gaps and the menu
bank changed, and runs the 65C02 model:
- the reset key logic for P, M, B and other keys;
- the end-of-cold-start hook with and without B held, including the bank-select reads;
- the copier and the menu screen;
- every choice, down to the final jump;
- the drive-2 path: the 2.7 entry state, and for 2.9/3.0 the RAM copy, byte for byte.

It can't model the real Laser hardware, so the burn-and-boot test above is still needed.
