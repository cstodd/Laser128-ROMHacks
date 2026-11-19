; BANKTEST - which $C800 ROM bank does each select sequence reach?
; Load at $6000; 6000G (monitor), CALL 24576 (BASIC) or BRUN BANKTEST (ProDOS).
;
; For each test: read $CFFF (release the $C800 window), read $Cn00, optionally read $Cm00, then add up
; $C800-$CFFE into a 16-bit checksum and keep the bytes at $C800-$C803. All tests run first, with interrupts
; off; printing comes afterwards because the screen firmware may itself switch banks.
; Output line: SEQUENCE  SUM  first four bytes.   Compare with tools/c800banks.py on the ROM dump.
PTR     = $06
SUM     = $08
T       = $0A           ; test index
HOME    = $FC58
COUT    = $FDED
PRBYTE  = $FDDA
CROUT   = $FD8E

START:  PHP
        SEI
        LDX #0
RUN:    STX T
        LDA $CFFF
        STZ PTR
        LDA SEQ1,X      ; first slot page ($C1-$C7, or 0 = none)
        BEQ R2
        STA PTR+1
        LDA (PTR)
R2:     LDX T
        LDA SEQ2,X      ; optional second slot page
        BEQ R3
        STA PTR+1
        LDA (PTR)
R3:     STZ SUM
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
SL2:    LDA (PTR),Y     ; last page: $CF00-$CFFE (reading $CFFF would release the window)
        CLC
        ADC SUM
        STA SUM
        BCC SL3
        INC SUM+1
SL3:    INY
        CPY #$FF
        BNE SL2
        LDX T           ; store results
        TXA
        ASL A
        ASL A
        TAY
        LDA $C800
        STA HEAD,Y
        LDA $C801
        STA HEAD+1,Y
        LDA $C802
        STA HEAD+2,Y
        LDA $C803
        STA HEAD+3,Y
        LDA SUM
        STA SUMLO,X
        LDA SUM+1
        STA SUMHI,X
        INX
        CPX #NTEST
        BEQ DONE
        JMP RUN
DONE:   LDA $CFFF
        PLP
        JSR HOME
        LDX #0
PL:     LDA TITLE,X
        BEQ PR
        JSR COUT
        INX
        BNE PL
PR:     LDX #0
PR1:    STX T
        LDA SEQ1,X      ; sequence, e.g. "C6 C1" or "-- --"
        JSR PSLOT
        LDA #$A0
        JSR COUT
        LDX T
        LDA SEQ2,X
        JSR PSLOT
        LDA #$A0
        JSR COUT
        JSR COUT
        LDX T
        LDA SUMHI,X
        JSR PRBYTE
        LDX T
        LDA SUMLO,X
        JSR PRBYTE
        LDA #$A0
        JSR COUT
        JSR COUT
        LDA T
        ASL A
        ASL A
        TAX
        LDY #4
PH:     LDA HEAD,X
        PHX
        PHY
        JSR PRBYTE
        LDA #$A0
        JSR COUT
        PLY
        PLX
        INX
        DEY
        BNE PH
        JSR CROUT
        LDX T
        INX
        CPX #NTEST
        BNE PR1
        RTS

PSLOT:  BEQ PS0         ; A = $Cn or 0
        JMP PRBYTE
PS0:    LDA #$AD        ; "--"
        JSR COUT
        JMP COUT

NTEST   = 15
SEQ1:   .byte 0,$C1,$C2,$C3,$C4,$C5,$C6,$C7,$C6,$C6,$C6,$C6,$C6,$C6,$C3
SEQ2:   .byte 0,0,0,0,0,0,0,0,$C1,$C2,$C3,$C4,$C5,$C7,$C6
TITLE:  .aschi "LASER 128 $C800 BANK TEST"
        .byte $8D
        .aschi "SEL   SUM   $C800-$C803"
        .byte $8D,0
SUMLO:  .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
SUMHI:  .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
HEAD:   .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
        .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
