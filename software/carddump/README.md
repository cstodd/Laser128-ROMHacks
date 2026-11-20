# CARDDUMP: save a slot 7 card's ROM to disk

Copies the card's `$C700` page to `$2000` and its `$C800–$CFFF` expansion ROM to `$2100–$28FF`. It reads `$CFFF`
first to release any other card's window, then reads `$C700` so the card switches its own ROM in. Re-runnable.
Checked in the 65C02 model (`software/sim65.py`). For slot 5, change the two `C7` bytes (at `$030F` and `$0314`) to `C5`.

```
300: A9 C8 8D 1F 03 A9 21 8D 22 03 AD FF CF AD 00 C7
310: A2 00 BD 00 C7 9D 00 20 E8 D0 F7 A0 08 BD 00 C8
320: 9D 00 21 E8 D0 F7 EE 1F 03 EE 22 03 88 D0 EE 60
300G
```
Then back to BASIC (`3D0G`) and `BSAVE CARD.ROM,A$2000,L$900`. The last byte (`$CFFF`) isn't meaningful: reading
it releases the card's window.

## Cards with a banked `$C800` ROM
Some cards switch their `$C800` ROM between banks through their own I/O space. This version writes a value to
a card register before copying `$C800–$CFFF` to `$2100–$28FF`. It's checked in the model.

As written, it writes `$10` to `$C0F4` (`$C0n4` for slot 7), which is the second-bank switch of a CoGS card. For
another card:
- the register address is the bytes at `$0313–$0314` (`F4 C0`);
- the value is at `$0311` (`10`);
- for slot 5, also change the `C7` at `$030F` to `C5`.
```
300: A9 C8 8D 1B 03 A9 21 8D 1E 03 AD FF CF AD 00 C7
310: A9 10 8D F4 C0 A2 00 A0 08 BD 00 C8 9D 00 21 E8
320: D0 F7 EE 1B 03 EE 1E 03 88 D0 EE 60
300G
```
Then `3D0G` and `BSAVE CARD.ROM2,A$2100,L$800`.
