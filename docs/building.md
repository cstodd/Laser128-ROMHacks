# Building and testing

Everything is plain Python 3 (tested with 3.13). There are no other dependencies: the assembler, 65C02 model and
disk tools are in `software/`. Run commands from the repository root unless noted. Each build checks its output
in the 65C02 model and stops on an assertion if something is wrong.

## Boot menu ROMs
```
python3 software/bootmenu/build.py
```
- **Output:** writes `roms/bootmenu/Laser128_<ver>_bootmenu.bin` for 2.7, 2.9, 3.0, 4.1, 4.2, 4.3, 4.5, 6.0 and
  6.1, plus `CHECKSUMS.txt`. It prints each banner, the hook addresses, sizes and "model checks passed".
- **Run time:** about 1–3 minutes, mostly the model runs.
- **Reproducible:** an unchanged tree reproduces `CHECKSUMS.txt` byte for byte. Check with
  `git diff roms/bootmenu/`: no diff means no change to any released image.
- **Burning:** 27256 / 27C256, the whole 32K image, no offset.
- **Inputs:** the stock ROMs in `roms/` (verified by `roms/SHA256SUMS`: `cd roms && sha256sum -c SHA256SUMS`).
- **Sources:**
  - `software/bootmenu/menu.s`: the shared menu, with `{VERSION}`, `{S5}`, `{S7}` and `{EXTBOOT}` filled in by
    the build;
  - `copier.s`: the original-board copier (the new-board copier is generated in `build.py`);
  - `build.py`: `patch()` / `check()` for the original board, `patch_new()` / `check_new()` with the `NEW`
    profiles for 4.x / 6.0 / 6.1.

**Adding a ROM to the new-board family:** add a `NEW` profile. You need:
- `file`;
- `keyb` (a free gap of at least 13 bytes);
- `free0` (the start of the free tail in chip `$7800`);
- the stock `banner` text (and `newbanner` if it isn't "LASER 128 ROM Version xX");
- the slot labels;
- `key` / `cold` / `init` if the hook sites differ.

The build reads the original `JSR` targets and asserts that the patch sites look as expected.

## Test disks (bootable ProDOS 2.4, 140K `.po`)
```
cd software/banktest  && python3 build.py   # dist/BANKTEST.po (+ binary, monitor listing)
cd software/banktest2 && python3 build.py   # dist/BANKTEST2.po and BANKTEST2X.po ($C007 on)
```
Both reproduce their `dist/` files exactly. The disks boot ProDOS 2.4 and run the program from `STARTUP`. The
`.monitor.txt` files are hex listings for typing into the monitor instead.

New tool disks: `prodisk.boot_image(volname, files, run=None, startup=None, sys_first=())` returns the image bytes.
`files` is a list of ProDOS file entries, as in the existing `build.py`s.

## Analysis tools (`tools/`)
| Command | What it does |
|---|---|
| `python3 -I tools/dis65c02.py ROM START END` | disassemble a chip range (hex file offsets) |
| `python3 -I tools/freespace.py ROM` | free-space map (runs of 16+ `$FF`) |
| `python3 -I tools/c800banks.py ROM` | checksums of each `$C800` bank, to compare with BANKTEST screens |
| `python3 -I tools/softswitches.py ROM` | every `$C0xx` reference, by address |
| `python3 -I tools/strings.py ROM [minlen]` | high-bit / ASCII strings |

## Writing model checks
Subclass `sim65.Sim`:
- load the ROM's main bank into `main[$C100–$FFFF]`, and the bank under test into `$C800`;
- override `rd()` for soft switches (`$C010` key-held, `$C000` keys from `keys`);
- log interesting reads to `self.io`.

`run(start, stop={addr…}, limit=n)` returns the address where it stopped. It raises `RuntimeError('did not
finish')` at the limit, and `... not modelled` for missing opcodes (add them in `sim65.py`). See `Machine` and
`Machine60` in `software/bootmenu/build.py`, which also model the release wait and slot signatures.

**Limits:** the model has no real `$C800` decoding, no disk timing and no video. Hardware tests remain the final
word.

## Hardware test procedure (boot menu)
1. **Without B:** normal start, Ctrl-Reset, and the machine's own reset keys.
2. **B at power-on and at Ctrl-Reset, then release:** the menu appears.
3. **1** (internal drive); **2** with ProDOS on the FloppyEmu (in 5.25" mode), which stays on drive 2: check
   with `PREFIX` and `CAT`; **B**; **M**.
4. **5 / 7:** shown only when firmware or a card answers, and each boots.
5. **Record:** the machine's serial number, the image CRC32 and the results, in `boot-menu-research.md` and
   `CHANGELOG.md`.
