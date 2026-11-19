#!/usr/bin/env python3
"""Assemble BANKTEST, check it in the 65C02 model with simulated $C800 banks, write dist/."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import asm65, mkdisk
from sim65 import Sim
ORG = 0x6000

class BankSim(Sim):
    """Model: reading $CFFF releases the window; reading $Cn00 selects bank n (last access wins)."""
    def __init__(s, code, banks):
        super().__init__(code, ORG); s.banks = banks; s.sel = 0
    def rd(s, a):
        if a == 0xCFFF: s.sel = 0; return 0
        if 0xC100 <= a < 0xC800: s.sel = a >> 8 & 7; return 0
        if 0xC800 <= a < 0xCFFF: return s.banks[s.sel][a - 0xC800]
        return super().rd(a)

def main():
    code, sym = asm65.assemble(open(os.path.join(HERE, 'banktest.s')).read(), ORG)
    import random
    rnd = random.Random(1)
    banks = [bytes(rnd.randrange(256) for _ in range(0x800)) for _ in range(8)]
    m = BankSim(code, banks); m.run(limit=3_000_000)
    lines = ''.join(m.out).split('\r')
    seq1 = [0, 1, 2, 3, 4, 5, 6, 7, 6, 6, 6, 6, 6, 6, 3]; seq2 = [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 7, 6]
    for k, (a, b) in enumerate(zip(seq1, seq2)):
        sel = b or a
        want = '%04X  %s' % (sum(banks[sel][:0x7FF]) & 0xFFFF, ' '.join('%02X' % x for x in banks[sel][:4]))
        assert want in lines[2 + k], (k, lines[2 + k], want)
    d = os.path.join(HERE, 'dist'); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'BANKTEST'), 'wb').write(code)
    with open(os.path.join(d, 'BANKTEST.monitor.txt'), 'w') as f:
        f.write('Type CALL -151, then enter these lines at the * prompt, then 6000G to run.\n')
        f.write('(%d bytes, $%04X-$%04X)\n\n' % (len(code), ORG, ORG + len(code) - 1))
        for i in range(0, len(code), 8):
            f.write('%04X: %s\n' % (ORG + i, ' '.join('%02X' % b for b in code[i:i + 8])))
    img = mkdisk.build_image('BANKTEST', [('BANKTEST', 0x06, ORG, code)])
    assert mkdisk.read_image(img)['BANKTEST'] == (0x06, ORG, code)
    open(os.path.join(d, 'BANKTEST.po'), 'wb').write(img)
    print('BANKTEST: %d bytes, model check passed; wrote dist/' % len(code))
    print('\n'.join(lines[:4]))

if __name__ == '__main__':
    main()
