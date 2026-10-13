"""Assembled experimental ROM tests; synthetic raster/VIA, not VICE or hardware."""
import json
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/universal'
sys.path.insert(0, str(ROOT / '.tools'))
from py65.devices.mpu6502 import MPU

ROM = (OUT / 'vic20-universal.bin').read_bytes()
PAL = (ROOT / 'reference/kernal.901486-07.bin').read_bytes()
STABLE = (ROOT / 'roms/vic20-fixed.bin').read_bytes()
SYMBOLS = {}
for line in (OUT / 'vic20-universal.labels').read_text().splitlines():
    _, address, name = line.split()
    SYMBOLS[name.lstrip('.')] = int(address, 16)
RETURN = 0x7FFF
COUNTS = {}
CONFIGS = {
    # (RAM123 present, populated cartridge 8 KB blocks, expected BASIC bytes)
    'unexpanded': (False, (), 3583),
    '3k': (True, (), 6655),
    '8k': (False, (1,), 11775),
    '16k': (False, (1, 2), 19967),
    '24k': (False, (1, 2, 3), 28159),
    '32k': (False, (1, 2, 3, 5), 28159),
    '35k': (True, (1, 2, 3, 5), 28159),
    '3k-plus-8k': (True, (1,), 11775),
    'blk2-only': (False, (2,), 3583),
    'blk5-only': (False, (5,), 3583),
}
# Verified bytes from the immutable universal-8k-exp1 ROM, $FDF9..$FE38.
# Keep the baseline independent of the new assembler output and VIA modelling.
EXP1_IOINIT = bytes.fromhex(
    'A97F8D1E918D2E91A9408D2B918D1B91A9FE8D1C91A9DE8D2C91'
    'A2008E12918E23918E1F910820F6F028CA8E2291A2808E1391A200'
    '2084EFA9828D1E91208DEF')
assert len(EXP1_IOINIT) == 64
exp1 = bytearray(ROM)
exp1[0x3DF9:0x3E39] = EXP1_IOINIT
EXP1 = bytes(exp1)
assert hashlib.sha256(EXP1[8192:]).hexdigest() == 'a036a393263a3a12a3b1779b3fbcd3c704cea2c3d27d7534451ebba00acc974a'
assert hashlib.sha256(ROM[:8192]).hexdigest() == 'acae764369d325bb61b50974fb680dd9e79ad7d37392b8a3cb144fc55c977897'
NTSC_WORDS = [0x2792, 0x1A40, 0x11C6, 0x0E74, 0x0CEE, 0x0645,
              0x02F1, 0x0146, 0x00B8, 0x0071, 0x002A]
prefix = SYMBOLS['UNI_NTSC_PREFIX'] - 0xC000
expected_table = PAL[0x1F5A:0x1F5C] + b''.join(v.to_bytes(2, 'little') for v in NTSC_WORDS)
assert ROM[prefix:prefix+24] == expected_table


