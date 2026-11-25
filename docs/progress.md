# Progress

Where the project stands, and where it has been. Update when a status changes. Last updated **2026-11-25**.

## Status at a glance
| Area | State |
|---|---|
| Boot menu, 2.7X / 2.9X / 3.0X | **done, hardware-tested** (original Laser 128 S/N 59554) |
| Boot menu, 6.0X | **done, hardware-tested** (128EX S/N 1002869, New Laser 128 S/N 151202) |
| Boot menu, 6.1X | **done, hardware-tested** (EX/2) |
| Boot menu, 4.1X–4.5X | built, model-checked; **not yet on hardware** |
| `$C800` bank maps | original board and 128EX measured; all eight `$C0ED` slices confirmed |
| EX/2 settings and clock | settings storage and ProDOS clock hook traced in ROM; clock card partly identified |
| Undocumented features survey (4.x–6.1) | done; candidates listed in `models-and-versions.md` |

## Open items, in rough priority
1. **4.5X (or 4.2X) on the EX or New 128,** with the FloppyEmu in SmartPort Hard Disk and UniDisk 3.5 modes, via
   option 7. This tests a 4.x image and the reported 4.x SmartPort support at once.
2. **EX/2 clock card** (when the EX/2 is open):
   - photos of the underside, the 2×10 header and the motherboard around it;
   - map the header pins: battery rail to the settings RAM, data, select;
   - record the EX/2's serial number.
3. **EX/2 settings checks** (`ex2-settings-and-clock.md` §Hardware checks): read `$C8B8–$C8D0`, change one setting
   to map the fields, check retention.
4. **Quick probes:**
   - `PEEK(49248)` (`$C060` bit 7) on each machine;
   - other `$C074` values, carefully;
   - optional: sweep the unused `$C0xx` switches on the EX (low priority; the 64K is most likely shadow RAM).
5. **Ideas, not started:**
   - a driverless clock for the 128EX expansion card via a 6.0X ROM hook (Laser128EX-Expansion design notes §13);
   - a DOS 3.3 patch for booting from drive 2;
   - a modern EX/2 clock card.
6. **Not covered by the boot menu:** VTech 860801/860915 and 3.3/3.5. Possible if someone needs them.

## Where we've been
**2026-11-19: foundations and the original board**
- ROM collection, analysis tools, free-space survey, version boundaries per model.
- ROM 2.7 dumped from S/N 59554.
- BANKTEST and BANKTEST2 with a bank-marker ROM: found the original board's bank-select rule. Chip `$7800` is an
  empty, reachable 2K bank.
- Boot menu for 2.7/2.9/3.0. Hardware: the first build had ProDOS switching to drive 1, so FIXUP was added. It
  now stays on drive 2. Tested on 3.0X.

**2026-11-20: the 128EX and later ROMs**
- BANKTEST2 on the 128EX: a different select rule. Slot 7's window is buffer RAM plus a 1K ROM slice paged by
  `$C0ED` bits 4–6. All eight values confirmed.
- Boot menu 6.0X:
  - the first image never saw B (the banner routine waits for key release), so the hook moved;
  - the CoGS card read a held 7 as its own choice, so the menu now waits for release;
  - then every choice was tested on the EX and the New 128.
- 2.7X / 2.9X / 3.0X regression-tested.
- Slot 5 cards boot through an expansion box.
- DOS 3.3 from drive 2 switches to drive 1, as expected.
- Boot menu images for 4.1–4.5 and 6.1.
- EX/2: no SmartPort bus support in 6.1. BMOW's UDC article and the 1989 manual agree (UniDisk excluded on 6.x).

**2026-11-21: documentation and the EX/2**
- Docs split into design and research pairs (boot menu, free space).
- 6.1X tested on the EX/2.
- Traced in ROM:
  - the EX/2's settings storage (slot 7 buffer RAM, checksum);
  - its MSM6242 clock interface;
  - its driverless ProDOS clock hook.
- Clock card photo: OKI M6242, HCT glue, 74LS27, battery switchover; no RAM on the card.
- The 128EX's extra 64K is most likely shadow video RAM.

**2026-11-25:** added `CLAUDE.md`, `CHANGELOG.md`, `architecture.md`, `building.md` and this file, so a new
session can pick up without the old conversation.
