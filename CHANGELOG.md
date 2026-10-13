# Changelog

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

- Display `* CBM BASIC V2.26 *` in the existing 22-byte banner field.
- Draw a small rainbow in the top-right three columns, flat against the border.
- Use the existing character ROM and native red, yellow, green, cyan and blue.
- Retain the blue text, white background, cyan border and normal typing cursor.
- Preserve text rows and columns, dynamic free-memory output and ROM addresses.

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
