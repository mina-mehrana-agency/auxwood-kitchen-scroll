"""The kitchen as a real 3D model, rendered with Cycles. Units are metres; X right, Y into the room, Z up.

Run headless:
    blender -b -noaudio --python tools/render/scene.py -- --mode beauty,raw --width 960 --spp 24 --out out

Modes:
    beauty        finished room with everything in place
    raw           the raw construction-stage room
    pieces        every piece alone, lit as in the finished room, with transparency (use --chunk i/n to split)
    shadows       the soft shadow each group throws on the raw room, alpha only
"""
import argparse
import json
import math
import os
import random
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument('--mode', default='beauty')
ap.add_argument('--width', type=int, default=960)
ap.add_argument('--spp', type=int, default=24)
ap.add_argument('--chunk', default='0/1')
ap.add_argument('--out', default='out')
ARGS = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
os.makedirs(ARGS.out, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
coll = scene.collection
random.seed(7)

# ------------------------------------------------------------------ room dimensions
XL, XR, YB, YF, H = -4.1, 4.1, 6.0, -3.0, 2.9
DEPTH = 0.62
FRONT = YB - DEPTH  # front plane of the back run
PLINTH, BASE_TOP, TOP_T, TALL = 0.1, 0.86, 0.04, 2.45
UP0, UP1 = 1.5, 2.45

# ------------------------------------------------------------------ materials


def srgb(hex_):
    hex_ = hex_.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(hex_[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1)


def base_mat(name, color='#ffffff', rough=0.5, metal=0.0, bevel=0.0025):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = srgb(color)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    normal = None
    if bevel:
        b = nt.nodes.new('ShaderNodeBevel')
        b.samples = 3
        b.inputs['Radius'].default_value = bevel
        normal = b.outputs['Normal']
        nt.links.new(normal, p.inputs['Normal'])
    return m, nt, p, normal


def plain(name, color, rough=0.5, metal=0.0, bevel=0.0025):
    return base_mat(name, color, rough, metal, bevel)[0]


def emit(name, color, strength):
    m, nt, p, _ = base_mat(name, '#000000', 1, 0, 0)
    p.inputs['Emission Color'].default_value = srgb(color)
    p.inputs['Emission Strength'].default_value = strength
    return m


def coords(nt, scale=(1, 1, 1), rot=(0, 0, 0)):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = scale
    mp.inputs['Rotation'].default_value = rot
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    return mp.outputs[0]


def ramp(nt, fac, stops):
    r = nt.nodes.new('ShaderNodeValToRGB')
    cr = r.color_ramp
    cr.elements[0].position, cr.elements[0].color = stops[0][0], srgb(stops[0][1])
    cr.elements[1].position, cr.elements[1].color = stops[-1][0], srgb(stops[-1][1])
    for pos, col in stops[1:-1]:
        e = cr.elements.new(pos)
        e.color = srgb(col)
    nt.links.new(fac, r.inputs['Fac'])
    return r.outputs[0]


def noise(nt, vec, scale=1, detail=6, rough=0.55, dist=0):
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    n.inputs['Distortion'].default_value = dist
    nt.links.new(vec, n.inputs['Vector'])
    return n.outputs[0]


def bump(nt, p, height, strength, dist, normal=None):
    b = nt.nodes.new('ShaderNodeBump')
    b.inputs['Strength'].default_value = strength
    b.inputs['Distance'].default_value = dist
    nt.links.new(height, b.inputs['Height'])
    if normal is not None:
        nt.links.new(normal, b.inputs['Normal'])
    nt.links.new(b.outputs['Normal'], p.inputs['Normal'])


def wood(name, axis='z', dark='#3c2415', mid='#6b4427', light='#94673f', rough=0.38):
    m, nt, p, normal = base_mat(name, rough=rough)
    scale = {'z': (42, 42, 1.3), 'x': (1.3, 42, 42), 'y': (42, 1.3, 42)}[axis]
    v = coords(nt, scale)
    grain = noise(nt, v, 1, 7, 0.62, 1.4)
    col = ramp(nt, grain, [(0.3, dark), (0.5, mid), (0.72, light)])
    nt.links.new(col, p.inputs['Base Color'])
    fine = noise(nt, coords(nt, tuple(s * 9 for s in scale)), 1, 3, 0.5)
    bump(nt, p, fine, 0.12, 0.002, normal)
    return m


def marble(name, base='#f3f0ea', vein='#b3aea5', scale=1.6, rough=0.16):
    m, nt, p, normal = base_mat(name, base, rough, bevel=0.0015)
    w = nt.nodes.new('ShaderNodeTexWave')
    w.wave_type = 'BANDS'
    w.bands_direction = 'DIAGONAL'
    w.inputs['Scale'].default_value = scale
    w.inputs['Distortion'].default_value = 8
    w.inputs['Detail'].default_value = 7
    w.inputs['Detail Scale'].default_value = 1.3
    w.inputs['Detail Roughness'].default_value = 0.6
    nt.links.new(coords(nt), w.inputs['Vector'])
    col = ramp(nt, w.outputs[1], [(0.0, vein), (0.035, base), (1.0, base)])
    nt.links.new(col, p.inputs['Base Color'])
    return m


def concrete(name, a='#8d8a84', b='#a7a39c', c='#6f6c67', big=1.1, rough=0.86, bump_k=0.5):
    m, nt, p, normal = base_mat(name, a, rough, bevel=0)
    v = coords(nt)
    n1 = noise(nt, v, big, 8, 0.6, 0.3)
    col = ramp(nt, n1, [(0.32, c), (0.5, a), (0.68, b)])
    n2 = noise(nt, v, big * 26, 6, 0.65)
    mix = nt.nodes.new('ShaderNodeMixRGB')
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Fac'].default_value = 0.2
    nt.links.new(col, mix.inputs['Color1'])
    nt.links.new(ramp(nt, n2, [(0.35, '#b5b5b5'), (0.65, '#ffffff')]), mix.inputs['Color2'])
    nt.links.new(mix.outputs[0], p.inputs['Base Color'])
    bump(nt, p, n2, bump_k, 0.006)
    return m


def tile_floor(name):
    m, nt, p, normal = base_mat(name, '#d9d2c5', 0.28, bevel=0)
    v = coords(nt)
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.offset = 0
    br.inputs['Scale'].default_value = 1
    br.inputs['Mortar Size'].default_value = 0.0022
    br.inputs['Mortar Smooth'].default_value = 0.1
    br.inputs['Brick Width'].default_value = 0.9
    br.inputs['Row Height'].default_value = 0.9
    nt.links.new(v, br.inputs['Vector'])
    stone = ramp(nt, noise(nt, v, 2.4, 8, 0.6, 0.6), [(0.34, '#c9c1b2'), (0.55, '#dcd5c8'), (0.75, '#e8e2d7')])
    nt.links.new(stone, br.inputs['Color1'])
    nt.links.new(stone, br.inputs['Color2'])
    br.inputs['Mortar'].default_value = srgb('#8e887c')
    nt.links.new(br.outputs['Color'], p.inputs['Base Color'])
    bump(nt, p, br.outputs['Fac'], -0.5, 0.002)
    return m


MAT = {
    'blue': plain('blue', '#9fb6c1', 0.42),
    'blue2': plain('blue2', '#93abb7', 0.45),
    'carcass': plain('carcass', '#2a2c2e', 0.7, bevel=0),
    'walnut': wood('walnut'),
    'walnutx': wood('walnutx', 'x'),
    'slat': wood('slat', 'z', '#4a2d1a', '#7a5130', '#a2754a', 0.5),
    'oakx': wood('oakx', 'x', '#b08c62', '#c9a67c', '#dcbf9b', 0.45),
    'stone': marble('stone'),
    'stonedark': marble('stonedark', '#262729', '#cfc7b6', 1.8, 0.14),
    'brass': plain('brass', '#c79a57', 0.26, 1, 0.001),
    'steel': plain('steel', '#d2d4d5', 0.3, 1, 0.0015),
    'sinksteel': plain('sinksteel', '#d4d6d7', 0.55, 0.5, 0.001),
    'black': plain('black', '#17181a', 0.42, 0, 0.0015),
    'glassblack': plain('glassblack', '#08090a', 0.06, 0, 0.001),
    'ceramic': plain('ceramic', '#efece6', 0.18, 0, 0.001),
    'ceramicdark': plain('ceramicdark', '#3a3d40', 0.25, 0, 0.001),
    'terracotta': plain('terracotta', '#b96a42', 0.68),
    'leaf': plain('leaf', '#566b3e', 0.5, 0, 0),
    'leaf2': plain('leaf2', '#74885a', 0.5, 0, 0),
    'bark': plain('bark', '#5d4a38', 0.8, 0, 0),
    'coffee': plain('coffee', '#2c1a10', 0.6, 0, 0.001),
    'leather': plain('leather', '#6f4a2e', 0.5, 0, 0.004),
    'led': emit('led', '#ffd9a6', 7),
    'bulb': emit('bulb', '#ffe2b5', 22),
    'spot': emit('spot', '#fff0d8', 18),
    'wall': plain('wall', '#efeae1', 0.75, 0, 0),
    'ceiling': plain('ceiling', '#f6f3ee', 0.8, 0, 0),
    'trim': plain('trim', '#ded8cc', 0.6),
    'floor': tile_floor('floor'),
    'frame': plain('frame', '#1c1d1f', 0.4),
    'rawwall': concrete('rawwall', '#b8b4ac', '#c6c2ba', '#a6a29a', 0.9, 0.86, 0.35),
    'rawfloor': concrete('rawfloor', '#a9a69f', '#b8b5ad', '#97948d', 0.7, 0.9, 0.6),
    'rawceil': concrete('rawceil', '#b0aca5', '#bdb9b2', '#9f9b94', 1.3),
    'pvc': plain('pvc', '#3f4144', 0.55, 0, 0.001),
    'copper': plain('copper', '#b4744a', 0.3, 1, 0.001),
    'wire': plain('wire', '#a8352a', 0.5, 0, 0),
}

# ------------------------------------------------------------------ geometry helpers

PIECES, ORDER = {}, []
ENV_DONE, ENV_RAW, HELPERS = [], [], []
CUR = [ENV_DONE]


class piece:
    def __init__(self, pid):
        self.pid = pid

    def __enter__(self):
        PIECES.setdefault(self.pid, [])
        if self.pid not in ORDER:
            ORDER.append(self.pid)
        self.prev = CUR[0]
        CUR[0] = PIECES[self.pid]

    def __exit__(self, *a):
        CUR[0] = self.prev


class env:
    def __init__(self, target):
        self.target = target

    def __enter__(self):
        self.prev = CUR[0]
        CUR[0] = self.target

    def __exit__(self, *a):
        CUR[0] = self.prev


class B:
    """Collects geometry and turns it into one object."""

    def __init__(self):
        self.v, self.f = [], []

    def box(self, x0, x1, y0, y1, z0, z1):
        n = len(self.v)
        self.v += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        self.f += [(n, n + 3, n + 2, n + 1), (n + 4, n + 5, n + 6, n + 7), (n, n + 1, n + 5, n + 4), (n + 1, n + 2, n + 6, n + 5),
                   (n + 2, n + 3, n + 7, n + 6), (n + 3, n, n + 4, n + 7)]
        return self

    def prism(self, ring, z0, z1):
        n, k = len(self.v), len(ring)
        self.v += [(x, y, z0) for x, y in ring] + [(x, y, z1) for x, y in ring]
        self.f.append(tuple(n + i for i in range(k)))
        self.f.append(tuple(n + k + i for i in range(k)))
        for i in range(k):
            j = (i + 1) % k
            self.f.append((n + i, n + j, n + k + j, n + k + i))
        return self

    def cyl(self, cx, cy, r, z0, z1, seg=14):
        return self.prism([(cx + r * math.cos(2 * math.pi * i / seg), cy + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)], z0, z1)

    def lathe(self, cx, cy, prof, seg=26):
        n, k = len(self.v), len(prof)
        for r, z in prof:
            for i in range(seg):
                a = 2 * math.pi * i / seg
                self.v.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
        for j in range(k - 1):
            for i in range(seg):
                i2 = (i + 1) % seg
                self.f.append((n + j * seg + i, n + j * seg + i2, n + (j + 1) * seg + i2, n + (j + 1) * seg + i))
        if prof[0][0] > 0:
            self.f.append(tuple(n + i for i in range(seg)))
        if prof[-1][0] > 0:
            self.f.append(tuple(n + (k - 1) * seg + i for i in range(seg)))
        return self

    def poly(self, pts):
        n = len(self.v)
        self.v += pts
        self.f.append(tuple(range(n, n + len(pts))))
        return self

    def done(self, name, mat, smooth=False):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        me.update()
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        if smooth:
            me.polygons.foreach_set('use_smooth', [len(p.vertices) <= 4 for p in me.polygons])
            me.update()
        me.materials.append(MAT[mat] if isinstance(mat, str) else mat)
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        CUR[0].append(ob)
        return ob


def box(name, x0, x1, y0, y1, z0, z1, mat):
    return B().box(x0, x1, y0, y1, z0, z1).done(name, mat)


def tube(name, pts, r, mat, res=3):
    c = bpy.data.curves.new(name, 'CURVE')
    c.dimensions = '3D'
    c.bevel_depth = r
    c.bevel_resolution = res
    c.use_fill_caps = True
    s = c.splines.new('BEZIER')
    s.bezier_points.add(len(pts) - 1)
    for bp, p in zip(s.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
    c.materials.append(MAT[mat])
    ob = bpy.data.objects.new(name, c)
    coll.objects.link(ob)
    CUR[0].append(ob)
    return ob


def shaker(b, x0, x1, z0, z1, y=FRONT, t=0.02, rail=0.062, rec=0.008):
    """A framed door or drawer front."""
    g = 0.0015
    x0, x1, z0, z1 = x0 + g, x1 - g, z0 + g, z1 - g
    r = min(rail, (x1 - x0) * 0.22, (z1 - z0) * 0.3)
    b.box(x0, x0 + r, y, y + t, z0, z1).box(x1 - r, x1, y, y + t, z0, z1)
    b.box(x0 + r, x1 - r, y, y + t, z0, z0 + r).box(x0 + r, x1 - r, y, y + t, z1 - r, z1)
    b.box(x0 + r, x1 - r, y + rec, y + t, z0 + r, z1 - r)


def pull_h(b, x0, x1, z, y=FRONT):
    b.box(x0, x1, y - 0.03, y - 0.022, z - 0.005, z + 0.005)
    for x in (x0 + 0.02, x1 - 0.02):
        b.box(x - 0.004, x + 0.004, y - 0.03, y, z - 0.004, z + 0.004)


def pull_v(b, x, z0, z1, y=FRONT):
    b.box(x - 0.005, x + 0.005, y - 0.03, y - 0.022, z0, z1)
    for z in (z0 + 0.02, z1 - 0.02):
        b.box(x - 0.004, x + 0.004, y - 0.03, y, z - 0.004, z + 0.004)


def base_unit(pid, x0, x1, kind, mat='blue'):
    with piece(pid):
        box(pid + '_c', x0 + 0.002, x1 - 0.002, FRONT + 0.02, YB, PLINTH, BASE_TOP, 'carcass')
        box(pid + '_p', x0, x1, FRONT + 0.05, YB, 0, PLINTH, 'carcass')
        f, h = B(), B()
        if kind == 'door':
            shaker(f, x0, x1, PLINTH, BASE_TOP)
            pull_h(h, x0 + (x1 - x0) * 0.28, x1 - (x1 - x0) * 0.28, BASE_TOP - 0.07)
        elif kind == 'door2':
            m = (x0 + x1) / 2
            shaker(f, x0, m, PLINTH, BASE_TOP)
            shaker(f, m, x1, PLINTH, BASE_TOP)
            pull_v(h, m - 0.04, BASE_TOP - 0.2, BASE_TOP - 0.05)
            pull_v(h, m + 0.04, BASE_TOP - 0.2, BASE_TOP - 0.05)
        elif kind == 'drawers':
            zs = [PLINTH, 0.36, 0.62, BASE_TOP]
            for a, b_ in zip(zs, zs[1:]):
                shaker(f, x0, x1, a, b_)
                pull_h(h, x0 + (x1 - x0) * 0.22, x1 - (x1 - x0) * 0.22, b_ - 0.05)
        f.done(pid + '_f', mat)
        h.done(pid + '_h', 'brass')


def tall_unit(pid, x0, x1, kind='door', mat='blue'):
    with piece(pid):
        box(pid + '_c', x0 + 0.002, x1 - 0.002, FRONT + 0.02, YB, PLINTH, TALL, 'carcass')
        box(pid + '_p', x0, x1, FRONT + 0.05, YB, 0, PLINTH, 'carcass')
        f, h = B(), B()
        if kind == 'door':
            shaker(f, x0, x1, PLINTH, TALL)
            pull_v(h, x1 - 0.05, 0.86, 1.46)
        elif kind == 'door-l':
            shaker(f, x0, x1, PLINTH, TALL)
            pull_v(h, x0 + 0.05, 0.86, 1.46)
        elif kind == 'oven':
            shaker(f, x0, x1, PLINTH, 0.7)
            pull_h(h, x0 + 0.14, x1 - 0.14, 0.64)
            shaker(f, x0, x1, 1.72, TALL)
            pull_v(h, x1 - 0.05, 1.78, 2.14)
            s, g = B(), B()
            s.box(x0 + 0.004, x1 - 0.004, FRONT, FRONT + 0.03, 0.7, 1.72)
            g.box(x0 + 0.03, x1 - 0.03, FRONT - 0.003, FRONT + 0.01, 0.74, 1.24)
            g.box(x0 + 0.03, x1 - 0.03, FRONT - 0.003, FRONT + 0.01, 1.3, 1.68)
            s.box(x0 + 0.06, x1 - 0.06, FRONT - 0.035, FRONT - 0.022, 1.18, 1.195)
            s.box(x0 + 0.06, x1 - 0.06, FRONT - 0.035, FRONT - 0.022, 1.62, 1.635)
            s.done(pid + '_s', 'steel')
            g.done(pid + '_g', 'glassblack')
        elif kind == 'fridge':
            m = (x0 + x1) / 2
            shaker(f, x0, m, PLINTH, TALL)
            shaker(f, m, x1, PLINTH, TALL)
            pull_v(h, m - 0.05, 0.72, 1.62)
            pull_v(h, m + 0.05, 0.72, 1.62)
        f.done(pid + '_f', mat)
        h.done(pid + '_h', 'brass')


def upper_unit(pid, x0, x1, n=2):
    with piece(pid):
        y = YB - 0.35
        box(pid + '_c', x0 + 0.002, x1 - 0.002, y + 0.02, YB, UP0, UP1, 'carcass')
        f, h = B(), B()
        for i in range(n):
            a, b_ = x0 + (x1 - x0) * i / n, x0 + (x1 - x0) * (i + 1) / n
            shaker(f, a, b_, UP0, UP1, y)
            if n == 1:
                pull_v(h, x1 - 0.05, UP0 + 0.05, UP0 + 0.26, y)
            elif i == 0:
                pull_v(h, b_ - 0.04, UP0 + 0.05, UP0 + 0.26, y)
            elif i == 1:
                pull_v(h, a + 0.04, UP0 + 0.05, UP0 + 0.26, y)
        f.done(pid + '_f', 'blue')
        h.done(pid + '_h', 'brass')
        box(pid + '_l', x0 + 0.03, x1 - 0.03, YB - 0.1, YB - 0.08, UP0 - 0.008, UP0 - 0.001, 'led')


def cup(b, cx, cy, z, r=0.038, h=0.07):
    b.lathe(cx, cy, [(0.0, z), (r * 0.75, z), (r, z + 0.012), (r, z + h), (r - 0.004, z + h), (r - 0.004, z + 0.014), (0.0, z + 0.014)], 18)


def jar(b_body, b_lid, b_fill, cx, cy, z, r=0.055, h=0.17):
    b_body.lathe(cx, cy, [(0.0, z), (r, z), (r, z + h), (r * 0.72, z + h + 0.012)], 22)
    b_lid.lathe(cx, cy, [(0.0, z + h + 0.012), (r * 0.8, z + h + 0.012), (r * 0.8, z + h + 0.036), (0.0, z + h + 0.036)], 22)


def plates(b, cx, cy, z, n=5, r=0.1):
    for i in range(n):
        zz = z + i * 0.012
        b.lathe(cx, cy, [(0.0, zz), (r * 0.65, zz), (r, zz + 0.012), (r - 0.004, zz + 0.014), (r * 0.62, zz + 0.004), (0.0, zz + 0.004)], 26)


def leaves(b, cx, cy, cz, n, spread, size=0.06, ztall=0.7):
    for _ in range(n):
        a, rad = random.random() * 2 * math.pi, spread * math.sqrt(random.random())
        x, y = cx + rad * math.cos(a), cy + rad * math.sin(a)
        z = cz + random.uniform(-spread * ztall, spread * ztall)
        ang, tilt = random.random() * 2 * math.pi, random.uniform(-0.8, 0.8)
        dx, dy = math.cos(ang) * size, math.sin(ang) * size
        nx, ny = -dy * 0.36, dx * 0.36
        dz = math.sin(tilt) * size
        b.poly([(x - dx, y - dy, z - dz), (x + nx * 0.8, y + ny * 0.8, z + abs(dz) * 0.15), (x + dx, y + dy, z + dz), (x - nx * 0.8, y - ny * 0.8, z + abs(dz) * 0.15)])


def potted(pid_mat, cx, cy, z, r, h, mat='ceramic'):
    B().lathe(cx, cy, [(0.0, z), (r * 0.72, z), (r, z + h), (r * 0.94, z + h), (r * 0.7, z + 0.02), (0.0, z + 0.02)], 26).done(pid_mat + '_pot', mat, True)


# ------------------------------------------------------------------ the room, finished and raw


def walls(mat_wall, b_ceiling_mat, floor_mat, raw=False):
    win0, win1, wz0, wz1 = 3.2, 5.2, 0.8, 2.62
    t = 0.25
    box('floor', XL - 1, XR + 1, YF - 1, YB + 1, -0.2, 0, floor_mat)
    box('ceil', XL - 1, XR + 1, YF - 1, YB + 1, H, H + 0.2, b_ceiling_mat)
    box('back', XL - 1, XR + 1, YB, YB + t, 0, H, mat_wall)
    box('right', XR, XR + t, YF - 1, YB, 0, H, mat_wall)
    box('left1', XL - t, XL, YF - 1, win0, 0, H, mat_wall)
    box('left2', XL - t, XL, win1, YB, 0, H, mat_wall)
    box('left3', XL - t, XL, win0, win1, 0, wz0, mat_wall)
    box('left4', XL - t, XL, win0, win1, wz1, H, mat_wall)
    return win0, win1, wz0, wz1, t


with env(ENV_DONE):
    win0, win1, wz0, wz1, wt = walls('wall', 'ceiling', 'floor')
    fr = B()
    for y in (win0, win1, (win0 + win1) / 2, win0 + (win1 - win0) / 4, win0 + (win1 - win0) * 3 / 4):
        fr.box(XL - 0.1, XL - 0.03, y - 0.02, y + 0.02, wz0, wz1)
    fr.box(XL - 0.1, XL - 0.03, win0, win1, wz0, wz0 + 0.04).box(XL - 0.1, XL - 0.03, win0, win1, wz1 - 0.04, wz1)
    fr.box(XL - 0.1, XL - 0.03, win0, win1, 2.1, 2.13)
    fr.done('winframe', 'frame')
    box('sill', XL - 0.1, XL + 0.04, win0, win1, wz0 - 0.03, wz0, 'trim')
    box('skirtR', XR - 0.012, XR, YF, FRONT, 0, 0.09, 'trim')
    box('skirtL', XL, XL + 0.012, YF, FRONT, 0, 0.09, 'trim')
    # Slatted oak ceiling feature above the island, recessed spots elsewhere.
    sl = B()
    x = -1.9
    while x < 1.9:
        sl.box(x, x + 0.05, 3.2, 4.55, H - 0.05, H)
        x += 0.085
    sl.done('slats', 'oakx')
    sp = B()
    for x, y in [(-3, 1.6), (-3, 3.6), (-3, 5.0), (3, 1.6), (3, 3.6), (3, 5.0), (0, 1.6), (-1.5, 5.15), (1.5, 5.15), (0, 5.15)]:
        sp.cyl(x, y, 0.04, H - 0.002, H - 0.001, 16)
    sp.done('spots', 'spot')

with env(ENV_RAW):
    walls('rawwall', 'rawceil', 'rawfloor', raw=True)
    # Power boxes, wires, capped pipes and ceiling conduit: the marks of a building not yet fitted.
    pv = B()
    for x, z in [(-2.9, 1.1), (-1.8, 1.14), (-0.7, 1.14), (0.45, 1.14), (1.2, 0.3), (2.6, 1.14), (3.4, 1.14), (-0.7, 2.1), (2.8, 2.46), (-3.6, 0.32)]:
        pv.box(x - 0.055, x + 0.055, YB - 0.012, YB, z - 0.075, z + 0.075)
    pv.done('boxes', 'pvc')
    for i, (x, z) in enumerate([(-2.9, 1.1), (-1.8, 1.14), (-0.7, 1.14), (0.45, 1.14), (2.6, 1.14), (3.4, 1.14), (-0.7, 2.1)]):
        tube(f'wire{i}', [(x, YB - 0.012, z - 0.03), (x + 0.02, YB - 0.03, z - 0.09), (x - 0.01, YB - 0.05, z - 0.15), (x + 0.03, YB - 0.04, z - 0.21)], 0.004, 'wire', 2)
    for i, (x, z) in enumerate([(-0.15, 0.5), (0.0, 0.5), (0.18, 0.56), (2.95, 0.52), (3.1, 0.52)]):
        tube(f'stub{i}', [(x, YB, z), (x, YB - 0.05, z), (x, YB - 0.11, z)], 0.016, 'copper', 2)
    for i, (x, y) in enumerate([(0.32, 3.86), (0.42, 3.86)]):
        tube(f'floorstub{i}', [(x, y, 0), (x, y, 0.08), (x, y, 0.16)], 0.014, 'copper', 2)
    for i, x in enumerate((-0.7, -0.64)):
        tube(f'conduit{i}', [(x, -1, H - 0.02), (x, 2.5, H - 0.02), (x, YB - 0.02, H - 0.02)], 0.011, 'pvc', 2)
    tube('conduit2', [(-0.7, YB - 0.02, H - 0.02), (-0.7, YB - 0.02, 2.5), (-0.7, YB - 0.02, 2.17)], 0.011, 'pvc', 2)

# ------------------------------------------------------------------ cabinets: left bank
tall_unit('tall1', -4.0, -3.4, 'door')
tall_unit('tall2', -3.4, -2.8, 'door-l')
tall_unit('oven', -2.8, -2.2, 'oven')

# Cooking run.
base_unit('base1', -2.2, -1.6, 'door')
base_unit('base2', -1.6, -1.15, 'door')
base_unit('base3', -1.15, -0.25, 'drawers')
base_unit('base4', -0.25, 0.3, 'door')
base_unit('base5', 0.3, 0.8, 'door')

with piece('worktop'):
    box('wt', -2.2, 0.8, FRONT - 0.02, YB, BASE_TOP, BASE_TOP + TOP_T, 'stone')
    box('hob', -1.12, -0.28, FRONT + 0.1, FRONT + 0.58, BASE_TOP + TOP_T, BASE_TOP + TOP_T + 0.004, 'glassblack')
    rings = B()
    for x, y, r in [(-0.9, FRONT + 0.22, 0.075), (-0.9, FRONT + 0.46, 0.06), (-0.5, FRONT + 0.22, 0.06), (-0.5, FRONT + 0.46, 0.075)]:
        z = BASE_TOP + TOP_T + 0.004
        rings.lathe(x, y, [(r - 0.006, z), (r, z), (r, z + 0.012), (r - 0.006, z + 0.012)], 24)
        for a in range(6):
            ang = a * math.pi / 3
            rings.box(x + math.cos(ang) * 0.01 - 0.003, x + math.cos(ang) * r + 0.003, y + math.sin(ang) * 0.01 - 0.003, y + math.sin(ang) * r + 0.003, z + 0.012, z + 0.018)
    rings.done('burners', 'black')
    B().lathe(-0.5, FRONT + 0.46, [(0.0, BASE_TOP + TOP_T + 0.022), (0.09, BASE_TOP + TOP_T + 0.022), (0.095, BASE_TOP + TOP_T + 0.11), (0.088, BASE_TOP + TOP_T + 0.11), (0.0, BASE_TOP + TOP_T + 0.03)], 24).done('pot', 'steel', True)
    b = B()
    for i, r in enumerate((0.045, 0.038, 0.03)):
        cup(b, -1.85 + i * 0.13, YB - 0.12, BASE_TOP + TOP_T, r, 0.12 + i * 0.03)
    b.done('canisters', 'ceramic', True)
    B().lathe(0.42, YB - 0.14, [(0.0, 0.9), (0.05, 0.9), (0.075, 1.02), (0.05, 1.14), (0.025, 1.24), (0.028, 1.28), (0.02, 1.28)], 22).done('vase', 'terracotta', True)
    bo = B().box(-1.75, -1.4, FRONT + 0.2, FRONT + 0.46, 0.9, 0.925)
    bo.done('board', 'walnutx')

with piece('splash'):
    box('splash', -2.2, 0.8, YB - 0.012, YB, BASE_TOP + TOP_T, UP0, 'stone')

upper_unit('up1', -2.2, -1.2, 2)
upper_unit('up2', -0.2, 0.8, 2)

with piece('hood'):
    box('hoodbody', -1.14, -0.26, YB - 0.46, YB, 1.56, 1.7, 'black')
    box('hoodtrim', -1.14, -0.26, YB - 0.462, YB - 0.45, 1.56, 1.575, 'brass')
    box('hoodled', -1.05, -0.35, YB - 0.4, YB - 0.1, 1.555, 1.56, 'led')
    # Fluted chimney up to the ceiling.
    ch = B()
    r = 0.4
    n = 30
    for i in range(n + 1):
        t_ = math.pi + math.pi * i / n
        ch.cyl(-0.7 + math.cos(t_) * r, YB + math.sin(t_) * r * 0.75, 0.0165, 1.7, H, 10)
    ch.done('flutes', 'blue2', True)
    B().prism([(-0.7 + math.cos(math.pi + math.pi * i / 24) * (r - 0.006), YB + math.sin(math.pi + math.pi * i / 24) * (r - 0.006) * 0.75) for i in range(25)], 1.7, H).done('chcore', 'carcass')

tall_unit('fridge', 0.8, 1.7, 'fridge')



def top_unit(pid, x0, x1, n, y=FRONT, mat='blue', slab=False):
    with piece(pid):
        box(pid + '_c', x0 + 0.002, x1 - 0.002, y + 0.02, YB, UP1, H - 0.004, 'carcass')
        f, h = B(), B()
        for i in range(n):
            a, b_ = x0 + (x1 - x0) * i / n, x0 + (x1 - x0) * (i + 1) / n
            if slab:
                f.box(a + 0.0015, b_ - 0.0015, y, y + 0.02, UP1 + 0.0015, H - 0.006)
            else:
                shaker(f, a, b_, UP1, H - 0.004, y)
            pull_h(h, a + (b_ - a) * 0.3, b_ - (b_ - a) * 0.3, UP1 + 0.06, y)
        f.done(pid + '_f', mat)
        h.done(pid + '_h', 'brass')


top_unit('topl', -4.0, -2.2, 3)
top_unit('topu1', -2.2, -1.2, 2, YB - 0.35)
top_unit('topu2', -0.2, 0.8, 2, YB - 0.35)
top_unit('topf', 0.8, 1.7, 2)
top_unit('topc', 1.7, 4.0, 4, YB - 0.3, 'walnut', True)

# ------------------------------------------------------------------ coffee bar
with piece('cpanel'):
    sl = B()
    x = 1.7
    while x < 4.0:
        sl.box(x, x + 0.026, YB - 0.022, YB, BASE_TOP + TOP_T, TALL)
        x += 0.034
    sl.done('cslats', 'slat')
    box('cback', 1.7, 4.0, YB - 0.008, YB, BASE_TOP + TOP_T, TALL, 'carcass')
    box('cled', 1.74, 3.96, YB - 0.2, YB - 0.18, TALL - 0.006, TALL, 'led')


def coffee_base(pid, x0, x1):
    with piece(pid):
        box(pid + '_c', x0 + 0.002, x1 - 0.002, FRONT + 0.02, YB, PLINTH, BASE_TOP, 'carcass')
        box(pid + '_p', x0, x1, FRONT + 0.05, YB, 0, PLINTH, 'carcass')
        B().box(x0 + 0.0015, x1 - 0.0015, FRONT, FRONT + 0.02, PLINTH + 0.0015, BASE_TOP - 0.0015).done(pid + '_f', 'walnut')
        h = B()
        pull_h(h, x0 + 0.14, x1 - 0.14, BASE_TOP - 0.06)
        h.done(pid + '_h', 'brass')


coffee_base('cbase1', 1.7, 2.3)
coffee_base('cbase2', 2.3, 2.85)
coffee_base('cbase3', 2.85, 3.45)
coffee_base('cbase4', 3.45, 4.0)

with piece('cworktop'):
    box('cwt', 1.7, 4.0, FRONT - 0.02, YB, BASE_TOP, BASE_TOP + TOP_T, 'stonedark')

Z_T = BASE_TOP + TOP_T
with piece('espresso'):
    s = B()
    s.box(2.05, 2.62, 5.5, 5.9, Z_T + 0.09, Z_T + 0.42)  # body
    s.box(2.05, 2.62, 5.42, 5.9, Z_T + 0.0, Z_T + 0.05)  # drip tray
    s.box(2.05, 2.62, 5.5, 5.9, Z_T + 0.42, Z_T + 0.44)
    s.done('emb', 'steel')
    d = B().box(2.06, 2.61, 5.495, 5.5, Z_T + 0.1, Z_T + 0.3).done('emf', 'black')
    g = B()
    for x in (2.2, 2.47):
        g.cyl(x, 5.44, 0.036, Z_T + 0.2, Z_T + 0.28, 20)
        g.cyl(x, 5.44, 0.03, Z_T + 0.17, Z_T + 0.2, 20)
    g.done('groups', 'steel', True)
    pf = B()
    for x in (2.2, 2.47):
        pf.box(x - 0.01, x + 0.01, 5.3, 5.42, Z_T + 0.175, Z_T + 0.19)
    pf.done('pf', 'black')
    tube('wand', [(2.58, 5.48, Z_T + 0.3), (2.6, 5.42, Z_T + 0.22), (2.6, 5.42, Z_T + 0.12)], 0.005, 'steel', 2)
    ct = B()
    for i in range(5):
        cup(ct, 2.13 + i * 0.1, 5.7, Z_T + 0.44, 0.036, 0.062)
    ct.done('topcups', 'ceramic', True)
    B().box(2.72, 2.92, 5.56, 5.9, Z_T, Z_T + 0.06).done('gr0', 'black')
    B().box(2.76, 2.88, 5.62, 5.84, Z_T + 0.06, Z_T + 0.3).done('gr1', 'black')
    B().lathe(2.82, 5.73, [(0.04, Z_T + 0.3), (0.09, Z_T + 0.46), (0.09, Z_T + 0.47), (0.0, Z_T + 0.47)], 22).done('gr2', 'coffee', True)
    m = B()
    for x, y in [(3.1, 5.55), (3.22, 5.62), (3.34, 5.5)]:
        cup(m, x, y, Z_T, 0.04, 0.085)
    m.done('mugs', 'ceramicdark', True)
    bb = B()
    plates(bb, 3.66, 5.68, Z_T, 6, 0.11)
    bb.done('saucers', 'ceramic', True)


def shelf(pid, z, items):
    with piece(pid):
        y0, y1 = YB - 0.3, YB - 0.022
        box(pid + '_s', 1.86, 3.86, y0, y1, z, z + 0.036, 'walnutx')
        box(pid + '_l', 1.9, 3.82, y0 + 0.14, y0 + 0.16, z - 0.005, z, 'led')
        items(z + 0.036)


def shelf_a(z):
    a, l = B(), B()
    for i, x in enumerate((2.02, 2.17, 2.32)):
        jar(a, l, None, x, YB - 0.16, z, 0.056, 0.15 + (i % 2) * 0.03)
    a.done('jars', 'ceramicdark', True)
    l.done('lids', 'oakx', True)
    c = B()
    for i in range(6):
        cup(c, 2.62 + i * 0.09, YB - 0.16, z, 0.034, 0.066)
    c.done('cups1', 'ceramic', True)
    potted('sp1', 3.6, YB - 0.16, z, 0.07, 0.12, 'terracotta')
    lf = B()
    leaves(lf, 3.6, YB - 0.16, z + 0.2, 26, 0.13, 0.04, 0.6)
    lf.done('sp1l', 'leaf')


def shelf_b(z):
    bb = B()
    plates(bb, 2.1, YB - 0.16, z, 7, 0.1)
    plates(bb, 2.38, YB - 0.16, z, 5, 0.085)
    bb.done('plates', 'ceramic', True)
    c = B()
    for i in range(5):
        cup(c, 2.72 + i * 0.1, YB - 0.16, z, 0.042, 0.09)
    c.done('mugs2', 'ceramicdark', True)
    bk = B()
    x = 3.42
    for i, w in enumerate((0.03, 0.022, 0.035, 0.026)):
        bk.box(x, x + w, YB - 0.24, YB - 0.08, z, z + 0.2 + (i % 2) * 0.03)
        x += w + 0.002
    bk.done('books', 'stonedark')


def shelf_c(z):
    a, l = B(), B()
    for i, x in enumerate((2.0, 2.15)):
        jar(a, l, None, x, YB - 0.16, z, 0.06, 0.2 - i * 0.04)
    a.done('jars3', 'ceramic', True)
    l.done('lids3', 'walnutx', True)
    b_ = B()
    b_.lathe(2.62, YB - 0.16, [(0.0, z), (0.06, z), (0.11, z + 0.09), (0.105, z + 0.09), (0.05, z + 0.012), (0.0, z + 0.012)], 26)
    b_.done('bowl', 'terracotta', True)
    c = B()
    for i in range(5):
        cup(c, 3.0 + i * 0.1, YB - 0.16, z, 0.04, 0.07)
    c.done('cups3', 'ceramic', True)


shelf('shelf1', 1.28, shelf_a)
shelf('shelf2', 1.66, shelf_b)
shelf('shelf3', 2.04, shelf_c)

# ------------------------------------------------------------------ the curved island with the sink
IC_Y, IHALF, IR = 3.85, 1.1, 0.45
I_TOP = BASE_TOP + 0.02


def stadium(r, n=22):
    pts = []
    for i in range(n + 1):
        a = math.pi / 2 + math.pi * i / n
        pts.append((-IHALF + r * math.cos(a), IC_Y + r * math.sin(a)))
    for i in range(n + 1):
        a = -math.pi / 2 + math.pi * i / n
        pts.append((IHALF + r * math.cos(a), IC_Y + r * math.sin(a)))
    return pts


with piece('island'):
    B().prism(stadium(IR - 0.045), 0, 0.08).done('iplinth', 'carcass')
    icore = B().prism(stadium(IR - 0.01), 0.08, I_TOP).done('icore', 'carcass')
    fl = B()
    run = stadium(IR)
    run.append(run[0])
    # Evenly spaced flutes all the way round.
    seglen = [math.dist(run[i], run[i + 1]) for i in range(len(run) - 1)]
    total, step, pos, i, acc = sum(seglen), 0.033, 0.0, 0, 0.0
    while pos < total:
        while acc + seglen[i] < pos:
            acc += seglen[i]
            i += 1
        t_ = (pos - acc) / seglen[i]
        x = run[i][0] + (run[i + 1][0] - run[i][0]) * t_
        y = run[i][1] + (run[i + 1][1] - run[i][1]) * t_
        fl.cyl(x, y, 0.0172, 0.08, I_TOP, 10)
        pos += step
    fl.done('iflutes', 'blue2', True)

with piece('islandtop'):
    top = B().prism(stadium(IR + 0.05), I_TOP, I_TOP + 0.05).done('itop', 'stone')
    with env(HELPERS):
        cut = B().box(0.03, 0.73, IC_Y - 0.22, IC_Y + 0.22, I_TOP - 0.3, I_TOP + 0.1).done('sinkcut', 'black')
    mod = top.modifiers.new('sink', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cut
    mod2 = icore.modifiers.new('sink', 'BOOLEAN')
    mod2.operation = 'DIFFERENCE'
    mod2.solver = 'EXACT'
    mod2.object = cut
    s = B()
    z0 = I_TOP - 0.18
    # Satin steel: a mirror finish in a deep basin bounces light until it runs out and renders black.
    s.box(0.03, 0.73, IC_Y - 0.22, IC_Y + 0.22, z0 - 0.01, z0)
    s.box(0.03, 0.034, IC_Y - 0.22, IC_Y + 0.22, z0, I_TOP + 0.05)
    s.box(0.726, 0.73, IC_Y - 0.22, IC_Y + 0.22, z0, I_TOP + 0.05)
    s.box(0.034, 0.726, IC_Y - 0.22, IC_Y - 0.216, z0, I_TOP + 0.05)
    s.box(0.034, 0.726, IC_Y + 0.216, IC_Y + 0.22, z0, I_TOP + 0.05)
    rim0, rim1 = I_TOP + 0.05, I_TOP + 0.054
    s.box(0.015, 0.034, IC_Y - 0.235, IC_Y + 0.235, rim0, rim1)
    s.box(0.726, 0.745, IC_Y - 0.235, IC_Y + 0.235, rim0, rim1)
    s.box(0.034, 0.726, IC_Y - 0.235, IC_Y - 0.216, rim0, rim1)
    s.box(0.034, 0.726, IC_Y + 0.216, IC_Y + 0.235, rim0, rim1)
    s.done('basin', 'sinksteel')
    # Tall brass tap.
    ZT = I_TOP + 0.05
    B().cyl(0.38, IC_Y + 0.31, 0.024, ZT, ZT + 0.07, 18).done('tapbase', 'brass', True)
    tube('tap', [(0.38, IC_Y + 0.31, ZT + 0.05), (0.38, IC_Y + 0.31, ZT + 0.3), (0.38, IC_Y + 0.24, ZT + 0.47), (0.38, IC_Y + 0.12, ZT + 0.5), (0.38, IC_Y + 0.03, ZT + 0.42), (0.38, IC_Y + 0.03, ZT + 0.34)], 0.014, 'brass', 3)
    tube('lever', [(0.38, IC_Y + 0.31, ZT + 0.06), (0.44, IC_Y + 0.31, ZT + 0.07), (0.49, IC_Y + 0.31, ZT + 0.085)], 0.005, 'brass', 2)
    # A few things on the top.
    B().lathe(-0.72, IC_Y - 0.05, [(0.0, ZT), (0.07, ZT), (0.15, ZT + 0.09), (0.145, ZT + 0.09), (0.065, ZT + 0.012), (0.0, ZT + 0.012)], 28).done('fruitbowl', 'ceramicdark', True)
    fr_ = B()
    for x, y, r in [(-0.76, IC_Y - 0.07, 0.04), (-0.68, IC_Y - 0.09, 0.038), (-0.72, IC_Y, 0.04)]:
        fr_.lathe(x, y, [(r * math.sin(math.pi * i / 10), ZT + 0.05 + r - r * math.cos(math.pi * i / 10)) for i in range(11)], 16)
    fr_.done('fruit', plain('lemon', '#d9a521', 0.45, 0, 0), True)
    B().box(-0.32, -0.12, IC_Y - 0.25, IC_Y - 0.03, ZT, ZT + 0.018).done('iboard', 'walnutx')


def stool(pid, x):
    with piece(pid):
        y = 3.02
        B().lathe(x, y, [(0.0, 0.66), (0.17, 0.66), (0.18, 0.68), (0.16, 0.705), (0.0, 0.71)], 28).done(pid + '_s', 'leather', True)
        for i, (dx, dy) in enumerate([(-1, -1), (1, -1), (1, 1), (-1, 1)]):
            tube(f'{pid}_l{i}', [(x + dx * 0.09, y + dy * 0.09, 0.66), (x + dx * 0.15, y + dy * 0.15, 0.0)], 0.0085, 'black', 2)
        B().lathe(x, y, [(0.125, 0.22), (0.135, 0.22), (0.135, 0.232), (0.125, 0.232)], 28).done(pid + '_r', 'black', True)


stool('stool1', -0.92)
stool('stool2', 0.0)
stool('stool3', 0.92)

with piece('pendants'):
    for i, x in enumerate((-0.92, 0.0, 0.92)):
        z = 1.84
        tube(f'cord{i}', [(x, IC_Y, H - 0.05), (x, IC_Y, z + 0.5), (x, IC_Y, z + 0.26)], 0.0035, 'black', 2)
        B().lathe(x, IC_Y, [(0.015, z + 0.24), (0.03, z + 0.22), (0.08, z + 0.18), (0.118, z + 0.1), (0.14, z), (0.135, z), (0.11, z + 0.095), (0.07, z + 0.17)], 30).done(f'dome{i}', 'brass', True)
        B().lathe(x, IC_Y, [(0.0, z + 0.03), (0.04, z + 0.06), (0.045, z + 0.1), (0.02, z + 0.14), (0.0, z + 0.15)], 16).done(f'bulb{i}', 'bulb', True)

with piece('tree'):
    tx, ty = -3.35, 1.75
    B().lathe(tx, ty, [(0.0, 0), (0.17, 0), (0.25, 0.44), (0.235, 0.44), (0.16, 0.03), (0.0, 0.03)], 32).done('treepot', 'terracotta', True)
    B().cyl(tx, ty, 0.225, 0.38, 0.385, 28).done('soil', 'coffee')
    tube('trunk', [(tx, ty, 0.38), (tx - 0.03, ty, 0.95), (tx + 0.03, ty, 1.32)], 0.021, 'bark', 2)
    tube('br1', [(tx - 0.01, ty, 1.05), (tx - 0.2, ty + 0.05, 1.42)], 0.011, 'bark', 2)
    tube('br2', [(tx + 0.02, ty, 1.2), (tx + 0.22, ty - 0.04, 1.55)], 0.011, 'bark', 2)
    tube('br3', [(tx + 0.03, ty, 1.32), (tx - 0.02, ty + 0.02, 1.72)], 0.009, 'bark', 2)
    l1, l2 = B(), B()
    leaves(l1, tx, ty, 1.55, 210, 0.42, 0.05, 0.65)
    leaves(l2, tx, ty, 1.55, 120, 0.4, 0.045, 0.65)
    l1.done('leaves1', 'leaf')
    l2.done('leaves2', 'leaf2')

# ------------------------------------------------------------------ light and camera
world = bpy.data.worlds.new('w')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.86, 0.92, 1.0, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.85
scene.world = world

sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 3.4
sun.data.angle = math.radians(2.5)
sun.data.color = (1.0, 0.93, 0.82)
sun.rotation_mode = 'QUATERNION'
sun.rotation_quaternion = (-Vector((-0.74, 0.32, 0.6))).to_track_quat('-Z', 'Y')
coll.objects.link(sun)
area = bpy.data.objects.new('area', bpy.data.lights.new('area', 'AREA'))
area.data.shape = 'RECTANGLE'
area.data.size, area.data.size_y = 6.5, 3.2
area.data.energy = 170
area.data.color = (1.0, 0.95, 0.88)
area.location = (0.2, 3.4, H - 0.02)
coll.objects.link(area)

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
cam.data.lens = 27
cam.data.sensor_width = 36
cam.location = (0.0, -1.35, 1.7)
cam.data.shift_y = -0.05
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (Vector((0.0, 6.0, 1.7)) - cam.location).to_track_quat('-Z', 'Y')
coll.objects.link(cam)
scene.camera = cam

# ------------------------------------------------------------------ render settings
W = ARGS.width
Hpx = round(W * 1536 / 2752)
r = scene.render
r.engine = 'CYCLES'
r.resolution_x, r.resolution_y, r.resolution_percentage = W, Hpx, 100
r.image_settings.file_format = 'PNG'
r.image_settings.color_mode = 'RGBA'
r.image_settings.compression = 40
r.use_persistent_data = True
c = scene.cycles
c.device = 'CPU'
c.samples = ARGS.spp
c.use_adaptive_sampling = True
c.adaptive_threshold = 0.02
c.use_denoising = True
c.denoiser = 'OPENIMAGEDENOISE'
c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces = 10, 4, 7, 4
c.caustics_reflective = c.caustics_refractive = False
c.sample_clamp_indirect = 6
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = 0.42
for h in HELPERS:
    h.hide_render = True

ALL_PIECE_OBJS = [o for ids in PIECES.values() for o in ids]


def reset():
    r.use_border = False
    r.use_crop_to_border = False
    r.film_transparent = False
    for o in ALL_PIECE_OBJS + ENV_DONE + ENV_RAW:
        o.hide_render = False
        o.visible_camera = True
        o.is_shadow_catcher = False


def render_to(name):
    r.filepath = os.path.join(ARGS.out, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', name, flush=True)


def crop_of(objs):
    x0, y0, x1, y1 = 1.0, 1.0, 0.0, 0.0
    for o in objs:
        for corner in o.bound_box:
            p = world_to_camera_view(scene, cam, o.matrix_world @ Vector(corner))
            x0, x1 = min(x0, p.x), max(x1, p.x)
            y0, y1 = min(y0, p.y), max(y1, p.y)
    pad = 8 / W
    return max(0.0, x0 - pad), max(0.0, y0 - pad), min(1.0, x1 + pad), min(1.0, y1 + pad)


modes = ARGS.mode.split(',')
meta = {}

if 'beauty' in modes:
    reset()
    for o in ENV_RAW:
        o.hide_render = True
    render_to('beauty')

if 'sinkpatch' in modes:
    # Only the area around the sink, to paste into the finished beauty render.
    reset()
    for o in ENV_RAW:
        o.hide_render = True
    r.use_border, r.use_crop_to_border = True, True
    r.border_min_x, r.border_max_x = 930 / 1920, 1210 / 1920
    r.border_min_y, r.border_max_y = (1072 - 700) / 1072, (1072 - 615) / 1072
    render_to('beauty_sink')

if 'raw' in modes:
    reset()
    for o in ENV_DONE + ALL_PIECE_OBJS:
        o.hide_render = True
    render_to('raw')

if 'pieces' in modes or any(m.startswith('only:') for m in modes):
    i_, n_ = map(int, ARGS.chunk.split('/'))
    only = [m[5:] for m in modes if m.startswith('only:')]
    for k, pid in enumerate(ORDER):
        if (pid not in only) if only else (k % n_ != i_):
            continue
        reset()
        for o in ENV_RAW:
            o.hide_render = True
        for o in ENV_DONE + ALL_PIECE_OBJS:
            o.visible_camera = False
        for o in PIECES[pid]:
            o.visible_camera = True
        x0, y0, x1, y1 = crop_of(PIECES[pid])
        r.film_transparent = True
        r.use_border, r.use_crop_to_border = True, True
        r.border_min_x, r.border_min_y, r.border_max_x, r.border_max_y = x0, y0, x1, y1
        render_to('p_' + pid)
        meta[pid] = {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1}
    with open(os.path.join(ARGS.out, f'meta_{i_}.json'), 'w') as fh:
        json.dump({'order': ORDER, 'w': W, 'h': Hpx, 'boxes': meta}, fh)

if 'shadows' in modes:
    GROUPS = {
        'left': ['tall1', 'tall2', 'oven'], 'base': ['base1', 'base2', 'base3', 'base4', 'base5', 'worktop'],
        'upper': ['up1', 'up2', 'hood', 'topl', 'topu1', 'topu2', 'topf', 'topc'], 'fridge': ['fridge'],
        'coffee': ['cpanel', 'cbase1', 'cbase2', 'cbase3', 'cbase4', 'cworktop', 'espresso', 'shelf1', 'shelf2', 'shelf3'],
        'island': ['island', 'islandtop', 'stool1', 'stool2', 'stool3'],
    }
    for g, ids in GROUPS.items():
        reset()
        for o in ENV_DONE:
            o.hide_render = True
        for o in ENV_RAW:
            o.is_shadow_catcher = True
        for o in ALL_PIECE_OBJS:
            o.hide_render = True
        for pid in ids:
            for o in PIECES[pid]:
                o.hide_render = False
                o.visible_camera = False
        r.film_transparent = True
        render_to('s_' + g)

print('all done', flush=True)
