# Boot menu for the Laser 128 (ROM 2.7, 2.9, 3.0) and 128EX (ROM 6.0)

**Hold B while powering on, or while pressing Ctrl-Reset, and keep holding it until the menu appears:**
```
        LASER 128 BOOT MENU
        ROM 3.0X

      1  INTERNAL DRIVE
      2  EXTERNAL DRIVE (DRIVE 2)
      B  APPLESOFT BASIC
      M  MONITOR
      5  SLOT 5 CARD            (only shown if a card answers in slot 5)
      7  SLOT 7 CARD            (only shown if a card answers in slot 7)

   HOLD B DURING RESET FOR THIS MENU
```
Without B the machine starts exactly as before; the existing **P** (port configuration) and **M** (monitor) reset
keys still work.

The banner shown at cold start reads **"LASER 128 ROM Version 2.7X"** (2.9X; 3.0X keeps 3.0's spacing), to mark the
modified firmware.

Images (27256 / 27C256): `roms/bootmenu/Laser128_2.7_bootmenu.bin`, `…_2.9_…`, `…_3.0_…`. Checksums in
`roms/bootmenu/CHECKSUMS.txt`. **Original board only:** the menu lives in a `$C800` bank selected the way the
original board decodes it (`docs/free-space.md`).

## ROM 6.0 (Laser 128EX)
`roms/bootmenu/Laser128_6.0_bootmenu.bin`. **For 6.0 only** (the EX decodes the `$C800` banks differently). Same
use: hold B at power-on or Ctrl-Reset. The menu has the same choices, plus:
```
      5  SLOT 5 (RAM DISK OR CARD)   (only if slot 5's firmware answers)
      7  SLOT 7 (3.5 INCH OR CARD)   (only if slot 7's firmware answers)
```
The EX's own reset keys (P/0 control panel, M/Return monitor, 1/2/3 speed, space) are unchanged. Banner: "LASER
128 ROM Version 6.0X".
- **Hooks:** `$F9BB JSR $FA17` (after the reset-key table search) → KEYB at `$F758`: B clears `$03F3/$03F4` for a
  cold start. `$F9DA JMP $FEE0` (start of the autostart scan) → BOOTSEL at `$F1AB`: if B is still held, the stub
  at `$F209` reads `$CFFF`, `$C600` (chip `$7800` on the EX) and jumps to the copier at `$C91F`; otherwise `JMP $FEE0`.
- **Bank:** chip `$7800` holds 6.0's slot 6 helpers up to `$791E`. The copier and body use the free tail. The body
  is the drive-2 boot page (run at `$1000`) and `menu.s` (at `$1100`).
- **5 and 7** start the way 6.0's autostart does: `$00/$01 = $Cn00`, `JMP ($0000)`, after the same signature test.
  With a port switch on INT the slot is the built-in RAM disk / 3.5" firmware; on EXT it's whatever card is
  there. A card such as a hard-disk controller appears and boots if its ROM has the standard boot signature
  (`$Cn01=$20`, `$Cn03=$00`, `$Cn05=$03`). The menu can't read the switches, hence the generic labels.

## How it works (2.7, 2.9, 3.0)
- **Banner:** 3.0's trailing space becomes `X`; 2.7 and 2.9 close up `128  ROM` to `128 ROM` to make room.
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
  (monitor). 5 and 7 → shown only when the slot's ROM has the boot signature (`$Cn01=$20`, `$Cn03=$00`,
  `$Cn05=$03`), started like the ROM's own slot 7 start (`$00/$01 = $Cn00`, `JMP ($0000)`). Slot 5 is for a card
  on the expansion connector (e.g. a hard-disk controller); the original ROMs' own startup only checks slot 7.
- **External drive (all versions):** the menu runs a RAM copy of the ROM's own slot 6 boot page at `$1200`
  (page-aligned, so branch timing matches the ROM) with:
  - `$C0EA → $C0EB` (drive 2);
  - the window release `$CFFF → $C600` (keep the slot 6 helper bank selected);
  - its own-page references relocated;
  - its final `JMP $0801` sent to **FIXUP**.

  The boot code's `$C800` helpers return to whatever page called them, so they work from the copy.
- **FIXUP and ProDOS:** a ProDOS boot block saves X as the boot unit (`STX $43`) on each of its two entries; the
  second comes from the ROM's sector routine, always with X = `$60` (drive 1). That's why ProDOS switched back to
  the internal drive after loading started. When sector 0 is a ProDOS boot block (`38 B0 03 …` with `86 43` at
  `$0807`), FIXUP sets `$43 = $E0` (slot 6, drive 2) and turns the `STX $43` into NOPs. ProDOS then loads and runs
  from drive 2. Other boot sectors are left alone and get X = `$60` as usual.
- **DOS 3.3** from drive 2: its first stage loads from drive 2, but DOS's own disk code then uses drive 1.
  Fixing that would need a DOS-specific patch.
- 2.7 also has an unused drive-2 entry in its own boot code (`$C60D`; also in VTech's 860801/860915). The menu
  doesn't need it any more. On 2.7, a read error during a drive-2 boot makes the ROM retry from its normal boot
  path, which uses drive 1.

## What to test (with a FloppyEmu or a second drive on the external port)
1. Normal power-on and Ctrl-Reset without B: unchanged behaviour (boots / BASIC prompt).
2. P and M at reset still work.
3. B at power-on and B at Ctrl-Reset: menu appears.
4. 1, B, M, and 5 / 7 with and without a card (e.g. a hard-disk controller).
5. **2 with different disks**:
   - **ProDOS** (8 1.x or 2.x) should now boot and stay on drive 2: check that `PREFIX` and `CAT` show the
     external disk.
   - Single-load disks that read through the boot ROM should run from drive 2.
   - DOS 3.3 is expected to switch to drive 1 after its first stage.

## Build
`python3 build.py` builds all four images (6.0 with its own patch and checks, which cover the same ground plus 5
and 7 with and without their firmware). It patches each original-board ROM by byte pattern, checks that only the two hooks, the two gaps and the menu
bank changed, and runs the 65C02 model:
- the reset key logic for P, M, B and other keys;
- the end-of-cold-start hook with and without B held, including the bank-select reads;
- the copier and the menu screen;
- every choice, down to the final jump;
- the drive-2 path: the 2.7 entry state, and for 2.9/3.0 the RAM copy, byte for byte.

It can't model the real Laser hardware, so the burn-and-boot test above is still needed.
