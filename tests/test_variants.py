"""Execute the canonical regressions, then check all screen/fix combinations."""
import base64
import hashlib
import json
import runpy
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
core = runpy.run_path(str(ROOT/'tests/test_vic20.py'))
basic = runpy.run_path(str(ROOT/'tests/test_basic.py'))
original, fixed = core['ORIGINAL'], core['FIXED']
script = """
import fs from 'node:fs';
import {allOptions,compose,variantId} from './scripts/variants.mjs';
const original = Buffer.concat([fs.readFileSync('reference/basic.901486-01.bin'),
  fs.readFileSync('reference/kernal.901486-07.bin')]);
const fixed = fs.readFileSync('build/vic20-fixed.bin');
console.log(JSON.stringify(allOptions().map(options => ({
  id:variantId(options),options,image:compose(original,fixed,options).toString('base64')
}))));
"""
variants = json.loads(subprocess.check_output(
    ['node','--input-type=module','-e',script],cwd=ROOT,text=True))
assert len(variants) == 8
assert len({v['id'] for v in variants}) == 8
cases = 0
for variant in variants:
    rom = base64.b64decode(variant['image'])
    options = variant['options']
    assert len(rom) == 16384
    assert rom[0x3F80:0x3F85] == original[0x3F80:0x3F85]
    assert rom[0x3F8A:] == original[0x3F8A:]
    if not any(options.values()):
        assert rom == original, 'All-off must reproduce production ROMs exactly'
    if all(options.values()):
        assert rom == fixed, 'All-on must reproduce the published enhanced build'
    expected_banner = fixed if options['banner'] else original
    if options['rainbow'] and not options['banner']:
        assert rom[0x2436:0x244F] == b'\x93      CBM BASIC V2    \r\x00'
    else:
        assert rom[0x2436:0x244F] == expected_banner[0x2436:0x244F]
    # Only the screen patches may differ from a same-fixes baseline.
    baseline = next(v for v in variants if v['options'] == {
        'fixes':options['fixes'],'rainbow':False,'banner':options['banner']})
    baseline_rom = base64.b64decode(baseline['image'])
    for expanded in (False,True):
        before, base = core['boot_to_input'](baseline_rom,expanded)
        after, after_base = core['boot_to_input'](rom,expanded)
        assert base == after_base == (0x1000 if expanded else 0x1E00)
        colour_base = 0x9400 | (base & 0x300)
        screen = list(before[base:base+506])
        colours = list(before[colour_base:colour_base+506])
        if options['rainbow']:
            memory_text = screen[44:60]
            ready_text = screen[88:94]
            memory_colours = colours[44:60]
            ready_colours = colours[88:94]
            heading = ('CBM BASIC V2.26' if options['banner'] else 'CBM BASIC V2')
            screen[:22] = [0x20]*22
            screen[6:6+len(heading)] = [
                ord(c)-64 if 'A' <= c <= 'Z' else ord(c) for c in heading]
            screen[44:66] = [0x20]*22
            screen[50:66] = memory_text
            screen[88:94] = [0x20]*6
            screen[132:138] = ready_text
            colours[44:66] = [1]*22
            colours[50:66] = memory_colours
            colours[88:94] = [1]*6
            colours[132:138] = ready_colours
            for offset,glyph,colour in zip(core['rainbow_offsets'],
                                           core['rainbow_glyphs'],core['rainbow_colours']):
                screen[offset],colours[offset] = glyph,colour
        assert after[base:base+506] == screen
        assert after[colour_base:colour_base+506] == colours
        assert [after[i] for i in (0x286,0x2B,0x2C,0x37,0x38)] == [
            before[i] for i in (0x286,0x2B,0x2C,0x37,0x38)]
        if options['rainbow']:
            assert after[0xD3] == 0 and after[0xD6] == 7
            assert (after[0xD1] | after[0xD2]<<8) == base+154
            assert (after[0xF3] | after[0xF4]<<8) == colour_base+132
            cpu = core['MPU'](memory=after,pc=0xFFD2)
            cpu.a,cpu.sp = ord('A'),0xFF
            cpu.stPushWord(core['RETURN']-1)
            core['run'](cpu)
            assert after[base+154] == 1 and after[colour_base+154] == 6
            assert (after[0xD3],after[0xD6]) == (1,7)
        else:
            assert [after[i] for i in (0xD1,0xD2,0xD3,0xD6)] == [
                before[i] for i in (0xD1,0xD2,0xD3,0xD6)]
        cases += 1
    for value in ('123','1E39','-1E39','1E99'):
        for handler in (0x400,0xC43A):
            cpu,mem,before,stopped = basic['val'](rom,value,0x10FC,handler)
            comparison = fixed if options['fixes'] else original
            ref_cpu,ref_mem,_,ref_stop = basic['val'](comparison,value,0x10FC,handler)
            assert stopped == ref_stop and cpu.x == ref_cpu.x and cpu.sp == ref_cpu.sp
            assert mem[0x10FC:0x10FC+len(value)+1] == ref_mem[0x10FC:0x10FC+len(value)+1]
            assert mem[0x300:0x302] == ref_mem[0x300:0x302]
            if options['fixes']:
                assert mem[0x10FC:0x10FC+len(value)+1] == before
                assert mem[0xFB:0xFF] == bytes([0x9A,0xBC,0xDE,0xF1])
            cases += 1
    for fragmented in (False,True):
        mem,_,cycles,_ = basic['collector'](rom,8,200,fragmented,26)
        expected,_,expected_cycles,_ = basic['collector'](
            fixed if options['fixes'] else original,8,200,fragmented,26)
        assert mem[0x1000:0x8000] == expected[0x1000:0x8000]
        assert cycles == expected_cycles
        cases += 1
    cpu,mem = core['machine'](rom,entry=0xFE57)
    mem[0xBA],mem[0x297] = 2,0x55
    core['run'](cpu)
    assert cpu.a == (0x55 if options['fixes'] else 0)
    cases += 1
    cpu,mem = core['machine'](rom,entry=0xF822)
    mem[0xB7],mem[0x9E],mem[0x9F] = 188,0,5
    mem[0xB2],mem[0xB3],mem[0xBB],mem[0xBC] = 0x3C,3,0,8
    mem[0x800:0x8BC] = [0x41]*188
    mem[0x3FC] = 0xCC
    core['run'](cpu,stops=(0xF834,))
    assert mem[0x3FC] == (0xCC if options['fixes'] else 0x41)
    cases += 1
    print('PASS:',variant['id'])

