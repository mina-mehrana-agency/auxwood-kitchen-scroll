/*
 * Builds akx.js: the AUX501 kitchen as an architect's drawing, modelled in metres and projected
 * with a pinhole camera, so every line lands where a draughtsman would put it.
 * Run from the repo root:  node tools/build-scene.js
 *
 * Camera: eye 1.6 m above the floor, looking straight down the room. Room: 6 m wide, 2.8 m high,
 * back wall 7 m away. Drawing space: 1020 x 610.
 */
const fs = require('fs');

const F = 600, E = 1.6, CX = 510, HY = 235, VW = 1020, VH = 610;
const W = 3, H = 2.8, ZB = 7, ZN = 2.1;
const INK = '#23262b';

const r1 = (n) => Math.round(n * 10) / 10;
const proj = ([x, y, z]) => [CX + (F * x) / z, HY - (F * (y - E)) / z];
const pt = (p) => `${r1(p[0])} ${r1(p[1])}`;
const M = (...v) => `M${v.map((a) => pt(proj(a))).join('L')}`;
const Z = (...v) => `${M(...v)}Z`;
const ring = (x, y, z, r, n = 28) => `${Array.from({ length: n }, (_, i) => {
  const a = (i / n) * Math.PI * 2; return (i ? 'L' : 'M') + pt(proj([x + r * Math.cos(a), y, z + r * Math.sin(a)]));
}).join('')}Z`;

/* Seeded wobble for the pencil stage, identical on every build. */
let seed = 29;
const rnd = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
const jit = (a) => (rnd() - 0.5) * 2 * a;
const sketch2 = (a, b, over = 10, wob = 2.2) => {
  const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L;
  const s = [a[0] - ux * over * (0.4 + rnd()) + jit(1), a[1] - uy * over * (0.4 + rnd()) + jit(1)];
  const e = [b[0] + ux * over * (0.4 + rnd()) + jit(1), b[1] + uy * over * (0.4 + rnd()) + jit(1)];
  const m = [(s[0] + e[0]) / 2 - uy * jit(wob), (s[1] + e[1]) / 2 + ux * jit(wob)];
  return `M${pt(s)}Q${pt(m)} ${pt(e)}`;
};
const sk = (a, b, over) => sketch2(proj(a), proj(b), over);

/* Colours of the wash stage. */
const C = {
  ceiling: '#EFEAE2', left: '#EDE6DA', right: '#F1EBE0', back: '#E7C9B0', splash: '#F7F3EB', floor: '#F2EDE4', tile: '#E3DACA',
  front: '#C7D7DE', side: '#AEC3CC', plinth: '#B6C9D1', top: '#F4F0E9', edge: '#E7E1D6', hood: '#34373C', hob: '#3A3D42',
  panel: '#DF9A5E', shelf: '#3B3C3F', shelfTop: '#55565A', body: '#CDDBE1', wood: '#B98F6C', pot: '#C4764A', potB: '#E9E1D5', shade: '#2F3236',
};

/* A piece gathers fills and ink in drawing order. */
function piece(id, move) {
  const p = { id, m: move, f: [], push(d, col) { this.f.push([d, col]); return this; }, line(d, w = 1.1, op = 0.9) { this.f.push([d, 0, w, op]); return this; } };
  return p;
}

const quad = (x0, x1, y0, y1, z) => Z([x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z]);
function door(p, x0, x1, y0, y1, z, handle) {
  const i = 0.05;
  p.line(quad(x0 + i, x1 - i, y0 + i, y1 - i, z), 0.7, 0.7);
  if (handle) p.line(handle, 1.9, 1);
}
const vHandle = (x, y0, y1, z) => M([x, y0, z], [x, y1, z]);
const hHandle = (x0, x1, y, z) => M([x0, y, z], [x1, y, z]);

