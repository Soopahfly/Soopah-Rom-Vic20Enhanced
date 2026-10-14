import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import crypto from 'node:crypto';

// Experimental paired ROMs only. Never overwrite the stable source or images.
const root = fileURLToPath(new URL('../', import.meta.url));
const args = process.argv.slice(2);
if (args.some(arg => arg !== '--screen=stock')) throw new Error('Supported option: --screen=stock');
const stockScreen = args.includes('--screen=stock');
const out = path.join(root, stockScreen ? 'build/universal-stock' : 'build/universal');
fs.mkdirSync(out, { recursive: true });
let source = fs.readFileSync(path.join(root, 'src/vic20-fixed.s'), 'utf8').replaceAll('\r\n', '\n');
function replace(old, value) {
  if (source.split(old).length !== 2) throw new Error(`Expected exactly one source fragment: ${old}`);
  source = source.replace(old, value);
}
function region(start, end, value) {
  const begin = source.indexOf(`\n${start}\n`);
  const finish = source.indexOf(`\n${end}\n`, begin + 1);
  if (begin < 0 || finish < 0) throw new Error(`Missing region ${start}..${end}`);
  source = source.slice(0, begin) + '\n' + value.trim() + '\n' + source.slice(finish);
}
const pad = (end, fill = '$EA') => `.assert * <= $${end}, error, "Experimental slot overflow at ${end}"\n.res $${end}-*, ${fill}`;

// VAL is not reentrant (neither is BASIC's parser). Dedicated system RAM avoids
// borrowing $FB-$FE and their four stack saves, without reducing BASIC memory.
replace('\tJMP\tFIX_VAL_SAVE_SCRATCH\t; preserve caller scratch before installing cleanup', '\tJMP FIX_VAL_SETUP');
replace('; Carry selects normal return or the restored error vector after scratch pops.', '; Experimental VAL no longer needs the scratch-pop path.');
region('FIX_VAL_POP', 'LAB_D7E2', `FIX_VAL_POP
; BASIC's retired scratch-pop slot selects two strings on the same ROM page.
UNI_SHOW_REGION
    LDA #<UNI_PAL_TEXT
    LDY #>UNI_PAL_TEXT
    LDX UNI_REGION
    BMI UNI_REGION_SELECTED
    LDA #<UNI_NTSC_TEXT
UNI_REGION_SELECTED
    JMP UNI_PRINT_REGION
    .assert >UNI_PAL_TEXT = >UNI_NTSC_TEXT, error, "Region strings must share a page"
${pad('D7E2')}`);
replace('\tJSR\tFIX_GC_MOVE\t\t; avoid copying strings already in their final position', '\tJSR LAB_C3BF ; experimental fit uses the stock string mover');
replace('; Skip a self-copy when the string already ends at FRETOP. Retain the old\n; descriptor update convention: destination high byte is one page low.', '; Experimental fit: stock collection, with this slot assigned to VAL cleanup.');
const basicVal = `FIX_GC_MOVE = LAB_C3BF
; Reuse the former speed-up slot, NOT the BASIC checksum or RND seed.
FIX_VAL_ERROR
    TXA
    LDX $02A4
    TXS                 ; discard nested numeric-parser frames on overflow
    PHA
    JSR FIX_VAL_CLEAN
    JSR LAB_D7E2
    PLA
    TAX
    JMP (LAB_0300)      ; honour the caller's original error vector
FIX_VAL_CONVERT
    JSR LAB_0079
    JSR LAB_DCF3
    JSR FIX_VAL_CLEAN
    JMP LAB_D7E2
${pad('DF71')}`;
region('FIX_VAL_CLEAN', 'FIX_SCREEN_CHAR', `FIX_VAL_CLEAN
    LDA $02A1
    STA LAB_0300
    LDA $02A2
    STA LAB_0300+1
    LDY #0
    LDA $02A3
    STA (LAB_24),Y
    RTS
${pad('E672')}`);
region('FIX_VAL_SAVE_SCRATCH', 'FIX_SHIFTED_CHAR', `UNI_VIDEO
    PHP                 ; preserve C/V/D/I, just as the stock VIC write does
    CPX #3
    BCS UNI_VIDEO_STORE
    BIT UNI_REGION
    BMI UNI_VIDEO_STORE
    LDA UNI_ORIGINS-1,X
UNI_VIDEO_STORE
    PLP
    STA LAB_9000-1,X
    RTS
${pad('E815')}`);
replace('\tSTA\tLAB_9000-1,X\t; save byte to Vic chip', '\tJSR UNI_VIDEO ; PAL or NTSC origin, other VIC registers unchanged');
region('FIX_BOOT_RAINBOW', 'FIX_BOOT_HEADING', stockScreen ? `FIX_BOOT_RAINBOW
; Stock layout: label the blank row without moving READY or the input cursor.
; PLOT's write entry ignores carry; both calls recalculate editor pointers.
    LDX #3
    LDY #0
    JSR LAB_E50A+2
    JSR UNI_SHOW_REGION
    LDX #3
    LDY #0
    JSR LAB_E50A+2
    JMP LAB_C644
${pad('E96D')}` : `FIX_BOOT_RAINBOW
    LDX #3
    LDY #6
    JSR LAB_E50A+2      ; PLOT's write path: fixed row despite memory-count wrapping
    JSR UNI_SHOW_REGION ; returns screen page in A, with C clear
    STA $FC
    AND #3
    ORA #$94
    STA $FE
    LDY #0
    STY $FB
    STY $FD
    LDX #4
FIX_BOOT_ROW
    LDA FIX_BOOT_COLOURS,X
    STA $FF
    TXA
    TAY                 ; draw backwards; retain row width in X
    LDA #$69
    STA ($FB),Y         ; diagonal at the rightmost cell of each stripe
UNI_BOOT_PIXEL
    LDA $FF
    STA ($FD),Y
    DEY
    BMI UNI_BOOT_NEXT
    LDA #$A0
    STA ($FB),Y
    BMI UNI_BOOT_PIXEL  ; A=$A0 makes this an unconditional branch
UNI_BOOT_NEXT
    LDA $FB
    ADC #22             ; C starts clear; row bases 0..110 cannot overflow
    STA $FB
    STA $FD
    DEX
    BPL FIX_BOOT_ROW
    LDA #5
    STA LAB_D6
    ; Cursor stays disabled until input; READY's leading CR sets row-six pointers.
    JMP LAB_C644`);
