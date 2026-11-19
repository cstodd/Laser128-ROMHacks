#!/usr/bin/env python3
"""Assemble BANKTEST2, check it in the 65C02 model with simulated $C800 banks, write dist/ (bootable disk)."""
import os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import asm65, prodisk
from sim65 import Sim
ORG = 0x6000

class BankSim(Sim):
    """Test model only (any deterministic rule will do): $CFFF releases; the selected bank is a function of
    the sequence of slot pages read since, so every pair maps to a known bank."""
    def __init__(s, code, banks):
        super().__init__(code, ORG); s.banks = banks; s.seq = []
    def bank(s): return (sum(s.seq) * 7 + len(s.seq)) % len(s.banks)
    def rd(s, a):
        if a == 0xCFFF: s.seq = []; return 0
        if 0xC100 <= a < 0xC800 and (a & 0xFF) == 0: s.seq.append(a >> 8 & 7); return 0
        if 0xC800 <= a < 0xCFFF: return s.banks[s.bank()][a - 0xC800]
        return super().rd(a)

def main():
    code, sym = asm65.assemble(open(os.path.join(HERE, 'banktest2.s')).read(), ORG)
    rnd = random.Random(2)
    banks = [bytes(rnd.randrange(256) for _ in range(0x800)) for _ in range(11)]
    m = BankSim(code, banks); m.run(limit=20_000_000)
    rows = ''.join(m.out).split('\r')[3:10]
    for f in range(1, 8):
        want = []
        for s in range(8):
            seq = [f] + ([s] if s else [])
            want.append('%04X' % (sum(banks[(sum(seq) * 7 + len(seq)) % len(banks)][:0x7FF]) & 0xFFFF))
        assert rows[f - 1].strip() == ' '.join(want), (f, rows[f - 1], want)
    assert all(len(r) <= 39 for r in rows), 'rows must fit 40 columns'
    d = os.path.join(HERE, 'dist'); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'BANKTEST2'), 'wb').write(code)
    with open(os.path.join(d, 'BANKTEST2.monitor.txt'), 'w') as fo:
        fo.write('Type CALL -151, then enter these lines at the * prompt, then 6000G to run.\n')
        fo.write('(%d bytes, $%04X-$%04X)\n\n' % (len(code), ORG, ORG + len(code) - 1))
        for i in range(0, len(code), 8):
            fo.write('%04X: %s\n' % (ORG + i, ' '.join('%02X' % b for b in code[i:i + 8])))
    open(os.path.join(d, 'BANKTEST2.po'), 'wb').write(prodisk.boot_image('BANKTEST2', [('BANKTEST2', 0x06, ORG, code)], 'BANKTEST2'))
    print('BANKTEST2: %d bytes, model check passed; wrote dist/' % len(code))
    print('\n'.join(''.join(m.out).split('\r')[:10]))

if __name__ == '__main__':
    main()
