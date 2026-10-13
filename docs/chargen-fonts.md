# Optional CHARGEN Fonts

These optional main-repository downloads do not replace the default ROMs. They change the
separate 4096-byte character ROM, not BASIC or KERNAL, and consume no additional
BASIC memory or KERNAL ROM space.

## Designs

- `clean-5x7`: narrower, hand-drawn uppercase letters and digits.
- `compact-5x6`: narrower and shorter letters, with more white space below them.

Both retain eight-by-eight character cells, 22 screen columns and the existing
startup positions. They change A-Z, 0-9 and the full stop in both character
banks, together with their reverse-video partners. Lowercase letters, all other
punctuation, PETSCII graphics, spaces, cursor and rainbow shapes remain stock.
The mixed-case font is therefore deliberately unfinished: lowercase remains
the original design.

## Build And Preview

The stock 901460-03 image is included as `reference/characters.901460-03.bin`,
from <https://www.zimmers.net/anonftp/pub/cbm/firmware/characters/vic20.bin>.
Its SHA256 is `bda280726cfe069ca70ef5e2f2d95a29f69d3950c859a12e6979464963fcf502`.
Build the stable ROM using `node scripts/build.mjs`, install Pillow, then
run `python scripts/play-chargen.py --check-published` to rebuild and verify
the downloadable images byte for byte.
Use `--universal` to preview the universal build instead; this requires its
existing build outputs. Both preview choices produce identical CHARGEN binaries.

Outputs are in `build/chargen/`: two optional `.bin` files, individual screen
previews, `comparison.png`, and `report.json` with hashes and validation details.

The default preview runs the stable PAL ROM's reset instructions using the
existing test RAM map. The optional universal preview uses a static raster,
which triggers the detector's PAL fallback.
It renders the resulting screen and colour RAM using the actual character ROM
bitmaps. RGB values are approximate, and the cursor is shown in its visible
blink phase. This is not a VICE screenshot or an analogue-video simulation.

## Checks And Compatibility

The builder asserts 4096-byte output, restricts modifications to the declared
glyph slots, and checks each changed inverse against its normal character.
Neither ROM has been tested in VICE or on physical hardware.

Published files and SHA256 checksums are in `roms/chargen/`. The main README
links directly to both images. No experimental BASIC/KERNAL pair is required
to use them.

For an emulator experiment, select either file as the VIC-20 character ROM;
leave the existing BASIC and KERNAL selections unchanged. Restore stock CHARGEN
to undo the font change. Keep these optional: older software that uses letters
or digits as graphics, reads their bitmaps, or depends on ROM checksums may
look different or behave differently. Unchanged character codes alone do not
prove complete compatibility.
