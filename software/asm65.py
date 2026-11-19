"""Tiny two-pass 65C02 assembler (enough for small test programs).

A program is a list of lines: 'LABEL:' , 'OP operand', '.byte $xx,...', '.org $xxxx'.
Operands: #$nn, $nn, $nnnn, $nnnn,X/Y, ($nn),Y, ($nn), label, #<label, #>label, label+n.
"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
from dis65c02 import M, L

OPS = {(mn, md): c for c, (mn, md) in M.items()}
BRANCH = {mn for (mn, md) in OPS if md == 'rel'}

def _term(t, sym, final):
    t = t.strip()
    if t.startswith('$'): return int(t[1:], 16)
    if t.isdigit(): return int(t)
    if re.fullmatch(r'[A-Za-z_]\w*', t):
        if t in sym: return sym[t]
        if final: raise KeyError('undefined ' + t)
        return 0xFFFF
    raise ValueError('bad operand ' + t)

def _val(tok, sym, final):
    """Expression: optional < or > (low/high byte), then terms joined by + and -."""
    tok = tok.strip(); pre = ''
    if tok[:1] in '<>': pre, tok = tok[0], tok[1:]
    parts = re.split(r'([+-])', tok)
    v = _term(parts[0], sym, final)
    for op, t in zip(parts[1::2], parts[2::2]):
        v = v + _term(t, sym, final) if op == '+' else v - _term(t, sym, final)
    if not final and v < 0: v = 0
    return (v & 0xFF) if pre == '<' else (v >> 8) & 0xFF if pre == '>' else v

def _mode(mn, opnd, sym, final):
    o = opnd.strip()
    if not o: return ('acc' if (mn, 'acc') in OPS else 'imp'), 0
    if o.upper() == 'A': return 'acc', 0
    if o.startswith('#'): return 'imm', _val(o[1:], sym, final)
    if mn in BRANCH: return 'rel', _val(o, sym, final)
    m = re.fullmatch(r'\((.+),[Xx]\)', o)
    if m: return ('iax' if mn == 'JMP' else 'izx'), _val(m.group(1), sym, final)
    m = re.fullmatch(r'\((.+)\),[Yy]', o)
    if m: return 'izy', _val(m.group(1), sym, final)
    m = re.fullmatch(r'\((.+)\)', o)
    if m:
        v = _val(m.group(1), sym, final)
        return ('ind' if mn == 'JMP' else 'izp'), v
    m = re.fullmatch(r'(.+),([XxYy])', o)
    idx = m.group(2).upper() if m else ''
    v = _val(m.group(1) if m else o, sym, final)
    zp = v < 0x100          # forward references are code labels (>= $100), so both passes agree
    if idx:
        md = ('zpx' if idx == 'X' else 'zpy') if zp and (mn, 'zp' + idx.lower()) in OPS else ('abx' if idx == 'X' else 'aby')
        return md, v
    return ('zp' if zp and (mn, 'zp') in OPS else 'abs'), v

def assemble(src, org):
    sym = {}
    for final in (False, True):
        pc, out = org, bytearray()
        for raw in src.splitlines():
            line = raw.split(';')[0].rstrip()
            if not line.strip(): continue
            m = re.match(r'\s*([A-Za-z_]\w*):(.*)', line)
            if m:
                sym[m.group(1)] = pc; line = m.group(2)
                if not line.strip(): continue
            m = re.match(r'\s*([A-Za-z_]\w*)\s*=\s*(\S+)', line)
            if m: sym[m.group(1)] = _val(m.group(2), sym, final); continue
            parts = line.split(None, 1)
            mn = parts[0].upper(); opnd = parts[1] if len(parts) > 1 else ''
            if mn == '.WORD':
                for t in opnd.split(','):
                    v = _val(t, sym, final); out += bytes((v & 0xFF, (v >> 8) & 0xFF))
                pc = org + len(out); continue
            if mn == '.BYTE':
                for t in opnd.split(','): out.append(_val(t, sym, final) & 0xFF)
                pc = org + len(out); continue
            if mn == '.ASCHI':                     # high-bit ASCII string (no terminator)
                s = re.fullmatch(r'\s*"(.*)"\s*', opnd).group(1)
                out += bytes(ord(c) | 0x80 for c in s); pc = org + len(out); continue
            md, v = _mode(mn, opnd, sym, final)
            if (mn, md) not in OPS: raise ValueError(f'no {mn} {md}: {raw}')
            out.append(OPS[(mn, md)])
            if md == 'rel':
                d = v - (pc + 2)
                if final and not -128 <= d <= 127: raise ValueError('branch out of range: ' + raw)
                out.append(d & 0xFF)
            elif L[md] == 2: out.append(v & 0xFF)
            elif L[md] == 3: out += bytes((v & 0xFF, (v >> 8) & 0xFF))
            pc = org + len(out)
    return bytes(out), sym
