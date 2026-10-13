# Soopah ROM V2.26

Commented, address-preserving changes for VIC-20 BASIC 901486-01 and PAL KERNAL
901486-07. This is a modified derivative, not an official Commodore revision.
The language and token set remain standard BASIC V2.

- [Building ROMs](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/wiki/Building-ROMs): choose fixes, rainbow and heading.
- [Patch Notes](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/wiki/Patch-Notes): corrections and performance limits.
- [Compatibility And Testing](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/wiki/Compatibility-And-Testing): installation and verification.
- [Repository](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced)
- [Default ROMs](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/tree/main/roms)
- [Character Fonts](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/wiki/Character-Fonts): clean 5x7 and compact 5x6, each with smooth or striped tips.
- [Universal Experimental](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/wiki/Universal-Experimental): 8 KB PAL/NTSC pair for VICE testing.

All eight option combinations are supported. All three choices default to enabled.
The stable PAL build allocates no permanent RAM; an unexpanded machine still displays 3583 bytes
free. All 1,409 original ROM labels and public vectors retain their addresses.
Use BASIC and KERNAL from the same build folder. Stock CHARGEN remains the default;
the four optional character fonts are separate normal downloads on main.
Physical hardware testing remains outstanding.

The separate universal experiment keeps the bug fixes and screen, but uses stock
string-collection timing and reserves five system-RAM bytes. It has simulated
PAL/NTSC tests and limited user-supplied PAL startup screenshots from VICE, not
full compatibility or physical validation. Stable BASIC/KERNAL remain unchanged.
Experiment 3 adds the detected PAL/NTSC mode beneath the memory count and tests ten
RAM layouts. Experiments 1/2 remain available; install both new Experiment 3 images.