region('FIX_VAL_ERROR', 'FIX_SHIFT_TOGGLE', `UNI_KEY_READ
    LDY LAB_CB
    LDA LAB_F5
    CMP #<LAB_EDA3
    BNE UNI_KEY_NORMAL
    LDA LAB_F6
    CMP #>LAB_EDA3
    BNE UNI_KEY_NORMAL
    BEQ UNI_KEY_RANGE   ; only the ROM CTRL table has a compressed FF run
${pad('EC00')}`);
replace('\tSTA\t$FD\t\t\t; save the string end byte, often a closing quote', '\tSTA $02A3 ; retain the original string end byte until cleanup');
// Only the four stock pointers are reachable with the ROM keyboard selector.
const pointers = source.indexOf('\nLAB_EC46\n');
// Find the second unshifted pointer, after the four active entries.
const firstActive = source.indexOf('\t.word\tLAB_EC5E\t\t; unshifted', pointers);
const unused = source.indexOf('\t.word\tLAB_EC5E\t\t; unshifted', firstActive + 1);
const keyTable = source.indexOf('\nLAB_EC5E\n', unused);
if (unused < 0 || keyTable < 0) throw new Error('Keyboard pointer layout changed');
source = source.slice(0, unused) + `; Retired pointer words: ROM selector only indexes 0,2,4,6.
UNI_KEY_RANGE
    CPY #11
    BCC UNI_KEY_NORMAL
    CPY #56
    BCS UNI_KEY_NORMAL
    LDA #$FF
    RTS
UNI_KEY_NORMAL
    LDA (LAB_F5),Y
    RTS
${pad('EC5E')}
` + source.slice(keyTable);
replace('LAB_EB74\n\tLDY\tLAB_CB\t\t; get saved key count\n\tLDA\t(LAB_F5),Y\t\t; get character from decode table', 'LAB_EB74\n\tJSR UNI_KEY_READ\n\tNOP');

