# Changelog

## Documentation Refresh - 2026-10-13

- Add a wiki font page with all four downloads, both tip-style comparisons,
  checksums, rebuilding instructions and compatibility limits.
- Update wiki navigation, installation, build choices and patch notes so stock
  CHARGEN is a default rather than a requirement.
- Record the user's limited PAL VICE startup screenshots without claiming NTSC,
  full compatibility, exact emulator configuration or physical validation.

## Keep Both CHARGEN Tip Styles - 2026-10-13

- Restore the original clean 5x7 and compact 5x6 fonts as `-smooth.bin` downloads.
- Keep the striped versions at their existing URLs; all four are main downloads.
- Check smooth images against their original published hashes and retain stock
  graphics. Mixed-case mode keeps its original striped tile in every version.
- Add smooth previews, labelled download choices and all four checksums.

## Striped CHARGEN Rainbow Tips - 2026-10-13

- Give both optional fonts the stock mixed-case diagonal stripe tile at uppercase
  screen code $69, with a matching inverse at $E9. Retain the mixed-case tile.
- Match the textured rainbow tips preferred in the user's VICE screenshot.
- Keep all text glyphs, other graphics, stock CHARGEN, BASIC and KERNAL unchanged.
- Refresh both main downloads, checksums and stable startup previews.
- Previous font versions were user-tested at PAL startup in VICE. This new
  uppercase glyph change is locally checked, not yet VICE- or hardware-tested.

## Optional CHARGEN Fonts - 2026-10-13

- Add clean 5x7 and compact 5x6 character ROMs to the main download section.
- Keep stock CHARGEN as default; no changes to released BASIC or KERNAL images.
- Redraw uppercase, digits and full stop in both banks, with matching inverses.
  Preserve lowercase, remaining punctuation, PETSCII graphics and character codes.
- Include a reproducible builder, stock-ROM hash check, modification allowlist,
  inverse-glyph checks, output checksums and stable-ROM startup previews.
- Each image remains 4096 bytes; character cells and memory availability do not change.
- Fonts are optional normal downloads, not universal experimental prereleases.
  VICE, physical video readability and software compatibility remain unverified.

## Universal 8 KB Experiment 3 - 2026-10-13

- Display the detected PAL/NTSC mode in blue at row three, column six.
- Use a fixed editor position so five-digit memory counts cannot move the label.
- Preserve the V2.26 heading, all fifteen rainbow cells, colours, READY and typing rows.
- Fit the selector into BASIC's retired scratch-pop slot, strings into skipped
  KERNAL padding and the print tail into retired timer space.
- Tighten the rainbow loop to draw backwards and remove its row-offset table.
  Seed pointer-increment carry explicitly and retain original public addresses.
- Let READY's initial CR update the line pointers; test the cursor remains disabled
  until then and typing still reaches the correct screen/colour RAM locations.
- Keep both ROMs at 8,192 bytes and all 1,409 original addresses and vectors fixed.
- Change both BASIC and KERNAL: Experiment 3 must be installed as its own pair.
- Keep all correctness fixes, stock collector behaviour and RS-232 caveats unchanged.
- Pass 2,382 universal simulated cases, 2,275 core cases and 193 BASIC cases,
  including whole-screen/colour comparisons with only the mode label added.
- Preserve Experiments 1/2 and stable ROMs; supply separate new download images.
- VICE, physical machines and end-to-end peripheral tests remain outstanding.

## Universal 8 KB Experiment 2 - 2026-10-13

- Verify shared VIA selection against early and cost-reduced Commodore schematics
  and VICE source, rather than relying solely on the blog's suggested optimisation.
- Replace duplicate interrupt-disable and ACR writes with write-only $913E/$913B.
- Remove six instruction bytes, spend two on a proven-always-taken skip branch,
  and recover four usable bytes at $FE35-$FE38. Retain every original ROM label.
- Measure five fewer IOINIT cycles against Experiment 1 with a frozen raster;
  this is not a meaningful overall machine-speed improvement.
- Compare ordered per-chip writes, register/flag contracts and final VIA state
  against Experiment 1 across 80 prior-state/flag/origin cases. Reject shared reads.
- Test PAL/NTSC boot, complete screen and colours, free-memory counts and typing
  across ten RAM maps: none, 3/8/16/24/32/35 KB, 3+8 KB, BLK2-only and BLK5-only.
- Pass 2,342 universal simulated cases, 2,275 core regressions and 193 BASIC cases.
- Keep BASIC byte-identical to Experiment 1, KERNAL at 8,192 bytes, and the stock
  collector, bug fixes, rainbow and V2.26 banner unchanged.