/* ---------- Tall unit on the left of the back wall (two parts) ---------- */
const Z0 = 6.4;
const TL = { x0: -2.85, x1: -1.75 };
const tallLower = piece('tall-lower', [0, 0.68, 1.1, 0.2, 0.27]);
tallLower.push(Z([TL.x1, 0, Z0], [TL.x1, 0, ZB], [TL.x1, 1.02, ZB], [TL.x1, 1.02, Z0]), C.side)
  .line(Z([TL.x1, 0, Z0], [TL.x1, 0, ZB], [TL.x1, 1.02, ZB], [TL.x1, 1.02, Z0]), 1)
  .push(quad(TL.x0, TL.x1, 0, 1.02, Z0), C.front).line(quad(TL.x0, TL.x1, 0, 1.02, Z0), 1.35, 0.95)
  .line(M([TL.x0, 0.1, Z0], [TL.x1, 0.1, Z0]), 0.9, 0.8).line(M([-2.3, 0.1, Z0], [-2.3, 1.02, Z0]), 1, 0.9);
door(tallLower, TL.x0, -2.3, 0.1, 1.02, Z0, vHandle(-2.38, 0.68, 0.96, Z0));
door(tallLower, -2.3, TL.x1, 0.1, 1.02, Z0, vHandle(-2.22, 0.68, 0.96, Z0));

const tallUpper = piece('tall-upper', [0, -0.72, 1, 0.24, 0.31]);
tallUpper.push(Z([TL.x1, 1.02, Z0], [TL.x1, 1.02, ZB], [TL.x1, 2.42, ZB], [TL.x1, 2.42, Z0]), C.side)
  .line(Z([TL.x1, 1.02, Z0], [TL.x1, 1.02, ZB], [TL.x1, 2.42, ZB], [TL.x1, 2.42, Z0]), 1)
  .push(quad(TL.x0, TL.x1, 1.02, 2.42, Z0), C.front).line(quad(TL.x0, TL.x1, 1.02, 2.42, Z0), 1.35, 0.95)
  .line(M([-2.3, 1.02, Z0], [-2.3, 2.42, Z0]), 1, 0.9);
door(tallUpper, TL.x0, -2.3, 1.02, 2.42, Z0, vHandle(-2.38, 1.08, 1.38, Z0));
door(tallUpper, -2.3, TL.x1, 1.02, 2.42, Z0, vHandle(-2.22, 1.08, 1.38, Z0));

/* ---------- Base run, three modules ---------- */
const baseModule = (id, x0, x1, a, b, drawers) => {
  const p = piece(id, [0, 0.55, 1.14, a, b]);
  p.push(quad(x0, x1, 0, 0.1, Z0 + 0.05), C.plinth).line(quad(x0, x1, 0, 0.1, Z0 + 0.05), 0.8, 0.8);
  p.push(quad(x0, x1, 0.1, 0.86, Z0), C.front).line(quad(x0, x1, 0.1, 0.86, Z0), 1.2, 0.95);
  if (drawers) {
    p.line(M([x0, 0.47, Z0], [x1, 0.47, Z0]), 1, 0.9);
    door(p, x0, x1, 0.1, 0.47, Z0, hHandle(x0 + 0.32, x1 - 0.32, 0.4, Z0));
    door(p, x0, x1, 0.47, 0.86, Z0, hHandle(x0 + 0.32, x1 - 0.32, 0.79, Z0));
  } else {
    door(p, x0, x1, 0.1, 0.86, Z0, hHandle(x0 + 0.26, x1 - 0.26, 0.79, Z0));
  }
  return p;
};
const baseL = baseModule('base-l', -1.75, -0.85, 0.3, 0.36, false);
const baseM = baseModule('base-m', -0.85, 0.85, 0.32, 0.38, true);
const baseR = baseModule('base-r', 0.85, 1.75, 0.34, 0.4, false);

