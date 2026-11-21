# ROM layout, bank selection and free space

How the Laser 128's 32K system ROM appears to the CPU, how each board selects its `$C800` banks, and where there's
room for new code. The evidence for each point (BANKTEST runs, monitor dumps, disassembly) is in
`free-space-research.md`. Per-block free-space lists are in `freespace-detail.txt` (from `tools/freespace.py`).

## 1. The 32K chip (all versions)
| Chip range | CPU address | Notes |
|---|---|---|
| `$0000–$3FFF` | main bank, `$C000–$FFFF` | `$0000–$00FF` is under the I/O page and never visible. `$0800–$0FFF` is the `$C800` code reached with C3. |
| `$4000–$47FF` | alternate slot pages `$C100–$C7FF` | the real slot firmware (slot 6 boot at chip `$4600`); `$4000–$40FF` is under the I/O page |
| `$4800–$7FFF` | 2K banks switched into `$C800–$CFFF` | which ones a board can reach depends on the board (§2) |

## 2. Selecting `$C800` banks
Every board follows the same pattern:
- **Release:** reading `$CFFF` releases the window.
- **Select:** touching a slot page (`$Cnxx`) sets a latch, which is held until the next `$CFFF`.
- **C3 overrides:** touching `$C3xx` gives chip `$0800` (the main bank's own `$C800` code) until `$CFFF`.
- **INTCXROM:** with `$C007` on, all of `$C100–$CFFF` is the main bank, and slot-page reads select nothing.

### Original Laser 128 (ROM 2.7–3.0; measured on S/N 59554)
| After `$CFFF`, touch | Window shows |
|---|---|
| C1 | chip `$4800` (port configuration program) |
| C2 | `$5800` |
| C6 | `$6800` |
| **C2 and C6** (either order) | **`$7800`** |
| C3 | `$0800` |
| C4, C5, C7 | nothing (floating bus) |

C2 drives chip A12 and C6 drives A13, while A11 and A14 are always high. So **chip `$5000`, `$6000` and `$7000`
are unreachable** on this board.

### 128EX and New Laser 128 (ROM 4.x/6.0; measured on the 128EX, 6.0)
| After `$CFFF`, touch | Window shows |
|---|---|
| C1 | `$4800` |
| C2 | `$5800` |
| C5 | `$5000` |
| **C6** | **`$7800`** (the slot 6 boot helpers' bank) |
| C5 and C6 | `$7000` |
| C3 | `$0800` |
| C4 | nothing |
| C7, port 7 on INT | the 3.5" controller window, below |
| C7, port 7 on EXT | the external card's ROM |

**The slot 7 window (port 7 on INT):**
- **`$C800–$CBFF`:** 1K of the controller's buffer RAM, uninitialised at power-up.
- **`$CC00–$CFFF`:** a 1K ROM slice chosen by **`$C0ED` bits 4–6**. `$00` gives chip `$6000`, `$10` gives
  `$6400`, and so on linearly up to `$70`, which gives `$7C00`. That's eight slices covering chip `$6000–$7FFF`.
  - The 6.0 firmware uses pages `$00–$50`.
  - `$C0ED` bits 0–3 are the disk controller's mode bits. Bit 7 is set and cleared separately.
  - Write it the way the firmware does: `CMP $C0E8`, `CMP $C0ED`, `STA $C0ED`, keeping bits 0–3 and 7.

**6.0's ROM by how it's reached:**

| Chip | Reached by |
|---|---|
| `$0000–$3FFF` | main bank |
| `$4000–$47FF` | alternate slot pages |
| `$0800` | C3 |
| `$4800` | C1 |
| `$5000` | C5 |
| `$5800` | C2 |
| `$6000–$6FFF` | C7 + `$C0ED` page `$00–$30` (1K at a time at `$CC00`) |
| `$7000` | C5 + C6, or C7 + pages `$40`/`$50` |
| `$7800` | C6, or C7 + pages `$60`/`$70` |

The New Laser 128 (S/N 151202) runs 6.0 and the 6.0X boot menu without change, so it decodes the same way
(BANKTEST2 not run on it). The EX/2 (6.1) is assumed to decode the same way: its `$7800` bank is laid out like
6.0's. Not yet measured.

## 3. Free space
Runs of at least 16 `$FF` bytes, in usable bytes:

| ROM | Main bank | Alt slot pages | `$C800` banks | Total |
|---|---|---|---|---|
| VTech 860801 | 901 | 955 | 8,796 | 10,652 |
| VTech 860915 | 901 | 926 | 8,644 | 10,471 |
| 2.7 | 757 | 859 | 8,601 | 10,217 |
| 2.9 | 757 | 856 | 9,427 | 11,040 |
| 3.0 | 695 | 856 | 9,423 | 10,974 |
| 3.3 | 465 | 824 | 9,395 | 10,684 |
| 3.5 | 442 | 824 | 9,374 | 10,640 |
| 4.1 | 680 | 308 | 1,936 | 2,924 |
| 4.2 | 544 | 308 | 1,936 | 2,788 |
| 4.3 | 465 | 308 | 1,904 | 2,677 |
| 4.5 | 442 | 308 | 1,883 | 2,633 |
| 6.0 | 326 | 327 | 2,625 | 3,278 |
| 6.1 (EX/2) | 346 | 355 | 1,738 | 2,439 |

**What's actually usable:**
- **Main bank:** almost full in every version. Applesoft has nothing free. The monitor area has gaps of about
  12–54 bytes. On 3.3 and later, the gaps at `$F1AB`, `$F209` and `$F379` (23 bytes each) and `$F758`/`$F75B`
  are `$FF`, with no code referring into them. The boot menu uses them.
- **`$C800` banks, original board:** only reachable banks count. That's 2,636 bytes on 2.7, of which **chip
  `$7800` is a completely empty 2K bank** (`$CFFF`, `$C600`, `$C200`). The boot menu lives there. Chips `$6000`
  and `$7000` are also empty, but this board can't reach them.
- **`$C800` banks, 4.x/6.x:**
  - diagnostics, the expansion RAM test, 3.5" support and (on the EX/2) the clock and setup additions fill most
    of it;
  - the largest free run is the tail of chip `$7800`: `$78A0–$7CFF` (1,120 bytes) in 4.x, `$791F–$7CFF`
    (993 bytes) in 6.x. The boot menu lives there.
- **Alternate slot pages:** free bytes there are only reachable as slot firmware, so they don't count for new
  code.

## 4. Used by the boot menu
| ROM | Main bank | `$C800` bank | Spare in the bank |
|---|---|---|---|
| 2.7, 2.9, 3.0 | `$FAF5` (20), `$FEE9` (32) | chip `$7800`, copier + 1,024-byte body | about 1K |
| 4.1–4.5 | `$F1AB`, `$F209`, `$F75B` | chip `$78A0` on | 280 |
| 6.0 | `$F1AB`, `$F209`, `$F758` | chip `$791F` on | 134 |
| 6.1 | `$F1AB`, `$F209`, `$F379`, `$F758` | chip `$791F` on | 136 |

Details: `boot-menu-design.md`.
