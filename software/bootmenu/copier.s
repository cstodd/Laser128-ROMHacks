; Runs at $C800 in the menu bank (chip $7800): copy the menu body from $C900-$CEFF to $1000-$15FF, then run it.
; (Stops before $CFFF, since reading $CFFF releases the window.)
SRC     = $06
DST     = $08
        STZ SRC
        LDA #$C9
        STA SRC+1
        STZ DST
        LDA #$10
        STA DST+1
        LDX #6
        LDY #0
CP:     LDA (SRC),Y
        STA (DST),Y
        INY
        BNE CP
        INC SRC+1
        INC DST+1
        DEX
        BNE CP
        JMP $1000
