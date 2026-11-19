#!/usr/bin/env python3
"""Build boot-menu ROMs for the original Laser 128 (ROM 2.7, 2.9, 3.0) and check them in the 65C02 model.

Patches (located by byte pattern, not fixed addresses):
  1. power-up key check  "AND #$1F / CMP #$10 / BEQ p / CMP #$0D / BEQ m": the CMP #$10/BEQ becomes JMP KEYX.
     KEYX (gap at $FAF5, 20 bytes): P and M as before; B clears $03F3/$03F4 so reset takes the cold-start path.
  2. end of cold start   "LDA $C701 / CMP #$20" (slot 7 card test): the LDA becomes JMP BOOTSEL.
     BOOTSEL (gap at $FEE9): if B is still held, select the menu bank ($CFFF, $C600, $C200 -> chip $7800)
     and JMP $C800; otherwise do the LDA $C701 and carry on.
  3. chip $7800 (empty): copier.s at $C800, menu body at $C900, copied to $1000 and run from RAM.
External drive: 2.7 enters its own unused drive-2 entry at $C60D; 2.9/3.0 run a relocated RAM copy of the
slot 6 boot page with drive 2 selected ($C0EA -> $C0EB) and the window release ($CFFF) changed to a slot 6 select.
"""
import os, re, sys, hashlib, zlib
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import asm65
from sim65 import Sim
from dis65c02 import dis1

VERSIONS = {'2.7': 'Laser128_2.7.bin', '2.9': 'Laser128_2.9.bin', '3.0': 'laser128-v3.0.bin'}
KEYX, BOOTSEL, BODY, BANK = 0xFAF5, 0xFEE9, 0x1000, 0x7800
cpu = lambda off: 0xC000 + off            # main bank: chip offset -> CPU address

def rel_target(rom, off):                 # target of a branch at chip offset off
    r = rom[off + 1]; return cpu(off) + 2 + (r - 256 if r > 127 else r)

def boot_copy(rom, base):
    """Relocated, drive-2 copy of the alternate slot 6 page (2.9/3.0) for RAM at base."""
    page = bytearray(rom[0x4600:0x4700]); notes = []
    i = 0
    while i < 0x100:
        n, txt, md, w = dis1(rom, 0x4600 + i, 0x8000)
        if md in ('abs', 'abx', 'aby', 'ind') and i + n <= 0x100:
            new = None
            if w == 0xC0EA: new = 0xC0EB                                   # drive 1 -> drive 2
            elif w == 0xCFFF: new = 0xC600                                 # release -> select slot 6 bank
            elif 0xC600 <= w <= 0xC6FF: new = base + (w - 0xC600)          # own page -> RAM copy
            if new is not None:
                page[i + 1], page[i + 2] = new & 0xFF, new >> 8
                notes.append('$C6%02X %s -> $%04X' % (i, txt, new))
        i += n
    return bytes(page), notes

def extboot(ver, rom, base_guess, pad=0):
    if ver == '2.7':
        assert rom[0x4608:0x4610] == bytes.fromhex('0deac080030debc0'), '2.7 drive-2 entry'
        return ('EXTBOOT: LDA $CFFF\n        LDY #0\n        LDX #3\n        STX $3C\n'
                '        JMP $C60D       ; the ROM\'s own (unused) drive-2 entry\n'), None
    page, notes = boot_copy(rom, base_guess)
    src = ('EXTBOOT: LDA $CFFF      ; clear the bank latches\n'
           '        LDA $C600       ; select the slot 6 bank for the boot code\'s $C800 helpers\n'
           '        JMP BOOT2\n')
    if pad: src += '        .byte ' + ','.join(['$00'] * pad) + '   ; page-align BOOT2 (same branch timing as in ROM)\n'
    src += 'BOOT2:\n'
    for k in range(0, 256, 16):
        src += '        .byte ' + ','.join('$%02X' % b for b in page[k:k + 16]) + '\n'
    return src, notes

def build_body(ver, rom):
    tmpl = open(os.path.join(HERE, 'menu.s')).read().replace('{VERSION}', ver + ' + BOOT MENU')
    src, _ = extboot(ver, rom, 0x1E00)
    code, sym = asm65.assemble(tmpl.replace('{EXTBOOT}', src), BODY)
    notes = None
    if 'BOOT2' in sym:                                 # second pass: page-align BOOT2, then relocate to it
        pad = (-sym['BOOT2']) & 0xFF
        base = sym['BOOT2'] + pad
        src, notes = extboot(ver, rom, base, pad)
        code, sym2 = asm65.assemble(tmpl.replace('{EXTBOOT}', src), BODY)
        assert sym2['BOOT2'] == base and base & 0xFF == 0; sym = sym2
    assert len(code) <= 0x600, 'menu body must fit $C900-$CEFF'
    return code, sym, notes

