# AUX travelling cabinet (auxwood.com redesign, home page), rendered with Cycles as transparent frames.
#
# Frames 1-48 (24 fps, played by time on the page): the parts fly in from round the frame and assemble -
#   bottom, sides, back, top, shelf, then the two doors; the left door ends ajar.
# Frames 49-140 (played by scroll): the open door closes, a light line routes the classic door profile
#   (top to bottom), white lacquer sweeps over the whole cabinet (right to left), and it turns to face the
#   viewer. The last frame is a straight front view that the page maps onto the kitchen photo's upper doors.
#
# blender -b --python tools/cabinet/cabinet.py -- --frames 1-140 --width 1000 --spp 128 --chunk 0/4 --out out
# Writes f###.png (RGBA, shadow in alpha) and meta.json (projected points per frame, 0..1 of the frame).
import argparse
import glob
import json
import math
import os
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--frames', default='1-140')
ap.add_argument('--width', type=int, default=1000)
ap.add_argument('--spp', type=int, default=128)
ap.add_argument('--chunk', default='0/1')
ap.add_argument('--out', default='out')
ARGS = ap.parse_args(argv)
os.makedirs(ARGS.out, exist_ok=True)

INTRO, END, FPS = 48, 140, 24
W, H, D = 0.60, 0.62, 0.32          # cabinet (m): an upper two-door unit
T, DT, GAP, BACK = 0.018, 0.019, 0.003, 0.008
DW = (W - GAP - 0.002) / 2          # door width
YF = -D / 2 - 0.0015                # back plane of the doors (they sit in front of the carcass)
REST_L, REST_R = -58.0, 8.0         # door angles at rest in the hero (deg)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
coll = scene.collection
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, END


def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# ------------------------------------------------------------------ materials
def node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n


def math_node(nt, op, a=None, b=None):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


ROOT = bpy.data.objects.new('cabinet', None)   # the cabinet's own space (masks are drawn in it)
coll.objects.link(ROOT)
ANIM_VALUES = []                               # (value node, 'cut'|'paint')