/* ---------- Worktop with the hob ---------- */
const worktop = piece('worktop', [0, -0.42, 1, 0.38, 0.43]);
const WZ0 = 6.34;
worktop.push(Z([-1.78, 0.9, WZ0], [1.78, 0.9, WZ0], [1.75, 0.9, ZB], [-1.75, 0.9, ZB]), C.top)
  .line(Z([-1.78, 0.9, WZ0], [1.78, 0.9, WZ0], [1.75, 0.9, ZB], [-1.75, 0.9, ZB]), 1)
  .push(quad(-1.78, 1.78, 0.86, 0.9, WZ0), C.edge).line(quad(-1.78, 1.78, 0.86, 0.9, WZ0), 1.1, 0.95)
  .push(Z([-0.46, 0.905, 6.5], [0.46, 0.905, 6.5], [0.46, 0.905, 6.86], [-0.46, 0.905, 6.86]), C.hob)
  .line(Z([-0.46, 0.905, 6.5], [0.46, 0.905, 6.5], [0.46, 0.905, 6.86], [-0.46, 0.905, 6.86]), 0.8);

/* ---------- Ribbed chimney and hood ---------- */
const CH_R = 0.58;
const chimneyArc = (y) => Array.from({ length: 13 }, (_, i) => { const t = Math.PI - (i / 12) * Math.PI; return [Math.cos(t) * CH_R, y, ZB - Math.sin(t) * CH_R]; });
const chimney = piece('chimney', [0, -0.42, 1, 0.42, 0.47]);
const arcLo = chimneyArc(1.64), arcHi = chimneyArc(H);
chimney.push(Z(...arcLo, ...[...arcHi].reverse()), C.body).line(Z(...arcLo, ...[...arcHi].reverse()), 1.2, 0.95);
for (let i = 1; i < 18; i++) {
  const t = Math.PI - (i / 18) * Math.PI, x = Math.cos(t) * CH_R, z = ZB - Math.sin(t) * CH_R;
  chimney.line(M([x, 1.64, z], [x, H, z]), 0.55, 0.55);
}
const hood = piece('hood', [0, -0.3, 1, 0.44, 0.49]);
hood.push(quad(-0.98, 0.98, 1.5, 1.64, 6.46), C.hood).line(quad(-0.98, 0.98, 1.5, 1.64, 6.46), 1.1, 1)
  .line(M([-0.98, 1.53, 6.46], [0.98, 1.53, 6.46]), 0.5, 0.5);

/* ---------- Tall fridge unit on the right ---------- */
const TR = { x0: 1.75, x1: 2.85 };
const fridge = piece('fridge', [0.5, 0, 1, 0.47, 0.53]);
fridge.push(Z([TR.x0, 0, Z0], [TR.x0, 0, ZB], [TR.x0, 2.42, ZB], [TR.x0, 2.42, Z0]), C.side)
  .line(Z([TR.x0, 0, Z0], [TR.x0, 0, ZB], [TR.x0, 2.42, ZB], [TR.x0, 2.42, Z0]), 1)
  .push(quad(TR.x0, TR.x1, 0, 2.42, Z0), C.front).line(quad(TR.x0, TR.x1, 0, 2.42, Z0), 1.35, 0.95)
  .line(M([TR.x0, 0.1, Z0], [TR.x1, 0.1, Z0]), 0.9, 0.8);
door(fridge, TR.x0, TR.x1, 0.1, 2.42, Z0, vHandle(1.88, 0.72, 1.62, Z0));

/* ---------- Orange panel and black shelves on the right wall ---------- */
const shelves = piece('shelves', [0.34, 0, 1, 0.52, 0.58]);
const SZ0 = 4.85, SZ1 = 6.25, SX = 2.7;
shelves.push(Z([W, 0, 4.7], [W, 0, 6.4], [W, 2.62, 6.4], [W, 2.62, 4.7]), C.panel).line(Z([W, 0, 4.7], [W, 0, 6.4], [W, 2.62, 6.4], [W, 2.62, 4.7]), 1.1, 0.9);
const shelfBox = (y0, y1) => {
  const below = y0 > E;
  const side = Z([SX, y0, SZ0], [SX, y0, SZ1], [SX, y1, SZ1], [SX, y1, SZ0]);
  const end = Z([SX, y0, SZ0], [W, y0, SZ0], [W, y1, SZ0], [SX, y1, SZ0]);
  const lid = below ? Z([SX, y0, SZ0], [SX, y0, SZ1], [W, y0, SZ1], [W, y0, SZ0]) : Z([SX, y1, SZ0], [SX, y1, SZ1], [W, y1, SZ1], [W, y1, SZ0]);
  shelves.push(lid, C.shelfTop).line(lid, 0.7, 0.9).push(side, C.shelf).line(side, 0.9, 1).push(end, C.shelf).line(end, 0.9, 1);
};
shelfBox(1.92, 2.3); shelfBox(1.5, 1.54); shelfBox(1.22, 1.26); shelfBox(0.52, 0.98);
shelves.line(M([SX - 0.03, 0.06, 5.25], [SX - 0.03, 2.56, 5.25]), 2.2, 1).line(M([SX - 0.03, 0.06, 5.85], [SX - 0.03, 2.56, 5.85]), 2.2, 1);