def patch(ver):
    rom = bytearray(open(os.path.join(ROOT, 'roms', VERSIONS[ver]), 'rb').read())
    orig = bytes(rom)
    m = [x.start() for x in re.finditer(rb'\x29\x1f\xc9\x10\xf0.\xc9\x0d\xf0.', bytes(rom[0x3800:0x4000]), re.S)]
    assert len(m) == 1, 'key check'; k = 0x3800 + m[0] + 2           # at CMP #$10
    p_target, m_target = rel_target(rom, k + 2), rel_target(rom, k + 6)
    cmp0d = cpu(k + 4)
    m = [x.start() for x in re.finditer(rb'\xad\x01\xc7\xc9\x20', bytes(rom[0x3800:0x4000]))]
    assert len(m) == 1, 'slot 7 test'; s7 = 0x3800 + m[0]
    keyx_src = (f'        CMP #$10\n        BNE K1\n        JMP ${p_target:04X}\n'
                f'K1:     CMP #$02\n        BNE K2\n        STZ $03F3\n        STZ $03F4\n'
                f'K2:     JMP ${cmp0d:04X}\n')
    keyx, _ = asm65.assemble(keyx_src, KEYX)
    sel_src = (f'        LDA $C010\n        BPL NORM\n        LDA $C000\n        AND #$1F\n        CMP #$02\n'
               f'        BNE NORM\n        LDA $CFFF\n        LDA $C600\n        LDA $C200\n        JMP $C800\n'
               f'NORM:   LDA $C701\n        JMP ${cpu(s7 + 3):04X}\n')
    sel, _ = asm65.assemble(sel_src, BOOTSEL)
    for addr, blob in ((KEYX, keyx), (BOOTSEL, sel)):
        o = addr - 0xC000; assert all(b == 0xFF for b in rom[o:o + len(blob)]), 'gap not free'
        rom[o:o + len(blob)] = blob
    assert len(keyx) <= 20
    rom[k:k + 4] = bytes((0x4C, KEYX & 0xFF, KEYX >> 8, 0xEA))
    rom[s7:s7 + 3] = bytes((0x4C, BOOTSEL & 0xFF, BOOTSEL >> 8))
    body, sym, notes = build_body(ver, orig)
    copier, _ = asm65.assemble(open(os.path.join(HERE, 'copier.s')).read(), 0xC800)
    assert len(copier) <= 0x100 and all(b == 0xFF for b in orig[BANK:BANK + 0x800])
    rom[BANK:BANK + len(copier)] = copier
    rom[BANK + 0x100:BANK + 0x100 + len(body)] = body
    info = dict(key=cpu(k), p=p_target, m=m_target, cmp0d=cmp0d, s7=cpu(s7), keyx=len(keyx), sel=len(sel),
                body=len(body), sym=sym, notes=notes)
    return bytes(rom), orig, info

class Machine(Sim):
    """Main bank as memory; menu bank at $C800 (as RAM); $C010 bit 7 = key held."""
    def __init__(s, rom, keys=(), held=False):
        super().__init__(b'', 0x1000, keys); s.main[0xC100:0x10000] = rom[0x0100:0x4000]
        s.main[0xC800:0xD000] = rom[BANK:BANK + 0x800]; s.held = held
        for a in (0xFB2F, 0xFE93, 0xFE89): s.main[a] = 0x60   # INIT, SETVID, SETKBD stubs
    def rd(s, a):
        if a == 0xC010: s.io.append(('R', a)); s.kbd &= 0x7F; return 0x80 if s.held else 0
        if a in (0xCFFF, 0xC600, 0xC200, 0xC701, 0xC703, 0xC705): s.io.append(('R', a))
        return super().rd(a)

