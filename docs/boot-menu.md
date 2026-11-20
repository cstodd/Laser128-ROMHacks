# Boot menu: design notes

**Status (Nov 2026): built for ROM 2.7, 2.9 and 3.0 (`software/bootmenu/README.md`), and tested on real hardware
with 3.0 on S/N 59554 (original Laser 128):**
- **Menu:** B at reset brings up the menu; normal startup, and the P and M reset keys, are unchanged.
- **External drive with ProDOS:** first build: ProDOS started from the FloppyEmu on the external port, then
  switched to the internal drive as predicted. With the FIXUP version: **boots and stays on drive 2.**
- **Banner:** "3.0X" banner version tested.
- **Quad Hi-Res:** still works with the new ROM (DHGRTEST2).
- **Not yet tried on hardware:** the 2.7 and 2.9 images, option 7 with a card, and DOS 3.3 from drive 2 (expected
  to switch to drive 1).

**Goal:** choose the boot device at power-up or reset, especially the **external** 5.25" port, so a FloppyEmu or
second drive can boot without opening the machine.

## How the Laser boots today (all versions)
- The slot 6 boot ROM lives in the **alternate** slot pages (chip `$4600` = `$C600`). It builds its
  denibblizing table with helpers at `$C800`, then switches the drive on with absolute, slot-6-only addresses:
  ```
  C624  ORA $C0EE   ; read mode
  C627  ORA $C0EC
  C62A  ORA $C0EA   ; select drive 1   <- drive 2 would be $C0EB
  C62D  ORA $C0E9   ; motor on
  ```
  It then seeks track 0, reads sector 0 to `$0800` and jumps to `$0801` with X = `$60`, as on an Apple II.
- 2.x and 3.x have no other boot firmware (slots 5 and 7 are empty). 4.x and later have SmartPort/block
  firmware in slots 5 and 7, so **`PR#5`/`PR#7` can already boot a SmartPort device on those ROMs**; a menu
  just makes it reachable at power-up.
