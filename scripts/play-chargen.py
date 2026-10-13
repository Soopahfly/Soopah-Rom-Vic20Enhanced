"""Build optional CHARGEN fonts; never alter BASIC, KERNAL or stock ROMs.

Requires Pillow and reference/characters.901460-03.bin from:
https://www.zimmers.net/anonftp/pub/cbm/firmware/characters/vic20.bin
Previews use screen RAM from the stable ROM's reset path by default.
"""
import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/chargen'
sys.path.insert(0, str(ROOT / '.tools'))
from py65.devices.mpu6502 import MPU

# Five-bit rows, centred inside the unchanged eight-pixel character cell.
# Hand-drawn letters avoid scaling artefacts and preserve meaningful strokes.
CLEAN = {
    'A':'0E11111F111111', 'B':'1E11111E11111E', 'C':'0F10101010100F',
    'D':'1E11111111111E', 'E':'1F10101E10101F', 'F':'1F10101E101010',
    'G':'0F10101711110F', 'H':'1111111F111111', 'I':'0E04040404040E',
    'J':'0702020212120C', 'K':'11121418141211', 'L':'1010101010101F',
    'M':'111B1515111111', 'N':'11191513111111', 'O':'0E11111111110E',
    'P':'1E11111E101010', 'Q':'0E11111115120D', 'R':'1E11111E141211',
    'S':'0F10100E01011E', 'T':'1F040404040404', 'U':'1111111111110E',
    'V':'11111111110A04', 'W':'11111115151B11', 'X':'11110A040A1111',
    'Y':'11110A04040404', 'Z':'1F01020408101F',
    '0':'0E11131519110E', '1':'040C040404040E', '2':'0E11010204081F',
    '3':'1E01010E01011E', '4':'02060A121F0202', '5':'1F10101E01011E',
    '6':'0E10101E11110E', '7':'1F010204080808', '8':'0E11110E11110E',
    '9':'0E11110F01010E', '.':'00000000000606',
}
COMPACT = {
    'A':'0E111F111111', 'B':'1E111E11111E', 'C':'0F101010100F',
    'D':'1E111111111E', 'E':'1F101E10101F', 'F':'1F101E101010',
    'G':'0F101017110F', 'H':'11111F111111', 'I':'0E040404040E',
    'J':'07020212120C', 'K':'111218141211', 'L':'10101010101F',
    'M':'111B15111111', 'N':'111915131111', 'O':'0E111111110E',
    'P':'1E111E101010', 'Q':'0E111115120D', 'R':'1E111E141211',
    'S':'0F100E01011E', 'T':'1F0404040404', 'U':'11111111110E',
    'V':'111111110A04', 'W':'111115151B11', 'X':'110A040A1111',
    'Y':'11110A040404', 'Z':'1F010204081F',
    '0':'0E111515110E', '1':'040C0404040E', '2':'0E110204081F',
    '3':'1E010E01011E', '4':'02060A1F0202', '5':'1F101E01011E',
    '6':'0E101E11110E', '7':'1F0102040808', '8':'0E110E11110E',
    '9':'0E11110F010E', '.':'000000000606',
}


def make_rom(stock, glyphs, height):
    result = bytearray(stock)
    allowed = set()
    for char, encoded in glyphs.items():
        rows = bytes.fromhex(encoded)
        assert len(rows) == height and all(row < 32 for row in rows)
        rows = bytes(row << 2 for row in rows) + bytes(8-height)
        # Uppercase/graphics: A at 1. Mixed case: A at 65, lowercase untouched.
        codes = ((0, ord(char)-64), (2048, ord(char))) if char.isalpha() else (
            (0, ord(char)), (2048, ord(char)))
        for bank, code in codes:
            for reverse in (0, 128):
                offset = bank + (code+reverse)*8
                bitmap = bytes(row ^ (255 if reverse else 0) for row in rows)
                result[offset:offset+8] = bitmap
                allowed.update(range(offset, offset+8))
    # Reuse the stock mixed-case diagonal stripes seen in the user's VICE
    # screen. CHARGEN cannot colour individual pixels: gaps use the background.
    # Code $69 is a full patterned tile, not a striped triangular wedge.
    striped_tip = stock[2048+0x69*8:2048+0x6A*8]
    assert striped_tip == bytes.fromhex('993366CC993366CC')
    for reverse in (0,128):
        offset = (0x69+reverse)*8
        result[offset:offset+8] = bytes(v ^ (255 if reverse else 0) for v in striped_tip)
        allowed.update(range(offset,offset+8))
    assert result[0x69*8:0x6A*8] == result[2048+0x69*8:2048+0x6A*8]
    assert result[0xA0*8:0xA1*8] == stock[0xA0*8:0xA1*8]  # Solid rainbow blocks.
    assert len(result) == 4096
    assert all(a == b or i in allowed for i, (a,b) in enumerate(zip(stock,result)))
    for bank in (0,2048):
        for code in range(128):
            if bank + code*8 in allowed:
                start = bank + code*8
                assert result[start+1024:start+1032] == bytes(v ^ 255 for v in result[start:start+8])
    return bytes(result), len(allowed)//8


