# Compatibility And Testing

## Installation

Stable target: PAL KERNAL 901486-07 and BASIC 901486-01. NTSC is supported only
by the separate experimental universal pair, not the stable build.
Keep backups of your originals. Stock CHARGEN remains the default; optional
[Character Fonts](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/wiki/Character-Fonts)
can replace it independently of BASIC/KERNAL. Use both 8 KB
images from the same variant folder: fixed BASIC calls helpers in its KERNAL.
The 16 KB combined image is BASIC first, KERNAL second, not an 8 KB chip image.

Standard BASIC V2 commands, tokens, free memory and entry addresses are retained.
No Microsoft BASIC-M6502 commands are included.

## Risks

- Software depending on original bugs can differ with fixes enabled.
- VAL uses more temporary stack space; unusually deep expressions need testing.
- Custom error handlers must respect the normal X-error-number convention.
- Collector shortcuts and reclaimed padding change instruction timing.
- Stock checksum diagnostics reject modified images. All-off images match stock.
- The rainbow writes startup cells, not a permanent overlay.
- Optional fonts alter text bitmaps; striped versions also change uppercase
  graphic $69 and its inverse. Bitmap-dependent or checksum-sensitive software
  may differ. Smooth versions retain stock graphics; lowercase remains stock.

Address preservation does not prove that every program is compatible.

## Verification

Canonical tests: ten core groups, 2,275 cases including 1,409 label checks; five
BASIC groups, 192 cases. Checks cover tape bounds, RS-232 status/handshake/NUL,
VERIFY, transmit NMI injection, VAL overflow and ordinary results, custom
vectors, scratch/stack restoration, collector equivalence and padding paths.

Variant tests exercise all eight combinations: stock/default reproduction,
headings, screen/colour memory, cursor and memory pointers, VAL, collector
results/timing, status, tape behaviour, deliverable files and checksums.
Reset-to-input paths run with expanded and unexpanded RAM maps.

Tests execute ROM instructions using py65 1.2.0, static I/O and selected VIA
semantics. These are not full-machine timing or peripheral tests. Physical
hardware, real tape, real RS-232 and full-machine timing remain unverified.

User-supplied VICE screenshots on 2026-10-13 show the original smooth-tip fonts
at PAL-labelled startup with 28159 bytes free, and clean 5x7 in mixed-case mode.
This establishes only the displayed behaviour in those runs, not exact ROM
hashes, expansion settings, full compatibility or NTSC operation. Updated
uppercase striped-tip images remain locally checked, not VICE-tested.

## Provenance

The base is Lee Davison's *The almost completely commented Vic 20 ROM disassembly*,
V1.01 (2005-2012). Before modification it assembled byte-for-byte to the production
BASIC and PAL revision-7 KERNAL. Original references and attribution are preserved.
Their respective owners retain ownership; no new licence is asserted here.
