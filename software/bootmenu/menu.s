; BOOT MENU body, shared by all ROM versions. The build fills in {VERSION}, the slot 5/7 labels {S5}/{S7} and
; the external-drive routine (EXTBOOT). Copied from a $C800 bank to RAM and run there, so it never depends on
; which $C800 bank is selected. 5 and 7 are offered only when the slot's ROM has the autostart boot signature
; (any card or built-in firmware: RAM disk, 3.5" drive, hard-disk controller...).
; Writes straight to text page 1 and reads the keyboard directly: no firmware I/O until a choice is made.
BASL    = $06
TMP     = $08           ; 2 bytes
INIT    = $FB2F
SETVID  = $FE93
SETKBD  = $FE89

START:  LDA $CFFF       ; release the $C800 window
        STA $C000       ; 80STORE off
        STA $C00C       ; 40 columns
        STA $C00E       ; primary character set
        STA $C051       ; text
        STA $C054       ; page 1
        JSR CLS
        LDX #0
PL:     LDA LINES,X     ; row, column, string offset; row $FF ends
        BMI PDONE
        JSR PRINT
        INX
        INX
        INX
        BRA PL
PDONE:  LDA #$C5         ; offer 5 and 7 only when their firmware answers
        JSR HASSLOT
        BCC PD7
        LDX #L5-LINES
        JSR PRINT
PD7:    LDA #$C7
        JSR HASSLOT
        BCC WREL
        LDX #L7-LINES
        JSR PRINT
WREL:   LDA $C010       ; wait until B is released (reading $C010 also clears the strobe)
        BMI WREL
KEY:    LDA $C000
        BPL KEY
        STA $C010
        CMP #$B1        ; 1
        BEQ INT
        CMP #$B2        ; 2
        BEQ EXT
        CMP #$B5        ; 5
        BEQ SL5
        CMP #$B7        ; 7
        BEQ SL7
        AND #$DF
        CMP #$C2        ; B
        BEQ BAS
        CMP #$CD        ; M
        BEQ MON
        BRA KEY
INT:    JSR CLS
        LDA $CFFF
        JMP $C600       ; internal drive: the normal slot 6 boot
EXT:    JSR CLS
        JMP EXTBOOT
SL5:    LDA #$C5
        BRA SLN
SL7:    LDA #$C7
SLN:    PHA
        JSR HASSLOT
        PLA
        BCC KEY
        PHA
        JSR CLS
        PLA
        STZ $00         ; as the autostart does: $00/$01 = $Cn00, JMP ($0000)
        STA $01
        LDA $CFFF
        JMP ($0000)
BAS:    JSR SETUP
        JMP $E000       ; Applesoft cold start
MON:    JSR SETUP
        JMP $FF69       ; monitor

SETUP:  JSR CLS
        JSR INIT
        JSR SETVID
        JMP SETKBD

; HASSLOT: A = $C5 or $C7. Carry set if the autostart signature is there ($Cn01=$20, $Cn03=$00, $Cn05=$03)
HASSLOT: STA TMP+1
        STZ TMP
        LDY #1
        LDA (TMP),Y
        CMP #$20
        BNE NOS
        LDY #3
        LDA (TMP),Y
        BNE NOS
        LDY #5
        LDA (TMP),Y
        CMP #$03
        BNE NOS
        SEC
        RTS
NOS:    CLC
        RTS

CLS:    LDA #$04        ; text page 1 = spaces
        STA BASL+1
        STZ BASL
        LDY #0
        LDA #$A0
CL1:    STA (BASL),Y
        INY
        BNE CL1
        INC BASL+1
        LDY BASL+1
        CPY #$08
        BEQ CL2
        LDY #0
        BRA CL1
CL2:    RTS

; PRINT: X = offset of a (row, column, string) entry in LINES
PRINT:  LDA LINES,X
        PHA
        LSR A           ; BASCALC
        AND #$03
        ORA #$04
        STA BASL+1
        PLA
        AND #$18
        BCC PR1
        ADC #$7F
PR1:    STA BASL
        ASL A
        ASL A
        ORA BASL
        STA BASL
        LDA LINES+1,X
        TAY
        LDA LINES+2,X
        PHX
        TAX
PR2:    LDA STRS,X
        BEQ PR3
        STA (BASL),Y
        INX
        INY
        BRA PR2
PR3:    PLX
        RTS

LINES:  .byte 3,8,S0-STRS
        .byte 4,8,S1-STRS
        .byte 7,6,S2-STRS
        .byte 9,6,S3-STRS
        .byte 11,6,S4-STRS
        .byte 13,6,S5-STRS
        .byte 20,3,S6-STRS
        .byte $FF
L5:     .byte 15,6,S5R-STRS
L7:     .byte 17,6,S7-STRS

STRS:
S0:     .aschi "LASER 128 BOOT MENU"
        .byte 0
S1:     .aschi "ROM {VERSION}"
        .byte 0
S2:     .aschi "1  INTERNAL DRIVE"
        .byte 0
S3:     .aschi "2  EXTERNAL DRIVE (DRIVE 2)"
        .byte 0
S7:     .aschi "{S7}"
        .byte 0
S5R:    .aschi "{S5}"
        .byte 0
S4:     .aschi "B  APPLESOFT BASIC"
        .byte 0
S5:     .aschi "M  MONITOR"
        .byte 0
S6:     .aschi "HOLD B DURING RESET FOR THIS MENU"
        .byte 0

; ---- FIXUP: the RAM boot copy (drive 2) jumps here instead of $0801, with sector 0 at $0800, X = $60.
; A ProDOS boot block ("38 B0 03 .. .. .. 86 43" = SEC / BCS / JMP / STX $43) saves X as the boot unit in $43 on
; each of its two entries (the second from the ROM's sector routine, always X = $60). Make the unit $E0 (slot 6,
; drive 2) and turn its STX $43 into NOPs, so ProDOS boots and stays on drive 2. Anything else is left alone.
FIXUP:  PHP
        PHA
        LDA $0801
        CMP #$38
        BNE FX9
        LDA $0802
        CMP #$B0
        BNE FX9
        LDA $0803
        CMP #$03
        BNE FX9
        LDA $0807
        CMP #$86
        BNE FX9
        LDA $0808
        CMP #$43
        BNE FX9
        LDA #$EA
        STA $0807
        STA $0808
        TXA
        ORA #$80
        STA $43
FX9:    PLA
        PLP
        JMP $0801

; ---- external drive boot: RAM copy of this ROM's slot 6 boot page (filled in by build.py)
{EXTBOOT}
