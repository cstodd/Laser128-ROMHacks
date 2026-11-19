"""Free-space map of a Laser 128 32K system ROM.

Counts runs of $FF (default >= 16 bytes) per 2K block of the chip and shows where each block appears to the CPU:
  chip $0000-$3FFF  main bank, $C000-$FFFF ($0000-$00FF lies under the I/O page and is never visible)
  chip $4000-$47FF  alternate $C100-$C7FF slot pages
  chip $4800-$7FFF  seven 2K banks switched into the $C800-$CFFF window
Usage: python3 -I freespace.py ROM [minrun]
"""
import re, sys
d = open(sys.argv[1], 'rb').read(); minrun = int(sys.argv[2]) if len(sys.argv) > 2 else 16
assert len(d) == 0x8000, 'expects a 32K system ROM'
free = bytearray(len(d))
for m in re.finditer(rb'\xff{%d,}' % minrun, d):
    free[m.start():m.end()] = b'\1' * (m.end() - m.start())
free[0:0x100] = bytes(0x100); free[0x4000:0x4100] = bytes(0x100)   # under the I/O page: unusable
def where(b):
    if b < 8: return 'main $%04X-$%04X' % (0xC000 + b * 0x800, 0xC7FF + b * 0x800)
    if b == 8: return 'alt slot pages $C100-$C7FF'
    return '$C800 bank (chip $%04X)' % (b * 0x800)
total = 0
for b in range(16):
    n = sum(free[b * 0x800:(b + 1) * 0x800]); total += n
    runs = [(m.start(), m.end() - m.start()) for m in re.finditer(rb'\x01+', bytes(free[b * 0x800:(b + 1) * 0x800]))]
    base = 0xC000 + b * 0x800 if b < 8 else (0xC000 if b == 8 else 0xC800)
    print('chip $%04X  %-30s free %5d  %s' % (b * 0x800, where(b), n,
          ', '.join('$%04X+%d' % (base + o, l) for o, l in runs[:6]) + (' ...' if len(runs) > 6 else '')))
print('total usable free: %d bytes' % total)