def mdf_lacquer(name, door=None):
    """Raw MDF that turns to white lacquer where the sweep has passed. door: 'slab' shows below the cut
    line, 'routed' above it; both glow along the line itself."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    own = nt.nodes.new('ShaderNodeTexCoord')                  # the part's own space: grain moves with it
    cab = nt.nodes.new('ShaderNodeTexCoord')
    cab.object = ROOT                                         # cabinet space: where the line / sweep is
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(cab.outputs['Object'], sep.inputs[0])

    # MDF: fine speckled fibre over a soft mottle
    speck = node(nt, 'ShaderNodeTexNoise', Scale=900.0, Detail=4.0, Roughness=0.6)
    mott = node(nt, 'ShaderNodeTexNoise', Scale=14.0, Detail=3.0, Roughness=0.5)
    nt.links.new(own.outputs['Object'], speck.inputs['Vector'])
    nt.links.new(own.outputs['Object'], mott.inputs['Vector'])
    mixf = node(nt, 'ShaderNodeMath')
    mixf.operation = 'MULTIPLY_ADD'
    nt.links.new(speck.outputs['Fac'], mixf.inputs[0])
    mixf.inputs[1].default_value = 0.45
    nt.links.new(mott.outputs['Fac'], mixf.inputs[2])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.55
    ramp.color_ramp.elements[0].color = (0.40, 0.25, 0.13, 1)
    ramp.color_ramp.elements[1].position = 0.95
    ramp.color_ramp.elements[1].color = (0.60, 0.42, 0.24, 1)
    nt.links.new(mixf.outputs[0], ramp.inputs['Fac'])
    bump = node(nt, 'ShaderNodeBump', Strength=0.08, Distance=0.0004)
    nt.links.new(speck.outputs['Fac'], bump.inputs['Height'])
    mdf = node(nt, 'ShaderNodeBsdfPrincipled', Roughness=0.74)
    mdf.inputs['Specular IOR Level'].default_value = 0.35
    nt.links.new(ramp.outputs['Color'], mdf.inputs['Base Color'])
    nt.links.new(bump.outputs['Normal'], mdf.inputs['Normal'])

    # white satin lacquer
    lac = node(nt, 'ShaderNodeBsdfPrincipled', Roughness=0.33)
    lac.inputs['Base Color'].default_value = (0.84, 0.83, 0.81, 1)
    lac.inputs['Coat Weight'].default_value = 0.3
    lac.inputs['Coat Roughness'].default_value = 0.1

    # the sweep: lacquered where x > paint (moves from the right edge to the left)
    paint = nt.nodes.new('ShaderNodeValue')
    paint.outputs[0].default_value = 10.0
    ANIM_VALUES.append((paint, 'paint'))
    hi = math_node(nt, 'ADD', paint.outputs[0], 0.05)
    mr = nt.nodes.new('ShaderNodeMapRange')
    nt.links.new(sep.outputs['X'], mr.inputs['Value'])
    nt.links.new(paint.outputs[0], mr.inputs['From Min'])
    nt.links.new(hi, mr.inputs['From Max'])
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(mr.outputs['Result'], mix.inputs[0])
    nt.links.new(mdf.outputs[0], mix.inputs[1])
    nt.links.new(lac.outputs[0], mix.inputs[2])
    shader = mix.outputs[0]

    if door:
        cut = nt.nodes.new('ShaderNodeValue')
        cut.outputs[0].default_value = 100.0
        ANIM_VALUES.append((cut, 'cut'))
        show = math_node(nt, 'GREATER_THAN' if door == 'routed' else 'LESS_THAN', sep.outputs['Z'], cut.outputs[0])
        # the router's glowing line
        dist = math_node(nt, 'ABSOLUTE', math_node(nt, 'SUBTRACT', sep.outputs['Z'], cut.outputs[0]))
        glow = nt.nodes.new('ShaderNodeMapRange')
        nt.links.new(dist, glow.inputs['Value'])
        glow.inputs['From Min'].default_value = 0.0
        glow.inputs['From Max'].default_value = 0.0035
        glow.inputs['To Min'].default_value = 45.0
        glow.inputs['To Max'].default_value = 0.0
        em = nt.nodes.new('ShaderNodeEmission')
        em.inputs['Color'].default_value = (1.0, 0.55, 0.2, 1)
        nt.links.new(glow.outputs['Result'], em.inputs['Strength'])
        add = nt.nodes.new('ShaderNodeAddShader')
        nt.links.new(shader, add.inputs[0])
        nt.links.new(em.outputs[0], add.inputs[1])
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        fin = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(show, fin.inputs[0])
        nt.links.new(tr.outputs[0], fin.inputs[1])
        nt.links.new(add.outputs[0], fin.inputs[2])
        shader = fin.outputs[0]
    nt.links.new(shader, out.inputs['Surface'])
    return m


def plain(name, color, rough, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    return m


M_CARCASS = mdf_lacquer('carcass')
M_SLAB = mdf_lacquer('door_slab', 'slab')
M_ROUTED = mdf_lacquer('door_routed', 'routed')
M_METAL = plain('nickel', (0.78, 0.78, 0.76), 0.22, 1.0)
M_HOLE = plain('hole', (0.02, 0.015, 0.01), 0.9)


# ------------------------------------------------------------------ geometry
def bevel_edges(bm, width, segs=2, min_angle=10):
    edges = [e for e in bm.edges if e.is_manifold and e.calc_face_angle(0) > math.radians(min_angle)]
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=width, offset_type='OFFSET', segments=segs, profile=0.5,
                        affect='EDGES', clamp_overlap=True)


def box_mesh(name, sx, sy, sz, bev=0.0012):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    if bev:
        bevel_edges(bm, bev)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def routed_mesh(name, w, t, h):
    """A classic door: frame, a small step, a cove down into the panel, a slightly raised field."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * w, v.co.y * t, v.co.z * h))
    centre = Vector((0, -t / 2, 0))

    def inner():
        bm.normal_update()
        return min((f for f in bm.faces if f.normal.y < -0.9), key=lambda f: (f.calc_center_median() - centre).length)

    for thick, depth in ((0.052, 0.0), (0.004, -0.0015), (0.012, -0.0055), (0.012, 0.002)):
        bmesh.ops.inset_individual(bm, faces=[inner()], thickness=thick, depth=depth, use_even_offset=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    bevel_edges(bm, 0.0008)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def cyl_mesh(name, r, depth, axis='Y', verts=24):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=depth)
    for v in bm.verts:
        x, y, z = v.co
        v.co = Vector((x, z, y)) if axis == 'Y' else (Vector((z, y, x)) if axis == 'X' else v.co)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def put(name, me, mat, loc, parent):
    o = bpy.data.objects.new(name, me)
    me.materials.append(mat)
    coll.objects.link(o)
    o.parent = parent
    o.location = loc
    return o


