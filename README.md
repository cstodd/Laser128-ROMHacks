# Laser 128 ROM hacks

Firmware modifications for the VTech Laser 128 family, in the spirit of the Apple //c "ROM 4X".

| Path | What |
|---|---|
| `docs/free-space.md` | ROM layout, `$C800` bank selection on each board, and free space in every version |
| `docs/free-space-research.md` | Evidence for the layout and bank rules: BANKTEST results, `$C0ED` paging, dead ends |
| `docs/models-and-versions.md` | ROM version boundaries and which Laser 128 model each likely belongs to |
| `docs/boot-menu-design.md` | Boot menu design: what it does, per-ROM implementation, status |
| `docs/boot-menu-research.md` | Boot menu research notes: findings and how each was established, test record |
| `docs/freespace-detail.txt` | Per-block free-space lists for every ROM |
| `docs/ref/` | VTech *Laser 128, 128EX, 128EX/2 User's Guide & BASIC Manual* (1989, OCR'd scan) |
| `roms/` | System ROM dumps (VTech 860801 / 860915, Central Point 2.7 – 6.0, EX/2 6.1), with `SHA256SUMS` |
| `tools/dis65c02.py` | 65C02 disassembler: `python3 -I dis65c02.py ROM START END` (hex file offsets) |
| `tools/freespace.py` | Free-space map of a 32K system ROM |
| `tools/c800banks.py` | Checksums of the ROM's `$C800` banks, to compare with BANKTEST |
| `software/bootmenu/`, `roms/bootmenu/` | **Boot menu** for the original Laser 128 (2.7, 2.9, 3.0): hold B at reset; external drive boot |
| `software/banktest2/` | BANKTEST2: every pair of slot-page accesses, as a grid of checksums |
| `software/banktest/` | BANKTEST: finds which `$C800` bank each select sequence reaches, on real hardware |
| `software/asm65.py`, `sim65.py`, `mkdisk.py`, `prodisk.py` | 65C02 assembler, 65C02 test model, ProDOS disk builder, bootable-disk maker |
| `software/prodos/` | ProDOS 2.4 (freely distributable): boot blocks, `PRODOS` and `BASIC.SYSTEM` for the tool disks |
| `tools/softswitches.py`, `tools/strings.py` | Soft-switch reference scan and high-bit string extractor |

Related: `cstodd/Laser128-QHGR` (the Quad Hi-Res investigation and the VT27-0430-0 video ROM dump).
The ROMs are copyrighted firmware (VTech / Central Point Software), kept here for research.
