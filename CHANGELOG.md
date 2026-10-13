# Changelog

## V2.26 - 2026-10-13

### ROM Corrections

- Limit cassette filenames to the 187-character capacity of the header buffer.
- Store RS-232 transmit bytes before publishing the queue pointer to the NMI.
- Read DSR/CTS from the user-port VIA in the transmit and OPEN handshake checks.
- Return RS-232 status before clearing it, preserving the caller's X/Y registers.
- Return received NUL bytes from blocking RS-232 input.
- Print successful VERIFY's OK message only in direct mode.

### Startup Screen

- Display `* CBM BASIC V2.26 *` in the existing 22-byte banner field.
- Draw a small rainbow in the top-right three columns, flat against the border.
- Use the existing character ROM and native red, yellow, green, cyan and blue.
- Retain the blue text, white background, cyan border and normal typing cursor.
- Preserve text rows and columns, dynamic free-memory output and ROM addresses.

### Scope And Verification

- Target the PAL 901486-07 KERNAL; the BASIC 901486-01 ROM remains unchanged.
- Preserve the standard BASIC V2 language and token set.
- Build and compare the published 8 KB images and combined 16 KB image.
- Pass ten focused test groups, including reset-to-input tests with static I/O
  and expanded/unexpanded RAM maps. All 1,409 existing ROM labels remain in place.
- Full-machine timing, real tape and real RS-232 operation remain untested.

Original source attribution is retained in the assembly and reference files.
