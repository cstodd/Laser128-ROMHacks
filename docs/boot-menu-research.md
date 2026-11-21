# Boot menu: research notes

The findings behind the boot menu (`boot-menu-design.md`), each with how it was established. Findings come
first; the test record and history follow. "Model" means the 65C02 model in `software/sim65.py`. "Hardware"
means the owner's machines:
- original Laser 128 **S/N 59554** (ROM 2.7, also run with 2.9 and 3.0);
- 128EX **S/N 1002869** (6.0);
- New Laser 128 **S/N 151202** (6.0, owner-installed);
- 128EX/2 (6.1).

## Findings
### 1. The stock firmware boots slot 6 drive 1 only, and the drive is fixed in the boot code
- **Finding:** the slot 6 boot ROM is the **alternate** slot page (chip `$4600`, seen at `$C600`). It selects
  drive 1 with an absolute `$C0EA`, reads sector 0 to `$0800`, and jumps to `$0801` with X = `$60`. Booting
  drive 2 needs a copy of that page with `$C0EB`.
- **How we know:** disassembly of every ROM's `$C600` page. The relevant sequence:
  ```
  C624  ORA $C0EE   ; read mode
  C627  ORA $C0EC
  C62A  ORA $C0EA   ; select drive 1   <- drive 2 would be $C0EB
  C62D  ORA $C0E9   ; motor on
  ```
  `boot_copy()` relocates the page from every supported ROM, and its asserts require exactly one `$C0EA` and
  one `JMP $0801`.
