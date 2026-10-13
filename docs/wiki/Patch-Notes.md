# Patch Notes

All corrections belong to the **Fixes** switch. Screen switches do not enable them.

## KERNAL

1. **Tape filename overflow:** cap the header copy at 187 characters after its
   five-byte prefix. Correct the active length when truncating.
2. **RS-232 transmit race:** store each byte before publishing its queue pointer
   to the NMI consumer.
3. **RS-232 handshake:** use user-port VIA $9110 instead of keyboard VIA $9120
   in transmit and OPEN checks.
4. **RS-232 status:** return saved status before clearing it, preserving X/Y.
5. **RS-232 NUL input:** wait for availability, rather than rejecting zero bytes.
6. **VERIFY:** print successful OK in direct mode, not during programs.

## BASIC

**VAL overflow:** restore the temporarily overwritten string-end byte before an
overflow error can leave program text, such as a closing quote, damaged.
Restore the execution pointer and original error vector, forwarding the original
X error number. Normal numeric results and overflow errors remain unchanged.
Unwind nested parser frames and restore all borrowed $FB-$FE bytes. Four extra
temporary stack bytes plus helper frames are used; no permanent RAM is allocated.

**String collection:** skip copies for strings already at their final position.
Descriptor handling and order remain unchanged. Repeated descriptor scans remain;
this is not a replacement algorithm.

| Emulated collector sample | Original cycles | Patched cycles | Change |
| --- | --- | --- | --- |
| 8 packed strings, 200 bytes | 36,262 | 9,723 | 73.19% fewer |
| 32 packed strings, 128 bytes | 173,508 | 106,676 | 38.52% fewer |
| 32 fragmented strings, 128 bytes | 174,395 | 174,779 | 0.22% more |

These are routine-level emulator measurements, not hardware or whole-program
speed promises. Short strings and fragmented heaps may gain little or incur overhead.

## Screen

The top-right rainbow uses eleven cells, existing character-ROM glyphs and
native red, yellow, green, cyan and blue. Blue text, white background, cyan
border and the normal blue cursor remain. The V2.26 heading fits the original
22-byte field. Both choices are independent of fixes.

Free memory is calculated normally. V2.26 is a build identifier, not a new
BASIC language or token set.