def check(ver, rom, orig, info):
    diff = sorted({i for i in range(len(rom)) if rom[i] != orig[i]})
    regions = [(info['key'] - 0xC000, 4), (info['s7'] - 0xC000, 3), (KEYX - 0xC000, info['keyx']),
               (BOOTSEL - 0xC000, info['sel']), (BANK, 0x800)]
    assert all(any(o <= i < o + n for o, n in regions) for i in diff), 'unexpected change'
    # 1. key check
    for key, want in ((0x10, info['p']), (0x0D, info['m']), (0x02, info['cmp0d'] + 4), (0x01, info['cmp0d'] + 4)):
        m = Machine(rom); m.main[0x3F3], m.main[0x3F4] = 0x12, 0x34; m.a = key
        assert m.run(start=info['key'], stop={info['p'], info['m'], info['cmp0d'] + 4}) == want, (ver, key)
        if key == 0x02: assert (m.main[0x3F3], m.main[0x3F4]) == (0, 0), 'B forces cold start'
        elif key == 0x01: assert (m.main[0x3F3], m.main[0x3F4]) == (0x12, 0x34)
    # 2. end of cold start: B held -> menu bank; otherwise carry on
    m = Machine(rom, held=True); m.kbd = 0xC2
    assert m.run(start=info['s7'], stop={0xC800}) == 0xC800
    sel = [e[1] for e in m.io if e[1] in (0xCFFF, 0xC600, 0xC200)]
    assert sel[-3:] == [0xCFFF, 0xC600, 0xC200], sel
    m = Machine(rom, held=False); m.main[0xC701] = 0x55
    assert m.run(start=info['s7'], stop={info['s7'] + 3}) == info['s7'] + 3 and m.a == 0x55
    # 3. menu: copier, screen, each choice
    def menu(keys, card=False, stop=()):
        m = Machine(rom, keys=[ord(c) for c in keys])
        if card: m.main[0xC701], m.main[0xC703], m.main[0xC705] = 0x20, 0x00, 0x03
        pc = m.run(start=0xC800, stop=set(stop), limit=2_000_000); return m, pc
    m, pc = menu('1', stop={0xC600})
    assert pc == 0xC600
    scr = lambda m, y: bytes(c & 0x7F for c in m.main[0x400 + (y & 7) * 0x80 + (y >> 3) * 0x28:][:40]).decode()
    # screen was cleared at the end (CLS before booting), so check the menu text on a run that waits:
    w = Machine(rom, keys=[]); w.run(start=0xC800, stop={0x1000 + 0}, limit=200000)
    try: w.run(start=0x1000, limit=300000)
    except RuntimeError as e: assert 'did not finish' in str(e)
    assert 'LASER 128 BOOT MENU' in scr(w, 3) and ver in scr(w, 4) and '2  EXTERNAL DRIVE' in scr(w, 9), scr(w, 3)
    assert '7  SLOT 7' not in scr(w, 11)
    m, pc = menu('b', stop={0xE000}); assert pc == 0xE000
    m, pc = menu('M', stop={0xFF69}); assert pc == 0xFF69
    m, pc = menu('7b', card=False, stop={0xC700, 0xE000}); assert pc == 0xE000, 'no card: 7 ignored'
    m, pc = menu('7', card=True, stop={0xC700}); assert pc == 0xC700 and m.main[0] == 0 and m.main[1] == 0xC7
    if ver == '2.7':
        m, pc = menu('2', stop={0xC60D}); assert pc == 0xC60D and m.x == 3 and m.y == 0 and m.main[0x3C] == 3
    else:
        b2 = info['sym']['BOOT2']
        m, pc = menu('2', stop={b2}); assert pc == b2
        assert [e[1] for e in m.io if e[1] in (0xCFFF, 0xC600)][-2:] == [0xCFFF, 0xC600]
        assert bytes(m.main[b2:b2 + 256]) == boot_copy(orig, b2)[0]

def main():
    out = os.path.join(ROOT, 'roms', 'bootmenu'); os.makedirs(out, exist_ok=True)
    lines = []
    for ver in VERSIONS:
        rom, orig, info = patch(ver)
        check(ver, rom, orig, info)
        name = 'Laser128_%s_bootmenu.bin' % ver
        open(os.path.join(out, name), 'wb').write(rom)
        lines.append('%-28s crc32 %08x  sha256 %s' % (name, zlib.crc32(rom), hashlib.sha256(rom).hexdigest()))
        print(f"{ver}: key check ${info['key']:04X} (P ${info['p']:04X}, M ${info['m']:04X}), slot 7 test ${info['s7']:04X}; "
              f"KEYX {info['keyx']} bytes, BOOTSEL {info['sel']} bytes, menu body {info['body']} bytes; model checks passed")
        for n in info['notes'] or []: print('    boot copy:', n)
    open(os.path.join(out, 'CHECKSUMS.txt'), 'w').write('\n'.join(lines) + '\n')

if __name__ == '__main__':
    main()