/* ---------- The curved island ---------- */
const IS = { xc: 0, zc: 3.95, half: 0.86, R: 0.42 };
const stadium = (r, n = 18) => {
  const pts = [];
  for (let i = 0; i <= n; i++) { const a = -Math.PI / 2 - (i / n) * Math.PI; pts.push([IS.xc - IS.half + Math.cos(a) * r, IS.zc + Math.sin(a) * r, a]); }
  for (let i = 0; i <= n; i++) { const a = Math.PI / 2 - (i / n) * Math.PI; pts.push([IS.xc + IS.half + Math.cos(a) * r, IS.zc + Math.sin(a) * r, a]); }
  return pts;
};
/* The part of the outline that faces the camera, ordered left to right. */
const frontRun = (r) => {
  const out = [];
  for (let i = 0; i <= 18; i++) { const a = Math.PI + (i / 18) * (Math.PI / 2); out.push([IS.xc - IS.half + Math.cos(a) * r, IS.zc + Math.sin(a) * r]); }
  for (let i = 0; i <= 18; i++) { const a = -Math.PI / 2 + (i / 18) * (Math.PI / 2); out.push([IS.xc + IS.half + Math.cos(a) * r, IS.zc + Math.sin(a) * r]); }
  return out;
};
const island = piece('island', [0, 0.62, 1.2, 0.57, 0.63]);
{
  const run = frontRun(IS.R), lo = run.map(([x, z]) => [x, 0, z]), hi = run.map(([x, z]) => [x, 0.88, z]);
  const body = Z(...lo, ...[...hi].reverse());
  island.push(body, C.body).line(body, 1.3, 0.95);
  for (let i = 1; i < 19; i++) {
    const a = Math.PI + (i / 19) * (Math.PI / 2), x = IS.xc - IS.half + Math.cos(a) * IS.R, z = IS.zc + Math.sin(a) * IS.R;
    island.line(M([x, 0.03, z], [x, 0.86, z]), 0.55, 0.6);
  }
  for (let i = 1; i < 19; i++) {
    const a = -Math.PI / 2 + (i / 19) * (Math.PI / 2), x = IS.xc + IS.half + Math.cos(a) * IS.R, z = IS.zc + Math.sin(a) * IS.R;
    island.line(M([x, 0.03, z], [x, 0.86, z]), 0.55, 0.6);
  }
  island.line(M([-0.3, 0.02, IS.zc - IS.R], [-0.3, 0.87, IS.zc - IS.R]), 0.6, 0.45).line(M([0.3, 0.02, IS.zc - IS.R], [0.3, 0.87, IS.zc - IS.R]), 0.6, 0.45);
  const topOut = stadium(IS.R + 0.05).map(([x, z]) => [x, 0.92, z]);
  const lipLo = frontRun(IS.R + 0.05).map(([x, z]) => [x, 0.88, z]), lipHi = frontRun(IS.R + 0.05).map(([x, z]) => [x, 0.92, z]);
  const lip = Z(...lipLo, ...[...lipHi].reverse());
  island.push(lip, C.edge).line(lip, 1, 0.95).push(Z(...topOut), C.top).line(Z(...topOut), 1.2, 0.95);
}

