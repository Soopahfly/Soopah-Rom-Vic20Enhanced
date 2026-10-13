# Universal 8 KB KERNAL: Experiment 3

**Experimental, not the stable release.** One 8,192-byte KERNAL detects PAL or
NTSC. The matching BASIC is also 8,192 bytes. There is no bank switching or extra
ROM chip. Keep the original character ROM.

## Downloads And Installation

Download the pair from the
[Experiment 3 prerelease](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/releases/tag/universal-8k-exp3),
or a successful Actions run's separate `vic20-universal-8k-experimental` artifact.
The [Experiment 1 download](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/releases/tag/universal-8k-exp1)
and [Experiment 2 download](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/releases/tag/universal-8k-exp2)
remain available unchanged for comparison. Experiment 3 changes both images:
**install its new BASIC and KERNAL together**, not either earlier BASIC image.

Use `kernal-universal-experimental.bin` as KERNAL and
`basic-universal-experimental.bin` as BASIC. **Do not mix this pair with the stable
patched images.** Their VAL helper placement differs. The combined
`vic20-universal.bin` is 16 KB, BASIC first, and is not the KERNAL chip image.

For VICE's `xvic` executable, select the machine model before the custom ROMs:

```sh
xvic -model vic20pal -kernal kernal-universal-experimental.bin -basic basic-universal-experimental.bin
xvic -model vic20ntsc -kernal kernal-universal-experimental.bin -basic basic-universal-experimental.bin
```

