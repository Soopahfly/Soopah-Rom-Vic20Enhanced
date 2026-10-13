import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.tools'))
from py65.devices.mpu6502 import MPU

EXPERIMENTAL = os.environ.get('VIC20_EXPERIMENTAL') == '1'
OUT = ROOT / ('build/universal' if EXPERIMENTAL else 'verification')
FIXED = (ROOT / ('build/universal/vic20-universal.bin' if EXPERIMENTAL else 'build/vic20-fixed.bin')).read_bytes()
ORIGINAL = ((ROOT / 'reference/basic.901486-01.bin').read_bytes()
            + (ROOT / 'reference/kernal.901486-07.bin').read_bytes())
RETURN = 0x7FFF
results = []


def machine(rom, entry):
    memory = bytearray(65536)
    memory[0xC000:] = rom
    cpu = MPU(memory=memory, pc=entry)
    cpu.p = cpu.UNUSED
    cpu.sp = 0xFF
    cpu.stPushWord(RETURN - 1)
    return cpu, memory


def run(cpu, stops=(RETURN,), limit=2000000):
    for _ in range(limit):
        if cpu.pc in stops:
            return cpu.pc
        cpu.step()
    raise AssertionError(f'Execution did not finish at ${cpu.pc:04X}')


def word(memory, address, value):
    memory[address:address+2] = bytes([value & 255, value >> 8])


def record(name, cases):
    results.append({'test': name, 'cases': cases, 'passed': True})
    print(f'PASS: {name} ({cases} cases)')


def val(rom, value, address, handler):
    cpu, memory = machine(rom, 0xD7AD)
    memory[0x73:0x90] = rom[0x2387:0x23A4]
    memory[0xD] = 0xFF
    word(memory, 0x64, 0x800)
    memory[0x800:0x803] = bytes([len(value), address & 255, address >> 8])
    memory[address:address+len(value)] = value.encode('ascii')
    memory[address+len(value)] = 0x22
    word(memory, 0x7A, 0x1211)
    word(memory, 0x300, handler)
    memory[0xFB:0xFF] = bytes([0x9A,0xBC,0xDE,0xF1])
    before = bytes(memory[address:address+len(value)+1])
    stopped = run(cpu, stops=(RETURN, handler))
    return cpu, memory, before, stopped


val_cases = 0
inputs = ('', '123', ' -12.5', '1E38', '1E39', '-1E39', '1E99',
          '1E-99', 'E39', '1.2.3', '9' * 255)
for value in inputs:
    for address in (0x1000, 0x10FC):
        for handler in (0x400, 0xC43A):
            old_cpu, old_mem, _, old_stop = val(ORIGINAL, value, address, handler)
            cpu, mem, before, stopped = val(FIXED, value, address, handler)
            assert stopped == old_stop
            assert mem[address:address+len(value)+1] == before, 'VAL changed the string'
            assert mem[0x300:0x302] == bytes([handler & 255, handler >> 8])
            assert mem[0xFB:0xFF] == bytes([0x9A,0xBC,0xDE,0xF1]), 'Caller scratch changed'
            if stopped == handler:
                assert cpu.x == old_cpu.x == 15
                assert cpu.sp == 0xFD, 'Nested parser frames were not discarded'
                assert mem[0x7A:0x7C] == bytes([0x11,0x12])
                assert old_mem[address+len(value)] == 0, 'Original overflow not reproduced'
            else:
                assert mem[0x61:0x67] == old_mem[0x61:0x67], 'Normal numeric result changed'
                assert mem[0x7A:0x7C] == old_mem[0x7A:0x7C]
                assert cpu.sp == old_cpu.sp == 0xFF
            val_cases += 1
record('VAL overflow restoration, ordinary results, page crossing and custom error vectors', val_cases)


