"""Checksums of the 2K blocks of a Laser 128 system ROM that can appear in the $C800-$CFFF window,
in the same form BANKTEST prints: 16-bit sum of the block's first $7FF bytes ($C800-$CFFE), and its first 4 bytes.
Usage: python3 -I c800banks.py ROM
"""
import sys
d = open(sys.argv[1], 'rb').read()
for blk in [0x0800] + list(range(0x4800, 0x8000, 0x800)):
    b = d[blk:blk + 0x7FF]
    print('chip $%04X  sum %04X  %s' % (blk, sum(b) & 0xFFFF, ' '.join('%02X' % x for x in d[blk:blk + 4])))
