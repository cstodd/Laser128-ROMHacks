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
| 6.0 | – | 10 | slots 5, 6, 7 | + 3.5" drive support ("eject disk from 1st 3.5" drive") | "LASER 128 ROM Version 6.0" (1985–88) | **128EX**: confirmed in the owner's 128EX, S/N 1002869 (Nov 2026) |
| EX/2 6.1 | – | 11 | slots 5, 6, 7 | + Boot Slot, System Speed and Date and Time added to the port configuration program; MSM6242 clock at `$C078`; MIDI through the Port 2 serial connector | "LASER 128EX/2 ROM Version 6.1" | **128EX/2** |

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

## From the 1989 User's Guide (Laser 128, 128EX, 128EX/2)
Source: `docs/ref/Laser 128 128EX 128EX2 User's Guide & BASIC Manual (1989).pdf` (VTech).

**Models**
- **Laser 128:** 65C02 at 1 MHz, 128K RAM, up to 1 MB expansion RAM with an optional Memory Expansion Card.
- **128EX:** adds a CPU clock selectable between **1, 2.3 and 3.6 MHz**, an extra **64K of video RAM**, 3.5" drive
  support, and the Memory Expansion Card already fitted (add RAM chips). Speed is set by **holding 1, 2 or 3
  during power-up**.
  The extra 64K of video RAM is for the accelerator. Laser's own 1988 EX/2 ad ("Inside Story",
  `docs/ref/Laser 128EX2 Inside Story ad (1988).jpg`) says: "64K Video RAM. Controlled by our own Video Display
  Generator (VDG) array, this feature off-loads video work from the 128K system RAM, providing both analog and
  digital (IBM®-type RGB) outputs." So the video has its own copy of display memory, freeing main RAM for the CPU
  at 2.3/3.6 MHz. EX teardowns agree it's shadow RAM, most likely not user-accessible (see "Worth probing" below).
- **The same ad** names the other custom arrays:
  - a "Memory Management Unit (MMU) array" controlling the 1 MB RAM board (256K × 1 DRAMs);
  - a "Universal Disk Controller (UDC) array" for 3.5" and 5.25" drives, with the EX/2 supporting IIGS-style
    "Daisy Chain" drives;
  - the EX/2's MIDI port and real-time clock;
  - and it calls the ROM "the only legal Apple compatible ROM on the market".
- **128EX/2:** adds a battery-backed **time and date clock**, **MIDI**, and an optional internal 3.5" (800K) drive.

**Ports (Table 6-1)**

| Port | Device |
|---|---|
| 0 | 40-column display |
| 1 | parallel or serial printer |
| 2 | serial communications |
| 3 | 80-column display |
| 4 | mouse |
| 5 | 1M expansion RAM interface |
| 6 | 5.25" disk drives |
| 7 | 3.5" disk drives |