def boot_screen(universal):
    # Load only fixture definitions, avoiding test-suite/report side effects.
    global RETURN
    RETURN = 0x7FFF
    tree = ast.parse((ROOT / 'tests/test_vic20.py').read_text())
    nodes = [node for node in tree.body if isinstance(node, (ast.ClassDef,ast.FunctionDef))
             and node.name in ('Memory','BootMemory','run','boot_to_input')]
    exec(compile(ast.Module(body=nodes,type_ignores=[]), 'boot-fixtures', 'exec'), globals())
    rom = (ROOT / ('build/universal/vic20-universal.bin' if universal else 'build/vic20-fixed.bin')).read_bytes()
    memory, base = boot_to_input(rom, False)
    if universal:
        assert memory[0x2A6] & 128  # Static raster uses the detector's PAL fallback.
        assert bytes(memory[base+72:base+75]) == bytes([16,1,12])
    return memory, base


def render(rom, memory, base):
    # Approximate RGB only; this is not a VIC analogue-video emulation.
    palette = [(0,0,0),(255,255,255),(182,31,33),(77,240,255),
               (180,40,200),(68,213,68),(33,36,255),(220,215,27)]
    image = Image.new('RGB', (256,240), palette[3])
    draw = ImageDraw.Draw(image)
    draw.rectangle((40,28,215,211), fill=palette[1])
    colour_base = 0x9400 | (base & 0x300)
    for cell in range(506):
        code = memory[base+cell]
        rows = rom[code*8:code*8+8]
        for y, mask in enumerate(rows):
            for x in range(8):
                if mask & (128 >> x):
                    image.putpixel((40+cell%22*8+x,28+cell//22*8+y),
                                   palette[memory[colour_base+cell]&7])
    col,row = memory[0xD3],memory[0xD6]
    draw.rectangle((40+col*8,28+row*8,47+col*8,35+row*8), fill=palette[6])
    return image.resize((512,480), Image.Resampling.NEAREST)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--universal', action='store_true', help='Preview the universal PAL fallback screen instead of stable PAL')
    parser.add_argument('--check-published', action='store_true', help='Check that the generated fonts match the main repository downloads')
    args = parser.parse_args()
    stock = (ROOT / 'reference/characters.901460-03.bin').read_bytes()
    assert len(stock) == 4096, 'Requires the 4 KB 901460-03 ROM'
    assert hashlib.sha256(stock).hexdigest() == 'bda280726cfe069ca70ef5e2f2d95a29f69d3950c859a12e6979464963fcf502', 'Unexpected stock CHARGEN'
    assert stock[8:16] == bytes([24,36,66,126,66,66,66,0])
    OUT.mkdir(parents=True, exist_ok=True)
    memory, base = boot_screen(args.universal)
    variants = [('stock',stock,0), ('clean-5x7',*make_rom(stock,CLEAN,7)),
                ('compact-5x6',*make_rom(stock,COMPACT,6))]
    comparison = Image.new('RGB',(1536,532),(238,241,244))
    draw = ImageDraw.Draw(comparison)
    font = ImageFont.load_default(size=20)
    report = {'source':'https://www.zimmers.net/anonftp/pub/cbm/firmware/characters/vic20.bin',
              'stockSha256':hashlib.sha256(stock).hexdigest(), 'variants':[],
              'startup':'universal PAL fallback' if args.universal else 'stable PAL',
              'rainbow':'Uppercase screen code $69 uses stock mixed-case diagonal stripes, with matching inverse.',
              'limitations':'ROM-executed screen; approximate colours. Previous font versions were user-tested at PAL startup in VICE; updated uppercase striped tips are not yet VICE/hardware-tested. Lowercase and other punctuation remain stock.'}
    for index,(name,rom,count) in enumerate(variants):
        preview = render(rom,memory,base)
        preview.save(OUT / f'{name}.png')
        comparison.paste(preview,(index*512,52))
        draw.text((index*512+20,16),name.upper().replace('-',' '), fill=(30,35,40),font=font)
        if name != 'stock':
            (OUT / f'chargen-{name}.bin').write_bytes(rom)
            if args.check_published:
                assert (ROOT / f'roms/chargen/chargen-{name}.bin').read_bytes() == rom, f'Published font differs: {name}'
        report['variants'].append({'name':name,'bytes':len(rom),'modifiedGlyphSlots':count,
                                   'sha256':hashlib.sha256(rom).hexdigest()})
    comparison.save(OUT / 'comparison.png')
    (OUT / 'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS: both 4096-byte sketches preserve all non-target glyphs and matching inverses.\n{OUT / "comparison.png"}')


if __name__ == '__main__':
    main()
