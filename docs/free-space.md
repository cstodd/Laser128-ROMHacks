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
