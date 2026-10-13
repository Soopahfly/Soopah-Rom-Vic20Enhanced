# Optional Character Fonts

These are normal main-repository downloads, not experimental prereleases.
Stock CHARGEN remains the default. Each optional image is 4096 bytes and replaces
only the character ROM; leave your selected BASIC/KERNAL pair unchanged.

## Downloads

| Font | Smooth Tips (Original) | Striped Tips |
| --- | --- | --- |
| Clean 5x7 | [Download](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/raw/refs/heads/main/roms/chargen/chargen-clean-5x7-smooth.bin) | [Download](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/raw/refs/heads/main/roms/chargen/chargen-clean-5x7.bin) |
| Compact 5x6 | [Download](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/raw/refs/heads/main/roms/chargen/chargen-compact-5x6-smooth.bin) | [Download](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/raw/refs/heads/main/roms/chargen/chargen-compact-5x6.bin) |

Clean 5x7 is the user's preferred design following the VICE comparison.
Smooth files are byte-identical to the original downloads. Existing unsuffixed
filenames select striped tips. All four hashes are listed in
[SHA256SUMS](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/blob/main/roms/chargen/SHA256SUMS).

## Previews

Smooth tips:

![Stock, clean and compact with smooth tips](https://raw.githubusercontent.com/Soopahfly/Soopah-Rom-Vic20Enhanced/main/docs/chargen/smooth-comparison.png)

Striped tips:

![Stock, clean and compact with striped tips](https://raw.githubusercontent.com/Soopahfly/Soopah-Rom-Vic20Enhanced/main/docs/chargen-comparison.png)

These previews render screen RAM produced by the stable PAL ROM. They use
approximate colours and a visible cursor phase, not a VICE capture.
[Individual previews and build instructions](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/blob/main/docs/chargen-fonts.md)
are included in the repository.

## Behaviour And Compatibility

Both fonts change uppercase A-Z, digits 0-9 and the full stop in both character
banks, with matching inverses. Lowercase and remaining punctuation stay stock.
Character cells remain 8x8; there are still 22 columns and no extra free memory.
No BASIC or KERNAL ROM space is consumed.

Smooth versions retain every stock graphic. Striped versions copy the stock
mixed-case stripe tile into uppercase screen code $69 and change its inverse
at $E9. Solid rainbow blocks and other graphics remain stock. The stripe tile
is a full patterned square, not a triangle. Mixed-case mode has striped tips
in every version, including smooth downloads.

For lowercase mode, enter `PRINT CHR$(14)`; `PRINT CHR$(142)` selects
uppercase/graphics again. A character-bank switch changes the whole displayed
screen, not just subsequently typed letters.

User-supplied VICE screenshots on 2026-10-13 show both original smooth fonts
at PAL-labelled startup with 28159 bytes free, and clean 5x7 in mixed-case mode.
They are limited visual checks, not confirmation of exact ROM hashes or a full
compatibility test. Updated uppercase striped-tip fonts, NTSC display behaviour
and physical machines remain unverified.

Software using text or graphics bitmaps directly, drawing with letters, or
checking ROM checksums can be affected. Restore the stock character ROM to undo
the change. Use the correct hardware ROM configuration when testing physically;
the downloadable bytes do not validate a replacement board's electrical setup.

## Rebuilding

Build the stable ROM, install Pillow, then run:

```sh
python scripts/play-chargen.py --check-published
```

The stock 901460-03 reference is hash-checked. The builder checks output size,
modification boundaries, inverse glyphs, all four published images, and the
original hashes of both smooth fonts. Outputs are under `build/chargen/`.
Optional `--universal` changes only the preview's startup ROM, not font bytes;
it needs the existing universal build outputs. Fonts are not currently included
in Actions artifacts or controlled by its BASIC/KERNAL switches.