/* ---------- Pendants and stools ---------- */
const pendants = piece('pendants', [0, -0.5, 1, 0.61, 0.65]);
for (const x of [-0.82, 0.82]) {
  const z = IS.zc, top = 2.02, bot = 1.78, r = 0.17;
  const [lx, ly] = proj([x - r, bot, z]); const [rx] = proj([x + r, bot, z]); const [, ty] = proj([x, top, z]);
  const dome = `M${r1(lx)} ${r1(ly)}C${r1(lx + 2)} ${r1(ty + 1)} ${r1(rx - 2)} ${r1(ty + 1)} ${r1(rx)} ${r1(ly)}Z`;
  pendants.line(M([x, H, z], [x, top, z]), 0.7, 0.85).push(dome, C.shade).line(dome, 1.1, 1);
}
const stools = piece('stools', [0, 0.3, 1.08, 0.63, 0.67]);
for (const x of [-0.6, 0.6]) {
  const z = 3.15, r = 0.17, s = 0.68;
  for (const [i, j] of [[-1, 1], [1, 1], [-1, -1], [1, -1]]) stools.line(M([x + i * r * 0.65, s, z + j * r * 0.65], [x + i * r * 0.95, 0, z + j * r * 0.95]), 1, 0.9);
  stools.line(ring(x, 0.24, z, r * 0.82, 22), 0.7, 0.75).push(ring(x, s, z, r, 24), C.wood).line(ring(x, s, z, r, 24), 1.1, 0.95);
}

const pieces = [tallLower, tallUpper, baseL, baseM, baseR, worktop, chimney, hood, fridge, shelves, island, pendants, stools];

/* ---------- Bounding boxes: each piece only paints its own small area ---------- */
const nums = (d) => (d.match(/-?\d+(\.\d+)?/g) || []).map(Number);
const bbox = (ds) => {
  let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
  for (const d of ds) { const n = nums(d); for (let i = 0; i + 1 < n.length; i += 2) { x0 = Math.min(x0, n[i]); x1 = Math.max(x1, n[i]); y0 = Math.min(y0, n[i + 1]); y1 = Math.max(y1, n[i + 1]); } }
  return [Math.floor(x0 - 3), Math.floor(y0 - 3), Math.ceil(x1 - x0 + 6), Math.ceil(y1 - y0 + 6)];
};

/* ---------- Pencil: the first sketch ---------- */
const BW = { tl: [-W, H, ZB], tr: [W, H, ZB], br: [W, 0, ZB], bl: [-W, 0, ZB] };
const pencil = [
  sketch2([6, HY], [VW - 6, HY], 4, 1.4),
  ...[[0, 0], [VW, 0], [0, VH], [VW, VH]].map((c) => sketch2([CX, HY], c, 12, 3)),
  sk(BW.tl, BW.tr), sk(BW.tr, BW.br), sk(BW.br, BW.bl), sk(BW.bl, BW.tl),
  sk([TL.x0, 2.42, Z0], [TL.x1, 2.42, Z0], 8), sk([TL.x1, 0, Z0], [TL.x1, 2.42, Z0], 6),
  sk([TR.x0, 2.42, Z0], [TR.x1, 2.42, Z0], 8), sk([TR.x0, 0, Z0], [TR.x0, 2.42, Z0], 6),
  sk([-1.75, 0.9, Z0], [1.75, 0.9, Z0], 8),
  sk([W, 2.62, 4.7], [W, 2.62, 6.4], 8), sk([W, 0, 4.7], [W, 0, 6.4], 8),
  ring(IS.xc - IS.half, 0.92, IS.zc, IS.R + 0.05, 14), ring(IS.xc + IS.half, 0.92, IS.zc, IS.R + 0.05, 14),
  sk([-IS.half, 0.92, IS.zc - IS.R], [IS.half, 0.92, IS.zc - IS.R], 8),
];
const notes = [
  { x: pt(proj([-2.3, 2.62, Z0])).split(' ')[0], y: r1(proj([-2.3, 2.62, Z0])[1]), t: 'کابینت بلند' },
  { x: r1(proj([0, 2.05, Z0])[0]), y: r1(proj([0, 2.05, Z0])[1]), t: 'هود' },
  { x: r1(proj([0, 0.3, 3.2])[0]), y: r1(proj([0, 0.3, 3.2])[1]), t: 'جزیرهٔ منحنی' },
];

