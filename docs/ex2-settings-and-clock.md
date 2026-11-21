# Laser 128EX/2: where the settings live, and the clock

Traced from ROM 6.1 (Nov 2026). Hardware checks are listed at the end.

## Findings
### 1. The settings are 24 bytes plus a checksum in slot 7's buffer RAM
- **What:** the control panel settings live at **`$C8B8–$C8CF`** in slot 7's `$C800` window, with an additive
  checksum at **`$C8D0`**. That window's lower half, `$C800–$CBFF`, is the 3.5" controller's 1K buffer RAM
  (`free-space.md` §2). The EX/2 has no port 7 switch, so it's always the internal controller.
- **At every reset:** the cold start calls the 3.5" firmware (`$C71A` with X=3, Y=`$14`). That reaches the
  routine at `$CE64` in the `$C0ED` page `$00` slice (chip `$6264`), which calls **`$CE17`**:
  1. sum `$C8B8` plus `$C8B9–$C8CF`, and compare the result with `$C8D0`;
  2. if they differ, copy the **24-byte defaults** from ROM (`$CE4C`, chip `$624C`) into `$C8B8–$C8CF`, and store
     the new checksum;
  3. set the speed: `$07FE = table[$C8CD]` (table at `$CE48`: `60 56 96 D6`).
- **The ROM defaults:**
  ```
  $C8B8: 01 02 04 01 01 06 06 01   01 02 04 01 01 05 03 01
  $C8C8: 01 02 01 02 03 03 0B 08
  ```
  - **Probably:** the two serial/printer ports' settings (bits, baud, parity, echo, LF, width, CR, ZAP), then
    the mouse scaling, Boot Slot and speed.
  - **Known:** `$C8CD` is the speed index (3 = `$D6`, fast). `$C8CE`/`$C8CF` (`0B 08`) are copied to `$C8B6`/`$C8B7`
    for the clock display, probably the date and hour formats.
  - The exact field order hasn't been mapped yet. Hardware check 2 would settle it.
- **So the buffer RAM must be battery-backed on the EX/2.** On the 128EX the same RAM holds random values at
  power-up (seen in the `$C800` dumps), so the EX's settings don't survive, and its defaults reload each time.
  On the EX/2 the settings survive power-off, so something keeps that RAM powered.

### 2. The clock is a 4-bit, MSM6242-style RTC at `$C078`
- **Interface:** one address, `$C078`. The driver writes the register number, then reads or writes the data
  (`$CC70`: `CMP $C078`, `STX $C078`, `STA $C078`). Registers are `$00–$0F`, with 4-bit data (`AND #$0F`). The
  driver lives in slot 7's ROM, in the `$C0ED` page `$10` slice (chip `$6400`).
- **Register `$0D` is a HOLD/BUSY handshake:** set HOLD (bit 0), wait while BUSY (bit 1) is set, access the
  registers, then clear HOLD. That's the MSM6242 / RTC-62421 register map. That chip has no general-purpose
  RAM, so it holds only the time, not the settings.
- **Entry points** (slot 7 dispatcher, page `$10` commands):
  - `$CC00`: ProDOS clock read, filling `$BF90–$BF93`;
  - `$CC09`: write a clock register;
  - `$CE44`: the control panel's date/time display.

  Working copies of the time are kept at `$C8B0–$C8B7` in the same buffer RAM.

### 3. ProDOS gets the clock with no driver file: the firmware installs itself
- **What:** slot 7's firmware patches ProDOS's date/time vector the first time it handles a ProDOS call.
  - **The patch** (slice `$6800`, `$CC27`): if `$BF00` is a `JMP` (ProDOS is present) and `$BF06` isn't already
    one, it writes **`JMP $C718`** at `$BF06`. Normally `$BF06` is an `RTS`, meaning no clock.
  - **Reading the time:** `$C718` enters the slot 7 firmware with carry clear (`CLC` / `BCS`, falling into
    `$C71B`). That leads to `$CE64` and dispatches command `$2C`, which runs `$CC0C` in the `$C0ED` page `$10`
    slice. That routine reads the clock and fills ProDOS's `$BF90–$BF93`.
  - **The same entry at reset:** `$C71A` is the same code with carry set. The `$38` at `$C71A` is the `BCS`
    operand, read as `SEC`.
- **So stock ProDOS time-stamps files on the EX/2,** with no CLOCK.SYSTEM or other driver file. ProDOS normally
  calls slot 7's firmware at startup (to count its devices), so the hook is in place from boot. If a clock
  driver has already installed itself (`$BF06` is a `JMP`), the firmware leaves it alone.
- **6.0 has neither part:** no `$C078` access and no `$BF06` patch. That fits the 128EX having no clock.

### 4. The clock card (owner's photo, `ref/photos/ex2-clock-card-top.jpg`)
A VTech daughter card with a 2×10 header. What's readable on top:
- **OKI M6242** (MSM6242): confirms the register map inferred from the ROM.
- **A 32.768 kHz crystal.**
- **Logic:** KS74HCTLS10N (74HCT10), two KS74HCTLS74AN (74HCT74), and a CD74HCT04E. The two '74s give four
  flip-flops, enough to latch the 4-bit register number. That fits the ROM's `$C078` sequence: a read (`CMP`)
  resets the sequence, the first write is the register number, the second is the data.
- **A fifth, larger chip** at the lower left whose label can't be read in this photo.
- **Q1–Q3, D1–D4 and electrolytics:** typical of a battery switchover circuit.
- **The battery:** the original soldered cell, replaced by a CR2032 holder on wires.

**Open:** whether the card holds the settings RAM (the unreadable chip?), or only powers the motherboard's
slot 7 buffer RAM from its battery through the header. Needed:
- close-ups of every chip label;
- the card's underside;
- the header's traces;
- the motherboard around the header and the UDC.

No schematic of this card has turned up: the v1 Technical Reference is earlier than the EX/2, and the 1989 User's
Guide only describes the clock's use.

## What this means for a modern clock card
A replacement has to reproduce two things:
1. **The `$C078` register interface:** an MSM6242-compatible register set, 4-bit, with HOLD/BUSY in `$0D`. The
   6.1 firmware and its driverless ProDOS time-stamping then work unchanged. A modern RTC (an RV-3028, DS3231, …) can sit behind
   a small CPLD or microcontroller that emulates the 6242 registers.
2. **Battery backup for the settings RAM,** if the original card supplies it. Which part does is still to be
   checked: the 1K buffer RAM chip may be on the motherboard and fed from the card's battery through the
   connector, or it may sit on the card itself.

The card's connector pinout and what's on the card decide which. Photos of both sides of the card, and of the
motherboard connector, are the next step.

## Hardware checks
1. **Read the settings:** in the monitor, `CFFF`, then `C700`, then `C8B8.C8D0`, each on its own line. Expect
   the defaults above, or your own settings. `$C8D0` should equal the sum.
2. **Map the fields:** change one setting in the control panel (e.g. Speed or Boot Slot), then read again. One
   byte changes.
3. **Retention:** power off for a minute, then read again. The bytes should be unchanged, which confirms
   battery backup.
4. **Optional, on the 128EX:** the same read shows the defaults after each power-up, since there the checksum
   fails and the defaults reload.
