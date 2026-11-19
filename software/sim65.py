"""Small 65C02 model for checking the test programs: main/aux RAM via RAMWRT, a scripted keyboard,
logged soft-switch accesses, and stubs for the monitor's HOME, COUT and RDKEY. Only the instructions the
programs use are modelled; anything else raises."""

class Sim:
    def __init__(s, code, org, keys=()):
        s.main, s.aux = bytearray(65536), bytearray(65536)
        s.main[org:org + len(code)] = code
        s.org = org; s.ramwrt = False; s.keys = list(keys); s.kbd = 0; s.io = []; s.out = []
        s.a = s.x = s.y = 0; s.sp = 0xFF; s.z = s.n = s.c = False
    def rd(s, a):
        if a == 0xC000:
            if not s.kbd & 0x80 and s.keys: s.kbd = s.keys.pop(0) | 0x80
            return s.kbd
        if 0xC000 < a < 0xC100:
            s.io.append(('R', a))
            if a == 0xC010: s.kbd &= 0x7F
            return 0
        return s.main[a]
    def wr(s, a, v):
        if 0xC000 <= a < 0xC100:
            s.io.append(('W', a, v))
            if a in (0xC004, 0xC005): s.ramwrt = a == 0xC005
            if a == 0xC010: s.kbd &= 0x7F
            return
        (s.aux if s.ramwrt and 0x200 <= a < 0xC000 else s.main)[a] = v
    def push(s, v): s.main[0x100 + s.sp] = v; s.sp = (s.sp - 1) & 0xFF
    def pull(s): s.sp = (s.sp + 1) & 0xFF; return s.main[0x100 + s.sp]
    def nz(s, v): v &= 0xFF; s.z, s.n = v == 0, bool(v & 0x80); return v
    def rts(s): lo = s.pull(); return ((s.pull() << 8) | lo) + 1
    def writes(s, skip=(0xC000, 0xC004, 0xC005, 0xC010)):
        return [e[1] for e in s.io if e[0] == 'W' and e[1] not in skip]
    def run(s, limit=3_000_000):
        pc = s.org; s.push(0xFF); s.push(0xFE)            # RTS to $FFFF ends the run
        for _ in range(limit):
            if pc == 0xFFFF: return
            if pc == 0xFC58:                               # HOME: clear text page 1
                for a in range(0x400, 0x800): s.main[a] = 0xA0
                pc = s.rts(); continue
            if pc == 0xFDED: s.out.append(chr(s.a & 0x7F)); pc = s.rts(); continue
            if pc == 0xFD0C: s.a = s.rd(0xC000); s.kbd &= 0x7F; pc = s.rts(); continue
            if pc == 0xFDDA: s.out.append('%02X' % s.a); pc = s.rts(); continue      # PRBYTE
            if pc == 0xFD8E: s.out.append('\r'); pc = s.rts(); continue             # CROUT
            op = s.main[pc]; b1 = s.main[pc + 1]; w = b1 | s.main[pc + 2] << 8
            zpi = lambda: s.main[b1] | s.main[(b1 + 1) & 0xFF] << 8
            if   op == 0x20: s.push((pc + 2) >> 8); s.push((pc + 2) & 0xFF); pc = w; continue
            elif op == 0x60: pc = s.rts(); continue
            elif op == 0x4C: pc = w; continue
            elif op == 0x7C: a = (w + s.x) & 0xFFFF; pc = s.main[a] | s.main[a + 1] << 8; continue
            elif op == 0x1A: s.a = s.nz(s.a + 1); n = 1
            elif op == 0xB2: s.a = s.nz(s.rd(zpi())); n = 2
            elif op == 0xDA: s.push(s.x); n = 1
            elif op == 0xFA: s.x = s.nz(s.pull()); n = 1
            elif op == 0x5A: s.push(s.y); n = 1
            elif op == 0x7A: s.y = s.nz(s.pull()); n = 1
            elif op == 0x08: s.push((s.n << 7) | (s.z << 1) | s.c | 0x30); n = 1
            elif op == 0x28: p = s.pull(); s.n, s.z, s.c = bool(p & 0x80), bool(p & 2), bool(p & 1); n = 1
            elif op in (0x78, 0x58, 0xEA): n = 1                                      # SEI CLI NOP
            elif op == 0xCA: s.x = s.nz(s.x - 1); n = 1
            elif op == 0x9D: s.wr(w + s.x, s.a); n = 3
            elif op == 0x99: s.wr(w + s.y, s.a); n = 3
            elif op == 0x9E: s.wr(w + s.x, 0); n = 3
            elif op == 0x5D: s.a = s.nz(s.a ^ s.rd(w + s.x)); n = 3
            elif op == 0xDD: v = s.rd(w + s.x); s.c = s.a >= v; s.nz(s.a - v); n = 3
            elif op == 0x06: v = s.main[b1]; s.c = bool(v & 0x80); s.main[b1] = s.nz(v << 1); n = 2
            elif op == 0xA9: s.a = s.nz(b1); n = 2
            elif op == 0xAD: s.a = s.nz(s.rd(w)); n = 3
            elif op == 0xA5: s.a = s.nz(s.main[b1]); n = 2
            elif op == 0xBD: s.a = s.nz(s.rd(w + s.x)); n = 3
            elif op == 0xB9: s.a = s.nz(s.rd(w + s.y)); n = 3
            elif op == 0xB1: s.a = s.nz(s.rd(zpi() + s.y)); n = 2
            elif op == 0xA2: s.x = s.nz(b1); n = 2
            elif op == 0xA6: s.x = s.nz(s.main[b1]); n = 2
            elif op == 0xA0: s.y = s.nz(b1); n = 2
            elif op == 0xA4: s.y = s.nz(s.main[b1]); n = 2
            elif op == 0x8D: s.wr(w, s.a); n = 3
            elif op == 0x85: s.main[b1] = s.a; n = 2
            elif op == 0x86: s.main[b1] = s.x; n = 2
            elif op == 0x84: s.main[b1] = s.y; n = 2
            elif op == 0x9C: s.wr(w, 0); n = 3
            elif op == 0x64: s.main[b1] = 0; n = 2
            elif op == 0x91: s.wr(zpi() + s.y, s.a); n = 2
            elif op == 0xE8: s.x = s.nz(s.x + 1); n = 1
            elif op == 0xC8: s.y = s.nz(s.y + 1); n = 1
            elif op == 0x88: s.y = s.nz(s.y - 1); n = 1
            elif op == 0xE6: s.main[b1] = s.nz(s.main[b1] + 1); n = 2
            elif op == 0x98: s.a = s.nz(s.y); n = 1
            elif op == 0x8A: s.a = s.nz(s.x); n = 1
            elif op == 0xA8: s.y = s.nz(s.a); n = 1
            elif op == 0xAA: s.x = s.nz(s.a); n = 1
            elif op == 0x48: s.push(s.a); n = 1
            elif op == 0x68: s.a = s.nz(s.pull()); n = 1
            elif op == 0x29: s.a = s.nz(s.a & b1); n = 2
            elif op == 0x09: s.a = s.nz(s.a | b1); n = 2
            elif op == 0x05: s.a = s.nz(s.a | s.main[b1]); n = 2
            elif op == 0x49: s.a = s.nz(s.a ^ b1); n = 2
            elif op == 0x4A: s.c = bool(s.a & 1); s.a = s.nz(s.a >> 1); n = 1
            elif op == 0x0A: s.c = bool(s.a & 0x80); s.a = s.nz(s.a << 1); n = 1
            elif op == 0x18: s.c = False; n = 1
            elif op == 0x38: s.c = True; n = 1
            elif op == 0x69: r = s.a + b1 + s.c; s.c = r > 255; s.a = s.nz(r); n = 2
            elif op == 0x65: r = s.a + s.main[b1] + s.c; s.c = r > 255; s.a = s.nz(r); n = 2
            elif op == 0xC9: s.c = s.a >= b1; s.nz(s.a - b1); n = 2
            elif op == 0xE0: s.c = s.x >= b1; s.nz(s.x - b1); n = 2
            elif op == 0xC0: s.c = s.y >= b1; s.nz(s.y - b1); n = 2
            elif op in (0xF0, 0xD0, 0x10, 0x30, 0xB0, 0x90, 0x80):
                take = {0xF0: s.z, 0xD0: not s.z, 0x10: not s.n, 0x30: s.n, 0xB0: s.c, 0x90: not s.c, 0x80: True}[op]
                pc = (pc + 2 + (b1 - 256 if b1 > 127 else b1)) & 0xFFFF if take else pc + 2; continue
            else: raise RuntimeError(f'opcode {op:02X} at {pc:04X} not modelled')
            pc += n
        raise RuntimeError('did not finish')
