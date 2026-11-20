# Free space in the Laser 128 system ROMs

Survey of the 12 system ROMs in `roms/` (Nov 2026). Free space is counted as runs of at least 16 `$FF` bytes,
which is how unused EPROM space normally reads. Full per-block lists: `freespace-detail.txt`
(from `tools/freespace.py`).

## How the 32K chip appears to the CPU
The CPU addresses were inferred from the code itself: for each 2K block, the base address at which its own
`JSR`/`JMP` targets land inside the block. The result is the same in every version:

| Chip range | CPU address | Notes |
|---|---|---|
| `$0000–$3FFF` | main bank, `$C000–$FFFF` | `$0000–$00FF` lies under the I/O page and is never visible. `$0800–$0FFF` is the `$C800` window's default bank. |
| `$4000–$47FF` | alternate `$C100–$C7FF` slot pages | `$4000–$40FF` also lies under the I/O page |
| `$4800–$7FFF` | seven 2K banks, each switched into `$C800–$CFFF` | |

COMPUTIST #66 (1989) describes selecting `$C800` banks by touching `$CFFF` and then `$C100`, `$C200`, `$C300` or
`$C600` in sequence, but it lists only four banks, at chip `$4800`, `$5800`, `$6800` and `$7800`. Later ROMs run code
from all seven blocks, so later hardware can select them all. **Whether every block can be selected on early
boards still has to be checked**, by tracing the firmware's bank-select code and by a test on hardware.

## Results (usable bytes)
| ROM | Main bank `$C000–$FFFF` | Alt slot pages | `$C800` banks | Total |
|---|---|---|---|---|
| VTech 860801 | 901 | 955 | 8,796 | **10,652** |
| VTech 860915 | 901 | 926 | 8,644 | **10,471** |
| Central Point 2.7 | 757 | 859 | 8,601 | **10,217** |
| Central Point 2.9 | 757 | 856 | 9,427 | **11,040** |
| 3.0 | 695 | 856 | 9,423 | **10,974** |
| 3.3 | 465 | 824 | 9,395 | **10,684** |
| 3.5 | 442 | 824 | 9,374 | **10,640** |
| 4.1 | 680 | 308 | 1,936 | **2,924** |
| 4.2 | 544 | 308 | 1,936 | **2,788** |
| 4.3 | 465 | 308 | 1,904 | **2,677** |
| 4.5 | 442 | 308 | 1,883 | **2,633** |
| 6.0 | 326 | 327 | 2,625 | **3,278** |
| EX/2 6.1 | 346 | 355 | 1,738 | **2,439** |

Per-block figures are in `freespace-detail.txt`.

- **The main bank is almost full in every version.** Applesoft at `$D000–$EFFF` has nothing free. The monitor
  area has scattered 17–54-byte gaps. The biggest pieces are in the slot pages (`$C787`, about 120 bytes) and at the
  top of the default `$C800` bank (`$CEC9`–`$CFAF`, about 80–310 bytes depending on version).
- **The `$C800` banks hold nearly all the room.**
  - **Up to 3.5:** about 9K is free, including three completely empty 2K blocks (chip `$6000`, `$7000` and
    `$7800`) and most of `$5000` and `$6800`.
  - **From 4.x on:** most of that is used by the diagnostics, the expansion RAM test, 3.5" drive support and
    the EX/2's additions to the configuration program and its clock. About 2–2.5K remains, the largest piece a 1,120-byte run (4.x) or a
    993-byte run (6.x) in chip `$7800`.

## What this means for a ROM 4X-style project
- **An early ROM (2.9 to 3.5) is the roomy base:** about 9K across 2K banks. A newer ROM leaves about 2.5K.
- **Code in the `$C800` banks runs 2K at a time.** Each feature needs a small stub in the main bank that
  selects a bank and jumps in, plus a way back. With only a few hundred scattered bytes free in the main bank,
  those stubs have to be compact. The existing bank-select code (for example the `C50AG` entry used for the
  expansion RAM test) shows the pattern to copy.
