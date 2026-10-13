import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCHED = ROOT / 'build'
sys.path.insert(0, str(ROOT / '.tools'))
from py65.devices.mpu6502 import MPU

ORIGINAL = ((ROOT / 'reference/basic.901486-01.bin').read_bytes()
            + (ROOT / 'reference/kernal.901486-07.bin').read_bytes())
FIXED = (PATCHED / 'vic20-fixed.bin').read_bytes()
RETURN = 0x7FFF
results = []


class Memory(list):
    def __init__(self, rom):
        super().__init__([0] * 65536)
        self[0xC000:0x10000] = rom
        self.ier = 0x40
        self.transmitted = []

    def __getitem__(self, address):
        if address == 0x911E:
            return 0x80 | self.ier
        return super().__getitem__(address)

    def __setitem__(self, address, value):
        if address == 0x911E:
            if value & 0x80:
                self.ier |= value & 0x7F
            else:
                self.ier &= ~(value & 0x7F)
            return
        if address == 0xB6:
            self.transmitted.append(value)
        super().__setitem__(address, value)


def machine(rom=FIXED, entry=0, a=0, x=0x37, y=0x5A):
    memory = Memory(rom)
    cpu = MPU(memory=memory, pc=entry)
    cpu.a, cpu.x, cpu.y = a, x, y
    cpu.p = cpu.UNUSED
    cpu.sp = 0xFF
    cpu.stPushWord(RETURN - 1)
    return cpu, memory


def run(cpu, stops=(RETURN,), limit=20000):
    for _ in range(limit):
        if cpu.pc in stops:
            return cpu.pc
        cpu.step()
    raise AssertionError(f'Execution did not finish, PC=${cpu.pc:04X}')


def record(name, cases):
    results.append({'test': name, 'cases': cases, 'passed': True})
    print(f'PASS: {name} ({cases} cases)')


# All old ROM labels must retain their addresses, including internal entry points.
label_count = 0
for line in (PATCHED / 'vic20-fixed.labels').read_text().splitlines():
    fields = line.split()
    if len(fields) == 3 and fields[2].startswith('.LAB_'):
        expected = int(fields[2][5:], 16)
        if expected >= 0xC000:
            assert int(fields[1], 16) == expected, line
            label_count += 1
assert label_count > 500
assert FIXED[0x3F80:0x3F85] == ORIGINAL[0x3F80:0x3F85]
assert FIXED[0x3F8A:] == ORIGINAL[0x3F8A:], 'KERNAL public jump table or vectors changed'
assert FIXED[0x239F:0x23A4] == ORIGINAL[0x239F:0x23A4], 'Initial RND seed changed'
record('ROM labels, public jump table and hardware vectors preserved', label_count)

assert FIXED[0x2436:0x244F] == b'\x93      CBM BASIC V2.26 \r\x00', 'Wrong startup banner'
record('V2.26 startup banner fits the original 22-column field', 1)

rainbow_offsets = [0,1,2,3,4,22,23,24,25,44,45,46,66,67,88]
rainbow_glyphs = [0xA0,0xA0,0xA0,0xA0,0x69,0xA0,0xA0,0xA0,0x69,0xA0,0xA0,0x69,0xA0,0x69,0x69]
rainbow_colours = [2,2,2,2,2,7,7,7,7,5,5,5,3,3,6]
assert FIXED[0x2426:0x2429] == bytes([0x4C,0x29,0xE9]), 'Missing startup hook'
for screen_base in (0x1000, 0x1E00):
    cpu, mem = machine(entry=0xE929)
    colour_base = 0x9400 | (screen_base & 0x300)
    mem[0x288] = screen_base >> 8
    mem[screen_base:screen_base+506] = [0x20] * 506
    mem[colour_base:colour_base+506] = [6] * 506
    mem[0xD3], mem[0xD6], mem[0x286] = 0, 3, 6
    for row in range(24):
        mem[0xD9+row] = 0x80 | ((row*22) >> 8)
    expected_screen = list(mem[screen_base:screen_base+506])
    expected_colours = list(mem[colour_base:colour_base+506])
    for offset, glyph_value, colour in zip(rainbow_offsets, rainbow_glyphs, rainbow_colours):
        assert offset % 22 < 5 and offset // 22 < 5
        expected_screen[offset] = glyph_value
        expected_colours[offset] = colour
    # An IRQ keyboard scan can update F5/F6 between any drawing instructions.
    for _ in range(20000):
        if cpu.pc == 0xC644:
            break
        mem[0xF5], mem[0xF6] = 0x9F,0xEC
        cpu.step()
    else:
        raise AssertionError('Startup drawing did not finish')
    assert mem[screen_base:screen_base+506] == expected_screen
    assert mem[colour_base:colour_base+506] == expected_colours
    assert (mem[0xD3], mem[0xD6], mem[0x286]) == (0,5,6)
    assert cpu.sp == 0xFD, 'Startup helper altered the return stack'
