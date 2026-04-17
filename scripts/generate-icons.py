"""Generate PWA icons for Inkdown."""
import struct
import zlib
import os

def create_png(width, height, pixels):
    """Create a minimal PNG from raw RGBA pixel data."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack('>I', len(data)) + c + crc

    raw = b''
    for y in range(height):
        raw += b'\x00'
        for x in range(width):
            idx = (y * width + x) * 4
            raw += bytes(pixels[idx:idx+4])

    signature = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    idat = zlib.compress(raw, 9)

    return signature + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')

def draw_icon(size, maskable=False):
    """Draw the Inkdown icon: green document icon on dark slate background."""
    pixels = [0] * (size * size * 4)
    bg = (15, 23, 42, 255)      # #0F172A
    fg = (34, 197, 94, 255)     # #22C55E

    safe_zone = size * 0.1 if maskable else 0

    for y in range(size):
        for x in range(size):
            idx = (y * size + x) * 4
            pixels[idx:idx+4] = bg

    icon_size = size - int(safe_zone * 2)
    offset = int(safe_zone)

    doc_w = int(icon_size * 0.5)
    doc_h = int(icon_size * 0.65)
    doc_x = offset + (icon_size - doc_w) // 2
    doc_y = offset + (icon_size - doc_h) // 2
    fold = int(doc_w * 0.3)
    border = max(1, size // 64)

    for y in range(doc_y, doc_y + doc_h):
        for x in range(doc_x, doc_x + doc_w):
            if x - doc_x > doc_w - fold and y - doc_y < fold:
                continue
            iy = y - doc_y
            ix = x - doc_x
            is_border = (iy < border or iy >= doc_h - border or
                        ix < border or ix >= doc_w - border)
            if x - doc_x == doc_w - fold and y - doc_y < fold:
                is_border = True
            if y - doc_y == fold and x - doc_x >= doc_w - fold:
                is_border = True

            if is_border:
                idx = (y * size + x) * 4
                pixels[idx:idx+4] = fg

    for dy in range(fold):
        for dx in range(fold):
            if dx + dy >= fold - border:
                x = doc_x + doc_w - fold + dx
                y = doc_y + dy
                if 0 <= x < size and 0 <= y < size:
                    idx = (y * size + x) * 4
                    if dx + dy <= fold:
                        pixels[idx:idx+4] = fg

    line_h = max(1, size // 48)
    line_gap = max(3, size // 24)
    line_start_x = doc_x + int(doc_w * 0.15)
    line_start_y = doc_y + int(doc_h * 0.35)

    for i in range(4):
        ly = line_start_y + i * line_gap
        line_w = int(doc_w * (0.7 if i < 3 else 0.45))
        if i == 0:
            line_w = int(doc_w * 0.5)
        for y in range(ly, min(ly + line_h, doc_y + doc_h - border)):
            for x in range(line_start_x, min(line_start_x + line_w, doc_x + doc_w - border)):
                idx = (y * size + x) * 4
                pixels[idx:idx+4] = fg

    return create_png(size, size, pixels)

os.makedirs('public/icons', exist_ok=True)

for size in [192, 512]:
    png = draw_icon(size, maskable=False)
    with open(f'public/icons/icon-{size}.png', 'wb') as f:
        f.write(png)
    print(f'Created icon-{size}.png ({len(png)} bytes)')

    png = draw_icon(size, maskable=True)
    with open(f'public/icons/icon-maskable-{size}.png', 'wb') as f:
        f.write(png)
    print(f'Created icon-maskable-{size}.png ({len(png)} bytes)')

# Favicon (simple 32x32)
png = draw_icon(32, maskable=False)
with open('public/favicon.png', 'wb') as f:
    f.write(png)
print(f'Created favicon.png ({len(png)} bytes)')

print('Done!')
