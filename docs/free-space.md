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
| VTech 860801 / 860915 | ≈ 960 | ≈ 1,100 | ≈ 8,600 | 10,652 / ≈ 10,500 |
| Central Point 2.9 | 757 | 856 | 7,427 | **11,040** |
| 3.0 | 695 | ≈ 860 | ≈ 9,400 | 10,974 |
| 3.5 | 442 | ≈ 820 | ≈ 9,380 | 10,640 |
| 4.5 | 442 | ≈ 310 | ≈ 1,880 | 2,633 |
| 6.0 | ≈ 410 | ≈ 330 | ≈ 2,540 | 3,278 |
| EX/2 6.1 | 346 | ≈ 360 | ≈ 1,730 | 2,439 |

(Exact per-block figures are in `freespace-detail.txt`. The rows marked ≈ are rounded from those.)

- **The main bank is almost full in every version.** Applesoft at `$D000–$EFFF` has nothing free. The monitor
  area has scattered 17–54-byte gaps. The biggest pieces are in the slot pages (`$C787`, about 120 bytes) and at the
  top of the default `$C800` bank (`$CEC9`–`$CFAF`, about 80–310 bytes depending on version).
- **The `$C800` banks hold nearly all the room.**
  - **Up to 3.5:** about 9K is free, including three completely empty 2K blocks (chip `$6000`, `$7000` and
    `$7800`) and most of `$5000` and `$6800`.
  - **From 4.x on:** most of that is used by the diagnostics, the expansion RAM test, 3.5" drive support and
    the EX/2's setup menu and clock. About 2–2.5K remains, the largest piece a 1,120-byte run (4.x) or a
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
