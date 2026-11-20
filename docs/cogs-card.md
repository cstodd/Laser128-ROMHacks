# CoGS card on the Laser 128EX (slot 7, port switch EXT, no expansion box)

Dump: `roms/cards/COGS_slot7_dump.bin`. Taken with CARDDUMP (`software/carddump/`) on the 128EX:
- `$C700` page, then the `$C800–$CFFF` ROM as selected after reading `$C700`. 2304 bytes.
- CRC32 `76b31abc`, SHA-256 `5a177e0a70793510c2f3e99f838f14a9e32fa79dd5a4bc61b31bdbdbfac205a1`.
- The last byte (`$CFFF`) isn't meaningful.
- This is the card's first `$C800` bank only (see below).

## What the boot code does
- **Signature:** `$C701=$20`, `$C703=$00`, `$C705=$03` (ProDOS/SmartPort-style), so the boot menu offers 7.
  - Boot entry `$C711`: `SEI`, `BIT $CFFF`, `JSR $C812` (slot from the return address), then `$CEA1`.
  - There are also 65816 paths for the IIGS (`REP`/`SEP`/`XCE`/`RTL`).
- **Card registers:** slot I/O at `$C0n0–$C0nF` (`$C0F0`+ in slot 7):
  - `$C0n0` data, `$C0n1` bit 7 = ready;
  - `$C0n4` control. Writing `$10` there at `$C800`/`$C809` switches the card's `$C800` ROM bank: the next byte
    (`NOP`) runs in the new bank. `$C800` (entered with carry) and `$C809` are the two bank-switch entries.
  - **Implication:** the card is a coprocessor/network design that depends on its device-select I/O working.
- **Menu keys** (`$CF58`, polled 24 times with a delay between, about 1 s at 1 MHz and about 0.3 s at 3.6 MHz):
  - The key comes from `$C000`, plus `$C010` bit 7 (key held) when `$FBB3 = $06`. The EX's `$FBB3` is `$06`, so
    a held key counts.
  - **C or M** → `CLC`, `JSR $C800`: the bank switch, then the menu in the other bank.
  - **1–8** → stored at `$51`, apparently a boot choice.
- **Network boot:** the code sends commands (`$66`, `$E6`) and waits for replies on `$C0n1`. It then makes up to
  240 attempts (`$CBCC`/`$CCD7`). Errors `$10` and `$0B` end the attempts early. On success it jumps to
  `$0801`. The name `COGS.NETWORK` is at `$CFEA`.
- **Fallback** (`$CF8E`): `SEC`, `JSR $C800` (other bank). If carry comes back set → `JMP $FABA`, the Apple
  "boot next slot" entry. **6.0 has `JMP $FEE0` at `$FABA`**, so the autostart scan continues: slot 6, the
  internal drive. That is the "pause, then internal drive" seen with `PR#7`, `7` Ctrl-P and the menu.

## Working theory: the card's I/O doesn't reach it without the box
The ROM reads fine (the dump is real code), but holding C did nothing. That fits if writes to `$C0F4` never
reach the card:
- **No bank switch:** `JSR $C800` would run on in the *same* bank at `$C805: NOP / RTS`, with carry unchanged.
- **C pressed:** carry clear → nothing happens, so no menu.
- **Fallback:** carry set → `JMP $FABA` → slot 6.

A card with no network would fall back too, but it should still show its menu on C. Test (monitor, separate
lines, slot 7 on EXT):
```
C700
C800.C80F
C0F4:10
C800.C80F
```
- **Same bytes both times** (`A9 10 9D 04 C0 EA 60 00 00 A9 10 9D 04 C0 EA 60`): the card's I/O isn't reaching
  it.
- **Different bytes:** the bank switch works, and the cause is elsewhere (for example, no network).

Power-cycle afterwards.