region('LAB_ED69', 'LAB_EDA3', `LAB_ED69
; X must be zero on entry. IOINIT establishes it before this call.
UNI_DETECT
    TXA
    STA LAB_9000       ; force non-interlaced scanning before measuring a wrap
UNI_SAMPLE
    CMP $9004
    BEQ UNI_SAME
    BCC UNI_ADVANCE
    CMP #140           ; final raster/2 is about 130 NTSC or 155 PAL
    ROR A
UNI_STORE_REGION
    STA UNI_REGION     ; sign bit: PAL=1, NTSC=0
    LDX #0             ; IOINIT reuses zero for the next DDR setup
    RTS
UNI_SAME
    DEX
    BNE UNI_SAMPLE
    LDA #$80           ; frozen raster: bounded timeout, default to PAL
    BNE UNI_STORE_REGION
UNI_ADVANCE
    LDA $9004
    LDX #0             ; restart timeout whenever the raster advances
    BCC UNI_SAMPLE
UNI_NTSC_PREFIX
    .byte $68,$40      ; match stock lookup semantics for unsupported code zero
    .word $2792,$1A40,$11C6,$0E74,$0CEE,$0645,$02F1,$0146,$00B8,$0071,$002A
${pad('EDA3')}`);
region('LAB_EDA3', 'LAB_EDE4', `LAB_EDA3
    .byte $90,$1C,$9C,$1F,$12,$FF,$FF,$FF,$06,$FF,$12
; Keys 11..55 are all FF. UNI_KEY_READ supplies those values without reading
; these bytes as characters; custom keyboard pointers still read their own RAM.
UNI_TICK
    LDA UNI_REGION
    BMI UNI_PAL_TICK
    LDA #$89
    STA LAB_9124
    LDA #$42
    BNE UNI_TICK_HIGH
UNI_PAL_TICK
    LDA #$26
    STA LAB_9124
    LDA #$48
UNI_TICK_HIGH
    STA LAB_9125
    RTS                ; both regions use the stock 60 Hz system tick
UNI_BAUD_BYTE
    PHP                ; high-byte caller must retain the low-byte ASL carry
    CPX #24
    BCS UNI_PAL_BAUD
    LDA UNI_REGION
    BMI UNI_PAL_BAUD
    LDA UNI_NTSC_PREFIX,X
    BCC UNI_BAUD_RETURN ; CPX guaranteed C=0; saves a byte over JMP
UNI_PAL_BAUD
    LDA LAB_FF5C-2,X
UNI_BAUD_RETURN
    PLP
    RTS
${pad('EDDB')}
    .byte $05,$9F,$1E,$9E,$92,$FF,$FF,$FF,$FF`);
replace("; Retired transmit code holds VAL's conversion and normal cleanup path.", '; Retired transmit code holds the video-preserving detection wrapper.');
region('FIX_VAL_CONVERT', 'LAB_F102', `; IOINIT is callable without screen initialisation afterwards. Do not leave
; its caller's horizontal origin/interlace register altered by the measurement.
UNI_DETECT_PRESERVE
    LDA LAB_9000
    PHA
    JSR UNI_DETECT
    PLA
    STA LAB_9000
    RTS
${pad('F102')}`);
region('FIX_VAL_NORMAL', 'LAB_F279', `UNI_BAUD_HIGH
    INX
    JSR UNI_BAUD_BYTE
    DEX
    RTS
${pad('F279')}`);
region('FIX_VAL_SETUP', 'LAB_F834', `FIX_VAL_SETUP
    LDX #1
UNI_SAVE_VECTOR
    LDA LAB_0300,X
    STA $02A1,X
    DEX
    BPL UNI_SAVE_VECTOR
    JMP UNI_VAL_CHECKPOINT
${pad('F834')}`);
replace('\t.res\t$E4A0-*, $FF', `UNI_VAL_CHECKPOINT
    TSX
    STX $02A4
    JMP FIX_VAL_TERMINATE
${pad('E4A0')}`);

