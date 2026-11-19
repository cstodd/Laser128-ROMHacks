# Boot menu: design notes

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
- At power-up, holding a key selects special actions through a small table in the main bank (P, M and from 3.3
  also Q, R, S, @; M = Return = break into the monitor, per COMPUTIST #66). A boot-menu key could join this
  table.

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
1. Run BANKTEST (`software/banktest`) on the early machine; match its sums to the 2.7 dump with
   `tools/c800banks.py`. This shows which `$C800` banks exist and how to select them.
2. Map the 2.7 ROM: find the power-up key table, its handlers and free gaps in the main bank.
3. Build the menu in the free bank, with the drive-2 boot variant, and test in the 65C02 model.
4. Produce a patched 27256 image, try it in an EPROM, and test boots from both drives with a FloppyEmu.
