# CARDDUMP: save a slot 7 card's ROM to disk

Copies the card's `$C700` page to `$2000` and its `$C800–$CFFF` expansion ROM to `$2100–$28FF`. It reads `$CFFF`
first to release any other card's window, then reads `$C700` so the card switches its own ROM in. Re-runnable.
Checked in the 65C02 model (`software/sim65.py`). For slot 5, change the three `C7` bytes to `C5`.

```
300: A9 C8 8D 1F 03 A9 21 8D 22 03 AD FF CF AD 00 C7
310: A2 00 BD 00 C7 9D 00 20 E8 D0 F7 A0 08 BD 00 C8
320: 9D 00 21 E8 D0 F7 EE 1F 03 EE 22 03 88 D0 EE 60
300G
```
Then back to BASIC (`3D0G`) and `BSAVE COGS.ROM,A$2000,L$900`. The last byte (`$CFFF`) isn't meaningful: reading
it releases the card's window.
