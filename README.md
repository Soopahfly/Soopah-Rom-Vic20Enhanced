# Soopah-Rom-Vic20Enhanced

Commented, address-preserving corrections for the Commodore VIC-20 PAL KERNAL
901486-07, with the standard BASIC 901486-01 ROM.

The patched source builds to a 16 KB image at $C000-$FFFF. All 1,409 existing ROM
labels, the public KERNAL jump table and hardware vectors retain their addresses.
The BASIC ROM is unchanged. The patched KERNAL differs from the production image
at 129 bytes, including helper routines in existing spare ROM space.

## Corrections

1. **Tape filename overflow:** copy at most 187 characters into the 192-byte
   cassette buffer after its five-byte prefix. Longer names are truncated and the
   current filename length is updated. Names longer than 16 displayed characters
   remain supported.
2. **RS-232 transmit race:** write each queued byte before publishing its end
   pointer to the NMI consumer.
3. **RS-232 handshake inputs:** use user-port VIA $9110 rather than keyboard VIA
   $9120 in the transmit and OPEN checks.
4. **RS-232 status:** return the saved status before clearing it, preserving X/Y.
5. **RS-232 NUL input:** blocking input polls queue availability rather than
   rejecting zero-valued characters.
6. **VERIFY message:** identify direct commands using the execution pointer's high
   byte and suppress OK during program execution.

The assembly comments explain each correction. No additional RAM allocation or
performance optimisations are included.

## Files

| Location | Contents |
| --- | --- |
| `src/` | Complete commented assembly and linker configuration |
| `roms/` | Patched 8 KB KERNAL, unchanged 8 KB BASIC and combined 16 KB image |
| `reference/` | Original disassembly and unmodified production ROMs |
| `scripts/build.mjs` | Portable build, address checks and published-ROM comparison |
| `tests/test_vic20.py` | Focused NMOS 6502 emulator tests |
| `verification/` | Build differences and test results |

## Build And Test

Install Node.js, Python and the cc65 assembler toolchain. Make `ca65` and `ld65`
available on PATH, or set the `CA65` and `LD65` environment variables to their
executable paths. From the repository root:

```sh
python -m pip install -r requirements-test.txt
node scripts/build.mjs
python tests/test_vic20.py
```

Build outputs go to `build/`. The build checks that the resulting images match
the files in `roms/`, that existing ROM labels remain in place, and that changed
bytes stay within the defined patch ranges.

All seven test groups pass. They cover status and received-byte values 0-255,
filename lengths 0-255, handshake combinations, empty/full queues, pointer wrap,
direct/program VERIFY modes, and NMI injection at every transmit instruction
boundary. Each original failure is reproduced before its correction is checked.
The reported case total includes 1,409 ROM-label checks.

Tests execute real ROM instructions using py65 1.2.0. VIA interrupt-enable
semantics are modelled, and a synthetic NMI wrapper calls the actual ROM consumer.
These are routine-level tests, not full VIC-20 peripheral emulation. Full-machine
boot, real tape and real RS-232 operation have not been tested. This build targets
PAL systems; no NTSC build is supplied. Stock-ROM checksum diagnostics will not
recognise the modified KERNAL as an original ROM.

## Provenance

The base is Lee Davison's *The almost completely commented Vic 20 ROM disassembly*,
V1.01 (2005-2012), preserved with its original attribution in `reference/` and
`src/`. Before modification, its assembled output matched the downloaded
production BASIC 901486-01 and PAL KERNAL 901486-07 byte-for-byte.

- [Source archive](https://www.zimmers.net/anonftp/pub/cbm/src/vic20/index.html)
- [Production ROM archive](https://www.zimmers.net/anonftp/pub/cbm/firmware/computers/vic20/index.html)

This is a modified derivative, not an official Commodore ROM revision. The
original Commodore ROM code and Davison's annotations retain their respective
ownership; this repository does not assert a new licence over that material.