// A4/A5 select each VIA independently (Commodore schematics and VICE vic20.c).
// $913x writes select both, without the VIC. Never read these shared addresses.
// Interrupts stay disabled during detection; retain caller flags and final X=0.
region('LAB_FDF9', 'LAB_FE39', `LAB_FDF9
    LDA #$7F
    STA $913E          ; clear both interrupt-enable registers in one bus write
    LDA #$40
    STA $913B          ; both ACRs need the same T1 free-run configuration
    LDA #$FE
    STA LAB_911C
    LDA #$DE
    STA LAB_912C
    LDX #0
    STX LAB_9112
    STX LAB_9123
    STX LAB_911F
    PHP
    JSR UNI_DETECT_PRESERVE
    PLP
    DEX
    STX LAB_9122
    LDX #$80
    STX LAB_9113
    LDX #0
    JSR LAB_EF84
    LDA #$82
    STA LAB_911E
    JSR LAB_EF8D
    BNE LAB_FE39       ; EF8D ORs in bit 1, so Z is always clear on return
UNI_IOINIT_SPARE
    .assert * = $FE35, error, "Shared VIA writes must leave four bytes spare"
UNI_PAL_TEXT
    .byte "PAL",0
${pad('FE39')}`);
region('LAB_FE39', 'LAB_FE49', `LAB_FE39
    LDA #$C0
    STA LAB_912E
    JMP UNI_TICK
UNI_PRINT_REGION
    JSR LAB_CB1E        ; normal CHROUT applies text colour and RAM-layout mapping
    LDA LAB_0288
    CLC                 ; seed the rainbow's bounded pointer increments
    RTS
${pad('FE49')}`);
replace('\t.res\t$FE66-*, $EA\t\t; retain SETMSG and serial-status entry addresses', `UNI_NTSC_TEXT
    .byte "NTSC",0
${pad('FE66')}`);
// Both OPEN and the receive-start NMI use the regional table, not just transmit.
for (const [old, replacement] of [
  ['\tLDA\tLAB_FF5C-2,X\t; get timer constant low byte', '\tJSR UNI_BAUD_BYTE'],
  ['\tLDA\tLAB_FF5C-1,X\t; get timer constant high byte', '\tJSR UNI_BAUD_HIGH'],
  ['\tLDA\tLAB_FF5C-2,X\t; get baud count low byte', '\tJSR UNI_BAUD_BYTE'],
  ['\tLDA\tLAB_FF5C-1,X\t; get baud count high byte', '\tJSR UNI_BAUD_HIGH'],
]) replace(old, replacement);
// Four genuinely unused bytes before hardware vectors, not a public jump slot.
const unusedVectorBytes = source.lastIndexOf('\t.byte\t$FF,$FF,$FF,$FF\n');
if (unusedVectorBytes < source.indexOf('\nLAB_FFF3\n')) throw new Error('Missing vector padding');
source = source.slice(0, unusedVectorBytes) + 'UNI_ORIGINS\n\t.byte $05,$19,$FF,$FF\n' + source.slice(unusedVectorBytes + '\t.byte\t$FF,$FF,$FF,$FF\n'.length);
for (const obsolete of ['FIX_VAL_SAVE_SCRATCH', 'FIX_VAL_NORMAL']) replace(`.export ${obsolete}\n`, '');
region('FIX_GC_MOVE', 'LAB_DF71', basicVal);
source += '\nUNI_REGION = $02A6\n.export UNI_REGION, UNI_DETECT, UNI_DETECT_PRESERVE, UNI_VIDEO, UNI_TICK, UNI_BAUD_BYTE, UNI_BAUD_HIGH, UNI_KEY_READ, UNI_NTSC_PREFIX, UNI_IOINIT_SPARE, UNI_SHOW_REGION, UNI_PRINT_REGION\n';
if (stockScreen) {
  replace('\tJSR\tFIX_BOOT_HEADING\t\t; print heading and align the following memory count', '\tJSR LAB_CB1E ; stock memory-count alignment, star-framed V2.26 heading');
  // Shorten the framing stars, not the version, to retain the 22-column field.
  // One trailing space preserves the stock wrap/CR and subsequent row positions.
  region('LAB_E436', 'LAB_E44F', `LAB_E436\n; Stock layout, updated version, identical heading-field size.\n    .byte $93,"** CBM BASIC V2.26 ** ",$0D,$00`);
}
const generated = path.join(out, 'vic20-universal.s');
fs.writeFileSync(generated, '; EXPERIMENT 3: region label; use the matching experimental ROM pair.\n' + source);
function run(name, args) {
  const exe = process.env[name.toUpperCase()] || (process.platform === 'win32' ? `${name}.exe` : name);
  const result = spawnSync(exe, args, { encoding: 'utf8' });
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  if (result.error || result.status !== 0) throw result.error ?? new Error(`${name} failed`);
}
run('ca65', ['--cpu', '6502', '--feature', 'labels_without_colons', '-l', path.join(out, 'vic20-universal.lst'), '-o', path.join(out, 'vic20-universal.o'), generated]);
run('ld65', ['-C', path.join(root, 'src/vic20.cfg'), '-Ln', path.join(out, 'vic20-universal.labels'), '-o', path.join(out, 'vic20-universal.bin'), path.join(out, 'vic20-universal.o')]);
const binary = fs.readFileSync(path.join(out, 'vic20-universal.bin'));
if (binary.length !== 16384) throw new Error(`Wrong combined size: ${binary.length}`);
const labels = fs.readFileSync(path.join(out, 'vic20-universal.labels'), 'utf8');
let preservedLabels = 0;
for (const match of labels.matchAll(/^al\s+([0-9A-F]+)\s+\.LAB_([0-9A-F]{4})$/gm)) {
  if (parseInt(match[2], 16) < 0xc000) continue;
  if (parseInt(match[1], 16) !== parseInt(match[2], 16)) throw new Error(`Moved original label: ${match[0]}`);
  preservedLabels++;
}
if (preservedLabels !== 1409) throw new Error(`Missing original labels: ${preservedLabels}`);
const stable = fs.readFileSync(path.join(root, 'roms/vic20-fixed.bin'));
const allowed = [[0xd629,0xd62c], [0xd7cf,0xd7e2], [0xdf53,0xdf71], [0xe40f,0xe412],
  [0xe499,0xe4a0], [0xe5c8,0xe5cb], [0xe65e,0xe672], [0xe803,0xe815], [0xe929,0xe975],
  [0xeb74,0xeb78], [0xebf0,0xec00], [0xec1b,0xec38], [0xec4e,0xec5e],
  [0xed69,0xede4], [0xf0f6,0xf102], [0xf272,0xf279],
  [0xf4f6,0xf4f9], [0xf4fb,0xf4fe], [0xf825,0xf834], [0xfdf9,0xfe49],
  [0xfe60,0xfe66], [0xff3a,0xff3d], [0xff40,0xff43], [0xfff6,0xfff8]];