/* ---------- Ink: the raw room ---------- */
const shell = [
  Z(BW.tl, BW.tr, BW.br, BW.bl),
  M([-W, H, ZN], BW.tl), M([W, H, ZN], BW.tr), M([-W, 0, ZN], BW.bl), M([W, 0, ZN], BW.br),
  Z([-W, 0.82, 4], [-W, 0.82, 5.8], [-W, 2.42, 5.8], [-W, 2.42, 4]),
];
/* Raw-building marks: power boxes, capped pipes, ceiling conduit, plaster strokes. */
const box2 = (x, y, s = 0.09) => quad(x - s, x + s, y - s * 0.72, y + s * 0.72, ZB);
const wire = (x, y) => { const [a, b] = proj([x, y - 0.07, ZB]); return `M${r1(a)} ${r1(b)}q-3 7 1 12q3 4 0 8`; };
const stub = (x, y) => `${ring(x, y, ZB - 0.02, 0.035, 12)}${M([x - 0.05, y, ZB], [x + 0.05, y, ZB])}`;
let hatch = '';
for (const [x0, y0, z, n] of [[-W, 1.5, 6.3, 7], [-W, 0.42, 4.6, 6], [W, 1.2, 3.8, 7], [W, 2.2, 5.6, 5]]) {
  for (let i = 0; i < n; i++) { const dz = i * 0.11; hatch += M([x0, y0 - i * 0.03, z + dz], [x0, y0 + 0.32 - i * 0.03, z + dz + 0.14]); }
}
for (const [x0, y0, n] of [[-1.9, 2.15, 8], [1.15, 0.5, 8], [1.55, 2.25, 6], [-2.55, 0.42, 6]]) {
  for (let i = 0; i < n; i++) { const dx = i * 0.07; hatch += M([x0 + dx, y0, ZB], [x0 + dx + 0.13, y0 + 0.24, ZB]); }
}
let specks = '';
for (let i = 0; i < 46; i++) { const x = -2.7 + rnd() * 5.4, z = 2.8 + rnd() * 3.9, s = 0.03 + rnd() * 0.07; specks += M([x, 0, z], [x + s, 0, z + s * 0.5]); }
const rawMarks = [
  [box2(-1.05, 1.16), 0.9, 0.85], [box2(1.05, 1.16), 0.9, 0.85], [box2(0, 1.72, 0.12), 0.9, 0.85],
  [wire(-1.05, 1.16) + wire(1.05, 1.16) + wire(0, 1.72), 0.7, 0.8],
  [stub(-0.3, 0.46) + stub(0, 0.46) + stub(0.34, 0.52), 0.9, 0.85],
  [`${M([-1.35, H - 0.02, ZN + 0.9], [-1.35, H - 0.02, ZB])}${M([-1.29, H - 0.02, ZN + 0.9], [-1.29, H - 0.02, ZB])}${M([-1.32, H - 0.02, ZB], [-1.32, 1.28, ZB])}`, 0.7, 0.7],
  [hatch, 0.5, 0.35], [specks, 0.6, 0.3],
];

/* ---------- Finished room ---------- */
const T = 0.6;
const tileX = []; for (let x = -W + T; x < W - 0.01; x += T) tileX.push(x);
const tileZ = []; for (let z = 2.1; z < ZB; z += T) tileZ.push(z);
const floorLines = [...tileX.map((x) => M([x, 0, ZN], [x, 0, ZB])), ...tileZ.map((z) => M([-W, 0, z], [W, 0, z]))].join('');
let checker = '';
for (let i = 0; i < 10; i++) for (let j = 0; j < 10; j++) {
  if ((i + j) % 2) continue;
  const x0 = -W + i * T, z0 = 2.1 - T + j * T, z1 = Math.min(ZB, z0 + T);
  if (z0 >= ZB) continue;
  const a = Math.max(z0, ZN);
  checker += Z([x0, 0, a], [x0 + T, 0, a], [x0 + T, 0, z1], [x0, 0, z1]);
}
let planks = '';
for (let x = -W + 0.24; x < W; x += 0.24) planks += M([x, H, ZN], [x, H, ZB]);