record('Left-hand stepped rainbow and editor pointers on both screen bases', 2)

class BootMemory(Memory):
    """Only the VIC RAM map and static I/O; no video or interrupt timing."""
    def __init__(self, rom, expanded):
        self.expanded = expanded
        super().__init__(rom)

    def present(self, address):
        return address < 0x400 or 0x1000 <= address < (0x8000 if self.expanded else 0x2000)

    def __getitem__(self, address):
        if isinstance(address, int) and not (self.present(address) or 0x9000 <= address < 0x9800 or address >= 0xC000):
            return 0xFF
        return super().__getitem__(address)

    def __setitem__(self, address, value):
        if isinstance(address, int) and not (self.present(address) or 0x9000 <= address < 0x9800):
            return
        super().__setitem__(address, value)


def boot_to_input(rom, expanded):
    mem = BootMemory(rom, expanded)
    cpu = MPU(memory=mem, pc=0xFD22)
    run(cpu, stops=(0xE5E8,), limit=2000000)
    base = mem[0x288] << 8
    return mem, base


without_rainbow = bytearray(FIXED)
without_rainbow[0x240F:0x2412] = ORIGINAL[0x240F:0x2412]
without_rainbow[0x2426:0x2429] = ORIGINAL[0x2426:0x2429]
without_rainbow[0x2929:0x2975] = ORIGINAL[0x2929:0x2975]
without_rainbow[0x3F85:0x3F8A] = ORIGINAL[0x3F85:0x3F8A]
for expanded in (False, True):
    baseline, base = boot_to_input(without_rainbow, expanded)
    decorated, decorated_base = boot_to_input(FIXED, expanded)
    assert decorated_base == base == (0x1000 if expanded else 0x1E00)
    colour_base = 0x9400 | (base & 0x300)
    expected_screen = list(baseline[base:base+506])
    expected_colours = list(baseline[colour_base:colour_base+506])
    memory_text = expected_screen[44:60]
    ready_text = expected_screen[88:94]
    memory_colours = expected_colours[44:60]
    ready_colours = expected_colours[88:94]
    expected_screen[44:66] = [0x20]*22
    expected_screen[50:66] = memory_text
    expected_screen[88:94] = [0x20]*6
    expected_screen[132:138] = ready_text
    expected_colours[44:66] = [1]*22
    expected_colours[50:66] = memory_colours
    expected_colours[88:94] = [1]*6
    expected_colours[132:138] = ready_colours
    for offset, glyph_value, colour in zip(rainbow_offsets, rainbow_glyphs, rainbow_colours):
        expected_screen[offset] = glyph_value
        expected_colours[offset] = colour
    assert decorated[base:base+506] == expected_screen, 'Startup text or logo differs'
    assert decorated[colour_base:colour_base+506] == expected_colours
    assert decorated[0xD3] == 0 and decorated[0xD6] == 7
    assert (decorated[0xD1] | decorated[0xD2]<<8) == base+154
    assert (decorated[0xF3] | decorated[0xF4]<<8) == colour_base+132
    assert decorated[0x286] == baseline[0x286] == 6
    assert decorated[0x2B:0x39] == baseline[0x2B:0x39], 'BASIC memory pointers changed'
    # Colour pointers are lazy on stock ROMs too: the next output must refresh them.
    cpu = MPU(memory=decorated, pc=0xFFD2)
    cpu.a, cpu.sp = ord('A'), 0xFF
    cpu.stPushWord(RETURN-1)
    run(cpu)
    assert decorated[base+154] == 1 and decorated[colour_base+154] == 6
    assert (decorated[0xD3], decorated[0xD6]) == (1,7)
record('Aligned startup text and clear typing area with/without RAM expansion', 2)

# Status values survive read-and-clear; register and stack contracts are retained.
for value in range(256):
    cpu, mem = machine(entry=0xFE57)
    mem[0xBA], mem[0x297] = 2, value
    run(cpu)
    assert (cpu.a, cpu.x, cpu.y, cpu.sp, mem[0x297]) == (value, 0x37, 0x5A, 0xFF, 0)
