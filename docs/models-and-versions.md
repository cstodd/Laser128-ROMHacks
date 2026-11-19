# ROM versions and the four Laser 128 models

What the ROMs themselves show, version by version. The model names in the last column are a **working
hypothesis**. They're consistent with the evidence below but need confirming from the ROM labels in real machines
(please note the ROM version and serial number of each machine you open).

| ROM | Quad Hi-Res reset (`$C021–$C026`) | `$C074` writes | Boot devices (alt slot pages) | Diagnostics, 3.5", setup | Banner | Likely model |
|---|---|---|---|---|---|---|
| VTech 860801, 860915 | yes | – | slot 6 (Disk II) | – | none ("© 1986 Language Arts & Video Technology") | Original Laser 128, pre-production or first firmware |
| 2.7 | yes | – | slot 6 | – | "LASER 128 ROM Version 2.7"; `$FBBF` = `$FF` as in VTech's ROMs | **Original Laser 128** (S/N 59554) |
| 2.9, 3.0 | yes | – | slot 6 | – | "LASER 128 ROM Version n" | Original Laser 128 |
| 3.3, 3.5 | **removed** | 2 (power-up key handler) | slot 6 | – | same | **New Laser 128** (redesigned gate array, VT27-0706-0 video ROM) |
| 4.1, 4.2, 4.3, 4.5 | – | 11–12 (speed control) | **slots 5 and 7 gain SmartPort / block firmware**; slot 6 | expansion memory test | same | **New Laser 128 / 128EX** (accelerator, memory expansion) |
| 6.0 | – | 10 | slots 5, 6, 7 | + 3.5" drive support ("eject disk from 1st 3.5" drive") | "LASER 128 ROM Version 6.0" (1985–88) | **128EX**, later ROM (or early EX/2) |
| EX/2 6.1 | – | 11 | slots 5, 6, 7 | + Boot Slot, System Speed and Date and Time added to the port configuration program; MSM6242 clock at `$C078`; built-in MIDI port (location not yet found) | "LASER 128EX/2 ROM Version 6.1" | **128EX/2** |

2.7 sits between VTech's firmware and 2.9: it checks only the **P** and **M** power-up keys (as VTech's ROMs do),
keeps VTech's backwards "CHECK DISK, PRESS A KEY TO REBOOT" message in the `$6800` bank, and otherwise is closest
to 2.9 (about 3,300 bytes differ, mostly in the banked code).

## The boundaries the ROMs show clearly
1. **3.0 → 3.3: the original hardware ends.** The Quad Hi-Res reset code goes. That fits the new gate array
   and video ROM of the rounded-case "New" Laser 128. The `$C074` register first appears here, written from the
   power-up key handler.
2. **3.5 → 4.1: SmartPort and expansion memory.** Slots 5 and 7 get ProDOS/SmartPort firmware, the expansion
   memory test appears, and `$C074` becomes a speed control used throughout. The accelerated 128EX and its
   memory expansion need this. Whether the 4.x ROMs also shipped in later New Laser 128s, with the speed code
   doing nothing there, needs a real machine to check.
3. **4.5 → 6.0: 3.5" drive support.**
4. **6.0 → 6.1: the EX/2.** The banner names the EX/2, and it adds the battery-backed clock and extends the
   port configuration program with Boot Slot, System Speed and Date and Time.

Every version keeps the same 32K layout (`free-space.md`) and the same slot 6 Disk II boot code. Every version,
from VTech's 1986 firmware on, also has the **port configuration program** ("LASER 128 PORT CONFIGURATION":
printer, serial ports, mouse scaling; run it with `CFFF`, `C100`, `CADEG` per COMPUTIST #66). The EX/2 extends
it; it isn't new there.

## Unknowns to settle with real machines
- Which ROM versions are in your New Laser 128, 128EX and EX/2 (label and banner). The banner can be listed with
  the Applesoft loop in Laser128-QHGR's `docs/qhgr-investigation.md` ("Identifying a ROM").
- Whether `$C074` does anything on a New Laser 128.
- ~~Which slot is the expansion-RAM disk~~ **Answered:** on New Lasers it's always **slot 5**, auto-formatted by
  the firmware as `/RAM5` (found in the Laser128EX-Expansion work). Switches under the ROM door set slots 5 and 7
  each to internal or external (external routes the slot to the expansion box); internal slot 5 = the RAM disk.
  What internal slot 7 is should be in the documentation.
- Where the EX/2's built-in **MIDI port** lives (slot / I/O addresses). No "MIDI" text in 6.1; to find in the
  firmware or documentation.
