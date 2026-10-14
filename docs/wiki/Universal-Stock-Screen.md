# Experiment 3: Stock Screen Plus Region

A separate experimental variant of the universal PAL/NTSC pair. All Experiment 3
features and correctness fixes remain; only startup presentation changes.
The original rainbow Experiment 3 release and stable PAL ROMs remain available.

## Screen

The heading is the original `**** CBM BASIC V2 ****`, not V2.26. There is no
rainbow or six-column indentation. The memory count retains its stock row and
alignment. PAL or NTSC appears in blue on the blank row between the memory count
and READY, at row three, column zero. READY stays on row four and typing starts
on row five (zero-based). Stock blue text, white background and cyan border remain.
The ROM still uses this project's Experiment 3 code despite the stock BASIC V2 heading.

![ROM-rendered stock startup plus PAL label](https://raw.githubusercontent.com/Soopahfly/Soopah-Rom-Vic20Enhanced/main/docs/universal-stock-screen.png)

## Downloads

[Separate prerelease](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/releases/tag/universal-8k-exp3-stock-screen):

- [KERNAL](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/releases/download/universal-8k-exp3-stock-screen/kernal-universal-experimental-stock-screen.bin)
- [BASIC](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/releases/download/universal-8k-exp3-stock-screen/basic-universal-experimental-stock-screen.bin)

Use both supplied 8192-byte images together. BASIC is byte-identical to the
rainbow Experiment 3 BASIC; if you already use that exact BASIC it need not be
replaced. Do not substitute stable or Experiment 1/2 BASIC. The combined 16 KB
image is not a single KERNAL chip image. CHARGEN selection is independent.

## Retained Features And Tests

PAL/NTSC detection, regional video origins, 60 Hz tick, regional RS-232 tables,
shared VIA writes, keyboard handling, all correctness fixes and VAL cleanup are
unchanged. The stock garbage collector remains, as in rainbow Experiment 3.
The same five reserved system-RAM bytes are used; BASIC free memory is unchanged.
Both ROMs remain 8 KB and all 1409 original addresses are preserved.

Tests compare every non-screen byte against rainbow Experiment 3, require
identical BASIC, and compare entire screen/colour RAM against production stock
with only the mode label added. PAL and NTSC are tested at two raster phases in
all ten existing RAM layouts, including five-digit counts and typing at the
original input position. Universal tests cover 2382 cases; BASIC tests cover 193.

This stock-screen variant has not been tested in VICE or physically. Existing
Experiment 3 serial timing, cassette, cartridge and compatibility caveats still
apply; see [Universal Experimental](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/wiki/Universal-Experimental).
Preview colours are approximate; the preview is ROM-rendered, not a VICE capture.

## Build

```sh
node scripts/build-universal.mjs
node scripts/build-universal.mjs --screen=stock
VIC20_UNIVERSAL_SCREEN=stock python tests/test_universal.py
VIC20_EXPERIMENTAL=1 VIC20_UNIVERSAL_SCREEN=stock python tests/test_basic.py
```

On PowerShell set the corresponding `$env:` variables before running tests.
Outputs are separate in `build/universal-stock/`; rainbow outputs stay in
`build/universal/`. The stock universal test needs both builds for byte comparison.
Actions builds/tests both screen choices whenever universal builds are enabled,
uploading a separate `vic20-universal-8k-stock-screen` artifact. Stable Actions
switches do not alter either universal build.
