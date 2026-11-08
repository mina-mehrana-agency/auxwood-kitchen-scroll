"""Builds the web images from the 2752x1536 masters in source/ (git-ignored).

Needs numpy and ffmpeg with libwebp. Run from the repo root:
    python tools/build-assets.py
"""
import base64
import os
import subprocess

import numpy as np

W, H = 2752, 1536
# Outline of the island in the real project photo, in master pixels.
ISLAND = [(908, 884), (950, 868), (1040, 856), (1147, 843), (1260, 830), (1376, 816), (1490, 805), (1604, 797),
          (1719, 797), (1833, 800), (1900, 808), (1934, 820), (1930, 828), (1921, 838), (1921, 1207), (1880, 1203),
          (1835, 1200), (1135, 1423), (1135, 1476), (1080, 1468), (1020, 1455), (975, 1437), (945, 1410), (932, 1380),
          (932, 905), (915, 895)]
# name: (width, quality of raw, quality of room, quality of island)
SIZES = {'l': (1920, 52, 62, 68), 's': (1280, 50, 58, 64)}


def read_rgb(path):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, np.uint8).reshape(H, W, 3)


def poly_mask(poly, w, h, ss=4):
    """Anti-aliased scanline fill of a simple polygon."""
    pts = np.array(poly, float) * ss
    mask = np.zeros((h * ss, w * ss), np.uint8)
    n = len(pts)
    for row in range(h * ss):
        y = row + 0.5
        xs = []
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if (y1 <= y < y2) or (y2 <= y < y1):
                xs.append(x1 + (y - y1) / (y2 - y1) * (x2 - x1))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            mask[row, max(0, int(a)):max(0, int(b))] = 255
    return mask.reshape(h, ss, w, ss).mean(axis=(1, 3))


def blur(a, r):
    """Box blur of radius r."""
    c = np.cumsum(np.cumsum(np.pad(a, ((r + 1, r), (r + 1, r)), mode='edge'), axis=0), axis=1)
    d = 2 * r + 1
    return (c[d:, d:] - c[:-d, d:] - c[d:, :-d] + c[:-d, :-d]) / d ** 2


def webp(src, vf, out, quality):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', vf, '-c:v', 'libwebp', '-preset', 'photo',
                    '-quality', str(quality), '-compression_level', '6', '-frames:v', '1', '-update', '1', out],
                   check=True)


def main():
    os.makedirs('img', exist_ok=True)

    # The island keeps the true pixels of the real photo, with a soft alpha from its outline.
    e = read_rgb('source/e16.png')
    x0, y0 = min(p[0] for p in ISLAND) - 4, min(p[1] for p in ISLAND) - 4
    x1, y1 = max(p[0] for p in ISLAND) + 4, max(p[1] for p in ISLAND) + 4
    cw, ch = x1 - x0, y1 - y0
    alpha = poly_mask([(px - x0, py - y0) for px, py in ISLAND], cw, ch)
    rgba = np.dstack([e[y0:y1, x0:x1], alpha.astype(np.uint8)]).astype(np.uint8)
    master = 'source/island-master.png'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{cw}x{ch}', '-i', '-',
                    '-frames:v', '1', '-update', '1', master], input=rgba.tobytes(), check=True)
    print('island box', x0, y0, cw, ch)

    # Floor shadow: how much darker the real photo is than the no-island image, outside the island.
    n = read_rgb('source/finished16.png')
    ratio = blur(e.mean(axis=2), 14) / np.maximum(blur(n.mean(axis=2), 14), 1)
    dark = np.clip(1 - ratio - 0.03, 0, 1)
    full = np.zeros((H, W), float)
    full[y0:y1, x0:x1] = alpha / 255
    dark *= 1 - full
    sx0, sy0, sx1, sy1 = 500, 780, 2250, 1536
    crop = (dark[sy0:sy1, sx0:sx1] * 255).astype(np.uint8)
    black = np.zeros(crop.shape + (3,), np.uint8)
    shadow = np.dstack([black, crop]).astype(np.uint8)
    master2 = 'source/shadow-master.png'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba',
                    '-s', f'{sx1 - sx0}x{sy1 - sy0}', '-i', '-', '-frames:v', '1', '-update', '1', master2],
                   input=shadow.tobytes(), check=True)
    webp(master2, f'scale={(sx1 - sx0) // 4}:{(sy1 - sy0) // 4}:flags=area,format=yuva420p', 'img/shadow.webp', 50)

    for name, (width, q_raw, q_room, q_island) in SIZES.items():
        height = round(width * H / W)
        scale = f'scale={width}:{height}:flags=lanczos'
        webp('source/raw16.jpg', scale, f'img/raw-{name}.webp', q_raw)
        webp('source/finished16.png', scale, f'img/room-{name}.webp', q_room)
        s = width / W
        webp(master, f'scale={round(cw * s)}:{round(ch * s)}:flags=lanczos,format=yuva420p',
             f'img/island-{name}.webp', q_island)

    # Tiny placeholder inlined in the page, so the first paint is never empty.
    tmp = 'source/_lqip.webp'
    webp('source/raw16.jpg', 'scale=32:18:flags=area,hue=s=0', tmp, 45)
    print('lqip data:image/webp;base64,' + base64.b64encode(open(tmp, 'rb').read()).decode())
    os.remove(tmp)

    for f in sorted(os.listdir('img')):
        print(f, os.path.getsize(f'img/{f}'))


if __name__ == '__main__':
    main()