ROOT.location = (0, 0, 0)
ROOT.rotation_euler = (0, 0, math.radians(28))
sideL = put('sideL', box_mesh('sideL', T, D, H), M_CARCASS, (-W / 2 + T / 2, 0, H / 2), ROOT)
sideR = put('sideR', box_mesh('sideR', T, D, H), M_CARCASS, (W / 2 - T / 2, 0, H / 2), ROOT)
top = put('top', box_mesh('top', W - 2 * T, D, T), M_CARCASS, (0, 0, H - T / 2), ROOT)
bottom = put('bottom', box_mesh('bottom', W - 2 * T, D, T), M_CARCASS, (0, 0, T / 2), ROOT)
back = put('back', box_mesh('back', W - 2 * T, BACK, H - 2 * T, 0.0006), M_CARCASS, (0, D / 2 - 0.012 - BACK / 2, H / 2), ROOT)
SD = D - 0.05
shelf = put('shelf', box_mesh('shelf', W - 2 * T - 0.002, SD, T), M_CARCASS, (0, -D / 2 + 0.015 + SD / 2, H / 2), ROOT)

# 32 mm system holes on the inner faces of the sides, and the hinge plates
for side, sx in ((sideL, 1), (sideR, -1)):
    for yy in (-D / 2 + 0.037, D / 2 - 0.05):
        for k in range(14):
            z = -H / 2 + 0.105 + k * 0.032
            if z > H / 2 - 0.1:
                break
            put('hole', cyl_mesh('hole', 0.0025, 0.0008, 'X', 12), M_HOLE, (sx * (T / 2 + 0.0002), yy, z), side)
    for hz in (-H / 2 + 0.09, H / 2 - 0.09):
        put('plate', box_mesh('plate', 0.004, 0.046, 0.013, 0.0008), M_METAL, (sx * (T / 2 + 0.002), -D / 2 + 0.036, hz), side)

hinges, doors = [], []
for s in (-1, 1):   # -1 left door, +1 right door
    hg = bpy.data.objects.new('hingeL' if s < 0 else 'hingeR', None)
    coll.objects.link(hg)
    hg.parent = ROOT
    hg.location = (s * (W / 2 - 0.001), YF, 0)
    cx = -s * DW / 2
    slab = put('slab', box_mesh('slab', DW, DT, H), M_SLAB, (cx, -DT / 2, H / 2), hg)
    routed = put('routed', routed_mesh('routed', DW, DT, H), M_ROUTED, (cx, -DT / 2, H / 2), hg)
    for hz in (-H / 2 + 0.09, H / 2 - 0.09):   # hinge cups on the back of the door
        put('cup', cyl_mesh('cup', 0.0175, 0.0016), M_METAL, (s * (DW / 2 - 0.0225), DT / 2 + 0.0006, hz), slab)
    hinges.append(hg)

# floor that only catches the shadow
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
catcher = bpy.context.active_object
catcher.is_shadow_catcher = True

# ------------------------------------------------------------------ animation
# intro: (object, offset in cabinet space (m), extra rotation it sheds (rad), start (s))
FLY = [
    (bottom, (-1.3, -0.4, 0.15), (0.0, 0.9, -1.2), 0.00),
    (sideL, (-1.4, 0.2, 0.9), (0.4, -1.4, 0.8), 0.10),
    (sideR, (1.5, -0.3, 0.5), (-0.5, 1.5, -0.6), 0.18),
    (back, (0.3, 2.5, 1.8), (0.8, 0.3, 0.4), 0.30),
    (top, (-0.2, -0.2, 1.3), (-0.9, -0.4, 0.7), 0.40),
    (shelf, (1.3, -1.0, 0.2), (0.4, 1.1, 0.5), 0.52),
    (hinges[0], (-1.3, -1.2, 0.3), (0.2, 0.3, -1.8), 0.66),
    (hinges[1], (1.4, -1.0, 0.2), (-0.25, -0.3, 1.9), 0.76),
]
DUR = 0.85
REST = {o: (o.location.copy(), o.rotation_euler.copy()) for o, *_ in FLY}