**Switches under the ROM door:** INT/EXT for port 5 and for port 7. INT selects the built-in interface (port 5 =
expansion memory, port 7 = 3.5" drive interface); EXT selects a card in the optional expansion box (one card).

**Control panel:** hold **P** at power-on, or with Ctrl-Reset. On all models: printer, serial port and mouse
settings.
- The **EX/2** adds:
  - **Boot Slot:** 7 (3.5" drives, the default), 6 (5.25" drives, internal or external) or 5 (RAM disk, bootable
    once formatted and given an OS).
  - **System Speed:** Fast 3.6, Medium 2.3 or Standard 1.0 MHz.
  - **Date and Time.**

  The EX/2 keeps these settings with the power off.
- If the chosen boot slot has nothing bootable, the EX/2 tries the next lower-numbered slot.

**MIDI (EX/2 only):** through the **Port 2 (serial communications) connector**, with a Y cable (MIDI IN / MIDI OUT).
On the v1 board that port is the second 6551 ACIA, at `$C0A8–$C0AB`. MIDI's 31,250 baud isn't a standard 6551
rate, so the EX/2 presumably clocks that ACIA differently. MIDI software came with the machine.

**Video expansion connector (Figure C-6):**
- digital **RGBI** (pins 3, 15, 4, 1);
- HSYNC / VSYNC / CSYNC (pins 9, 14, 10);
- composite video (pin 12);
- the LCD signals (SEROUT, LOAD PULSE, DISPEN, F14M);
- +12 V and the speaker.

The manual describes it as being for "a flat-panel LCD display, a TV interface or a RGB monitor".

Also in Appendix C: the expansion connector and the RAM expansion connector pinouts (relevant to the
Laser128EX-Expansion card project).

## Unknowns to settle with real machines
- Which ROM versions are in your New Laser 128, 128EX and EX/2 (label and banner). The banner can be listed with
  the Applesoft loop in Laser128-QHGR's `docs/qhgr-investigation.md` ("Identifying a ROM").
- Whether `$C074` does anything on a New Laser 128.
- ~~Which slot is the expansion-RAM disk~~ **Answered:** on New Lasers it's always **slot 5**, auto-formatted by
  the firmware as `/RAM5` (found in the Laser128EX-Expansion work). Internal port 7 is the **3.5" drive
  interface** (User's Guide, Table 6-1). The ROM-door switches select internal or the expansion box for each.
- ~~Where the EX/2's MIDI port lives~~ **Answered:** the Port 2 serial connector (User's Guide). Still open: how
  the EX/2 gets 31,250 baud from that ACIA.
- Which ROM version each model shipped with. The User's Guide doesn't say; machine labels will. So far:
  original Laser 128 S/N 59554 = 2.7; owner's 128EX (S/N 1002869) = **6.0**. Owner's **New Laser 128, S/N 151202**: now runs ROM 6.0, put in by the owner. The owner thinks it
  came with a 4.x, but isn't certain. It has port 5/7 INT/EXT switches and an expansion RAM header. Still to check: its board's `$C800` bank decoding (BANKTEST2) and the
  EX/2 (6.1, owner has one).
- **Owner's EX/2 (ROM 6.1), first notes (Nov 2026):**
  - It has **only a port 5 INT/EXT switch**, no port 7 switch.
  - With the control panel's Boot Slot set to 7, it doesn't boot the FloppyEmu. The FloppyEmu can emulate a
    3.5" drive or a SmartPort device as well as a 5.25" drive, so which mode and port it's in matters.
  - **6.1X boot menu: tested, everything works as expected** (Nov 2026).
    - **Slot 5:** `/RAM5` (port 5 INT) and the expansion card (EXT) are mutually exclusive.
    - **Slot 7:** always the internal 3.5" firmware (no port 7 switch), driving a 3.5" drive on the drive port.
  - **Reset keys (6.1):** the same six as 6.0 (table at `$FDAC`, handlers via `$FAF5`):
    - P/0 → control panel (`$C1D9`);
    - M/Return → monitor (`$F8A2`);
    - 1/Q, 2/R, 3/S → speed 1, 2, 3 (through `$FF02`, which stores the setting in `$07FE`), then the normal
      reset;
    - space/@ → same as 2.

    No new keys. The boot menu's B is the only addition (6.1X).
  - **Internal drive:** 5.25" (the owner doubts the 5.25" EX/2 is the rare one).
  - **FloppyEmu on the rear "external drive" port, Boot Slot 7:**

    | FloppyEmu mode | Result |
    |---|---|
    | Apple II 5.25 Floppy | no boot (it's drive 2; the autostart only boots drive 1) |
    | **Apple II 3.5 Floppy** | **boots** (with an 800K image) |
    | UniDisk 3.5 | no boot |
    | SmartPort Hard Disk | no boot |

    So the EX/2's slot 7 drives a plain (non-intelligent) 3.5" drive on the external port, not SmartPort devices.
    With nothing bootable: "Unable to find a bootable disk".
  - **Slot 5 SmartPort test** (port 5 INT, FloppyEmu in SmartPort Hard Disk mode, a STATUS call to `$C551` from
    the monitor): **1 device.** Its DIB reads `F8 00 08 00 07 52 41 4D…`: status `$F8`, `$000800` blocks (1 MB),
    name of 7 characters starting "RAM". So slot 5's SmartPort firmware serves only the RAM disk. It doesn't
    see SmartPort devices on the external drive port the way an Apple //c's slot 5 does.
  - **Slot 7 SmartPort test** (`$C70D`, FloppyEmu still in SmartPort Hard Disk mode): no error, **0 devices.**
    So **neither slot supports SmartPort bus devices** (UniDisk 3.5, SmartPort hard disks) on the EX/2. The
    external port takes a 5.25" drive or a plain 3.5" drive.
  - **Fits BMOW's findings.** Steve Chamberlin, "Unlocking the Secrets of the UDC Disk Controller", Big Mess o'
    Wires, 24 Dec 2020; saved as `docs/ref/BMOW - Unlocking the Secrets of the UDC Disk Controller (2020).pdf`.
    - **The UDC card:** long-card firmware 2.1 and 2.3 has SmartPort drive support, but no daisy-chaining.
      Short-card 3.0 and 4.0 has daisy-chaining, but the SmartPort support is gone. The firmware version is the
      byte at `$C615` (with the card in slot 6), read as hex digits ($20 = 2.0).
    - **Laser ROMs (Steve, in the comments):** the SmartPort enable sequence (PH1 and PH3 both on) is in **4.2
      and 4.5, but not in 6.0 or 6.1**. His conclusion: support was dropped between 4.5 and 6.0.
    - **Tom Greene (comments):**
      - SmartPort works on a red-label Laser 128 with 4.2 and a 128EX with 4.5, **in slot 7**, but not on an
        early gold-label Laser 128 (ROM dated 860801);
      - a first claim that the EX/2's 6.1 works was withdrawn after re-testing.
    - **Joshua Bell (comments):** a 128EX with ROM 4.2 reaches a directly connected FloppyEmu in SmartPort mode,
      but not one daisy-chained after an Apple 3.5 drive.

    - **The 1989 User's Guide** (`docs/ref/`, covering the 128, 128EX and EX/2) **excludes the UniDisk 3.5**. The
      external drive connector takes "any LASER or Apple® brand 5.25" or 3.5" daisy-chainable disk drive (with
      the exception of the Apple® Unidisk 3.5)". Apple IIc drives work.
      - External 5.25" = port 6 drive 2; external 3.5" = port 7 drives 1 and 2.
      - "Two external 3.5" drives are configured as Slot 7 with the Laser 128 and 128EX only. On the Laser
        128EX/2, you must use daisy-chain drives."

      BMOW's post mentions a Laser 128 manual chapter that *lists* the UniDisk 3.5, presumably an earlier edition
      from the 4.x / SmartPort era. The UniDisk 3.5 is a SmartPort device, so it would follow SmartPort: maybe on
      4.2/4.5, not on 6.x.

    **Our results agree:** 6.1 sees no SmartPort devices in slot 5 or 7. To check: the 4.5X (or 4.2X) boot menu
    image with a FloppyEmu in SmartPort mode, connected directly, using option 7.
  - **Port 5 EXT:** `/RAM5` goes away. It seeks the internal floppy, then boots the FloppyEmu in 3.5" mode if
    present. Without the FloppyEmu, it seeks the internal floppy, then boots a CoGS card in **slot 5**. So the
    EX/2's expansion slot is slot 5 (the EX's is slot 7).
  - 6.1's reset code differs from 6.0's. After the banner it selects slot 7, calls `$C71A`, then `$FEE0` (boot
    slot choice), then `JMP ($0000)`. It needs its own patch.