if (stockScreen) allowed.push([0xe436, 0xe44f]);
let changedBytes = 0;
for (let offset = 0; offset < binary.length; offset++) {
  if (binary[offset] === stable[offset]) continue;
  const address = 0xc000 + offset;
  if (!allowed.some(([start, end]) => start <= address && address < end)) {
    throw new Error(`Unexpected experimental modification at $${address.toString(16)}`);
  }
  changedBytes++;
}
const suffix = stockScreen ? '-stock-screen' : '';
const images = [[`basic-universal-experimental${suffix}.bin`, binary.subarray(0, 8192)], [`kernal-universal-experimental${suffix}.bin`, binary.subarray(8192)]];
const report = { experimental: true, experiment: 3, basicBytes: 8192, kernalBytes: 8192, preservedLabels,
  changedBytesFromStable: changedBytes, images: {}, stockGarbageCollector: true,
  sharedViaWrites: { addresses: ['$913E', '$913B'], rawInstructionBytesSaved: 6,
    skipBranchBytes: 2, usableBytesRecovered: 4, recoveredRange: '$FE35-$FE38', nowUsedFor: 'PAL text' },
  screen: stockScreen ? 'stock' : 'rainbow',
  regionDisplay: { row: 3, column: stockScreen ? 0 : 6, labels: ['PAL', 'NTSC'], matchedPairRequired: true },
  ram: { valCleanup: '$02A1-$02A4', regionFlag: '$02A6 (sign bit PAL=1, NTSC=0)' } };
const git = spawnSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' });
if (git.status !== 0) throw new Error('Cannot determine source commit');
report.sourceCommit = git.stdout.trim();
for (const [name, bytes] of images) {
  fs.writeFileSync(path.join(out, name), bytes);
  report.images[name] = crypto.createHash('sha256').update(bytes).digest('hex');
}
fs.writeFileSync(path.join(out, 'build-report.json'), JSON.stringify(report, null, 2) + '\n');
fs.writeFileSync(path.join(out, 'SHA256SUMS'), Object.entries(report.images).map(([name, hash]) => `${hash}  ${name}`).join('\n') + '\n');
fs.copyFileSync(path.join(root, stockScreen ? 'docs/wiki/Universal-Stock-Screen.md' : 'docs/wiki/Universal-Experimental.md'), path.join(out, 'README.md'));
console.log(JSON.stringify(report, null, 2));