def back_out(t, c=0.6):
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def state(f):
    s = {}
    if f <= INTRO:
        t = (f - 1) / FPS
        for o, off, spin, d in FLY:
            p = clamp((t - d) / DUR)
            k, ks = 1 - back_out(p), (1 - p) ** 3
            s[o] = (off, spin, k, ks)
        u = 0.0
    else:
        u = (f - INTRO - 1) / (END - INTRO - 1)
    s['u'] = u
    s['doorL'] = math.radians(REST_L) * (1 - smooth(u / 0.16))
    s['doorR'] = math.radians(REST_R) * (1 - smooth(u / 0.12))
    if f <= INTRO or u < 0.06:
        s['cut'] = 100.0
    elif u < 0.46:
        s['cut'] = lerp(H + 0.012, -0.012, (u - 0.06) / 0.4)
    else:
        s['cut'] = -0.012
    if f <= INTRO or u < 0.48:
        s['paint'] = 10.0
    elif u < 0.8:
        s['paint'] = lerp(W / 2 + 0.08, -W / 2 - 0.13, smooth((u - 0.48) / 0.32))
    else:
        s['paint'] = -W / 2 - 0.13
    if u < 0.5:
        rz = lerp(28, 26, smooth(u / 0.5))
    elif u < 0.8:
        rz = lerp(26, 16, smooth((u - 0.5) / 0.3))
    else:
        rz = lerp(16, 0, smooth((u - 0.8) / 0.2))
    s['rz'] = math.radians(rz)
    s['lift'] = 0.10 * smooth(u / 0.35)
    s['floor'] = -1.8 * smooth((u - 0.04) / 0.36)
    s['exposure'] = 0.0
    return s


for f in range(1, END + 1):
    s = state(f)
    ROOT.location = (0, 0, s['lift'])
    ROOT.rotation_euler = (0, 0, s['rz'])
    ROOT.keyframe_insert('location', frame=f)
    ROOT.keyframe_insert('rotation_euler', frame=f)
    catcher.location = (0, 0, s['floor'])
    catcher.keyframe_insert('location', frame=f)
    for o, (loc, rot) in REST.items():
        swing = s['doorL'] if o is hinges[0] else (s['doorR'] if o is hinges[1] else 0.0)
        if o in s:
            off, spin, k, ks = s[o]
            o.location = loc + Vector(off) * k
            o.rotation_euler = (rot.x + spin[0] * ks, rot.y + spin[1] * ks, rot.z + swing + spin[2] * ks)
        else:
            o.location = loc
            o.rotation_euler = (rot.x, rot.y, rot.z + swing)
        o.keyframe_insert('location', frame=f)
        o.keyframe_insert('rotation_euler', frame=f)
    for n, kind in ANIM_VALUES:
        n.outputs[0].default_value = s[kind]
        n.outputs[0].keyframe_insert('default_value', frame=f)

for idb in list(bpy.data.objects) + list(bpy.data.materials):
    ad = getattr(idb, 'animation_data', None) if isinstance(idb, bpy.types.Object) else (idb.node_tree.animation_data if idb.node_tree else None)
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT' if isinstance(idb, bpy.types.Material) else 'LINEAR'