These model and ROM options are documented in the
[VICE machine-specific manual](https://vice-emu.sourceforge.io/vice_7.html).
Use the same two files for both tests. Do a fresh reset after changing models;
do not use a snapshot made with different ROMs. VICE's own machine region still
needs choosing: a ROM cannot change the emulated video chip into another region.
Do not save over your working configuration until satisfied with the experiment.

Check the stepped V2.26 screen, 3583 bytes free on an unexpanded machine, keyboard,
cursor and SHIFT/Commodore character-set toggle. With RAM expansion, check the
memory count and typing as well. Try `PRINT 2+2`, a short BASIC program, and then
your usual software. Restore the original matched pair if anything behaves oddly.

To inspect detection in BASIC, `PRINT PEEK(678)` reads the region byte at $02A6:
values 128 or higher indicate PAL; values below 128 indicate NTSC. Only its sign
bit is meaningful, so the exact numeric value can vary.

## Experiment 3 Changes

The startup screen now shows **PAL** or **NTSC** in blue on row three, column six
(zero-based), directly beneath the memory count. The heading, stepped rainbow,
READY row six and typing row seven remain unchanged in every tested RAM map.
Five-digit memory counts wrap differently in the stock editor, so the label uses
the existing PLOT write path to select a fixed position rather than relying on
the cursor's position after printing the count.

Both ROMs still fit in exactly 8,192 bytes. No extra RAM is allocated. The label
selector uses BASIC's retired scratch-pop slot; PAL occupies the four bytes
recovered in Experiment 2, NTSC uses READST's skipped padding, and the print tail
uses the timer routine's skipped padding. A backward rainbow loop removes its
row-offset table while preserving all fifteen cells and their colours. It seeds
carry explicitly and never overflows its row pointers. BASIC's READY message
starts with CR, which refreshes the editor pointers before input; tests verify
the cursor stays disabled throughout the intervening boot stage.

All 1,409 original ROM addresses and public vectors remain fixed. The label and
drawing code are commented. Correctness fixes and the stock collector are
unchanged. Because the selector is now in BASIC, earlier experimental BASIC
images cannot be paired with this KERNAL. The full Experiment 1 KERNAL is retained
as a hash-verified regression fixture for independent IOINIT comparison.

## Experiment 2 Changes

The KERNAL remains exactly 8,192 bytes. Two pairs of identical VIA setup writes
are replaced with one shared write each: $913E clears both interrupt-enable
registers and $913B sets both auxiliary-control registers to $40. No shared
reads are used. Six instruction bytes are removed; a two-byte branch skips the
new padding, recovering four usable bytes at $FE35-$FE38. Experiment 3 uses
those bytes for the PAL string. All original label addresses stay fixed.

The branch is safe because the preceding serial-clock routine ORs bit 1 into A,
leaving Z clear. It also prevents running the padding. A repeatable frozen-raster
comparison measures five fewer CPU cycles in IOINIT than Experiment 1. This is
a small setup saving, not a noticeable general speed increase. Garbage collection
still uses the stock mover; this change does not restore that optimisation or
resolve the outstanding RS-232 receive-phase concern.

The decode was checked against the original Commodore
[early PAL schematic](https://www.zimmers.net/anonftp/pub/cbm/schematics/computers/vic20/324001_2.gif),
[cost-reduced schematic](https://www.zimmers.net/anonftp/pub/cbm/schematics/computers/vic20/251027l2.gif)
and [VICE's implementation](https://github.com/VICE-Team/svn-mirror/blob/fa7f1e1ec4f1b97d00c5b8117e12a592992f7262/vice/src/vic20/vic20.c).
Each VIA's positive chip-select input uses a separate address bit (A4/A5), so both
are selected for $913x writes within I/O0. The model now applies that decoding,
rejects shared reads, and compares each chip's ordered write trace and final state
against the immutable Experiment 1 image across 80 combinations of prior VIA
state, caller flags and video origin. Reviewing VICE source is not a VICE run.

### RAM Coverage

Reset-to-READY, complete screen/colour contents and typed-character checks now run
in PAL and NTSC at two starting raster phases for each of ten configurations.
Each screen is compared with the stable ROM booting in the same memory map.

| Expansion | BASIC Bytes Free |
| --- | --- |
| None | 3583 |
| 3 KB (RAM123) | 6655 |
| 8 KB (BLK1) | 11775 |
| 16 KB (BLK1/2) | 19967 |
| 24 KB (BLK1/2/3) | 28159 |
| 32 KB (BLK1/2/3/5) | 28159 |
| 35 KB (RAM123 + BLK1/2/3/5) | 28159 |
| 3 KB + 8 KB (RAM123 + BLK1) | 11775 |
| BLK2 only, with BLK1 absent | 3583 |
| BLK5 only | 3583 |

The last two cases check that disconnected expansion RAM is not incorrectly
counted by BASIC. These are simulated maps, not tests of physical cartridges.

## How It Fits

`scripts/build-universal.mjs` mechanically transforms the stable assembly with
checked, unique replacements. The output includes complete commented assembly,
labels, image sizes and hashes. Slot-size assertions prevent overflow, a change
allowlist rejects unexpected edits, and all 1,409 original ROM labels must retain
their addresses. Public jump slots and hardware vectors are regression-tested.

- Raster detection watches $9004 wrap. It temporarily disables interlace and
  restores the caller's $9000 after IOINIT. A frozen register defaults to PAL.
- Both regions retain the stock 60 Hz system tick. PAL uses $4826 and NTSC $4289.
- The VIC origins and both RS-232 lookup paths use the appropriate regional data.
- The four active keyboard pointers stay intact. Unselected pointer words and
  an unselected alternative table hold helper code and constants.
- Default CTRL keys 11..55 return FF through a guard instead of reading the
  reclaimed FF run. The guard checks the exact ROM pointer, not just CTRL state,
  so custom RAM keyboard tables still work.
- VAL cleanup uses $02A1-$02A4 instead of borrowing $FB-$FE. The region uses
  $02A6. These five previously unused system-RAM bytes do not reduce BASIC memory.
- The collector self-copy speed-up is omitted. Collection uses the stock mover;
  correctness fixes, the VAL repair and the stepped screen remain included.

Hardware detection/timing helpers remain in KERNAL. BASIC contains the mode-text
selector and relocated VAL cleanup; install this same experimental pair.
Stable `src/vic20-fixed.s`, `roms/` and all eight PAL permutations are unchanged.
The experimental Actions option currently builds this one fully patched layout,
not eight additional universal permutations.

## Verification And Risks

Simulated NMOS 6502 tests pass: 2,382 universal cases, 2,275 core regressions and
193 BASIC cases. This includes every PAL/NTSC raster phase, initial interlace,
frozen raster, register contracts, all baud codes, the actual receive-start
lookup, standard/custom keyboard tables, and reset-to-READY with typing in both
regions and all ten RAM layouts. Worst-case detector times in the model are 22,176 PAL
cycles and 16,998 NTSC cycles, approximately one frame.

**Not tested in VICE or on physical hardware.** Synthetic raster/VIA behaviour
does not validate all peripherals. Autostart cartridges can bypass normal KERNAL
initialisation; cartridge compatibility is not established.

Receive-start timer setup takes 96 PAL or 100 NTSC cycles, compared with stock
PAL's 20. Returning the right timer constants does not prove the first receive
sample is still correctly phased: these extra cycles need real serial tests and
possibly compensation. High baud rates are a particular risk. Tape and serial
bus operation have not been tested end to end.

Software that uses $02A1-$02A4/$02A6, directly reads the compressed CTRL bytes or
retired ROM tables, installs a selector expecting retired pointers, or checks ROM
checksums may be incompatible. Keeping addresses fixed does not preserve the
contents or timing of reclaimed private ROM data.

## Build Locally

With Node, cc65 and the project's Python test dependencies installed:

```sh
node scripts/build-universal.mjs
python tests/test_universal.py
VIC20_EXPERIMENTAL=1 python tests/test_basic.py
VIC20_EXPERIMENTAL=1 python tests/test_vic20.py
```

On PowerShell, set `$env:VIC20_EXPERIMENTAL='1'` before the two existing regression
scripts instead of the shell-prefix syntax. Clear that variable when returning
to stable tests. Generated files and reports are under `build/universal/`.

Build the stable canonical image before running its own test scripts. GitHub
Actions builds and tests both paths independently and uploads separate artifacts.
