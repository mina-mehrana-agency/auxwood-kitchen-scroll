"""Turns the Blender renders into web images and writes akx.js from tools/akx.template.js.

Needs numpy and ffmpeg with libwebp. Run from the repo root:
    python tools/build.py <render folder with room/, pieces/ and shadows/>
"""
import base64
import glob
import json
import os
import subprocess
import sys

import numpy as np

SRC = sys.argv[1]
SIZES = {'l': (1920, 70, 74, 68), 's': (1280, 66, 62, 60)}  # name: width, quality of raw, room, parts
ATLAS_W = 2600


def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=width,height',
                          '-of', 'csv=p=0', path], capture_output=True, text=True, check=True).stdout.strip()
    return tuple(map(int, out.split(',')[:2]))


def read_rgba(path):
    w, h = probe(path)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 4).copy()


def write_png(arr, path):
    h, w = arr.shape[:2]
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{w}x{h}', '-i', '-',
                    '-frames:v', '1', '-update', '1', path], input=arr.tobytes(), check=True)


def webp(src, vf, out, q):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', vf, '-c:v', 'libwebp', '-preset', 'photo',
                    '-quality', str(q), '-compression_level', '6', '-frames:v', '1', '-update', '1', out], check=True)


def bleed(a, n=3):
    """Spread edge colours into transparent pixels so the image codec leaves no dark fringe."""
    rgb, mask = a[..., :3].astype(np.float32), a[..., 3] > 0
    for _ in range(n):
        s, c = np.zeros_like(rgb), np.zeros(mask.shape, np.float32)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            m = np.roll(mask, (dy, dx), (0, 1))
            s += np.roll(rgb, (dy, dx), (0, 1)) * m[..., None]
            c += m
        grow = (~mask) & (c > 0)
        rgb[grow] = s[grow] / c[grow][..., None]
        mask = mask | grow
    a[..., :3] = rgb.astype(np.uint8)
    return a


def main():
    os.makedirs('img', exist_ok=True)
    os.makedirs('source', exist_ok=True)
    beauty = f'{SRC}/room/render-0/beauty.png'
    rawp = f'{SRC}/room/render-0/raw.png'
    W, H = probe(beauty)

    # Pieces, trimmed and packed in order of height.
    meta = {}
    order = []
    for f in glob.glob(f'{SRC}/pieces/render-*/meta_*.json'):
        m = json.load(open(f))
        meta.update(m['boxes'])
        order = m['order']
    items = []
    for pid in order:
        path = glob.glob(f'{SRC}/pieces/render-*/p_{pid}.png')[0]
        a = read_rgba(path)
        ys, xs = np.where(a[..., 3] > 3)
        if len(xs) == 0:
            print('empty piece', pid)
            continue
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        b = meta[pid]
        left, bottom = round(b['x0'] * W), round(b['y0'] * H)
        top = H - bottom - a.shape[0]
        items.append({'id': pid, 'img': bleed(a[y0:y1, x0:x1].copy()), 'x': int(left + x0), 'y': int(top + y0)})
    pad = 4
    packed = sorted(items, key=lambda i: -i['img'].shape[0])
    cx, cy, row = pad, pad, 0
    for it in packed:
        h, w = it['img'].shape[:2]
        if cx + w + pad > ATLAS_W:
            cx, cy, row = pad, cy + row + pad, 0
        it['ax'], it['ay'] = cx, cy
        cx += w + pad
        row = max(row, h)
    AH = cy + row + pad
    atlas = np.zeros((AH, ATLAS_W, 4), np.uint8)
    for it in packed:
        h, w = it['img'].shape[:2]
        atlas[it['ay']:it['ay'] + h, it['ax']:it['ax'] + w] = it['img']
    write_png(atlas, 'source/parts-master.png')
    print('atlas', ATLAS_W, AH, 'pieces', len(items), 'fill', round(float((atlas[..., 3] > 0).mean()) * 100), '%')

    for name, (width, q_raw, q_room, q_parts) in SIZES.items():
        height = round(width * H / W)
        scale = f'scale={width}:{height}:flags=lanczos'
        webp(rawp, scale, f'img/raw-{name}.webp', q_raw)
        webp(beauty, scale, f'img/room-{name}.webp', q_room)
        k = width / W
        webp('source/parts-master.png', f'scale={round(ATLAS_W * k)}:{round(AH * k)}:flags=lanczos,format=yuva420p',
             f'img/parts-{name}.webp', q_parts)

    # Shadows: alpha only, small, one strip.
    groups = sorted(os.path.basename(p)[2:-4] for p in glob.glob(f'{SRC}/shadows/render-0/s_*.png'))
    sw, sh = 320, round(320 * H / W)
    strip = np.zeros((sh * len(groups), sw, 4), np.uint8)
    for i, g in enumerate(groups):
        write_png(np.zeros((4, 4, 4), np.uint8), 'source/_t.png')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{SRC}/shadows/render-0/s_{g}.png', '-vf', f'scale={sw}:{sh}:flags=area',
                        '-frames:v', '1', '-update', '1', 'source/_t.png'], check=True)
        a = read_rgba('source/_t.png')
        a[..., :3] = 0
        # Soft and in few levels: render noise in the alpha channel is what makes this file heavy.
        al = a[..., 3].astype(np.float32)
        for _ in range(3):
            al = (np.roll(al, 1, 0) + np.roll(al, -1, 0) + np.roll(al, 1, 1) + np.roll(al, -1, 1) + al * 4) / 8
        al = np.round(al / 6) * 6
        al[al < 8] = 0
        a[..., 3] = np.clip(al, 0, 255).astype(np.uint8)
        strip[i * sh:(i + 1) * sh] = a
    os.remove('source/_t.png')
    write_png(strip, 'source/shadows-master.png')
    webp('source/shadows-master.png', 'format=yuva420p', 'img/shadows.webp', 40)

    # Inline placeholder of the raw room.
    webp(rawp, 'scale=32:18:flags=area,hue=s=0', 'source/_lqip.webp', 45)
    lqip = 'data:image/webp;base64,' + base64.b64encode(open('source/_lqip.webp', 'rb').read()).decode()
    os.remove('source/_lqip.webp')

    data = {'W': W, 'H': H, 'A': [ATLAS_W, AH], 'S': groups,
            'P': [{'id': i['id'], 'x': i['x'], 'y': i['y'], 'w': i['img'].shape[1], 'h': i['img'].shape[0], 'ax': i['ax'], 'ay': i['ay']} for i in items]}
    js = open('tools/akx.template.js', encoding='utf8').read().replace('__DATA__', json.dumps(data, separators=(',', ':'))).replace('__LQIP__', lqip)
    open('akx.js', 'w', encoding='utf8', newline='\n').write(js)

    total = {'l': 0, 's': 0}
    for f in sorted(os.listdir('img')):
        size = os.path.getsize(f'img/{f}')
        print(f, size)
        for n in total:
            if f.endswith(f'-{n}.webp') or f == 'shadows.webp':
                total[n] += size
    print('akx.js', os.path.getsize('akx.js'), 'totals', total)


if __name__ == '__main__':
    main()