# ------------------------------------------------------------------ light and camera
world = bpy.data.worlds.new('w')
world.use_nodes = True
scene.world = world
bg = world.node_tree.nodes['Background']
hdri = sorted(glob.glob(os.path.join(bpy.utils.system_resource('DATAFILES'), 'studiolights', 'world', '*.exr')))
pick = [h for h in hdri if 'interior' in h] or hdri
if pick:
    env = world.node_tree.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(pick[0])
    world.node_tree.links.new(env.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 0.35
    print('hdri', pick[0], flush=True)
else:
    bg.inputs['Color'].default_value = (0.6, 0.58, 0.55, 1)
    bg.inputs['Strength'].default_value = 0.3


def area(name, size, size_y, loc, energy, color, target=(0, 0, 0.33)):
    o = bpy.data.objects.new(name, bpy.data.lights.new(name, 'AREA'))
    o.data.shape = 'RECTANGLE'
    o.data.size, o.data.size_y = size, size_y
    o.data.energy = energy
    o.data.color = color
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    coll.objects.link(o)
    return o


area('key', 1.6, 1.0, (-1.7, -2.1, 2.1), 520, (1.0, 0.9, 0.78))      # window light, top left
area('fill', 2.2, 2.2, (2.4, -2.5, 0.8), 140, (0.9, 0.95, 1.0))      # soft fill, right
area('rim', 0.8, 1.8, (1.6, 1.9, 1.7), 320, (1.0, 0.97, 0.92))       # edge light from behind
area('top', 2.0, 2.0, (0.0, -0.4, 2.6), 160, (1.0, 0.98, 0.95), (0, -0.4, 0))

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
cam.data.lens = 85
cam.data.sensor_width = 36
cam.location = (0, -3.2, H / 2)          # level with the cabinet's middle: verticals stay vertical
cam.rotation_euler = (math.radians(90), 0, 0)
coll.objects.link(cam)
scene.camera = cam

# ------------------------------------------------------------------ render settings
r = scene.render
r.engine = 'CYCLES'
r.resolution_x = r.resolution_y = ARGS.width
r.resolution_percentage = 100
r.film_transparent = True
r.image_settings.file_format = 'PNG'
r.image_settings.color_mode = 'RGBA'
r.image_settings.compression = 30
r.use_persistent_data = True
r.motion_blur_shutter = 0.5
c = scene.cycles
c.device = 'CPU'
c.samples = ARGS.spp
c.use_adaptive_sampling = True
c.adaptive_threshold = 0.015
c.use_denoising = True
c.denoiser = 'OPENIMAGEDENOISE'
c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces = 8, 4, 4, 2
c.transparent_max_bounces = 24
c.caustics_reflective = c.caustics_refractive = False
c.sample_clamp_indirect = 5
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'


# ------------------------------------------------------------------ frames + meta
def frames_from(spec):
    out = []
    for part in spec.split(','):
        part = part.strip()
        if '-' in part:
            a, b = part.split('-')
            step = 1
            if ':' in b:
                b, step = b.split(':')
            out += list(range(int(a), int(b) + 1, int(step)))
        elif part:
            out.append(int(part))
    return out


def proj(co):
    v = world_to_camera_view(scene, cam, co)
    return [round(v.x, 4), round(1 - v.y, 4)]


def meta_of(f):
    scene.frame_set(f)
    bpy.context.view_layer.update()
    m = ROOT.matrix_world
    yf = YF - DT
    pts = [m @ Vector((x, y, z)) for x in (-W / 2, W / 2) for y in (yf, D / 2) for z in (0, H)]
    pp = [proj(p) for p in pts]
    s = state(f)
    out = {
        'c': proj(m @ Vector((0, 0, H / 2))),
        'box': [min(p[0] for p in pp), min(p[1] for p in pp), max(p[0] for p in pp), max(p[1] for p in pp)],
        'front': [proj(m @ Vector(p)) for p in ((-W / 2 + 0.001, yf, H), (W / 2 - 0.001, yf, H), (W / 2 - 0.001, yf, 0), (-W / 2 + 0.001, yf, 0))],
    }
    if -0.01 < s['cut'] < H + 0.01:
        out['cut'] = [proj(m @ Vector((-W / 2, yf, s['cut']))), proj(m @ Vector((W / 2, yf, s['cut'])))]
    if f > INTRO and s['paint'] < 1:
        out['paint'] = [proj(m @ Vector((s['paint'], yf, 0))), proj(m @ Vector((s['paint'], yf, H)))]
    return out


ci, cn = (int(x) for x in ARGS.chunk.split('/'))
if ci == 0:
    meta = {'intro': INTRO, 'end': END, 'fps': FPS, 'frames': {f: meta_of(f) for f in range(1, END + 1)}}
    with open(os.path.join(ARGS.out, 'meta.json'), 'w') as fh:
        json.dump(meta, fh)
    print('meta written', flush=True)

mine = frames_from(ARGS.frames)[ci::cn]
for f in mine:
    scene.frame_set(f)
    s = state(f)
    r.use_motion_blur = f <= INTRO
    scene.view_settings.exposure = s['exposure']
    r.filepath = os.path.join(ARGS.out, 'f%03d.png' % f)
    bpy.ops.render.render(write_still=True)
    print('rendered', f, flush=True)