class RasterMemory(list):
    def __init__(self, region='PAL', phase=0, stuck=None, interlace=False,
                 config=None, rom=ROM):
        super().__init__([0] * 65536)
        self.config = CONFIGS[config] if config is not None else None
        self.cpu = None
        self.region, self.phase, self.stuck = region, phase, stuck
        self.lines, self.cycles_per_line = (312, 71) if region == 'PAL' else (261, 65)
        self.ier = {0x911E: 0, 0x912E: 0}
        self.via_writes = []
        self[0xC000:] = rom
        self[0x9000] = 0x80 if interlace else 0

    def present(self, address):
        if self.config is None:
            return True
        ram123, blocks, _ = self.config
        return (address < 0x400 or 0x1000 <= address < 0x2000 or
                ram123 and 0x400 <= address < 0x1000 or
                any(block*0x2000 <= address < (block+1)*0x2000 for block in blocks))

    @staticmethod
    def via_targets(address):
        if not 0x9100 <= address < 0x9400:
            return ()
        # Independent CS1 pins use A4/A5; low nibble is the register number.
        return tuple(base+(address & 15) for base, bit in ((0x9110, 16), (0x9120, 32))
                     if address & bit)

    def __getitem__(self, address):
        if not isinstance(address, int):
            return super().__getitem__(address)
        if address >= 0xC000:
            return super().__getitem__(address)
        if address == 0x9004:
            if self.stuck is not None:
                return self.stuck
            cycles = self.phase*self.cycles_per_line + self.cpu.processorCycles
            return (cycles // self.cycles_per_line % self.lines) // 2
        targets = self.via_targets(address)
        if len(targets) > 1:
            raise AssertionError(f'ROM read from shared VIA address ${address:04X}')
        if targets:
            target = targets[0]
            return (self.ier[target] | 0x80 if target in self.ier
                    else super().__getitem__(target))
        if not (self.present(address) or 0x9000 <= address < 0x9800 or address >= 0xC000):
            return 0xFF
        return super().__getitem__(address)

    def __setitem__(self, address, value):
        if isinstance(address, int):
            targets = self.via_targets(address)
            if targets:
                self.via_writes.append((address, value, targets))
                for target in targets:
                    if target in self.ier:
                        if value & 0x80:
                            self.ier[target] |= value & 0x7F
                        else:
                            self.ier[target] &= ~(value & 0x7F)
                    else:
                        super().__setitem__(target, value)
                return
            if not (self.present(address) or 0x9000 <= address < 0x9800):
                return
        super().__setitem__(address, value)


def run(cpu, stop=RETURN, limit=2000000):
    for _ in range(limit):
        if cpu.pc == stop:
            return
        cpu.step()
    raise AssertionError(f'No return at ${cpu.pc:04X}')


def machine(entry, mem=None, a=0, x=0, y=0x5A, flags=0x20):
    mem = mem if mem is not None else RasterMemory()
    cpu = MPU(memory=mem, pc=SYMBOLS[entry] if isinstance(entry, str) else entry)
    mem.cpu = cpu
    cpu.a, cpu.x, cpu.y, cpu.p, cpu.sp = a, x, y, flags, 0xFF
    cpu.stPushWord(RETURN-1)
    return cpu, mem


def record(name, count):
    COUNTS[name] = count
    print(f'PASS: {name} ({count} cases)')


mem = RasterMemory()
mem.ier.update({0x911E: 0x55, 0x912E: 0x2A})
mem[0x913E] = 0x7F
assert mem.ier == {0x911E: 0, 0x912E: 0}
mem[0x913B] = 0x40
assert mem[0x911B] == mem[0x912B] == 0x40
mem[0x911E] = 0x82
assert mem.ier == {0x911E: 2, 0x912E: 0}, 'Single-VIA write leaked to the other chip'
for address in (0x9130, 0x913B, 0x913E, 0x913F):
    try:
        mem[address]
    except AssertionError:
        pass
    else:
        raise AssertionError('Test model accepted a dangerous shared read')
record('Independent VIA selects, shared writes and shared-read rejection', 7)

count = 0
ioinit_cycles = None
for flags in (0x20, 0x21, 0x60, 0x6D):
    for initial in (0, 0x7F, 0x55, 0xAA):
        for origin in (0, 5, 12, 0x80, 0xFF):
            states, cycles, traces = [], [], []
            for image in (EXP1, ROM):
                cpu, mem = machine(0xFDF9, RasterMemory(stuck=0, rom=image), x=0x37, flags=flags)
                mem.ier.update({0x911E: initial & 127, 0x912E: (initial ^ 0x7F) & 127})
                mem[0x911B], mem[0x912B], mem[0x9000] = initial, initial ^ 255, origin
                mem.via_writes.clear()
                run(cpu)
                states.append((bytes(mem[0x9110:0x9130]), dict(mem.ier), mem[0x9000],
                               cpu.a, cpu.x, cpu.y, cpu.p, cpu.sp))
                cycles.append(cpu.processorCycles)
                traces.append(mem.via_writes)
            assert states[0] == states[1], (flags, initial, origin)
            shared = [(address, value) for address, value, targets in traces[1] if len(targets) == 2]
            assert shared == [(0x913E, 0x7F), (0x913B, 0x40)]
            assert cycles[0] - cycles[1] == 5
            # Each chip must see exactly the same writes, in the same order.
            for base in (0x9110, 0x9120):
                per_chip = [[(target, value) for _, value, targets in trace
                             for target in targets if target & 0xFFF0 == base]
                            for trace in traces]
                assert per_chip[0] == per_chip[1]
            ioinit_cycles = {'experiment1': cycles[0], 'experiment2': cycles[1],
                             'cyclesSaved': 5, 'raster': 'frozen at zero for repeatable comparison'}
            count += 1
record('IOINIT matches Experiment 1 across flags, prior VIA states and video origins', count)
assert SYMBOLS['UNI_IOINIT_SPARE'] == 0xFE35
assert ROM[0x3E35:0x3E39] == b'\xEA'*4
record('Four recovered bytes are skipped, with FE39 still at its stock address', 1)


max_cycles = {}
count = 0
for region, lines in [('PAL', 312), ('NTSC', 261)]:
    maximum = 0
    for phase in range(lines):
        for interlace in (False, True):
            cpu, mem = machine('UNI_DETECT', RasterMemory(region, phase, interlace=interlace))
            run(cpu)
            assert bool(mem[0x2A6] & 0x80) == (region == 'PAL'), (region, phase)
            assert (cpu.x, cpu.y, cpu.sp) == (0, 0x5A, 0xFF)
            assert mem[0x9000] & 0x80 == 0
            maximum = max(maximum, cpu.processorCycles)
            count += 1
    max_cycles[region] = maximum
record('Detection at every raster phase, including initial interlace', count)
for value in (0, 1, 130, 155, 255):
    cpu, mem = machine('UNI_DETECT', RasterMemory(stuck=value))
    run(cpu)
    assert mem[0x2A6] == 0x80 and cpu.processorCycles < 5000
record('Frozen raster has a bounded PAL fallback', 5)

count = 0
for region, flag in [('PAL', 0x80), ('NTSC', 0)]:
    for flags in (0x20, 0x21, 0x60, 0x6D):
        cpu, mem = machine(0xE5C3, flags=flags)
        mem[0x2A6] = flag
        run(cpu)
        expected = bytearray(PAL[0xDE4:0xDF4])
        if region == 'NTSC':
            expected[:2] = bytes([5, 25])
        # Raster register is read-only hardware; compare the other registers.
        assert bytes(mem[0x9000:0x9004] + mem[0x9005:0x9010]) == expected[:4] + expected[5:]
        assert (cpu.x, cpu.y, cpu.sp) == (0, 0x5A, 0xFF)
        assert cpu.p & 0x4D == flags & 0x4D
        cpu, mem = machine(0xFE39, x=0x37, flags=flags)
        mem[0x2A6] = flag
        run(cpu)
        timer = 0x4826 if region == 'PAL' else 0x4289
        assert mem[0x9124] | mem[0x9125] << 8 == timer
        assert (cpu.a, cpu.x, cpu.y, cpu.sp) == (timer >> 8, 0x37, 0x5A, 0xFF)
        assert cpu.p & 0x4D == flags & 0x4D
        count += 2
record('Real video and system-timer entries preserve register contracts', count)

count = 0
for region, flag in [('PAL', 0x80), ('NTSC', 0)]:
    for code in range(16):
        index = code*2
        expected = int.from_bytes(PAL[0x1F5A+index:0x1F5C+index], 'little')
        if region == 'NTSC' and 1 <= code <= 11:
            expected = NTSC_WORDS[code-1]
        cpu, mem = machine(0xF4F4, a=code)
        mem[0x2A6] = flag
        run(cpu, stop=0xF50C)
        # Unsupported codes can set ROL's carry, which the stock ADC retains.
        assert mem[0x299] | mem[0x29A] << 8 == (expected*2+200+(expected >> 15)) & 0xFFFF, (region, code, hex(expected), mem[0x299:0x29B])
        cpu, mem = machine(0xFF38, a=code)
        mem[0x2A6] = flag
        run(cpu, stop=0xFF46)
        assert mem[0x9118] | mem[0x9119] << 8 == expected
        assert cpu.x == index
        for flags in (0x20, 0x21, 0x60, 0x6D):
            for helper, byte in [('UNI_BAUD_BYTE', expected & 255), ('UNI_BAUD_HIGH', expected >> 8)]:
                cpu, mem = machine(helper, x=index, flags=flags)
                mem[0x2A6] = flag
                run(cpu)
                assert (cpu.a, cpu.x, cpu.y, cpu.sp) == (byte, index, 0x5A, 0xFF)
                assert cpu.p & 0x4D == flags & 0x4D
                count += 1
        count += 2
record('All baud codes through OPEN, receive-start NMI and byte helpers', count)

count = 0
for pointer in (0xEC5E, 0xEC9F, 0xECE0, 0xEDA3, 0x0600, 0x06A3, 0xED00):
    for key in range(65):
        cpu, mem = machine('UNI_KEY_READ')
        mem[0xF5], mem[0xF6], mem[0xCB] = pointer & 255, pointer >> 8, key
        if pointer < 0xC000:
            mem[pointer:pointer+65] = [(i*7) & 255 for i in range(65)]
        expected = (STABLE[pointer+key-0xC000] if pointer == 0xEDA3 else mem[pointer+key])
        run(cpu)
        assert (cpu.a, cpu.y) == (expected, key), (hex(pointer), key)
        count += 1
record('Every standard key and custom-table pointer survives CTRL compression', count)
for value in range(256):
    cpu, mem = machine(0xEC0F, a=value)
    run(cpu, stop=0xEC38)
    assert cpu.a in (0, 2, 4, 6)
record('All keyboard selector inputs stay inside the four retained pointers', 256)
for flags, pointer in enumerate((0xEC5E, 0xEC9F, 0xECE0, 0xEC5E,
                                 0xEDA3, 0xEDA3, 0xEDA3, 0xEDA3)):
    cpu, mem = machine(0xEBDC)
    mem[0x28D], mem[0x28E], mem[0x291] = flags, 255, 0x80
    mem[0xF5], mem[0xF6] = 0x5E, 0xEC
    run(cpu, stop=0xEB74)
    assert mem[0xF5] | mem[0xF6] << 8 == pointer
record('Normal modifier combinations select the original keyboard tables', 8)

count = 0
baseline_screens = {}
for config in CONFIGS:
    cpu, mem = machine(0xFD22, RasterMemory(config=config, rom=STABLE))
    run(cpu, stop=0xE5E8)
    base = mem[0x288] << 8
    colour = 0x9400 | (base & 0x300)
    baseline_screens[config] = (bytes(mem[base:base+506]), bytes(mem[colour:colour+506]))
for region in ('PAL', 'NTSC'):
    for flags in (0x20, 0x21, 0x60, 0x6D):
        cpu, mem = machine(0xFDF9, RasterMemory(region), x=0x37, flags=flags)
        mem[0x9000] = 0x85 if flags & 1 else 12
        original_origin = mem[0x9000]
        run(cpu)
        timer = 0x4826 if region == 'PAL' else 0x4289
        assert (cpu.a, cpu.x, cpu.y, cpu.sp) == (timer >> 8, 0, 0x5A, 0xFF)
        assert cpu.p & 0x4D == flags & 0x4D
        assert [mem[a] for a in (0x9112, 0x9122, 0x9123, 0x9113, 0x911F)] == [0, 255, 0, 128, 0]
        assert mem.ier == {0x911E: 2, 0x912E: 64}
        assert mem[0x9000] == original_origin, 'IOINIT changed the caller video origin'
        count += 1
record('Public IOINIT completes with both regional timings and original DDRs', count)

count = 0
for region in ('PAL', 'NTSC'):
    for config, (_, blocks, free_bytes) in CONFIGS.items():
        for phase in (0, 130):
            cpu, mem = machine(0xFD22, RasterMemory(region, phase, config=config))
            run(cpu, stop=0xE5E8)
            base = mem[0x288] << 8
            assert base == (0x1000 if 1 in blocks else 0x1E00), config
            assert bool(mem[0x2A6] & 0x80) == (region == 'PAL')
            assert mem[0x9000:0x9002] == ([12, 38] if region == 'PAL' else [5, 25])
            assert mem[0x9124:0x9126] == ([38, 72] if region == 'PAL' else [137, 66])
            text = f'{free_bytes} BYTES FREE'
            screen_text = bytes(ord(c) & 0x3F if 'A' <= c <= 'Z' else ord(c) for c in text)
            assert bytes(mem[base+50:base+50+len(text)]) == screen_text, (region, config, mem[base+44:base+66])
            assert bytes(mem[base+132:base+138]) == bytes([18, 5, 1, 4, 25, 46])
            assert (mem[0xD3], mem[0xD6]) == (0, 7)
            colour = 0x9400 | (base & 0x300)
            assert (bytes(mem[base:base+506]), bytes(mem[colour:colour+506])) == baseline_screens[config]
            before = bytes(mem[base:base+506])
            cpu, mem = machine(0xFFD2, mem, a=ord('A'))
            run(cpu)
            colour = 0x9400 | (base & 0x300)
            assert mem[base+154] == 1 and mem[colour+154] == 6
            assert bytes(mem[base:base+154]) == before[:154]
            count += 1
record('Reset to READY and typed character in both regions and RAM layouts', count)

setup_cycles = {}
for name, image, flag in [('Stock PAL', STABLE[:8192]+PAL, 0x80),
                          ('Universal PAL', ROM, 0x80), ('Universal NTSC', ROM, 0)]:
    cpu, mem = machine(0xFF38, RasterMemory(rom=image), a=1)
    mem[0x2A6] = flag
    run(cpu, stop=0xFF46)
    setup_cycles[name] = cpu.processorCycles

report = {'experimental': True, 'experiment': 2, 'allPassed': True, 'cases': sum(COUNTS.values()),
          'tests': COUNTS, 'maximumDetectionCycles': max_cycles,
          'receiveStartTimerSetupCycles': setup_cycles,
          'ioinitCycles': ioinit_cycles,
          'ramConfigurations': {name: {'ram123': ram123, 'blocks': list(blocks), 'basicBytesFree': free}
                                for name, (ram123, blocks, free) in CONFIGS.items()},
          'limitations': ['Synthetic VIC raster and VIA registers, not full peripheral emulation',
                          'No VICE or physical-machine validation',
                          'No real cassette, serial bus or RS-232 device tests']}
(OUT / 'universal-test-report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
