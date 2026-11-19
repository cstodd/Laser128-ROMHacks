# Test images

`Laser128_2.7_bankmarkers.bin`: ROM 2.7 with each of its three empty `$C800` banks (chip `$6000`, `$7000`, `$7800`)
filled with a repeating text marker ("BANK 6000 ", "BANK 7000 ", "BANK 7800 "). Everything else is unchanged, so
the machine runs normally. Burn it to a 27256 and run BANKTEST. On the stock ROM those three banks are all
`$FF` and give identical checksums, and an unmapped window could look the same. With the markers, each one is
distinct. Expected sums: `python3 -I tools/c800banks.py roms/test/Laser128_2.7_bankmarkers.bin`. The first
four bytes on screen read `42 41 4E 4B` ("BANK" in ASCII) for a marker bank.
