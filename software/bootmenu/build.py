#!/usr/bin/env python3
"""Build boot-menu ROMs for the original Laser 128 (ROM 2.7, 2.9, 3.0) and check them in the 65C02 model.

Patches (located by byte pattern, not fixed addresses):
  1. power-up key check  "AND #$1F / CMP #$10 / BEQ p / CMP #$0D / BEQ m": the CMP #$10/BEQ becomes JMP KEYX.
     KEYX (gap at $FAF5, 20 bytes): P and M as before; B clears $03F3/$03F4 so reset takes the cold-start path.
  2. end of cold start   "LDA $C701 / CMP #$20" (slot 7 card test): the LDA becomes JMP BOOTSEL.
     BOOTSEL (gap at $FEE9): if B is still held, select the menu bank ($CFFF, $C600, $C200 -> chip $7800)
     and JMP $C800; otherwise do the LDA $C701 and carry on.
  3. chip $7800 (empty): copier.s at $C800, menu body at $C900, copied to $1000 and run from RAM.
External drive (all versions): a page-aligned, relocated RAM copy of the slot 6 boot page with drive 2 selected
($C0EA -> $C0EB), the window release ($CFFF) changed to a slot 6 select, and the final JMP $0801 sent to FIXUP,
which makes a ProDOS boot block use unit $E0 (slot 6, drive 2) so ProDOS stays on drive 2.
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

def boot_copy(rom, base, fixup):
    """Drive-2 copy of the alternate slot 6 boot page for RAM at base (all versions):
    $C0EA -> $C0EB (drive 2), $CFFF -> $C600 (keep the slot 6 helper bank selected instead of releasing it),
    own-page references -> the copy, and the final JMP $0801 -> FIXUP."""
    page = bytearray(rom[0x4600:0x4700]); notes = []
    i = 0
    while i < 0x100:
        n, txt, md, w = dis1(rom, 0x4600 + i, 0x8000)
        if md in ('abs', 'abx', 'aby', 'ind') and i + n <= 0x100:
            new = None
            if w == 0xC0EA: new = 0xC0EB
            elif w == 0xCFFF: new = 0xC600
            elif 0xC600 <= w <= 0xC6FF: new = base + (w - 0xC600)
            elif w == 0x0801 and txt.startswith('JMP'): new = fixup
            if new is not None:
                page[i + 1], page[i + 2] = new & 0xFF, new >> 8
                notes.append('$C6%02X %s -> $%04X' % (i, txt, new))
        i += n
    assert any('JMP $0801' in x for x in notes) and any('$C0EA' in x for x in notes), notes
    return bytes(page), notes

def extboot(rom, base, fixup, pad=0):
    page, notes = boot_copy(rom, base, fixup)
    src = ('EXTBOOT: LDA $CFFF      ; clear the bank latches\n'
           '        LDA $C600       ; select the slot 6 bank for the boot code\'s $C800 helpers\n'
           '        JMP BOOT2\n')
    if pad: src += '        .byte ' + ','.join(['$00'] * pad) + '   ; page-align BOOT2 (same branch timing as in ROM)\n'
    src += 'BOOT2:\n'
    for k in range(0, 256, 16):
        src += '        .byte ' + ','.join('$%02X' % b for b in page[k:k + 16]) + '\n'
    return src, notes

def menu_src(version, s5, s7):
    return (open(os.path.join(HERE, 'menu.s')).read()
            .replace('{VERSION}', version).replace('{S5}', s5).replace('{S7}', s7))

def build_body(ver, rom):
    tmpl = menu_src(ver + 'X', '5  SLOT 5 CARD', '7  SLOT 7 CARD')
    src, _ = extboot(rom, 0x1E00, 0x1000)                     # pass 1: sizes only
    _, sym = asm65.assemble(tmpl.replace('{EXTBOOT}', src), BODY)
    pad = (-sym['BOOT2']) & 0xFF; base = sym['BOOT2'] + pad    # pass 2: page-aligned copy, real FIXUP
    src, notes = extboot(rom, base, sym['FIXUP'], pad)
    code, sym = asm65.assemble(tmpl.replace('{EXTBOOT}', src), BODY)
    assert sym['BOOT2'] == base and base & 0xFF == 0
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
    hb = lambda t: bytes(c | 0x80 for c in t)          # banner: "...ROM Version 3.0X" (same length)
    old = hb(b'LASER 128  ROM Version ' + ver.encode())
    b = bytes(rom).find(old); assert b > 0 and bytes(rom).count(old) == 1, 'banner'
    if rom[b + len(old)] == 0xA0:                      # 3.0: trailing space -> X
        new, banner = old + hb(b'X'), (b, len(old) + 1)
    else:                                              # 2.7 / 2.9: "128  ROM" -> "128 ROM", then X
        new, banner = hb(b'LASER 128 ROM Version ' + ver.encode() + b'X'), (b, len(old))
    assert rom[b + len(new)] == 0x8D
    rom[b:b + len(new)] = new
    body, sym, notes = build_body(ver, orig)
    copier, _ = asm65.assemble(open(os.path.join(HERE, 'copier.s')).read(), 0xC800)
    assert len(copier) <= 0x100 and all(b == 0xFF for b in orig[BANK:BANK + 0x800])
    rom[BANK:BANK + len(copier)] = copier
    rom[BANK + 0x100:BANK + 0x100 + len(body)] = body
    info = dict(key=cpu(k), p=p_target, m=m_target, cmp0d=cmp0d, s7=cpu(s7), keyx=len(keyx), sel=len(sel),
                body=len(body), sym=sym, notes=notes, body_bytes=body, banner=banner)
    return bytes(rom), orig, info

class Machine(Sim):
    """Main bank as memory; menu bank at $C800 (as RAM); $C010 bit 7 = key held."""
    def __init__(s, rom, keys=(), held=False):
        super().__init__(b'', 0x1000, keys); s.main[0xC100:0x10000] = rom[0x0100:0x4000]
        s.main[0xC800:0xD000] = rom[BANK:BANK + 0x800]; s.held = held
        for a in (0xFB2F, 0xFE93, 0xFE89): s.main[a] = 0x60   # INIT, SETVID, SETKBD stubs
    def rd(s, a):
        if a == 0xC010: s.io.append(('R', a)); s.kbd &= 0x7F; return 0x80 if s.held else 0
        if a in (0xCFFF, 0xC600, 0xC200, 0xC501, 0xC503, 0xC505, 0xC701, 0xC703, 0xC705): s.io.append(('R', a))
        return super().rd(a)

def check(ver, rom, orig, info):
    diff = sorted({i for i in range(len(rom)) if rom[i] != orig[i]})
    regions = [(info['key'] - 0xC000, 4), (info['s7'] - 0xC000, 3), (KEYX - 0xC000, info['keyx']),
               (BOOTSEL - 0xC000, info['sel']), (BANK, 0x800), info['banner']]
    t = bytes(c & 0x7F for c in rom[info['banner'][0]:info['banner'][0] + 28])
    assert t.startswith(b'LASER 128') and (ver + 'X\r').encode() in t, t
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
    def menu(keys, slots=(), stop=()):
        m = Machine(rom, keys=[ord(c) for c in keys])
        for n in slots: m.main[0xC001 + n * 0x100], m.main[0xC003 + n * 0x100], m.main[0xC005 + n * 0x100] = 0x20, 0x00, 0x03
        pc = m.run(start=0xC800, stop=set(stop), limit=2_000_000); return m, pc
    m, pc = menu('1', stop={0xC600})
    assert pc == 0xC600
    scr = lambda m, y: bytes(c & 0x7F for c in m.main[0x400 + (y & 7) * 0x80 + (y >> 3) * 0x28:][:40]).decode()
    # screen was cleared at the end (CLS before booting), so check the menu text on runs that wait:
    for slots in ((), (5,), (7,), (5, 7)):
        w = Machine(rom, keys=[])
        for n in slots: w.main[0xC001 + n * 0x100], w.main[0xC003 + n * 0x100], w.main[0xC005 + n * 0x100] = 0x20, 0x00, 0x03
        try: w.run(start=0xC800, limit=500000)
        except RuntimeError as e: assert 'did not finish' in str(e)
        assert 'LASER 128 BOOT MENU' in scr(w, 3) and ver in scr(w, 4) and '2  EXTERNAL DRIVE' in scr(w, 9), scr(w, 3)
        assert 'M  MONITOR' in scr(w, 13)
        assert ('5  SLOT 5 CARD' in scr(w, 15)) == (5 in slots) and ('7  SLOT 7 CARD' in scr(w, 17)) == (7 in slots)
    m, pc = menu('b', stop={0xE000}); assert pc == 0xE000
    m, pc = menu('M', stop={0xFF69}); assert pc == 0xFF69
    m, pc = menu('57b', stop={0xC500, 0xC700, 0xE000}); assert pc == 0xE000, 'no card: 5/7 ignored'
    for n in (5, 7):
        m, pc = menu(str(n), slots=(5, 7), stop={0xC500, 0xC700})
        assert pc == 0xC000 + n * 0x100 and m.main[0] == 0 and m.main[1] == 0xC0 + n and m.io[-1][1] == 0xCFFF
    b2, fx = info['sym']['BOOT2'], info['sym']['FIXUP']
    m, pc = menu('2', stop={b2}); assert pc == b2
    assert [e[1] for e in m.io if e[1] in (0xCFFF, 0xC600)][-2:] == [0xCFFF, 0xC600]
    assert bytes(m.main[b2:b2 + 256]) == boot_copy(orig, b2, fx)[0]
    # FIXUP: ProDOS boot block -> unit $E0 and STX $43 removed; other boot sectors untouched
    prodos = bytes.fromhex('0138b0034c32a18643c903')
    for sector, is_pd in ((prodos, True), (bytes.fromhex('01a527c909d018a52b'), False)):
        m = Machine(rom); m.main[0x1000:0x1600] = info['body_bytes'][:0x600].ljust(0x600, b'\0')
        m.main[0x0800:0x0800 + len(sector)] = sector; m.main[0x43] = 0x11; m.x = 0x60; m.y = 0x5A; m.c = True
        assert m.run(start=fx, stop={0x0801}) == 0x0801 and m.x == 0x60 and m.y == 0x5A and m.c
        if is_pd: assert m.main[0x43] == 0xE0 and m.main[0x807:0x809] == b'\xea\xea'
        else: assert m.main[0x43] == 0x11 and bytes(m.main[0x800:0x800 + len(sector)]) == sector

# ---- ROM 6.0 (Laser 128EX) ----------------------------------------------------------------------------------
# 6.0 has no free 2K bank, and its power-up code differs, so it has its own patch (each patch site is
# checked for the expected bytes before patching):
#   $F9BB JSR $FA17   (end of the power-up key table search: A = key AND $1F) -> JSR KEYB (B forces a cold start)
#   $F9CE JSR $CE7C   (cold start: banner, then WAITS FOR THE KEY TO BE RELEASED) -> JSR BOOTSEL. BOOTSEL checks
#                     for B *before* that wait; with B it runs $CE7C itself, finishes the cold start's STA $C006,
#                     and enters the menu. (A check at $F9DA, just before the autostart scan, never sees B: by
#                     then it has been released. That was the first 6.0X build's bug.)
#   chip $791F-$7CFF  free tail of the $C800 bank selected by $CFFF, $C600 (chip $7800, the slot 6 helper bank):
#                     copier at $C91F, then the body: the drive-2 boot page (runs at $1000) and menu.s ($1100).
V60 = dict(file='Laser128_6.0.bin', key=0xF9BB, cold=0xF9CE,
           keyb=0xF758, sel=0xF1AB, stub=0xF209, free=(0x791F, 0x7D00))
COPY60 = 0xC800 + 0x791F - BANK
def gap_free(rom, addr, n): o = addr - 0xC000; return all(b == 0xFF for b in rom[o:o + n])

def build_body60(rom):
    tmpl = menu_src('6.0X', '5  SLOT 5 (RAM DISK OR CARD)', '7  SLOT 7 (3.5 INCH OR CARD)')
    ext = 'EXTBOOT: LDA $CFFF      ; clear the bank latches\n        LDA $C600       ; slot 6 helper bank\n        JMP $1000\n'
    code, sym = asm65.assemble(tmpl.replace('{EXTBOOT}', ext), 0x1100)
    page, notes = boot_copy(rom, 0x1000, sym['FIXUP'])
    sym['BOOT2'] = 0x1000
    return page + code, sym, notes

def patch60():
    rom = bytearray(open(os.path.join(ROOT, 'roms', V60['file']), 'rb').read()); orig = bytes(rom)
    o = lambda a: a - 0xC000
    assert rom[o(V60['key']):o(V60['key']) + 3] == b'\x20\x17\xfa', 'key search end'
    assert rom[o(V60['cold']):o(V60['cold']) + 3] == b'\x20\x7c\xce', 'cold start banner call'
    assert rom[o(V60['cold']) + 3:o(V60['cold']) + 12] == bytes.fromhex('8d06c06400a9c88501'), 'cold start tail'
    keyb, _ = asm65.assemble('        CMP #$02\n        BNE K1\n        STZ $03F3\n        STZ $03F4\nK1:     JMP $FA17\n', V60['keyb'])
    stub, _ = asm65.assemble(f'        JSR $CE7C       ; banner + wait for release, as normal\n        PLA\n        PLA\n'
                             f'        STA $C006       ; as the cold start does next\n'
                             f'        LDA $CFFF\n        LDA $C600\n        JMP ${COPY60:04X}\n', V60['stub'])
    sel, _ = asm65.assemble(f'        LDA $C010\n        BPL NORM\n        LDA $C000\n        AND #$1F\n        CMP #$02\n'
                            f'        BNE NORM\n        JMP ${V60["stub"]:04X}\nNORM:   JMP $CE7C\n', V60['sel'])
    assert len(keyb) <= 17 and len(sel) <= 23 and len(stub) <= 23
    for addr, blob in ((V60['keyb'], keyb), (V60['sel'], sel), (V60['stub'], stub)):
        assert gap_free(rom, addr, len(blob)), 'gap not free'; rom[o(addr):o(addr) + len(blob)] = blob
    rom[o(V60['key']) + 1:o(V60['key']) + 3] = bytes((V60['keyb'] & 0xFF, V60['keyb'] >> 8))
    rom[o(V60['cold']) + 1:o(V60['cold']) + 3] = bytes((V60['sel'] & 0xFF, V60['sel'] >> 8))
    hb = lambda t: bytes(c | 0x80 for c in t)
    old = hb(b'LASER 128 ROM  Version 6.0'); b = bytes(rom).find(old)
    assert b > 0 and bytes(rom).count(old) == 1 and rom[b + len(old)] == 0x8D, 'banner'
    rom[b:b + len(old)] = hb(b'LASER 128 ROM Version 6.0X'); banner = (b, len(old))
    body, sym, notes = build_body60(orig)
    f0, f1 = V60['free']; src = COPY60 + 0  # copier, then body
    pages = (len(body) + 255) // 256
    cop_src = lambda start: (f'SRC     = $06\nDST     = $08\n        LDA #<{start}\n        STA SRC\n        LDA #>{start}\n'
               f'        STA SRC+1\n        STZ DST\n        LDA #$10\n        STA DST+1\n        LDX #{pages}\n        LDY #0\n'
               f'CP:     LDA (SRC),Y\n        STA (DST),Y\n        INY\n        BNE CP\n        INC SRC+1\n        INC DST+1\n'
               f'        DEX\n        BNE CP\n        JMP $1100\n')
    cop, _ = asm65.assemble(cop_src(0), COPY60); start = COPY60 + len(cop)
    cop, _ = asm65.assemble(cop_src(start), COPY60); assert COPY60 + len(cop) == start
    assert f0 + len(cop) + len(body) <= f1, 'menu does not fit: %d bytes over' % (f0 + len(cop) + len(body) - f1)
    assert start + pages * 256 <= 0xCF00, 'copier would read $CFxx'
    assert all(x == 0xFF for x in orig[f0:f1])
    rom[f0:f0 + len(cop)] = cop; rom[f0 + len(cop):f0 + len(cop) + len(body)] = body
    info = dict(keyb=len(keyb), sel=len(sel), stub=len(stub), cop=len(cop), body=len(body), sym=sym, notes=notes,
                body_bytes=body, banner=banner, room=f1 - f0 - len(cop) - len(body))
    return bytes(rom), orig, info

class Machine60(Sim):
    """6.0 main bank; $C800-$CFFF = chip $7800 (slot 6 helper bank); $C010 bit 7 = key held."""
    def __init__(s, rom, keys=(), held=False):
        super().__init__(b'', 0x1000, keys); s.main[0xC100:0x10000] = rom[0x0100:0x4000]
        s.main[0xC100:0xC800] = rom[0x4100:0x4800]          # slot pages as seen with $C006 (slot ROMs)
        s.main[0xC800:0xD000] = rom[BANK:BANK + 0x800]; s.held = held
        for a in (0xFB2F, 0xFE93, 0xFE89): s.main[a] = 0x60
    def rd(s, a):
        if a == 0xC010: s.io.append(('R', a)); s.kbd &= 0x7F; return 0x80 if s.held else 0
        if a == 0xBFFE: s.io.append(('R', a)); s.held = False
        if a in (0xCFFF, 0xC600, 0xC501, 0xC503, 0xC505, 0xC701, 0xC703, 0xC705): s.io.append(('R', a))
        return super().rd(a)

def check60(rom, orig, info):
    diff = sorted({i for i in range(len(rom)) if rom[i] != orig[i]})
    o = lambda a: a - 0xC000
    regions = [(o(V60['key']) + 1, 2), (o(V60['cold']) + 1, 2), (o(V60['keyb']), info['keyb']),
               (o(V60['sel']), info['sel']), (o(V60['stub']), info['stub']), (V60['free'][0], V60['free'][1] - V60['free'][0]),
               info['banner']]
    assert all(any(a <= i < a + n for a, n in regions) for i in diff), 'unexpected change'
    t = bytes(c & 0x7F for c in rom[info['banner'][0]:info['banner'][0] + 27]); assert t == b'LASER 128 ROM Version 6.0X\r', t
    # key search end: B clears the power-up bytes and goes on to $FA17; other keys leave them
    for key, clear in ((0x02, True), (0x01, False), (0x42, False)):
        m = Machine60(rom); m.main[0x3F3], m.main[0x3F4] = 0x12, 0x34; m.a = key
        assert m.run(start=V60['key'], stop={0xFA17}) == 0xFA17
        assert ((m.main[0x3F3], m.main[0x3F4]) == (0, 0)) == clear, key
    # cold start: $CE7C prints the banner and waits until the key is released (modelled: reading $BFFE releases
    # it). B held at $F9CE -> $CE7C runs, then STA $C006, the bank select, and the copier. Otherwise back to $F9D1.
    def cold(held, kbd):
        m = Machine60(rom, held=held); m.kbd = kbd
        m.main[0xCE7C:0xCE80] = bytes.fromhex('adfebf60')           # LDA $BFFE / RTS
        s0 = m.sp; pc = m.run(start=V60['sel'], stop={COPY60}); return m, pc, s0  # run's own return = the JSR's
    m, pc, s0 = cold(True, 0xC2); assert pc == COPY60, hex(pc)
    assert ('R', 0xBFFE) in m.io, 'banner/wait routine ran'
    seq = [e[1] for e in m.io if e[1] in (0xBFFE, 0xC006, 0xCFFF, 0xC600)]
    assert seq[-4:] == [0xBFFE, 0xC006, 0xCFFF, 0xC600], seq
    assert m.sp == s0 and not m.held, 'return address dropped'
    for held, kbd in ((False, 0xC2), (True, 0xD0)):          # $CE7C reached by tail call, returns to the caller
        m, pc, s0 = cold(held, kbd); assert pc != COPY60 and ('R', 0xBFFE) in m.io, (held, kbd)
        assert not any(e[1] in (0xC006, 0xCFFF, 0xC600) for e in m.io), 'normal path untouched'
    # and the hook site itself: JSR BOOTSEL
    assert rom[o(V60['cold']):o(V60['cold']) + 3] == bytes((0x20, V60['sel'] & 0xFF, V60['sel'] >> 8))
    def menu(keys, slots=(), stop=()):
        m = Machine60(rom, keys=[ord(c) for c in keys])
        for n in (5, 7):
            base = 0xC000 + n * 0x100
            m.main[base + 1], m.main[base + 3], m.main[base + 5] = (0x20, 0x00, 0x03) if n in slots else (0xA9, 0xA9, 0x55)
        return m, m.run(start=COPY60, stop=set(stop), limit=3_000_000)
    scr = lambda m, y: bytes(c & 0x7F for c in m.main[0x400 + (y & 7) * 0x80 + (y >> 3) * 0x28:][:40]).decode()
    for slots in ((), (5, 7)):
        w = Machine60(rom)
        for n in (5, 7):
            base = 0xC000 + n * 0x100
            w.main[base + 1], w.main[base + 3], w.main[base + 5] = (0x20, 0x00, 0x03) if n in slots else (0xA9, 0xA9, 0x55)
        try: w.run(start=COPY60, limit=400000)
        except RuntimeError as e: assert 'did not finish' in str(e)
        assert 'LASER 128 BOOT MENU' in scr(w, 3) and '6.0X' in scr(w, 4) and '2  EXTERNAL DRIVE' in scr(w, 9), scr(w, 4)
        assert ('5  SLOT 5 (RAM DISK OR CARD)' in scr(w, 15)) == (5 in slots)
        assert ('7  SLOT 7 (3.5 INCH OR CARD)' in scr(w, 17)) == (7 in slots)
    assert bytes(w.main[0x1000:0x1000 + info['body']]) == info['body_bytes'], 'copier'
    m, pc = menu('1', stop={0xC600}); assert pc == 0xC600 and m.io[-1][1] == 0xCFFF
    m, pc = menu('b', stop={0xE000}); assert pc == 0xE000
    m, pc = menu('M', stop={0xFF69}); assert pc == 0xFF69
    m, pc = menu('57b', stop={0xC500, 0xC700, 0xE000}); assert pc == 0xE000, 'no firmware: 5/7 ignored'
    for n in (5, 7):
        m, pc = menu(str(n), slots=(5, 7), stop={0xC500, 0xC700})
        assert pc == 0xC000 + n * 0x100 and m.main[0] == 0 and m.main[1] == 0xC0 + n and m.io[-1][1] == 0xCFFF
    fx = info['sym']['FIXUP']
    m, pc = menu('2', stop={0x1000}); assert pc == 0x1000
    assert [e[1] for e in m.io if e[1] in (0xCFFF, 0xC600)][-2:] == [0xCFFF, 0xC600]
    assert bytes(m.main[0x1000:0x1100]) == boot_copy(orig, 0x1000, fx)[0]
    prodos = bytes.fromhex('0138b0034c32a18643c903')
    for sector, is_pd in ((prodos, True), (bytes.fromhex('01a527c909d018a52b'), False)):
        m = Machine60(rom); m.main[0x1000:0x1000 + info['body']] = info['body_bytes']
        m.main[0x0800:0x0800 + len(sector)] = sector; m.main[0x43] = 0x11; m.x = 0x60; m.y = 0x5A; m.c = True
        assert m.run(start=fx, stop={0x0801}) == 0x0801 and m.x == 0x60 and m.y == 0x5A and m.c
        if is_pd: assert m.main[0x43] == 0xE0 and m.main[0x807:0x809] == b'\xea\xea'
        else: assert m.main[0x43] == 0x11 and bytes(m.main[0x800:0x800 + len(sector)]) == sector

def main():
    out = os.path.join(ROOT, 'roms', 'bootmenu'); os.makedirs(out, exist_ok=True)
    lines = []
    for ver in VERSIONS:
        rom, orig, info = patch(ver)
        check(ver, rom, orig, info)
        name = 'Laser128_%s_bootmenu.bin' % ver
        open(os.path.join(out, name), 'wb').write(rom)
        lines.append('%-28s crc32 %08x  sha256 %s' % (name, zlib.crc32(rom), hashlib.sha256(rom).hexdigest()))
        bt = bytes(c & 0x7F for c in rom[info['banner'][0]:info['banner'][0] + 30]).split(b'\r')[0].decode()
        print(f"{ver}: banner '{bt}'")
        print(f"{ver}: key check ${info['key']:04X} (P ${info['p']:04X}, M ${info['m']:04X}), slot 7 test ${info['s7']:04X}; "
              f"KEYX {info['keyx']} bytes, BOOTSEL {info['sel']} bytes, menu body {info['body']} bytes; model checks passed")
        for n in info['notes'] or []: print('    boot copy:', n)
    rom, orig, info = patch60(); check60(rom, orig, info)
    name = 'Laser128_6.0_bootmenu.bin'; open(os.path.join(out, name), 'wb').write(rom)
    lines.append('%-28s crc32 %08x  sha256 %s' % (name, zlib.crc32(rom), hashlib.sha256(rom).hexdigest()))
    print(f"6.0: KEYB {info['keyb']}, BOOTSEL {info['sel']}, stub {info['stub']}, copier {info['cop']}, body {info['body']} bytes "
          f"({info['room']} bytes spare in the bank); model checks passed")
    for n in info['notes']: print('    boot copy:', n)
    open(os.path.join(out, 'CHECKSUMS.txt'), 'w').write('\n'.join(lines) + '\n')

if __name__ == '__main__':
    main()