- Publish a separate Experiment 2 prerelease; preserve Experiment 1 and stable ROMs.
- VICE runtime, physical hardware and end-to-end peripherals remain unverified.
  RS-232 receive-start overhead and possible sample-phase compensation are unchanged.

## Universal 8 KB Experiment 1 - 2026-10-13

- Assemble a universal KERNAL of exactly 8,192 bytes with a matching BASIC ROM.
- Detect PAL/NTSC from a raster wrap, forcing non-interlace during measurement.
- Restore the caller's VIC origin/interlace register after IOINIT detection.
- Bound frozen-raster waits and fall back to PAL rather than hanging startup.
- Select regional video origins, 60 Hz system timer and RS-232 baud constants,
  including receive-start NMI lookup, unsupported-code behaviour and caller carry.
- Preserve all 1,409 original label addresses, public jump slots and hardware vectors.
- Keep the correctness fixes and stepped V2.26 screen; revert only the collector
  self-copy speed-up to the stock mover to make room for VAL cleanup.
- Use $02A1-$02A4 for VAL cleanup and $02A6 for the region flag. BASIC free memory
  remains unchanged, but software using these formerly unused bytes can conflict.
- Reclaim unselected keyboard data and compress the default CTRL table's FF run.
  Standard keys and custom RAM tables are tested; direct reads of reclaimed ROM
  bytes and nonstandard keyboard selectors are not compatible by guarantee.
- Pass 2,230 universal-specific simulated cases, 2,275 core regression cases and
  193 BASIC cases. Detection takes up to roughly one frame in the tested model.
- Receive-start timer setup measures 96/100 CPU cycles (PAL/NTSC), versus stock
  PAL's 20. This timing change requires real RS-232 validation; no claim of full
  serial compatibility or corrected first-sample phase is made.
- Keep stable sources, published ROMs and eight PAL build permutations unchanged.
- Supply a separate experimental Actions artifact and commented generated source.
- VICE, physical hardware, real tapes, cartridges and serial devices are untested.

## V2.26 - 2026-10-13

### Selectable Builds And Wiki

- Add GitHub Actions switches for fixes, rainbow and the V2.26 heading.
- Support every combination, including exact stock ROMs and fixes on a stock screen.
- Build all eight variants automatically; allow one selection or all on manual runs.
- Supply labelled BASIC/KERNAL pairs, combined images, manifests and SHA-256 sums.
- Test each combination and verify requested download contents before upload.
- Add wiki pages covering build choices, patch notes and compatibility limits.

### ROM Corrections

- Limit cassette filenames to the 187-character capacity of the header buffer.
- Store RS-232 transmit bytes before publishing the queue pointer to the NMI.
- Read DSR/CTS from the user-port VIA in the transmit and OPEN handshake checks.
- Return RS-232 status before clearing it, preserving the caller's X/Y registers.
- Return received NUL bytes from blocking RS-232 input.
- Print successful VERIFY's OK message only in direct mode.
- Restore VAL's string terminator and execution pointer before overflow errors.
- Preserve custom BASIC error vectors and all borrowed $FB-$FE scratch bytes;
  unwind parser frames before error cleanup, without permanent RAM allocation.
- Skip garbage-collector self-copies for strings already in their final position.
  Retain the original descriptor scans and collection semantics.

### Startup Screen

- Display `CBM BASIC V2.26` at column six within the original 22-byte field.
- Draw a left-edge stepped rainbow, narrowing from five cells to one over five rows.
- Align the memory count with the heading and remove the framing asterisks.
- Put READY on row six and the typing cursor on row seven, below the stripes.
- Use the existing character ROM and native red, yellow, green, cyan and blue.
- Retain the blue text, white background, cyan border and normal typing cursor.
- Preserve dynamic free-memory output, original font and all ROM addresses.
- Keep complete stock-screen builds available when both screen switches are off.
- Render the preview from ROM-generated screen memory, not hand-positioned text.

### Scope And Verification

- Patch BASIC 901486-01 and PAL KERNAL 901486-07 as a matched pair.
- Preserve the standard BASIC V2 language and token set.
- Build and compare the published 8 KB images and combined 16 KB image.
- Pass fifteen focused test groups (2,275 core cases and 192 BASIC cases),
  including VAL overflow, custom vectors, collector differential tests and
  reset-to-input tests with static I/O
  and expanded/unexpanded RAM maps. All 1,409 existing ROM labels remain in place.
- Full-machine timing, real tape and real RS-232 operation remain untested.
- Packed-heap collector samples use 38.52% and 73.19% fewer emulated cycles;
  a fragmented sample uses 0.22% more. These are not general speed guarantees.

Original source attribution is retained in the assembly and reference files.