def collector(rom, count, length, fragmented, seed, top=0x8000):
    cpu, mem = machine(rom, 0xD526)
    rng = random.Random(seed)
    temporary = min(3, count)
    scalar = max(0, (count-temporary)//2)
    array = count-temporary-scalar
    variables = 0x1000
    arrays = variables + scalar*7 + 7  # include one ordinary numeric variable
    end = arrays + 7 + array*3
    word(mem, 0x2D, variables)
    word(mem, 0x2F, arrays)
    word(mem, 0x31, end)
    word(mem, 0x37, top)
    mem[0x16], mem[0x53] = 0x19+temporary*3, 3
    mem[arrays:arrays+7] = bytes([65,0x80,(7+array*3)&255,(7+array*3)>>8,1,0,array])
    descriptors = [0x19+i*3 for i in range(temporary)]
    for i in range(scalar):
        mem[variables+i*7:variables+i*7+2] = bytes([65+i,0x80])
        descriptors.append(variables+i*7+2)
    mem[variables+scalar*7:variables+scalar*7+7] = bytes([78,0,1,2,3,4,5])
    descriptors += [arrays+7+i*3 for i in range(array)]
    rng.shuffle(descriptors)
    cursor = top
    expected = {}
    for i, descriptor in enumerate(descriptors):
        size = length if length is not None else rng.randrange(256)
        cursor -= size + (rng.randrange(1,9) if fragmented else 0)
        assert cursor >= end
        data = bytes((i*31+j*7) & 255 for j in range(size))
        mem[cursor:cursor+size] = data
        mem[descriptor:descriptor+3] = bytes([size,cursor&255,cursor>>8])
        expected[descriptor] = data
    word(mem, 0x33, cursor)
    run(cpu)
    for descriptor, data in expected.items():
        pointer = mem[descriptor+1] | mem[descriptor+2]<<8
        assert mem[pointer:pointer+len(data)] == data, 'Collector corrupted a string'
    assert cpu.sp == 0xFF
    return mem, descriptors, cpu.processorCycles, end


gc_cases = 0
for seed in range(32):
    count = seed % 12 + 1
    length = (0,1,16,64,255,None)[seed % 6]
    for fragmented in (False, True):
        old, descriptors, _, end = collector(ORIGINAL,count,length,fragmented,seed)
        new, _, _, _ = collector(FIXED,count,length,fragmented,seed)
        assert new[0x33:0x35] == old[0x33:0x35]
        assert new[0x19:0x22] == old[0x19:0x22]
        assert new[0x1000:0x8000] == old[0x1000:0x8000], 'Heap/table result differs'
        gc_cases += 1
record('Collector equivalence across temporary, scalar, array and empty strings', gc_cases)

# Simulate the caller's small-memory configuration too.
for fragmented in (False,True):
    old, _, _, _ = collector(ORIGINAL,8,64,fragmented,26,top=0x1E00)
    new, _, _, _ = collector(FIXED,8,64,fragmented,26,top=0x1E00)
    assert new[0x1000:0x1E00] == old[0x1000:0x1E00]
record('Collector equivalence with an unexpanded-size heap', 2)

benchmarks = []
for count,length,fragmented in ((8,200,False),(32,128,False),(32,128,True)):
    _, _, old_cycles, _ = collector(ORIGINAL,count,length,fragmented,26)
    _, _, new_cycles, _ = collector(FIXED,count,length,fragmented,26)
    benchmarks.append({'strings':count,'length':length,'fragmented':fragmented,
                       'originalCycles':old_cycles,'patchedCycles':new_cycles,
                       'reductionPercent':round(100*(old_cycles-new_cycles)/old_cycles,2)})
if EXPERIMENTAL:
    assert all(item['patchedCycles'] == item['originalCycles'] for item in benchmarks)
    record('Experimental fit retains stock collector timing', 3)
else:
    assert all(item['patchedCycles'] < item['originalCycles'] for item in benchmarks if not item['fragmented'])
    record('Packed-heap cycle reduction measured against the original collector', 2)

# Reclaimed NOPs must preserve keyboard/editor A, X, Y and status flags.
for entry, stop in ((0xE65B,0xE672),(0xE800,0xE815),(0xEBED,0xEC00),(0xEC18,0xEC38)):
    for value in (0,1,0x40,0x80,0xFF):
        for flags in (0x20,0x21,0xA0,0x60):
            old, _ = machine(ORIGINAL,entry)
            new, _ = machine(FIXED,entry)
            for cpu in (old,new):
                cpu.a,cpu.x,cpu.y,cpu.p = value,0x43,0x17,flags
                run(cpu,stops=(stop,))
            assert (new.a,new.x,new.y,new.p,new.sp) == (old.a,old.x,old.y,old.p,old.sp)
record('Reclaimed editor/keyboard NOP paths preserve registers and flags', 80)

report = {'emulator':'py65 1.2.0, NMOS 6502','testGroups':len(results),
          'cases':sum(item['cases'] for item in results),'results':results,
          'collectorBenchmarks':benchmarks,
          'limits':['Collector still performs repeated descriptor scans',
                    'Cycle counts are routine-level emulation, not hardware measurements',
                    'Experimental VAL uses $02A1-$02A4' if EXPERIMENTAL else
                    'VAL borrows $FB-$FE but restores their caller values on both exits']}
(OUT/'basic-test-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['collectorBenchmarks'],indent=2))