for device in (0, 1, 3, 8, 31):
    cpu, mem = machine(entry=0xFE57)
    mem[0xBA], mem[0x90], mem[0x297] = device, 0xA5, 0xF3
    run(cpu)
    assert (cpu.a, mem[0x90], mem[0x297], cpu.x, cpu.y) == (0xA5, 0xA5, 0xF3, 0x37, 0x5A)
cpu, mem = machine(ORIGINAL, entry=0xFE57)
mem[0xBA], mem[0x297] = 2, 0x55
run(cpu)
assert cpu.a == 0, 'Original status bug did not reproduce'
record('RS-232 status values, other devices and original-bug reproduction', 262)

# Both handshake sites must follow user-port inputs regardless of keyboard outputs.
for user_port in (0, 0x40, 0x80, 0xC0):
    for keyboard in (0, 0x40, 0x80, 0xC0):
        cpu, mem = machine(entry=0xEFEE)
        mem[0x294], mem[0x298] = 1, 9
        mem[0x9110], mem[0x9120] = user_port, keyboard
        mem[0x29D], mem[0x29E], mem[0xF9], mem[0xFA] = 0, 1, 0, 8
        mem[0x800] = 0x41
        run(cpu)
        expected = 0x40 if not user_port & 0x80 else (0x10 if not user_port & 0x40 else 0)
        assert mem[0x297] == expected
        assert mem.transmitted == ([0x41] if expected == 0 else [])
        cpu, mem = machine(entry=0xF50C)
        mem[0x294], mem[0x9110], mem[0x9120] = 1, user_port, keyboard
        stop = run(cpu, stops=(RETURN, 0xF51B))
        assert stop == (0xF51B if user_port & 0x80 else RETURN)
        assert mem[0x297] == (0 if user_port & 0x80 else 0x40)
for entry in (0xEFEE, 0xF50C):
    cpu, mem = machine(ORIGINAL, entry=entry)
    mem[0x294], mem[0x9110], mem[0x9120] = 1, 0xC0, 0
    run(cpu, stops=(RETURN, 0xF51B))
    assert mem[0x297] == 0x40, 'Original wrong-VIA bug did not reproduce'
record('Transmit/open handshake inputs and original-bug reproduction', 34)

# Tape names use exactly the space available; guard bytes remain untouched.
for length in range(256):
    cpu, mem = machine(entry=0xF822)
    mem[0xB7], mem[0x9E], mem[0x9F] = length, 0, 5
    mem[0xB2], mem[0xB3], mem[0xBB], mem[0xBC] = 0x3C, 3, 0, 8
    data = bytes((i % 251) + 1 for i in range(255))
    mem[0x800:0x8FF] = data
    mem[0x33C:0x43C] = [0xCC] * 256
    run(cpu, stops=(0xF834,))
    copied = min(length, 187)
    assert bytes(mem[0x341:0x341 + copied]) == data[:copied]
    assert bytes(mem[0x341 + copied:0x43C]) == bytes([0xCC]) * (251 - copied)
    assert bytes(mem[0x33C:0x341]) == bytes([0xCC]) * 5
    assert mem[0xB7] == copied
cpu, mem = machine(ORIGINAL, entry=0xF822)
mem[0xB7], mem[0x9E], mem[0x9F] = 188, 0, 5
mem[0xB2], mem[0xB3], mem[0xBB], mem[0xBC] = 0x3C, 3, 0, 8
mem[0x800:0x8BC] = [0x41] * 188
mem[0x3FC] = 0xCC
run(cpu, stops=(0xF834,))
assert mem[0x3FC] == 0x41, 'Original tape overflow did not reproduce'
record('Every tape filename length 0-255, guards and original-bug reproduction', 257)

# Blocking input returns every byte, including zero, with original registers intact.
for value in range(256):
    cpu, mem = machine(entry=0xF26F)
    mem[0x29C], mem[0x29B], mem[0xF7], mem[0xF8] = 255, 0, 0, 8
    mem[0x8FF] = value
    run(cpu)
    assert (cpu.a, cpu.x, cpu.y, cpu.sp, mem[0x29C]) == (value, 0x37, 0x5A, 0xFF, 0)
    assert not cpu.p & cpu.CARRY
cpu, mem = machine(entry=0xF26F)
mem[0xF7], mem[0xF8] = 0, 8
for _ in range(40):
    assert cpu.pc != RETURN, 'Empty queue incorrectly returned'
    cpu.step()