/* Olive tree in the foreground, pot and leaves. */
const olive = (tx, tz, crown, spread, n, seed0) => {
  let sd = seed0;
  const rr = () => { sd = (sd * 16807) % 2147483647; return (sd - 1) / 2147483646; };
  const potFill = ring(tx, 0.4, tz, 0.2, 26);
  const potLines = `${potFill}${M([tx - 0.2, 0.4, tz], [tx - 0.15, 0, tz])}${M([tx + 0.2, 0.4, tz], [tx + 0.15, 0, tz])}`;
  const potBody = Z([tx - 0.2, 0.4, tz], [tx + 0.2, 0.4, tz], [tx + 0.15, 0, tz], [tx - 0.15, 0, tz]);
  const trunk = `${M([tx, 0.4, tz], [tx - 0.05, crown * 0.6, tz], [tx + 0.04, crown * 0.85, tz])}${M([tx - 0.03, crown * 0.68, tz], [tx - spread * 0.45, crown * 0.92, tz])}${M([tx + 0.02, crown * 0.75, tz], [tx + spread * 0.4, crown * 0.95, tz])}`;
  let leaves = '';
  for (let i = 0; i < n; i++) {
    const a = rr() * Math.PI * 2, rad = Math.sqrt(rr()), x = tx + Math.cos(a) * rad * spread, y = crown + Math.sin(a) * rad * spread * 0.62;
    const [cx, cy] = proj([x, y, tz]); const len = (F * (0.11 + rr() * 0.07)) / tz, ang = rr() * Math.PI;
    const dx = Math.cos(ang) * len, dy = Math.sin(ang) * len * 0.8, nx = -dy * 0.33, ny = dx * 0.33;
    leaves += `M${r1(cx - dx / 2)} ${r1(cy - dy / 2)}Q${r1(cx + nx)} ${r1(cy + ny)} ${r1(cx + dx / 2)} ${r1(cy + dy / 2)}Q${r1(cx - nx)} ${r1(cy - ny)} ${r1(cx - dx / 2)} ${r1(cy - dy / 2)}Z`;
  }
  return { potFill, potLines, potBody, trunk, leaves, shadow: ring(tx, 0.005, tz, 0.4) };
};
const tree = olive(-2.3, 3.5, 1.85, 0.56, 30, 5);

const finishBack = [
  [Z([-W, H, ZN], [W, H, ZN], BW.tr, BW.tl), C.ceiling], [Z([-W, H, ZN], BW.tl, BW.bl, [-W, 0, ZN]), C.left], [Z([W, H, ZN], BW.tr, BW.br, [W, 0, ZN]), C.right],
  [Z(BW.tl, BW.tr, BW.br, BW.bl), C.back], [quad(-1.75, 1.75, 0.9, 1.5, ZB), C.splash], [Z([-W, 0, ZN], [W, 0, ZN], BW.br, BW.bl), C.floor], [checker, C.tile],
  [`${ring(0, 0.005, IS.zc, 0, 3)}${Z([-1.5, 0.005, 3.35], [1.5, 0.005, 3.35], [1.7, 0.005, 4.6], [-1.7, 0.005, 4.6])}${tree.shadow}${Z([-1.75, 0.005, 6.4], [1.75, 0.005, 6.4], [1.75, 0.005, 6.05], [-1.75, 0.005, 6.05])}`, '#0B1526', 0.07],
  [floorLines, 0, 0.55, 0.3], [planks, 0, 0.5, 0.22], ...shell.map((d) => [d, 0, 1.4, 0.92]),
  [`${M([-W, 2.02, 4], [-W, 2.02, 5.8])}${M([-W, 0.82, 4.9], [-W, 2.42, 4.9])}`, 0, 0.8, 0.85],
  [M([-W + 0.08, 0.82, 4], [-W + 0.08, 0.82, 5.8]), 0, 0.8, 0.85],
];
const finishFront = [
  [tree.potBody, C.pot, 0.82], [tree.potFill, C.potB], [tree.potLines, 0, 1, 0.9], [tree.trunk, 0, 1, 0.9], [tree.leaves, '#8FA27D'], [tree.leaves, 0, 0.55, 0.75],
];

