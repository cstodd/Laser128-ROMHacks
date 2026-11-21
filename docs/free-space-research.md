# ROM layout and bank selection: research notes

The evidence behind `free-space.md`. Each finding comes with how it was established. Raw results and dead ends
follow.

Machines: original Laser 128 **S/N 59554** (ROM 2.7) and 128EX **S/N 1002869** (ROM 6.0). Tools:
- `software/banktest` and `software/banktest2`: checksum the `$C800` window after each sequence of slot-page
  reads;
- BANKTEST2X: the same with `$C007` on;
- `roms/test/Laser128_2.7_bankmarkers.bin`: 2.7 with a distinct marker in every 2K block, so empty blocks can be
  told apart.

## Findings
### 1. Where the chip's blocks appear
- **Finding:** chip `$0000–$3FFF` is the main bank, `$4000–$47FF` the alternate slot pages, and `$4800–$7FFF`
  the `$C800` banks. This holds in every version.
- **How we know:** for each 2K block, the base address that makes its own `JSR`/`JMP` targets land inside the
  block (`tools/c800banks.py`). It was later confirmed by BANKTEST: the sums match the chip blocks.

### 2. The original board's select rule: C2 → A12, C6 → A13, C3 overrides
- **Finding:** see the table in `free-space.md` §2. The empty bank at chip `$7800` is reached with `$CFFF`,
  `$C600`, `$C200`. Chips `$5000`, `$6000` and `$7000` can't be reached.
- **How we know:**
  - **BANKTEST, stock 2.7:** C6 then C2 gave an all-`$FF` sum, F701. That's an empty bank, but the stock ROM
    can't say which.
  - **BANKTEST2 with the marker ROM:** every pair of slot pages, below. Only the `$7800` marker (BBEF) appeared,
    for C2 + C6 in either order. No `$5000`/`$6000`/`$7000` marker ever appeared, which means chip A11 is always
    high in the window.
  - **On hardware:** the boot menu runs from that bank on 2.7, 2.9 and 3.0.
- **Background:** COMPUTIST #66 (1989) describes selecting banks by touching `$CFFF`, then `$C100`, `$C200`,
  `$C300` or `$C600`. It lists four banks (chip `$4800`, `$5800`, `$6800`, `$7800`), which fits this rule.

### 3. The 128EX's select rule differs: C5 → `$5000`, C6 → `$7800`
- **Finding:** see `free-space.md` §2.
- **How we know:** BANKTEST2 on the 128EX. 6.0 has no empty blocks, so the stock ROM identifies every bank by
  checksum (grid below).
- **Consequence:** the original-board boot menu images can't run on the EX. The 6.x images use C6 alone.

### 4. `$C007` (INTCXROM) maps the whole `$C100–$CFFF` to the main bank
- **Finding:** with `$C007` on, every sequence reads chip `$0800`. 6.0 uses `$C007` only to call main-bank
  `$C800` code. For example, the speed keys call `$CE4F`, which writes `$C074` and times a frame on `$C019`.
- **How we know:** BANKTEST2X on the 128EX: every entry 137D (chip `$0800`), with port 7 on INT and on EXT.

### 5. Slot 7's window (port 7 INT) is 1K of buffer RAM plus a 1K ROM slice paged by `$C0ED` bits 4–6
- **Finding:** `$C800–$CBFF` is RAM. `$CC00–$CFFF` shows chip `$6000 + page × $40` (×256 bytes), where
  `page = ($C0ED >> 4) AND 7`. All eight values from `$00` to `$70` were confirmed, linear.
