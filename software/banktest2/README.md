# BANKTEST2: every pair of slot-page accesses

Follow-up to BANKTEST. For each first page `$C1`–`$C7` and each second page (none, `$C1`–`$C7`), BANKTEST2 reads
`$CFFF`, then the first page, then the second, and checksums `$C800–$CFFE`. The 56 results are printed as a grid:
- **row** = first page (`C1` at the top, `C7` at the bottom);
- **column** = second page (none, then `C1`–`C7`).

Each sum is four hex digits. As with BANKTEST, all tests run with interrupts off before anything is printed.

**Run it with the bank-marker test ROM** (`roms/test/Laser128_2.7_bankmarkers.bin` in a 27256). Then each of the
empty blocks has its own sum:

| Chip block | Sum |
|---|---|
| `$0800` | 6C23 |
| `$4800` | 42E6 |
| `$5000` | 9781 |
| `$5800` | A43A |
| `$6000` | B4BA (marker) |
| `$6800` | 8AE3 |
| `$7000` | B587 (marker) |
| `$7800` | BBEF (marker) |

Anything else (around `07xx`) is the floating bus, meaning no ROM was selected.

Boot `dist/BANKTEST2.po` (bootable ProDOS 2.4) or type in `dist/BANKTEST2.monitor.txt` (366 bytes) and `6000G`.
`python3 build.py` checks the program in the 65C02 model against a simulated bank-select rule.

## BANKTEST2X: the same tests with `$C007` on
`dist/BANKTEST2X.po` turns on **INTCXROM** (`$C007`, internal slot ROM) before the 56 tests and off (`$C006`)
before printing. Its title line reads "C800 BANKS, $C007 ON". It's for the 128EX (ROM 6.0), where BANKTEST2
never reached chip `$6000` or `$6800`, although 6.0 has code in both and brackets some `$C800` calls with
`$C007`/`$C006`. The 6.0 block sums are: `$6000` = 699E, `$6800` = 5D88 (all eight: `tools/c800banks.py`).