## Possible undocumented features in 4.x–6.1 (survey, Nov 2026)
Not found:
- hidden reset keys: 4.x–6.1 only have the documented ones;
- a self-test: no Closed-Apple check at reset;
- hidden text or credits: the strings are only the copyright, configuration, memory test and boot messages.

Open-Apple at reset fills memory with `$65` before the cold start, as on Apple machines.

Worth probing:
1. **The 128EX's extra 64K of video RAM: most likely shadow RAM, not user-accessible.** Published EX teardowns
   agree it's **shadow video RAM**:
   - writes to display memory are copied into it;
   - the video circuitry reads its own copy;
   - so the CPU can run at 2.3/3.6 MHz without waiting on video fetches.

   That matches Laser's 1988 ad ("off-loads video work from the 128K system RAM"). It also matches the ROM: from
   4.5 to 6.0 the only new soft switch it touches is `$C01E`, the standard ALTCHARSET status, so the firmware
   never drives anything new in video. So this is probably not a source of hidden modes. A sweep of the unused
   `$C0xx` switches on the EX (as DHGRTEST did on the original board) could still confirm it, but it's low
   priority.
2. **`$C060` bit 7 at reset:** if set, the ROM turns on `$C00B` (SLOTC3ROM). On a //c that bit is the 80/40
   switch; what drives it on a Laser is unknown. Probe: `PEEK(49248)` on each machine.
3. **`$C074` (speed):** the documented values are `$00`, `$80`, `$C0`. The slot 5 firmware forces `$C0` around
   RAM-disk access and restores the saved setting. Other bits are untested.
4. **Where the EX/2 keeps its settings: answered.** They're 24 bytes plus a checksum at `$C8B8–$C8D0` in slot 7's
   3.5" controller buffer RAM, which must be battery-backed on the EX/2. The `$C078` clock is a 4-bit
   MSM6242-style RTC holding only the time. See `ex2-settings-and-clock.md`.
5. **The UDC 3.5" controller registers** (`$C0E8–$C0EF`: `$C0EC`, `$C0ED` bit 7). See BMOW's article.