# Check only the requested deliverables; manual builds can select a single variant.
reports = json.loads((ROOT/'dist/index.json').read_text())
assert reports
for report in reports:
    variant = next(v for v in variants if v['id'] == report['id'])
    assert report['options'] == variant['options']
    directory = ROOT/'dist'/report['id']
    rom = base64.b64decode(variant['image'])
    expected_files = {'vic20-combined.bin':rom,
                      'basic.901486-01.bin':rom[:8192],
                      'kernal.901486-07.bin':rom[8192:]}
    assert json.loads((directory/'manifest.json').read_text()) == report
    for name,expected in expected_files.items():
        actual = (directory/name).read_bytes()
        assert actual == expected
        assert report['files'][name] == {
            'bytes':len(actual),'sha256':hashlib.sha256(actual).hexdigest()}
        cases += 1
    sums = ''.join(f"{report['files'][name]['sha256']}  {name}\n" for name in expected_files)
    assert sorted((directory/'SHA256SUMS').read_text().splitlines()) == sorted(sums.splitlines())
report = {'allPassed':True,'variants':8,'variantCases':cases,
          'canonicalCoreCases':2275,'canonicalBasicCases':192,
          'limits':['Static I/O boot path, not full-machine timing or hardware validation']}
(ROOT/'verification/variant-test-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
