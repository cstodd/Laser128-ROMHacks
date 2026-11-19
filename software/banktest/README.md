# BANKTEST: which `$C800` ROM bank does each select sequence reach?

The Laser's 32K ROM shows 2K banks in the `$C800–$CFFF` window. The firmware selects them by reading `$CFFF`
and then a slot page (`$C100`–`$C700`). COMPUTIST #66 (1989) also lists two-step sequences such as
`$C600` then `$C100`. BANKTEST tries 15 sequences:
- none: `$CFFF` alone;
- each slot page `$C1`–`$C7` alone;
- `$C6` followed by `$C1`, `$C2`, `$C3`, `$C4`, `$C5` or `$C7`;
- `$C3` followed by `$C6`.

For each sequence it records a 16-bit checksum of `$C800–$CFFE` and the first four bytes. Interrupts are off while
the tests run, and printing waits until all tests are done, because the screen firmware itself switches banks.

## Use
1. `BRUN /BANKTEST/BANKTEST` from `dist/BANKTEST.po`, or type in `dist/BANKTEST.monitor.txt` (423 bytes) and `6000G`.
2. Photograph or copy the 15 lines.
3. On the same machine's ROM dump, run `python3 -I tools/c800banks.py ROM.bin`. Each line on screen should match
   one chip block's sum. A sequence that matches nothing (or shows `$FF`s or floating data) reached no ROM.

## Build
`python3 build.py` assembles `banktest.s` and runs it in the 65C02 model (`../sim65.py`) with eight
simulated banks. It checks that the printed sums and bytes match the selected bank for every sequence.