- **How we know:**
  1. **BANKTEST2 with port 7 on INT:** C7 gave sums that match no ROM block. Monitor dumps of `$C800` showed
     bits changing between dumps, which is RAM or an undriven bus, not ROM. The slot 7 firmware writes there
     (`$C8F4–$C8F9`, `$CABC`).
  2. **`CFFF C700 CC00.CC0F`:** gave `4C 03 CC A9 07 20 DC C7 …`, an exact match for chip `$6000`. That chip
     starts with `JMP $CC03`, which only makes sense at `$CC00`.
  3. **Disassembly of 6.0's slot 7 page:**
     - `$C76F` builds `($CACC AND #$8F) OR page`;
     - `$C7B5` writes it with `CMP $C0E8` / `CMP $C0ED` / `STA $C0ED`, and keeps a copy at `$CACC`;
     - the dispatcher at `$C739` takes `page = (command LSR) AND #$70`.
  4. **Monitor writes to `$C0ED`,** port 7 on INT:

     | `$C0ED` | `$CC00` shows |
     |---|---|
     | `$00` | chip `$6000` |
     | `$10` | `$6400` (`AE D4 CB BD`) |
     | `$20` | `$6800` |
     | `$30` | `$6C00` |
     | `$40` | `$7000` (`4C 40 CD 4C`) |
     | `$50` | `$7400` (`4C A2 CE 4C`) |
     | `$60` | `$7800` (`A9 00 85 3C`) |
     | `$70` | `$7C00` (the 6.0X boot menu's text) |

  5. **Pages the firmware calls**, counting the dispatcher's call sites:

     | Page | Calls |
     |---|---|
     | `$00` | 3 |
     | `$10` | 1 |
     | `$20` | 5 |
     | `$30` | 3 |
     | `$40` | 5 |
     | `$50` | 5 |

     `$60`/`$70` are never called.
- **Consequence:** chip `$6000–$6FFF` (the 3.5" drive code, including "Please eject disk from 1st 3.5" drive")
  is reached only this way. That explains why BANKTEST2 never saw it.

### 6. Free space and safe gaps
- **Finding:** `free-space.md` §3.
- **How we know:**
  - **Free space:** `tools/freespace.py` (runs of at least 16 `$FF` bytes).
  - **Gaps:** each gap the boot menu uses was scanned for absolute and indexed references within ±8 bytes. The
    only hits are a false positive (`STZ $F210,X` at chip `$287F`, which sits mid-instruction in `ROL $9E / BPL`)
    and `JSR $F220`, just past the 6.x stub.
  - **The 4.x and 6.x `$7800` free tails:** checked for code that refers into them (none).

## Raw results
### BANKTEST, original board, stock 2.7
| Sequence after `$CFFF` | Sum | Reached |
|---|---|---|
| none | 07F7 | nothing (floating) |
| C1 | 42E6 | chip `$4800` |
| C2 | A43A | `$5800` |
| C3 | 6C23 | `$0800` |
| C4, C5, C7 | 0793, 073F, 07F3 | nothing |
| C6 | 8AE3 | `$6800` |
| C6 then C1, C4, C5, C7 | 8AE3 | `$6800` |
| C6 then C2 | F701 (all `$FF`) | an empty bank |
| C6 then C3; C3 then C6 | 6C23 | `$0800` |

### BANKTEST2, original board, 2.7 with bank markers
42E6 = `$4800`, A43A = `$5800`, 6C23 = `$0800`, 8AE3 = `$6800`, BBEF = `$7800` marker.

| First \ then | none | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|---|---|---|
| C1 | 42E6 | 42E6 | A43A | 6C23 | 42E6 | 42E6 | 8AE3 | 42E6 |
| C2 | A43A | A43A | A43A | 6C23 | A43A | A43A | **BBEF** | A43A |
| C3 | 6C23 | 6C23 | 6C23 | 6C23 | 6C23 | 6C23 | 6C23 | 6C23 |
| C4 | float | 42E6 | A43A | 6C23 | float | float | 8AE3 | float |
| C5 | float | 42E6 | A43A | 6C23 | float | float | 8AE3 | float |
| C6 | 8AE3 | 8AE3 | **BBEF** | 6C23 | 8AE3 | 8AE3 | 8AE3 | 8AE3 |
| C7 | float | 42E6 | A43A | 6C23 | float | float | 8AE3 | float |

### BANKTEST2, 128EX, 6.0 (port 7 on EXT)
| First \ then | none | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|---|---|---|
| C1 | `$4800` | `$4800` | `$5800` | `$0800` | `$4800` | `$5000` | `$7800` | `$4800` |
| C2 | `$5800` | `$5800` | `$5800` | `$0800` | `$5800` | `$5000` | `$7800` | `$5800` |
| C3 | `$0800` | `$0800` | `$0800` | `$0800` | `$0800` | `$0800` | `$0800` | `$0800` |
| C4 | none | `$4800` | `$5800` | `$0800` | none | `$5000` | `$7800` | none |
| C5 | `$5000` | `$5000` | `$5000` | `$0800` | `$5000` | `$5000` | `$7000` | `$5000` |
| C6 | `$7800` | `$7800` | `$7800` | `$0800` | `$7800` | `$7000` | `$7800` | `$7800` |
| C7 | none | `$4800` | `$5800` | `$0800` | none | `$5000` | `$7800` | none |

With port 7 on INT, the C7 entries changed to sums matching no ROM (A513 alone, and others with C1/C2/C5/C6).
They turned out to be the drifting buffer RAM (finding 5), so they don't describe banks.

## Dead ends (kept so they aren't repeated)
- **"`$C0ED` bits 2–3 page the ROM slice":** wrong. Writing `$04`/`$08`/`$0C` left `$CC00` at chip `$6000`.
  Bits 0–3 are controller mode bits, and the page is bits 4–6.
- **"C7's BANKTEST2 sums are bank information":** they were RAM noise.
- **"`$50`–`$70` read `FF`":** the reads were taken with port 7 on EXT, which switches the internal firmware
  out. Repeated on INT, they read as expected.
- **Monitor procedure:** on the Apple monitor, values after `addr:` on the same line are *stored*. Give each
  read its own line. To reset the controller before a `$C0ED` write: `C0EE`, `C0EC`, `C0E8`.
