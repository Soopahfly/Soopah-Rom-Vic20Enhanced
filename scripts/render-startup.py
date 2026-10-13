"""Render screen RAM produced by the tested ROM, using stock character bitmaps."""
import json
import runpy
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
core = runpy.run_path(str(ROOT/'tests/test_vic20.py'))
memory, base = core['boot_to_input'](core['FIXED'], False)
colour_base = 0x9400 | (base & 0x300)

# Stock 901460-03 character rows used by the unexpanded startup screen.
glyphs = {
    ' ':[0,0,0,0,0,0,0,0], '.':[0,0,0,0,0,24,24,0],
    '2':[60,66,2,12,48,64,126,0], '3':[60,66,2,28,2,66,60,0],
    '5':[126,64,120,4,2,68,56,0], '6':[28,32,64,124,66,66,60,0],
    '8':[60,66,66,60,66,66,60,0], 'A':[24,36,66,126,66,66,66,0],
    'B':[124,34,34,60,34,34,124,0], 'C':[28,34,64,64,64,34,28,0],
    'D':[120,36,34,34,34,36,120,0], 'E':[126,64,64,120,64,64,126,0],
    'F':[126,64,64,120,64,64,64,0], 'I':[28,8,8,8,8,8,28,0],
    'M':[66,102,90,90,66,66,66,0], 'R':[124,66,66,124,72,68,66,0],
    'S':[60,66,64,60,2,66,60,0], 'T':[62,8,8,8,8,8,8,0],
    'V':[66,66,66,36,36,24,24,0], 'Y':[34,34,34,28,8,8,8,0],
}
bitmaps = {ord(c)-64 if 'A' <= c <= 'Z' else ord(c):rows for c,rows in glyphs.items()}
bitmaps[0xA0] = [255]*8
bitmaps[0x69] = [255,254,252,248,240,224,192,128]
# RGB approximations, not a claim about analogue VIC colour calibration.
palette = {1:(255,255,255),2:(182,31,33),3:(77,240,255),
           5:(68,213,68),6:(33,36,255),7:(220,215,27)}
width,height = 256,240
pixels = [palette[3]]*(width*height)
for y in range(184):
    for x in range(176):
        pixels[(28+y)*width+40+x] = palette[1]
for cell in range(506):
    rows = bitmaps[memory[base+cell]]
    colour = palette[memory[colour_base+cell] & 7]
    for y,mask in enumerate(rows):
        for x in range(8):
            if mask & (128 >> x):
                px,py = 40+(cell%22)*8+x,28+(cell//22)*8+y
                pixels[py*width+px] = colour
# Show the first visible blink phase at the editor's actual input position.
col,row = memory[0xD3],memory[0xD6]
for y in range(8):
    for x in range(8):
        pixels[(28+row*8+y)*width+40+col*8+x] = palette[6]

scale = 2
scanlines = bytearray()
for y in range(height):
    line = b''.join(bytes(pixel)*scale for pixel in pixels[y*width:(y+1)*width])
    scanlines.extend((b'\x00'+line)*scale)
def chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xFFFFFFFF)
png = (b'\x89PNG\r\n\x1a\n'
       +chunk(b'IHDR',struct.pack('>IIBBBBB',width*scale,height*scale,8,2,0,0,0))
       +chunk(b'IDAT',zlib.compress(scanlines,9))+chunk(b'IEND',b''))
destination = ROOT/'docs/startup-screen.png'
destination.write_bytes(png)
(ROOT/'build/startup-screen.json').write_text(json.dumps({
    'screenBase':base,'cursor':{'column':col,'row':row},
    'screen':list(memory[base:base+506]),
    'colours':list(memory[colour_base:colour_base+506]),
    'limits':'ROM-instruction screen RAM, approximate RGB and a visible cursor phase'
},indent=2)+'\n')
print(destination)
