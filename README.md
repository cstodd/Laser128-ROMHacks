# Laser 128 ROM hacks

Firmware modifications for the VTech Laser 128 family, in the spirit of the Apple //c "ROM 4X".

| Path | What |
|---|---|
| `docs/free-space.md` | Where there is room in each ROM version, and how the 32K chip maps into memory |
| `docs/freespace-detail.txt` | Per-block free-space lists for every ROM |
| `roms/` | System ROM dumps (VTech 860801 / 860915, Central Point 2.9 – 6.0, EX/2 6.1), with `SHA256SUMS` |
| `tools/dis65c02.py` | 65C02 disassembler: `python3 -I dis65c02.py ROM START END` (hex file offsets) |
| `tools/freespace.py` | Free-space map of a 32K system ROM |
| `tools/softswitches.py`, `tools/strings.py` | Soft-switch reference scan and high-bit string extractor |

Related: `cstodd/Laser128-QHGR` (the Quad Hi-Res investigation and the VT27-0430-0 video ROM dump).
The ROMs are copyrighted firmware (VTech / Central Point Software), kept here for research.
