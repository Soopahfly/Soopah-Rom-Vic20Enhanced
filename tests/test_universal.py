"""Assembled experimental ROM tests; synthetic raster/VIA, not VICE or hardware."""
import json
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
NTSC_WORDS = [0x2792, 0x1A40, 0x11C6, 0x0E74, 0x0CEE, 0x0645,
              0x02F1, 0x0146, 0x00B8, 0x0071, 0x002A]
prefix = SYMBOLS['UNI_NTSC_PREFIX'] - 0xC000
expected_table = PAL[0x1F5A:0x1F5C] + b''.join(v.to_bytes(2, 'little') for v in NTSC_WORDS)
assert ROM[prefix:prefix+24] == expected_table


class RasterMemory(list):
    def __init__(self, region='PAL', phase=0, stuck=None, interlace=False,
                 expanded=None, rom=ROM):
        super().__init__([0] * 65536)
        self.expanded = expanded
        self.cpu = None
        self.region, self.phase, self.stuck = region, phase, stuck
        self.lines, self.cycles_per_line = (312, 71) if region == 'PAL' else (261, 65)
        self.ier = {0x911E: 0, 0x912E: 0}
        self[0xC000:] = rom
        self[0x9000] = 0x80 if interlace else 0

    def present(self, address):
        return (self.expanded is None or address < 0x400 or
                0x1000 <= address < (0x8000 if self.expanded else 0x2000))

    def __getitem__(self, address):
        if not isinstance(address, int):
            return super().__getitem__(address)
        if address == 0x9004:
            if self.stuck is not None:
                return self.stuck
            cycles = self.phase*self.cycles_per_line + self.cpu.processorCycles
            return (cycles // self.cycles_per_line % self.lines) // 2
        if address in self.ier:
            return self.ier[address] | 0x80
        if not (self.present(address) or 0x9000 <= address < 0x9800 or address >= 0xC000):
            return 0xFF
        return super().__getitem__(address)

    def __setitem__(self, address, value):
        if isinstance(address, int):
            if address in self.ier:
                if value & 0x80:
                    self.ier[address] |= value & 0x7F
                else:
                    self.ier[address] &= ~(value & 0x7F)
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
for expanded in (False, True):
    cpu, mem = machine(0xFD22, RasterMemory(expanded=expanded, rom=STABLE))
    run(cpu, stop=0xE5E8)
    base = mem[0x288] << 8
    colour = 0x9400 | (base & 0x300)
    baseline_screens[expanded] = (bytes(mem[base:base+506]), bytes(mem[colour:colour+506]))
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
    for expanded in (False, True):
        for phase in (0, 1, 130, 260):
            cpu, mem = machine(0xFD22, RasterMemory(region, phase, expanded=expanded))
            run(cpu, stop=0xE5E8)
            base = mem[0x288] << 8
            assert base == (0x1000 if expanded else 0x1E00)
            assert bool(mem[0x2A6] & 0x80) == (region == 'PAL')
            assert mem[0x9000:0x9002] == ([12, 38] if region == 'PAL' else [5, 25])
            assert mem[0x9124:0x9126] == ([38, 72] if region == 'PAL' else [137, 66])
            text = '28159 BYTES FREE' if expanded else '3583 BYTES FREE'
            screen_text = bytes(ord(c) & 0x3F if 'A' <= c <= 'Z' else ord(c) for c in text)
            assert bytes(mem[base+50:base+50+len(text)]) == screen_text, (region, expanded, mem[base+44:base+66])
            assert bytes(mem[base+132:base+138]) == bytes([18, 5, 1, 4, 25, 46])
            assert (mem[0xD3], mem[0xD6]) == (0, 7)
            colour = 0x9400 | (base & 0x300)
            assert (bytes(mem[base:base+506]), bytes(mem[colour:colour+506])) == baseline_screens[expanded]
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

report = {'experimental': True, 'allPassed': True, 'cases': sum(COUNTS.values()),
          'tests': COUNTS, 'maximumDetectionCycles': max_cycles,
          'receiveStartTimerSetupCycles': setup_cycles,
          'limitations': ['Synthetic VIC raster and VIA registers, not full peripheral emulation',
                          'No VICE or physical-machine validation',
                          'No real cassette, serial bus or RS-232 device tests']}
(OUT / 'universal-test-report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
