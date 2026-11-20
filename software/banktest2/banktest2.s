; BANKTEST2 - $C800 bank select: every pair of slot-page accesses.
; For first = $C1..$C7 and second = none, $C1..$C7: read $CFFF, read $Cf00, read $Cs00 (if any), then
; checksum $C800-$CFFE (16-bit sum). All 56 tests run with interrupts off before anything is printed.
; Output: one row per first page (C1..C7), 8 columns (second: none, C1..C7), 4 hex digits each.
; Compare with tools/c800banks.py on the ROM in the machine (best: the bank-marker test ROM).
; Built twice by build.py: BANKTEST2 (INTCXROM as found) and BANKTEST2X ($C007 INTCXROM on during the tests).
PTR     = $06
SUM     = $08
F       = $0A           ; first page index 1-7
S       = $0B           ; second page index 0-7
K       = $0C           ; result index
HOME    = $FC58
COUT    = $FDED
PRBYTE  = $FDDA
CROUT   = $FD8E

START:  PHP
        SEI
{PRE}        STZ K
        LDA #1
        STA F
TF:     STZ S
TS:     LDA $CFFF
        STZ PTR
        LDA F
        ORA #$C0
        STA PTR+1
        LDA (PTR)
        LDA S
        BEQ T2
        ORA #$C0
        STA PTR+1
        LDA (PTR)
T2:     STZ SUM
        STZ SUM+1
        LDA #$C8
        STA PTR+1
        LDY #0
SL:     LDA (PTR),Y
        CLC
        ADC SUM
        STA SUM
        BCC SL1
        INC SUM+1
SL1:    INY
        BNE SL
        INC PTR+1
        LDA PTR+1
        CMP #$CF
        BNE SL
SL2:    LDA (PTR),Y     ; $CF00-$CFFE
        CLC
        ADC SUM
        STA SUM
        BCC SL3
        INC SUM+1
SL3:    INY
        CPY #$FF
        BNE SL2
        LDX K
        LDA SUM
        STA SUMLO,X
        LDA SUM+1
        STA SUMHI,X
        INC K
        INC S
        LDA S
        CMP #8
        BEQ NF
        JMP TS
NF:     INC F
        LDA F
        CMP #8
        BEQ DONE
        JMP TF
DONE:   LDA $CFFF
{POST}        PLP
        JSR HOME
        LDX #0
PT:     LDA TITLE,X
        BEQ PG
        JSR COUT
        INX
        BNE PT
PG:     STZ K
        LDA #1
        STA F
PR:     STZ S
PC:     LDX K
        LDA SUMHI,X
        JSR PRBYTE
        LDX K
        LDA SUMLO,X
        JSR PRBYTE
        INC K
        INC S
        LDA S
        CMP #8
        BEQ PN
        LDA #$A0
        JSR COUT
        BRA PC
PN:     JSR CROUT
        INC F
        LDA F
        CMP #8
        BNE PR
        RTS

TITLE:  .aschi "{TITLE}"
        .byte $8D
        .aschi "COL = 2ND PAGE: NONE,C1..C7"
        .byte $8D,$8D,0
SUMLO:  .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
        .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
SUMHI:  .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
        .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