- **Next steps:**
  1. Trace the firmware's `$C800` bank selection, so each of the seven banks can be reached reliably.
  2. Confirm on early hardware which banks can be selected (a short monitor test).
  3. Pick a base ROM and a first feature.

## ROM 2.7
S/N 59554 has ROM **2.7**, which is not in this collection. The earliest Central Point ROM here is 2.9. A dump
of 2.7 would be worth having, both as an archival item and as the exact base for hacks on that machine. It
plugs into the same tools.

## BANKTEST on S/N 59554 (original Laser 128, ROM 2.7, stock ROM), Nov 2026
| Sequence after `$CFFF` | Sum | Reached |
|---|---|---|
| none | 07F7 | nothing (floating bus) |
| `C1` | 42E6 | chip `$4800` (port configuration program) |
| `C2` | A43A | chip `$5800` (Applesoft hi-res helpers) |
| `C3` | 6C23 | chip `$0800` (main bank's `$C800` code) |
| `C4`, `C5`, `C7` | 0793, 073F, 07F3 | nothing (floating) |
| `C6` | 8AE3 | chip `$6800` (monitor disassembler) |
| `C6` then `C1`, `C4`, `C5`, `C7` | 8AE3 | chip `$6800` (unchanged) |
| **`C6` then `C2`** | **F701 (all `$FF`)** | **an empty bank: chip `$6000`, `$7000` or `$7800`** |
| `C6` then `C3`; `C3` then `C6` | 6C23 | chip `$0800`: once `C3` is touched it stays |

So the original board reaches five banks: `$0800`, `$4800`, `$5800`, `$6800`, and one empty 2K bank via
`$CFFF`, `$C600`, `$C200`. That empty bank is enough for a boot menu. Still open: which empty block it is (the stock
ROM can't tell them apart), and whether other pairs reach more. `software/banktest2` tries every pair of slot
pages, and run with `roms/test/Laser128_2.7_bankmarkers.bin` in the machine it answers both.

## BANKTEST2 with the bank-marker ROM (S/N 59554, ROM 2.7 + markers), Nov 2026: the select rule
| First page \ then | none | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|---|---|---|
| C1 | 42E6 | 42E6 | A43A | 6C23 | 42E6 | 42E6 | 8AE3 | 42E6 |
| C2 | A43A | A43A | A43A | 6C23 | A43A | A43A | **BBEF** | A43A |
| C3 | 6C23 | 6C23 | 6C23 | 6C23 | 6C23 | 6C23 | 6C23 | 6C23 |
| C4 | float | 42E6 | A43A | 6C23 | float | float | 8AE3 | float |
| C5 | float | 42E6 | A43A | 6C23 | float | float | 8AE3 | float |
| C6 | 8AE3 | 8AE3 | **BBEF** | 6C23 | 8AE3 | 8AE3 | 8AE3 | 8AE3 |
| C7 | float | 42E6 | A43A | 6C23 | float | float | 8AE3 | float |

(42E6 = chip `$4800`, A43A = `$5800`, 6C23 = `$0800`, 8AE3 = `$6800`, BBEF = `$7800` marker; float = no ROM.)

**Rule (original board):** after `$CFFF`,
- touching `$C1xx`, `$C2xx` or `$C6xx` enables the `$C800` window;
- `$C2` sets a latch that drives **chip A12**, and `$C6` sets a latch that drives **chip A13**, both held until
  `$CFFF`. With A11 and A14 always high, the window shows chip `$4800`, `$5800` (C2), `$6800` (C6) or
  **`$7800` (C2 and C6, in either order)**;
- `$C3xx` overrides all of them with chip `$0800` (the main bank's own `$C800` code) until `$CFFF`;
- `$C4`, `$C5`, `$C7` select nothing.

**Chip `$5000`, `$6000` and `$7000` are unreachable on this board** (A11 is always high in the window); none of
their markers appeared. Later boards must decode differently, since the 4.x ROMs run code from those blocks.

**Usable free space on an original board with 2.7**, counting only reachable areas: main bank 757 bytes,
`$C800` banks 2,636 bytes, of which chip `$7800` is a **completely empty 2K bank reached with `$CFFF`,
`$C600`, `$C200`**. That's the home for the boot menu. (The alternate slot pages' free space, 859 bytes, is
reachable only as slot firmware pages and isn't counted.)

## BANKTEST2 on the owner's 128EX (ROM 6.0), Nov 2026: a different select rule
6.0 has no empty blocks, so the stock ROM identifies every bank (4C74 = `$4800`, 904F = `$5800`, 137D = `$0800`,
5CED = `$5000`, 521F = `$7000`, 4A9B = `$7800`; F701 = all `$FF`, nothing selected):

| First page \ then | none | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|---|---|---|
| C1 | `$4800` | `$4800` | `$5800` | `$0800` | `$4800` | `$5000` | `$7800` | `$4800` |
| C2 | `$5800` | `$5800` | `$5800` | `$0800` | `$5800` | `$5000` | `$7800` | `$5800` |
| C3 | `$0800` | `$0800` | `$0800` | `$0800` | `$0800` | `$0800` | `$0800` | `$0800` |
| C4 | none | `$4800` | `$5800` | `$0800` | none | `$5000` | `$7800` | none |
| C5 | `$5000` | `$5000` | `$5000` | `$0800` | `$5000` | `$5000` | `$7000` | `$5000` |
| C6 | `$7800` | `$7800` | `$7800` | `$0800` | `$7800` | `$7000` | `$7800` | `$7800` |
| C7 | none | `$4800` | `$5800` | `$0800` | none | `$5000` | `$7800` | none |

**Rule (128EX, 6.0):** after `$CFFF`, latches held until `$CFFF`:
- **C1** enables the window (chip `$4800`);
- **C2** sets chip A12 (`$5800`);
- **C5** sets A12 and clears A11 (`$5000`);
- **C6** sets A13 and A12 (**`$7800`**; on the original board C6 alone gives `$6800`);
- **C5 + C6** give `$7000`;
- **C3** overrides with `$0800`;
- **C4** and **C7** select nothing (the window reads `$FF`).

**Chip `$6000` and `$6800` were not reached**, although 6.0 has code in both. Likely candidate: `$C007` (INTCXROM).
6.0 brackets some `$C800` calls with `STA $C007` / `STA $C006` (e.g. the speed keys: `$C007`, `JSR $CE4F`,
`$C006`), and BANKTEST2 runs with INTCXROM off. A variant with `$C007` on would show.

For a 6.0 boot menu: the free 993 bytes (chip `$791F` onward) are in the `$7800` bank, reached by C6 alone. That's
also the slot 6 boot helpers' bank.

**BANKTEST2X on the 128EX (`$C007` on):** every entry was 137D (chip `$0800`). With INTCXROM on, the whole
`$C100–$CFFF` range shows the main bank's own code, and slot-page reads don't switch banks. 6.0 uses `$C007` only
to call main-bank `$C800` code; for example the speed keys call `$CE4F`, which writes `$C074` and times a frame on
`$C019` to measure CPU speed.

**Likely reason `$6000`/`$6800` were missed:** chip `$6000` holds the 3.5" drive code (it contains
"Please eject disk from 1st 3.5" drive"), so `$6000`/`$6800` are probably **slot 7's** banks. On this EX, C7 selected
nothing (all `$FF`, like an empty slot), which fits the **port 7 INT/EXT switch under the ROM door being on EXT**:
internal slot 7 switched out, in favour of the expansion box. Next: set port 7 to INT and rerun BANKTEST2.

**BANKTEST2 on the 128EX with port 7 set to INT:** the grid is the same as before except where C7 is involved.
C7 now reaches something, but no ROM block or splice of two blocks matches any of the sums:

| | alone | with C1 | with C2 | with C3 | with C5 | with C6 |
|---|---|---|---|---|---|---|
| Cx then C7 | A513 | CCAC | CD6A | 00C9 | D081 | D0F2 |
| C7 then Cx | A513 | D09D | D119 | 025B | CDF3 | D2C9 |

C7 alone, C4 with C7 and C7 twice all give A513, so the result is stable. Working theory: with C7 selected, the
window shows **non-ROM space of the internal 3.5" controller** (the "Universal Disk Controller" array), probably
RAM, with the other latches choosing which part. Unlike everywhere else, C3 doesn't override it. It also means
6.0 must reach its `$6000`/`$6800` ROM another way, still to find. Next: monitor dumps of `$C800` after
`CFFF C700`, `CFFF C100 C700` and `CFFF C700 C100`.

**Monitor dumps of `$C800–$C87F` with C7 selected (128EX, port 7 INT):** `CFFF C700`, `CFFF C100 C700` and
`CFFF C700 C100` gave nearly the same bytes, mostly 1-bits with scattered 0s, but **individual bits differ
between dumps** (e.g. `$C80C` = 6A / 6A / 7A, `$C80F` = 3F / FF / FF). So the low part of the C7 window is
unstable memory or an undriven bus, not ROM, and the C7 checksums in BANKTEST2 were noise, not bank
information. The slot 7 firmware writes here (`$C8F4–$C8F9`, `$CABC`), so it's probably the 3.5" controller's
buffer, uninitialised since power-up.

**Slot 7 firmware (6.0 alternate `$C700` page):** it calls `$CC03` (a jump table), `$CD4E`, `$CDD6`, `$CDF3`.
The best fit for the top 1K of its window is chip `$6C00–$6FFF`: a `JMP` table at `$CC03`, and at `$CD4E`
`LDA $C800,Y` / `STA $C08D,X`, a write loop from the RAM buffer to the drive. It also writes a mode register at
**`$C0ED`** (`LDA $C0E8` then `$04`; elsewhere `STZ`, `ORA #$08`, save/restore). Code in chip `$6000`'s lower half
runs at `$C98B`, so `$C0ED` probably also switches the low part of the window to ROM: that's likely how
`$6000`/`$6800` are reached. Next: dump `CFFF C700 CC00.CC0F` (expect `4C C2 CD 4C 17 CD …` if it's chip
`$6C00`), then a probe that writes `$C0ED` values.

**`CFFF C700 CC00.CC0F` on the 128EX:** `4C 03 CC A9 07 20 DC C7 10 07 A9 2F 38 60 4C D3`. That's chip
**`$6000`**, an exact match. Chip `$6000` starts with `JMP $CC03`, which only makes sense at
`$CC00`. So the **slot 7 window is 1K of buffer RAM at `$C800–$CBFF` plus a 1K ROM slice at `$CC00–$CFFF`**,
here chip `$6000–$63FF`.

Theory: **bits `$04`/`$08` of `$C0ED`** (which the 3.5" firmware sets) page the other slices (chip `$6400`,
`$6800`, `$6C00`) into the same 1K, giving the 3.5" firmware 4K (chip `$6000–$6FFF`) behind slot 7. To test from
the monitor: `C0E8 C0ED:04 CFFF C700 CC00.CC07` (then 08, 0C; restore with `C0E8 C0ED:00`). Expected at `$CC00`:
`$04` → AE D4 CB BD…, `$08` → 4C 6C CF 4C…, `$0C` → 4C C2 CD 4C….

**Correction: `$C0ED` bits 0–3 are the disk controller's mode bits; bits 4–6 page the ROM slice.** Monitor tests
writing `$04`/`$08`/`$0C` to `$C0ED` left `$CC00` showing chip `$6000`. The 6.0 slot 7 page explains why:
- `$C76F` builds the new value as `($CACC AND #$8F) OR page`, with `page = bits 4–6` (the callers use
  `AND #$70`);
- `$C7B5` writes it as `CMP $C0E8` (motor off), `CMP $C0ED`, `STA $C0ED`, keeps a copy in RAM at `$CACC`, then
  writes `$CAD0` to `$C0EC` and turns the motor back on if it was on;
- elsewhere, `ORA #$08` sets mode bit 3 (fast 3.5" timing on an IWM-style controller), and `$C799` sets or clears
  bit 7.

So bits 4–5 (perhaps 6) should select the 1K slice at `$CC00`: `$00` → chip `$6000`, `$10` → `$6400`, `$20` →
`$6800`, `$30` → `$6C00`. The dispatcher at `$C739` takes a command byte, pages in the slice named by its upper
bits, and jumps through a table at `$CCxx`. Monitor test: `C0EE C0EC C0E8`, `C0ED`, `C0ED:10`,
`CFFF C700 CC00.CC07` (one per line).

**Confirmed on the 128EX (6.0):** after `C0EE C0EC C0E8`, `C0ED`, `C0ED:10`, then `CFFF C700 CC00.CC07` reads
`AE D4 CB BD FB C8 C9 02`, which is **chip `$6400`**. `$C0ED` bits 4–6 page the 1K ROM slice behind slot 7. (`$20`,
`$30` and bit 6 still to check.)

**Confirmed: `$20` → chip `$6800`, `$30` → chip `$6C00`.** On the 128EX (6.0), with port 7 set to INT, slot 7's `$C800`
window is:
- `$C800–$CBFF`: 1K buffer RAM (uninitialised, contents drift at power-up);
- `$CC00–$CFFF`: one 1K ROM slice chosen by `$C0ED` bits 4–5: `$00` → `$6000`, `$10` → `$6400`, `$20` → `$6800`,
  `$30` → `$6C00`, and **`$40` → `$7000`** (confirmed, Nov 2026, EX S/N 1002869: `4C 40 CD 4C 5D CF 4C 34`). So
  bits 4–6 together select one of eight 1K slices of chip `$6000–$7FFF`. That second 4K is also reachable as the C5+C6 and C6 banks.
  - **`$50`, `$60`, `$70`: all `FF` at `$CC00` on hardware** (Nov 2026), but port 7 was probably set to **EXT**
    for these reads, which hides the internal firmware. Redo with port 7 on INT.
  - **`$50` with port 7 on INT: chip `$7400` confirmed** (`4C A2 CE 4C 2D CD 4C 39`), so the conflict is gone. `$60` and `$70` fit: the firmware never
    asks for those pages.
  - **`$50` doesn't fit.** The firmware's dispatcher (`$C739`: page = command `LSR` `AND #$70`) is called with
    commands `$A0–$A3`, page `$50`, from five places, in the `$6800`, `$6C00` and `$7000` slices. Chip `$7400`
    starts with a matching jump table (`4C A2 CE 4C 2D CD 4C 39 …`). To re-check on hardware. Pages the
    firmware uses: `$00` (3 calls), `$10` (1), `$20` (5), `$30` (3), `$40` (5), `$50` (5).

Write `$C0ED` like the firmware does: `CMP $C0E8`, `CMP $C0ED`, `STA $C0ED`, keeping bits 0–3 (controller mode) and
bit 7. That accounts for all of 6.0's ROM:

| Chip | Reached by |
|---|---|
| `$0000–$3FFF` | main bank |
| `$4000–$47FF` | alternate slot pages |
| `$4800` | C1 |
| `$5000` | C5 |
| `$5800` | C2 |
| `$6000–$6FFF` | **C7 + `$C0ED` page**, 1K at `$CC00` (bit 6 also reaches `$7000` up) |
| `$7000` | C5 + C6 |
| `$7800` | C6 |
| `$0800` | C3 |