mem[0x800], mem[0x29B] = 0, 1
run(cpu)
assert cpu.a == 0 and mem[0x29C] == 1
cpu, mem = machine(ORIGINAL, entry=0xF26F)
mem[0x29B], mem[0xF7], mem[0xF8] = 2, 0, 8
mem[0x800], mem[0x801] = 0, 0x41
run(cpu)
assert cpu.a == 0x41 and mem[0x29C] == 2, 'Original NUL loss did not reproduce'
record('Every receive byte, wraparound, empty-queue wait and original-bug reproduction', 258)

for high in (2, 0x10, 0x12, 0x20, 0x7F):
    for low in (0, 2, 0x45, 0xFF):
        cpu, mem = machine(entry=0xE187)
        mem[0x7A], mem[0x7B] = low, high
        stopped = run(cpu, stops=(RETURN, 0xCB1E))
        assert stopped == (0xCB1E if high == 2 else RETURN)
cpu, mem = machine(ORIGINAL, entry=0xE187)
mem[0x7A], mem[0x7B] = 0x45, 0x10
assert run(cpu, stops=(RETURN, 0xCB1E)) == 0xCB1E
record('VERIFY direct/program modes and original-bug reproduction', 21)


def tx_machine(rom, index=0):
    cpu, mem = machine(rom, entry=0xF0ED, a=0x42)
    mem[0xF9], mem[0xFA] = 0, 8
    mem[0x29D], mem[0x29E], mem[0x298] = index, index, 9
    mem[0x800 + index] = 0x99
    # A synthetic NMI wrapper saves registers and calls the real ROM consumer.
    mem[0x900:0x90D] = [0x48, 0x8A, 0x48, 0x98, 0x48, 0x20, 0xEE, 0xEF,
                          0x68, 0xA8, 0x68, 0xAA, 0x68]
    mem[0x90D] = 0x40
    mem[0xFFFA], mem[0xFFFB] = 0, 9
    return cpu, mem


def boundaries(rom):
    cpu, _ = tx_machine(rom)
    pcs = []
    while cpu.pc != RETURN:
        pcs.append(cpu.pc)
        cpu.step()
    return pcs


interrupt_cases = 0
for index in (0, 255):
    for boundary in boundaries(FIXED):
        cpu, mem = tx_machine(FIXED, index)
        injected = False
        for _ in range(1000):
            if cpu.pc == RETURN:
                break
            if cpu.pc == boundary and not injected:
                injected = True
                cpu.nmi()
            cpu.step()
        else:
            raise AssertionError('Transmit did not return')
        assert injected
        if not mem.transmitted:
            cpu.pc = 0xEFEE
            cpu.stPushWord(RETURN - 1)
            run(cpu)
        assert mem.transmitted == [0x42], (index, hex(boundary), mem.transmitted)
        assert cpu.sp == 0xFF
        interrupt_cases += 1
original_race_found = False
for boundary in boundaries(ORIGINAL):
    cpu, mem = tx_machine(ORIGINAL)
    injected = False
    for _ in range(1000):
        if cpu.pc == RETURN:
            break
        if cpu.pc == boundary and not injected:
            injected = True
            cpu.nmi()
        cpu.step()
    if 0x99 in mem.transmitted:
        original_race_found = True
assert original_race_found, 'Original transmit race did not reproduce'
cpu, mem = tx_machine(FIXED, 255)
mem[0x29D] = 0
mem[0x800] = 0xAA
for _ in range(40):
    assert cpu.pc != RETURN, 'Full queue incorrectly accepted data'
    cpu.step()
cpu.nmi()
run(cpu)
assert mem.transmitted == [0xAA]
assert (mem[0x8FF], mem[0x29D], mem[0x29E]) == (0x42, 1, 0)
interrupt_cases += 1
record('NMI at every transmit instruction boundary, queue wrap and original-race reproduction', interrupt_cases)

report = {
    'emulator': 'py65 1.2.0, NMOS 6502',
    'scope': 'Focused ROM-routine tests; VIA IER semantics modelled; no full VIC-20 peripheral emulation',
    'testGroups': len(results),
    'cases': sum(result['cases'] for result in results),
    'results': results,
    'limitations': ['No full-machine boot test', 'No PAL/NTSC hardware or real tape/RS-232 tests'],
}
(ROOT / 'verification/test-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'testGroups': report['testGroups'], 'cases': report['cases'], 'allPassed': True}))