- **Side note:** 2.7 (and VTech's 860801/860915) also have an unused drive-2 entry at `$C60D`. It isn't needed
  now.

### 2. A copy of the boot page works from RAM, if the slot 6 helper bank stays selected
- **Finding:** the boot page calls helpers in the `$C800` bank selected by `$C600`. Those helpers return to the
  calling page, so they work from a RAM copy, provided the copy doesn't release the window. That's why its
  `$CFFF` becomes `$C600`. The copy has to be page-aligned to keep the ROM's branch timing.
- **How we know:** disassembly, the model (the copy reaches its relocated `JMP`), and hardware. Option 2 boots
  from the FloppyEmu on 3.0X, 2.7X, 2.9X and 6.0X.

### 3. ProDOS re-reads its boot unit, so the ROM must change what it sees
- **Finding:** a ProDOS boot block saves X as the boot unit (`STX $43` at `$0807`) on each of its two entries.
  The second entry comes through the ROM's sector routine, always with X = `$60` (drive 1). So ProDOS loaded
  from drive 2 switches to drive 1. FIXUP sets `$43 = $E0` and `NOP`s the `STX $43` before entering `$0801`.
- **How we know:**
  - The first 3.0X build (no FIXUP): ProDOS started from the FloppyEmu, then switched to the internal drive,
    as predicted from the boot block.
  - With FIXUP it boots and stays on drive 2, on every ROM tested. The model checks FIXUP on a ProDOS boot
    sector and on a DOS 3.3 one.
- **Limit:** DOS 3.3 has the same problem inside DOS, beyond the ROM's reach. Its first stage loads from drive
  2, then it switches to drive 1, on both the original board and the 128EX.

### 4. Where the code can live
- **Finding:** the main bank has only small gaps (13–23 bytes). The menu needs about 0.8–1K, so it lives in a
  `$C800` bank, is copied to RAM, and runs there.
  - **Original board:** chip `$7800` is an empty 2K bank, selected by `$CFFF`, `$C600`, `$C200`.
  - **New-board ROMs:** chip `$7800` is the slot 6 helper bank (selected by `$C600` alone), with a free tail:
    1,120 bytes in 4.x, 993 in 6.x.
- **How we know:** the free-space survey (`tools/freespace.py`, `free-space.md`), plus **BANKTEST2 on
  hardware**. That's what showed the original board and the 128EX decode the `$C800` banks differently
  (`free-space.md` has both maps).
- **Checking the gaps:** they were scanned for code that refers into them. The only hits are:
  - `STZ $F210,X` at chip `$287F`: a false positive, the bytes sit mid-instruction in a `ROL $9E / BPL`
    sequence;
  - `JSR $F220`: just past the stub.

### 5. The reset-key code has a usable hook point on every ROM
- **Finding:** all supported ROMs read the key at reset, `AND #$1F`, and compare it against their own keys,
  and none of them uses B (`$02`).
  - **2.7–3.0:** inline compares for P and M. The hook replaces the P compare with a jump to KEYX.
  - **4.x/6.x:** a table: P, M, and in 4.2+ Q/R/S/`$00` for the speed keys. A miss falls through to
    `JSR keyfn`, which becomes `JSR KEYB`.
- **How we know:** disassembly (6.0 table at `$F9FD` with jump table `$FAF5`; 6.1 at `$FDAC`/`$FAF5`; 4.x at
  `$FA05`), and hardware: all stock reset keys still work on every tested image.

### 6. On 4.x/6.x the cold start waits for the key to be released, so B must be checked earlier
- **Finding:** the new-board banner routine (`$CE7C` in 6.0) ends with `LDA $C010 / BMI` (wait for release).
  Any check after it never sees B held. BOOTSEL therefore replaces the `JSR` to the banner routine and checks
  first.
- **How we know:** the first 6.0X hooked the later `$F9DA JMP $FEE0`. On the EX, holding B only paused the
  banner, then the internal drive booted. Disassembly found the wait at `$CEA4`. The fixed image works on
  hardware. The model now has the banner routine release the key, which fails the old design.

### 7. 6.1's cold start initialises the 3.5" controller before choosing a slot
- **Finding:** after the banner, 6.1 runs `BIT $CFFF`, `BIT $C700`, `STZ $CABC`, `$C71A` (X=3, Y=`$14`), then
  picks the boot slot from the control panel setting. The menu path does the same init (INIT7) before entering
  the menu, so option 7 starts from the stock state.
- **How we know:** disassembly of 6.1's `$F9D1–$F9F8` and `$C71A`. Not yet confirmed on hardware.

### 8. Cards can see a held key, so the menu waits for 5/7 to be released
- **Finding:** some cards poll the keyboard as they start. A CoGS card takes C/M as "open my menu" and a digit
  1–8 as its own boot choice. Started from the menu with 7 still held, it booted "device 7" and fell back
  immediately.
- **How we know:**
  - **Disassembly of the card's boot ROM:** the poll at `$CF58`, about 1 s; digits stored at `$51`.
  - **Hardware:** before the fix, 7 from the menu gave no pause and no boot, while `PR#7` worked. After the
    fix, 7 boots the card's mounted drive.
  - **Tapping vs holding:** the card responds to a fresh keypress (tap C), not a held key.

### 9. The menu shows slots by signature, which covers internal firmware and cards alike
- **Finding:** 5 and 7 appear when `$Cn01/$Cn03/$Cn05` = `$20/$00/$03`. That's the same test 6.x's autostart
  uses (`$FEE0`), and the original board's slot 7 card test. The INT/EXT switches decide what answers.
- **How we know:** hardware.
  - **Original board:** 7 appears only with a card in the slot.
  - **128EX:**
    - 5 INT shows `/RAM5`;
    - 5 EXT with no expansion box reads `FF` at `$C500–$C507`, and 5 is hidden;
    - through an a2heaven expansion box replica, a card in "Slot 5" shows and boots as 5.
  - **EX/2:** the expansion slot is slot 5 (it has only a port 5 switch).

### 10. Stock autostart behaviour that the menu leaves alone
- **2.7–3.0:** the cold start boots a slot 7 card if present, else slot 6.
- **4.x:** slot 7, else slot 6.
- **6.0:** scans slots 7, 6, 5 by signature, else "Unable to find a bootable disk". `$FABA` is `JMP $FEE0`, so
  a card that hands on to "the next slot" continues the scan.
- **6.1:** boots from the control panel's Boot Slot, then lower slots.

**How we know:** disassembly, and hardware. A CoGS card boots by itself, without the menu, on the original
board, the 128EX and the New 128 once it has a drive mounted. An earlier report that the EX didn't was a test
with nothing mounted.

## Hardware test record
| Image | Machine | Result |
|---|---|---|
| 3.0X, first build (no FIXUP) | S/N 59554 | menu, 1, B, M; option 2 + ProDOS switched to drive 1 → FIXUP added |
| 3.0X with FIXUP (`fc99de78`) | S/N 59554 | 2 boots ProDOS from the FloppyEmu and stays on drive 2; stacked mode still works |
| 6.0X first (`1aec2386`) | 128EX | no menu: B checked after the release wait (finding 6) |
| 6.0X `5627f1a7` | 128EX | menu, reset keys, 1, 2 OK; 7 with the CoGS failed (finding 8) |
| **6.0X `4fb06d29`** | 128EX S/N 1002869 | all choices: 1, 2, 5 (`/RAM5`, and a card via the box), 7 (CoGS), B, M; reset keys; DOS 3.3 → drive 1 |
| **6.0X `4fb06d29`** | New Laser 128 S/N 151202 | same as the 128EX (no speed keys: no accelerator) |
| **3.0X `b7842da4`, 2.9X `1d5b5452`, 2.7X `9866b5bc`** | S/N 59554 | B/P/M at reset; 1, 2 (ProDOS stays on drive 2), 7 (CoGS, and tap C for its menu), B, M; stacked mode; DOS 3.3 → drive 1 |
| 4.1X–4.5X, 6.1X | — | not yet tested |

## Open items
- **6.1X on the EX/2:** the full test list, including 7 with the FloppyEmu in 3.5" mode and 2 in 5.25" mode.
- **4.5X (or 4.2X) on the EX or New 128,** with the FloppyEmu in SmartPort Hard Disk and UniDisk 3.5 modes, via
  option 7. This tests the 4.x image and the reported 4.x SmartPort support at the same time.