/* ---------- Light ---------- */
const sun = (y) => [0.95 * y, -0.3 * y];
const sunPatch = (a, b) => { const lo = 0.82, hi = 1.62; const c = (z, y) => { const [dx, dz] = sun(y); return [-W + dx, 0.001, z + dz]; }; return Z(c(a, lo), c(a, hi), c(b, hi), c(b, lo)); };
const skyPane = Z([-W, 0.82, 4], [-W, 0.82, 5.8], [-W, 2.42, 5.8], [-W, 2.42, 4]);
const outside = Z([-W, 0.82, 4.05], [-W, 1.4, 4.2], [-W, 1.72, 4.6], [-W, 1.5, 4.9], [-W, 1.8, 5.25], [-W, 1.42, 5.7], [-W, 0.82, 5.75]);
const glow = [-0.82, 0.82].map((x) => { const [cx, cy] = proj([x, 1.76, IS.zc]); return [r1(cx), r1(cy + 8)]; });
const cones = [-0.82, 0.82].map((x) => `${M([x - 0.14, 1.78, IS.zc], [x - 0.42, 0.93, IS.zc])}${M([x + 0.14, 1.78, IS.zc], [x + 0.42, 0.93, IS.zc])}`).join('');

/* ---------- People (architectural scale figures) ---------- */
const figure = (x, z, h) => {
  const [fx, fy] = proj([x, 0, z]); const s = (F * h) / z / 100;
  const P = (px, py) => `${r1(fx + px * s)} ${r1(fy + py * s)}`;
  const head = `M${P(-6, -93)}a${r1(6 * s)} ${r1(6.5 * s)} 0 1 0 ${r1(12 * s)} 0a${r1(6 * s)} ${r1(6.5 * s)} 0 1 0 ${r1(-12 * s)} 0`;
  return `${head}M${P(-9, -84)}C${P(-12, -80)} ${P(-13, -62)} ${P(-11, -50)}L${P(-9, -26)}L${P(-7, 0)}L${P(-2, 0)}L${P(0, -40)}L${P(2, 0)}L${P(7, 0)}L${P(9, -26)}L${P(11, -50)}C${P(13, -62)} ${P(12, -80)} ${P(9, -84)}C${P(4, -87)} ${P(-4, -87)} ${P(-9, -84)}Z`;
};
const people = [figure(1.22, 5.2, 1.72), figure(-1.3, 5.6, 1.66)].join('');

const out = {
  V: [VW, VH], INK,
  P: pencil, N: notes,
  S: shell, K: rawMarks,
  Q: pieces.map((p) => ({ id: p.id, m: p.m, f: p.f, b: bbox(p.f.map((x) => x[0])) })),
  A: finishBack, Z: finishFront,
  L: { sky: skyPane, out: outside, sun: [sunPatch(4, 4.86), sunPatch(4.94, 5.8)], glow, cones },
  U: people,
  D: { y: r1(proj(BW.tl)[1] - 12), x0: r1(proj(BW.tl)[0]), x1: r1(proj(BW.tr)[0]) },
};

const tpl = fs.readFileSync('tools/akx.template.js', 'utf8');
const js = tpl.replace('__SCENE__', JSON.stringify(out));
fs.writeFileSync('akx.js', js);
const gz = require('zlib').gzipSync(js).length;
console.log('akx.js', js.length, 'bytes, gzip', gz, '| pieces', pieces.length);