- At power-up, holding a key selects special actions. In 2.7 (and VTech's ROMs) the code at `$F9B0` selects the
  `$C100` bank, reads the key, masks it with `AND #$1F` (so Ctrl and plain letters both work) and checks two keys:
  - **P** → `JMP $CB06`: the **port configuration program** (in the `$C800` bank at chip `$4800`).
  - **M** (= Return) → wait for release, `JMP $FF69`: **the monitor** (COMPUTIST #66's "NMI").
  - otherwise → normal cold start, which ends in `JMP $C600` (boot slot 6).
  From 3.3 the check becomes a table (P, M, Q, R, S, @) with a jump table. A boot-menu key (for example **B**)
  belongs here: in 2.7 it needs one more compare-and-branch, which means moving a few bytes into a free gap
  (the nearest is 20 bytes at `$FAF5`).

## The existing configuration program
Every ROM has the port configuration program (in the `$C800` bank at chip `$4800`), and the EX/2 adds a Boot Slot
item to it. That's the natural place for a boot option, but the bank is nearly full (33 free bytes in 2.9, about 200
in 6.1). The likely approach: keep the menu itself in an empty bank, and add only a short hook (a key or menu line)
to the configuration program. The EX/2's Boot Slot code in 6.1 is worth reading first, as a model.

## Planned menu
```
  LASER 128 BOOT
  1  Internal 5.25" drive        (slot 6, drive 1)
  2  External 5.25" drive        (slot 6, drive 2)
  5  Slot 5 device               (4.x and later)
  7  Slot 7 device               (4.x and later)
  B  Applesoft BASIC
  M  Monitor
```
- **Entry:** a key held at power-up or reset, for example `B`, through the existing key table. Later possibly
  instead of "Unable to find a bootable disk".
- **Code:** in an empty `$C800` bank. On early boards that's chip `$7800` (2K free) if BANKTEST shows it is
  reachable. The main bank needs only a short stub (select bank, jump in) in one of its small free gaps.
- **External drive boot:** a copy of the slot 6 boot routine with `$C0EB` in place of `$C0EA`.

## The external-drive catch
Selecting drive 2 for the boot itself is easy, but **what happens after the boot sector loads depends on the
software**:
- Loaders that keep reading through the boot ROM's sector routine (`$C65C`), as many single-load games do, stay
  on drive 2 and work.
- DOS 3.3 and ProDOS take over with their own disk drivers and expect the boot device to be drive 1, so they
  may switch back to the internal drive after the first stage.

So the honest first version is "boot drive 2, works for what it works for", to be tested with a FloppyEmu. A
fuller fix would make the boot code tell the OS it came from drive 2, or swap the drives in hardware (the
second custom chip, IC2, drives `ENBL1`/`ENBL2` for the internal and external drives). For SmartPort/3.5" images
on 4.x+ machines there's no such problem: they boot through slot 5/7 firmware.

## Steps
1. ~~Find a home~~ **Done:** on the original board, chip `$7800` is an empty 2K bank, selected by `$CFFF`, then
   `$C600`, then `$C200` (`free-space.md`). Code there runs at `$C800–$CFFF`. Anything that touches `$C3xx`
   (the 80-column firmware, e.g. COUT once `PR#3` is active) or `$CFFF` switches it out. So the menu either
   copies itself to RAM and runs there, or avoids those routines.
2. Map the 2.7 ROM: find the power-up key table, its handlers and free gaps in the main bank.
3. Build the menu in the free bank, with the drive-2 boot variant, and test in the 65C02 model.
4. Produce a patched 27256 image, try it in an EPROM, and test boots from both drives with a FloppyEmu.

## Later: New Laser 128 / 128EX (4.x, 6.x)
Started Nov 2026 (survey of 3.3–6.1). Next: the ROM version in the owner's New Laser 128, and BANKTEST2 on it.
- **3.3 / 3.5:** same three empty `$C800` banks as the original-board ROMs (chip `$6000`, `$7000`, `$7800`).
  But the two gaps the original-board menu used (`$FAF5`, `$FEE9`) are taken, and the cold start has no
  `LDA $C701` slot 7 test. The power-up key check is table-driven (P, M, Q, R, S, @). The free main-bank gaps
  are ~22–23 bytes each (`$F1AB`, `$F209`, `$F379`, `$FF09`).
- **4.x:** no empty banks. The largest free run is 1,120 bytes in the `$7800` bank (993 in 6.x).
- These ROMs already have SmartPort/block firmware in **slots 5 and 7**. **Slot 5 is the expansion-RAM disk**,
  auto-formatted by the firmware as `/RAM5`. New Lasers have switches under the ROM door, one each for slots 5
  and 7, setting internal or external (external routes the slot to the expansion box). A menu here would add
  **5** and **7** choices: start the firmware, as the ROM's own slot 7 start does; no boot-code changes needed.
- Room: the main bank has about 440 bytes in small gaps. The biggest free `$C800` area is about 1.1K (4.x) or
  993 bytes (6.x), at chip `$7800`. The current menu is 768 bytes including the 256-byte drive-2 boot copy.
- First step: run BANKTEST2 on a New 128 / EX. The 4.x ROMs run code from chip `$5000`, `$6000` and `$7000`,
  which the original board can't reach, so these boards decode the `$C800` banks differently.
- **6.0 reset keys** (table at `$F9FD`, after `AND #$1F`, jump table at `$FAF5`):
  - **P/0** → `$C1D9` (control panel);
  - **M/Return** → `$F8A4` (monitor);
  - **1/Q, 2/R, 3/S** → the speed keys: speed codes `$56`, `$96` and `$D6`, set through `$CE4F` in a `$C800`
    bank, then the normal reset continues. The likely order is 1 MHz, 2.3 MHz and 3.6 MHz (not yet traced);
  - **Space/@** → the same code as 2.

  A boot-menu key (B = `$02`) would be a seventh entry. The table is inline at `$F9FD`, so adding one means
  moving the table or adding a compare in a free gap.

### Plan for ROM 6.0 (128EX), Nov 2026
- **Key hook:** `$F9BB JSR $FA17` (taken when no table key matched; A = key AND `$1F`) → `JSR KEYB`. KEYB (13 bytes):
  if A = `$02` (B), `STZ $03F3`, `STZ $03F4` to force the cold path, then `JMP $FA17`.
- **Cold-start hook:** `$F9DA JMP $FEE0` → `JMP BOOTSEL`. `$FEE0` is the autostart scan: slots 7, 6, 5 by
  signature (`$Cn01=$20`, `$Cn03=$00`, `$Cn05=$03`), then `JMP $CF4A` ("Unable to find a bootable disk").
  BOOTSEL: if B is still held, select the menu bank and enter; otherwise `JMP $FEE0`.
- **Menu bank:** chip `$7800` (C6 alone on the EX), free from chip `$791F` (993 bytes, `$C91F–$CCFF`). Stub:
  `LDA $CFFF`, `LDA $C600`, `JMP` into it. The menu copies itself to RAM as on the original board.
- **Gaps:** `$F1AB`, `$F209`, `$F379` (23 bytes each) and `$F758` (17 bytes). Check them for references first,
  as was done for the original-board gaps.
- **Choices:**
  - **1** internal 5.25" (slot 6);
  - **2** external 5.25" (RAM copy of the slot 6 boot page with drive 2, plus the ProDOS FIXUP);
  - **5** `/RAM5` (slot 5);
  - **7** 3.5" (slot 7);
  - **B** BASIC, **M** monitor.

  Show 5 and 7 only when their signatures answer; they start through `JMP $Cn00`, as the autostart does.
- **Build:** extend `software/bootmenu/build.py` with a 6.0 profile (different hooks and bank select), and check
  in the model as for 2.7, 2.9 and 3.0.
