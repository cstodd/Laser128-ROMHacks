# CLAUDE.md: working on Laser128-ROMHacks

Firmware modifications and hardware research for the VTech **Laser 128** family (original Laser 128, New Laser 128,
128EX, 128EX/2), in the spirit of the Apple //c "ROM 4X". The main deliverable so far is a **boot menu** for every
ROM version from 2.7 to 6.1, all hardware-tested except 4.x.

## Start here (new session)
Read these in order, and only open other files when the task needs them:
1. `docs/progress.md`: where things stand, what's open, what's next.
2. `docs/architecture.md`: how the repo, the hardware and the ROM fit together.
3. `CHANGELOG.md`: the most recent entries, for what changed lately.
4. `docs/building.md`: before building or changing code.
5. The topic doc for the task: see the index in `README.md`.

Don't re-derive what's in these docs. They record conclusions together with how they were established.

## The owner's machines
| Machine | Serial | ROM | Notes |
|---|---|---|---|
| Original Laser 128 | 59554 | 2.7 (socketed; 2.9X/3.0X/2.7X EPROMs tested) | Quad Hi-Res works; no port switches; external slot = 7 |
| 128EX | 1002869 | 6.0 | port 5/7 INT/EXT switches; 1 MB `/RAM5` |
| New Laser 128 | 151202 | 6.0 (owner-installed; originally probably 4.x) | port 5/7 switches, expansion RAM header, no accelerator |
| 128EX/2 | not yet recorded | 6.1 | port 5 switch only; internal 5.25" drive; OKI M6242 clock card |

Test kit: FloppyEmu on the external drive port; a CoGS network/disk card; an a2heaven replica of the Laser
expansion box; an A2C DVI adapter. EPROMs: 27C256 / 27256.

## Related repositories (same owner, private)
- `cstodd/Laser128-QHGR`: the Quad Hi-Res investigation and the VT27-0430-0 video ROM dump.
- `cstodd/Laser128EX-Expansion`: the owner's battery-backed 1 MB SRAM + RTC card for the 128EX. Its
  `docs/design-notes.md` §12–13 draw on this repo's ROM findings.

## Rules
- **Changelog:** keep `CHANGELOG.md` current. Add an entry **at least every couple of hours of work**, and
  always at the end of a session or before a long pause. Write in plain past tense: what changed and why, plus
  hardware results with machine and image CRC. Newest first, grouped by date.
- **Progress:** update `docs/progress.md` whenever the status of something changes: built, tested on hardware,
  answered, parked.
- **Hardware results** go in the topic doc too, with the machine (serial number) and the image CRC32. Never mark
  something "tested" without an explicit report from the owner.
- **Doc style:** lead with findings, then "how we know". Keep definitive docs (`*-design.md`, `free-space.md`)
  separate from evidence (`*-research.md`). Keep dead ends, briefly, so they aren't repeated.
- **Released images:** `python3 software/bootmenu/build.py` must reproduce `roms/bootmenu/CHECKSUMS.txt` exactly,
  unless a change is intended. If a CRC changes, say which images changed and why, and treat them as untested
  on hardware until re-checked.
- **Monitor instructions for the owner:** one command per line. On the Apple monitor, values after `addr:` on the
  same line are *stored*, not read.
- **Model vs hardware:** `software/sim65.py` checks logic, not real timing or bank decoding. Always say which
  results are model-only.
- **Git:** commit with clear messages and push to the session's development branch. Earlier work used
  `claude/nice-archimedes-ky1g0j`. Never put model identifiers in commits or files. No pull requests unless asked.
- The ROM dumps are copyrighted (VTech / Central Point Software) and kept for research. The repo is private.
