// Stick-figure characters and illustrated sets for engine.html ("scene" visuals).
// A scene: {type:"scene", bg, actors:[...], items:[...], panel:{<any other visual>}, camera}
const SVGNS = 'http://www.w3.org/2000/svg';
const GROUND = 800;
const L = {upperArm: 82, lowerArm: 78, upperLeg: 104, lowerLeg: 100, neck: 330, hip: 200, head: 385};

// Joint angles in degrees: 0 = hanging straight down, negative swings toward the facing direction.
const POSES = {
  stand:  {la: 14, lf: -6, ra: -14, rf: 6, ll: 6, lk: 0, rl: -6, rk: 0, tilt: 0, head: 0},
  walkA:  {la: 32, lf: -12, ra: -34, rf: -18, ll: -26, lk: 14, rl: 24, rk: 22, tilt: -4, head: 0},
  walkB:  {la: -34, lf: -18, ra: 32, rf: -12, ll: 24, lk: 22, rl: -26, rk: 14, tilt: -4, head: 0},
  point:  {la: 16, lf: -8, ra: -92, rf: -6, ll: 8, lk: 0, rl: -8, rk: 0, tilt: -3, head: -4},
  cheer:  {la: 150, lf: 20, ra: -150, rf: -20, ll: 10, lk: 0, rl: -10, rk: 0, tilt: 0, head: -6},
  shrug:  {la: 58, lf: -105, ra: -58, rf: 105, ll: 8, lk: 0, rl: -8, rk: 0, tilt: 0, head: 8},
  think:  {la: 14, lf: -6, ra: -35, rf: -128, ll: 6, lk: 0, rl: -6, rk: 0, tilt: 2, head: 10},
  shock:  {la: 128, lf: 35, ra: -128, rf: -35, ll: 18, lk: 0, rl: -18, rk: 0, tilt: 6, head: -10},
  sad:    {la: 6, lf: 0, ra: -6, rf: 0, ll: 4, lk: 0, rl: -4, rk: 0, tilt: 10, head: 22},
  push:   {la: -70, lf: -20, ra: -78, rf: -16, ll: -14, lk: 10, rl: 18, rk: 18, tilt: -10, head: 0},
  carry:  {la: -40, lf: -100, ra: -46, rf: -96, ll: 6, lk: 0, rl: -6, rk: 0, tilt: 4, head: 0},
  wave:   {la: 14, lf: -6, ra: -150, rf: -30, ll: 6, lk: 0, rl: -6, rk: 0, tilt: 0, head: -6},
  facepalm: {la: 14, lf: -6, ra: -60, rf: -150, ll: 6, lk: 0, rl: -6, rk: 0, tilt: 6, head: 18},
};
const MOUTHS = {
  happy: 'M -20 8 Q 0 30 20 8', grin: 'M -24 4 Q 0 40 24 4 Z', neutral: 'M -16 14 L 16 14',
  sad: 'M -18 22 Q 0 4 18 22', shock: 'M -10 16 a 10 13 0 1 0 20 0 a 10 13 0 1 0 -20 0',
  smug: 'M -18 14 Q 4 24 22 6', open: 'M -14 8 Q 0 34 14 8 Z', worried: 'M -18 18 Q -6 10 0 16 Q 8 22 18 14',
};
const BROWS = {
  happy: [[-30, -22, -8, -26], [8, -26, 30, -22]], neutral: null, sad: [[-30, -24, -8, -30], [8, -30, 30, -24]],
  shock: [[-30, -34, -8, -38], [8, -38, 30, -34]], smug: [[-30, -26, -8, -24], [8, -30, 30, -34]],
  worried: [[-30, -26, -8, -32], [8, -32, 30, -26]], grin: null, open: null,
};

function sv(tag, attrs = {}, parent) {
  const e = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
}
function joint(parent, x, y) {  // positioned group whose child rotates about the joint
  const g = sv('g', {transform: `translate(${x},${y})`}, parent);
  const r = sv('g', {}, g);
  r.style.transformBox = 'view-box'; r.style.transformOrigin = '0px 0px';
  return r;
}
let INK = '#f5f7ff', HEAD = '#141b34';   // stick-figure line and head colours; the paper theme swaps them
const STROKE = {stroke: INK, 'stroke-width': 15, 'stroke-linecap': 'round', fill: 'none'};
window.setInk = (ink, head) => { INK = ink; HEAD = head; STROKE.stroke = ink; };

function makeActor(svg, a) {
  const root = sv('g', {}, svg);                       // x position (walks)
  const bob = sv('g', {}, root);                       // vertical bounce
  const flip = sv('g', {transform: a.flip ? 'scale(-1,1)' : ''}, bob);
  const scale = a.scale || 1.35;
  const body = sv('g', {transform: `scale(${scale})`}, flip);
  const torso = joint(body, 0, -L.hip);                // tilts at the hip
  sv('line', {...STROKE, x1: 0, y1: 0, x2: 0, y2: -(L.neck - L.hip)}, torso);
  const limbs = {};
  const arm = (side) => {
    const sh = joint(torso, 0, -(L.neck - L.hip) + 22);
    sv('line', {...STROKE, x1: 0, y1: 0, x2: 0, y2: L.upperArm}, sh);
    const el = joint(sh, 0, L.upperArm);
    sv('line', {...STROKE, x1: 0, y1: 0, x2: 0, y2: L.lowerArm}, el);
    limbs[side + 'a'] = sh; limbs[side + 'f'] = el;
    return el;
  };
  arm('l'); const rightHand = arm('r');
  const leg = (side) => {
    const hp = joint(body, 0, -L.hip);
    sv('line', {...STROKE, x1: 0, y1: 0, x2: 0, y2: L.upperLeg}, hp);
    const kn = joint(hp, 0, L.upperLeg);
    sv('line', {...STROKE, x1: 0, y1: 0, x2: 0, y2: L.lowerLeg}, kn);
    sv('line', {...STROKE, x1: 0, y1: L.lowerLeg, x2: 16, y2: L.lowerLeg}, kn);
    limbs[side + 'l'] = hp; limbs[side + 'k'] = kn;
  };
  leg('l'); leg('r');
  body.insertBefore(body.lastChild, body.firstChild);  // legs behind torso
  body.insertBefore(body.lastChild, body.firstChild);
  const head = joint(torso, 0, -(L.head - L.hip) + 50);
  const face = sv('g', {transform: 'translate(0,-50)'}, head);
  sv('circle', {cx: 0, cy: 0, r: 56, fill: a.skin || HEAD, stroke: INK, 'stroke-width': 13}, face);
  if (a.cap) {
    sv('path', {d: 'M -58 -10 A 58 58 0 0 1 58 -10 Z', fill: COLORS[a.cap] || a.cap}, face);
    sv('path', {d: 'M 40 -14 L 92 -10 L 52 -2 Z', fill: COLORS[a.cap] || a.cap}, face);
  }
  if (a.tie) sv('path', {d: 'M -10 -112 L 10 -112 L 6 -60 L 0 -50 L -6 -60 Z', fill: COLORS[a.tie] || a.tie}, torso);
  if (a.hair) sv('path', {d: 'M -56 -6 Q -50 -70 6 -60 Q 50 -64 56 -10 Q 30 -40 -10 -36 Q -40 -34 -56 -6', fill: INK}, face);
  const eyes = sv('g', {}, face); eyes.style.transformBox = 'view-box'; eyes.style.transformOrigin = '0px -6px';
  sv('circle', {cx: -18, cy: -6, r: 7, fill: INK}, eyes); sv('circle', {cx: 18, cy: -6, r: 7, fill: INK}, eyes);
  const brow = sv('g', {}, face);
  const mouths = {};
  for (const [k, d] of Object.entries(MOUTHS)) {
    const fillable = d.endsWith('Z') || k === 'shock';
    mouths[k] = sv('path', {d, stroke: INK, 'stroke-width': 8, 'stroke-linecap': 'round',
      fill: fillable ? INK : 'none', opacity: 0}, face);
  }
  return {root, bob, limbs, eyes, brow, mouths, rightHand, face};
}

function setPose(actor, pose, at, dur) {
  const p = POSES[pose] || POSES.stand;
  const map = {la: 'la', lf: 'lf', ra: 'ra', rf: 'rf', ll: 'll', lk: 'lk', rl: 'rl', rk: 'rk'};
  for (const [k, limb] of Object.entries({la: actor.limbs.la, lf: actor.limbs.lf, ra: actor.limbs.ra, rf: actor.limbs.rf,
                                          ll: actor.limbs.ll, lk: actor.limbs.lk, rl: actor.limbs.rl, rk: actor.limbs.rk})) {
    const to = p[map[k]];
    const from = actor.cur ? actor.cur[k] : to;
    anim(limb, [{transform: `rotate(${from}deg)`}, {transform: `rotate(${to}deg)`}], at, dur, {easing: OVERSHOOT});
  }
  actor.cur = p;
}

function setFace(actor, expr, at, end) {
  const m = actor.mouths[expr] || actor.mouths.happy;
  const on = [{opacity: 1}, {opacity: 1, offset: .995}, {opacity: 0}];
  anim(m, on, at, Math.max(.05, end - at), {easing: 'linear', fill: 'forwards'});
  const b = BROWS[expr];
  if (b) b.forEach(([x1, y1, x2, y2]) => {
    const line = sv('line', {x1, y1, x2, y2, stroke: INK, 'stroke-width': 7, 'stroke-linecap': 'round', opacity: 0}, actor.brow);
    anim(line, on, at, Math.max(.05, end - at), {easing: 'linear', fill: 'forwards'});
  });
}

function talk(actor, at, end) {  // mouth flaps while speaking
  const m = actor.mouths.open;
  const n = Math.max(1, Math.floor((end - at) / .22));
  anim(m, [{opacity: 0}, {opacity: 1}, {opacity: 0}], at, .22, {iterations: n, easing: 'steps(2, jump-none)', fill: 'none'});
}

function blink(actor, at, end) {
  const period = 2.8;
  anim(actor.eyes, [{transform: 'scaleY(1)', offset: 0}, {transform: 'scaleY(1)', offset: .93},
                    {transform: 'scaleY(.1)', offset: .965}, {transform: 'scaleY(1)', offset: 1}],
       at + Math.random(), period, {iterations: Math.max(1, Math.ceil((end - at) / period)), easing: 'linear'});
}

function bubble(svg, x, y, b, at, end) {
  const g = sv('g', {}, svg); const inner = sv('g', {transform: `translate(${x},${y})`}, g);
  const w = b.icon ? 190 : Math.min(760, 60 + (b.text || '').length * 28), hgt = b.icon ? 170 : 120;
  sv('rect', {x: -w / 2, y: -hgt, width: w, height: hgt, rx: 40, fill: b.think ? '#f5f7ff' : '#ffffff', stroke: '#1b1f3b', 'stroke-width': 5}, inner);
  if (b.think) { sv('circle', {cx: -30, cy: 26, r: 16, fill: '#f5f7ff'}, inner); sv('circle', {cx: -54, cy: 56, r: 9, fill: '#f5f7ff'}, inner); }
  else { sv('path', {d: 'M -40 -2 L -70 50 L 0 -2', fill: '#ffffff', stroke: '#1b1f3b', 'stroke-width': 5, 'stroke-linejoin': 'round'}, inner);
         sv('rect', {x: -46, y: -8, width: 52, height: 9, fill: '#ffffff'}, inner); }
  if (b.icon) {
    const holder = sv('foreignObject', {x: -60, y: -145, width: 120, height: 120}, inner);
    const ic = icon(b.icon, b.color || '#0b1020'); ic.setAttribute('width', 120); ic.setAttribute('height', 120);
    ic.style.strokeWidth = 2.2; holder.appendChild(ic);
  } else {
    const t = sv('text', {x: 0, y: -hgt / 2 + 18, 'text-anchor': 'middle', 'font-family': 'Inter', 'font-weight': 900,
      'font-size': 50, fill: '#0b1020'}, inner); t.textContent = b.text;
  }
  g.style.transformBox = 'view-box'; g.style.transformOrigin = `${x}px ${y}px`;
  anim(g, [{transform: 'scale(0)', opacity: 0}, {transform: 'scale(1)', opacity: 1}], at, .4, {easing: OVERSHOOT});
  anim(g, [{opacity: 1}, {opacity: 0}], end - .15, .15, {easing: 'linear'});
  g.getAnimations()[1].effect.updateTiming({fill: 'forwards'});
}

const PALETTES = {
  dark:  {ceiling: '#10172f', light: '#ffe9a8', panel: '#1b2550', panel2: '#222d5e', line: '#2c3a72', floor: '#0e1430', dim: '#0b1020', dimOp: .35},
  paper: {ceiling: '#f1f1ec', light: '#ffe08a', panel: '#ffffff', panel2: '#f6f6f2', line: '#2b2f45', floor: '#ececE6', dim: '#ffffff', dimOp: .1},
  light: {ceiling: '#eadfca', light: '#fff3c4', panel: '#ffffff', panel2: '#f3ead9', line: '#d8cbb3', floor: '#e8dcc6', dim: '#f6f1e7', dimOp: .15},
};
let PAL = PALETTES.dark;

// --- illustrated sets -------------------------------------------------------------
const SETS = {
  store(svg) {
    sv('rect', {x: 0, y: 0, width: 1920, height: 120, fill: PAL.ceiling}, svg);
    for (let i = 0; i < 6; i++) { sv('rect', {x: 120 + i * 300, y: 110, width: 160, height: 14, rx: 7, fill: PAL.light, opacity: .8}, svg); }
    const boxColors = ['#ff5e5b', '#ffc93c', '#2ec4b6', '#4d7cfe', '#f78c6b', '#a78bfa'];
    for (let s = 0; s < 4; s++) {
      const x0 = 30 + s * 480;
      sv('rect', {x: x0, y: 230, width: 400, height: 570, fill: PAL.panel, stroke: PAL.line, 'stroke-width': 6}, svg);
      for (let r = 0; r < 4; r++) {
        sv('rect', {x: x0, y: 360 + r * 140, width: 400, height: 10, fill: PAL.line}, svg);
        for (let c = 0; c < 5; c++) {
          const hh = 60 + ((s * 7 + r * 3 + c * 5) % 4) * 14;
          sv('rect', {x: x0 + 14 + c * 77, y: 360 + r * 140 - hh, width: 66, height: hh, rx: 6,
            fill: boxColors[(s + r * 2 + c) % 6], opacity: .55}, svg);
        }
      }
    }
    sv('rect', {x: 0, y: GROUND, width: 1920, height: 80, fill: PAL.floor}, svg);
  },
  city(svg) {
    sv('circle', {cx: 1500, cy: 220, r: 110, fill: '#ffc93c', opacity: .9}, svg);
    const heights = [380, 520, 300, 610, 440, 350, 560, 410, 300, 480];
    heights.forEach((hh, i) => {
      const x = i * 196 - 20;
      sv('rect', {x, y: GROUND - hh, width: 170, height: hh, fill: i % 2 ? PAL.panel : PAL.panel2}, svg);
      for (let wy = GROUND - hh + 30; wy < GROUND - 40; wy += 60)
        for (let wx = x + 22; wx < x + 150; wx += 50)
          sv('rect', {x: wx, y: wy, width: 26, height: 30, fill: (wx * wy) % 7 < 3 ? PAL.light : PAL.line, opacity: .8}, svg);
    });
    sv('rect', {x: 0, y: GROUND, width: 1920, height: 80, fill: PAL.floor}, svg);
  },
  office(svg) {
    sv('rect', {x: 1180, y: 120, width: 560, height: 380, rx: 16, fill: PAL.panel, stroke: PAL.line, 'stroke-width': 8}, svg);
    [180, 240, 150, 300, 260].forEach((hh, i) => sv('rect', {x: 1240 + i * 95, y: 470 - hh, width: 60, height: hh, rx: 6,
      fill: ['#2ec4b6', '#4d7cfe', '#ff5e5b', '#ffc93c', '#2ec4b6'][i]}, svg));
    sv('rect', {x: 1100, y: 600, width: 700, height: 30, rx: 10, fill: PAL.line}, svg);
    sv('rect', {x: 1150, y: 630, width: 24, height: 170, fill: PAL.line}, svg);
    sv('rect', {x: 1730, y: 630, width: 24, height: 170, fill: PAL.line}, svg);
    sv('rect', {x: 0, y: GROUND, width: 1920, height: 80, fill: PAL.floor}, svg);
  },
  plain(svg) { sv('rect', {x: 0, y: GROUND, width: 1920, height: 6, fill: PAL.line}, svg); },
};

BUILD.scene = function (sec, s, t0, t1) {
  const stage = h('div'); stage.style.cssText = 'position:absolute;inset:0;';
  sec.appendChild(stage);
  const svg = sv('svg', {viewBox: '0 0 1920 880', width: 1920, height: 880});
  svg.style.cssText = 'position:absolute;inset:0;overflow:visible';
  stage.appendChild(svg);
  const set = sv('g', {}, svg); (SETS[s.bg] || SETS.plain)(set);
  if (s.bg && s.bg !== 'plain') {    // parallax drift on the set
    anim(set, [{transform: 'translateX(0px)'}, {transform: `translateX(${s.pan === 'right' ? -60 : 60}px)`}], t0, t1 - t0, {easing: 'linear'});
    sv('rect', {x: -200, y: -100, width: 2400, height: 1100, fill: PAL.dim, opacity: PAL.dimOp}, set);
  }
  const front = sv('g', {}, svg);
  const mid = (t0 + t1) / 2;
  (s.actors || []).forEach((a, i) => {
    if (a.cast || a.body) {          // cartoon person (peeps.js)
      const info = window.buildPeepActor(front, a, i, t0, t1);
      if (a.cart) {
        const cart = sv('foreignObject', {x: a.flip ? -380 : 120, y: GROUND - info.neckY - 250, width: 260, height: 260}, info.pos);
        const ic = icon('shopping-cart', a.cart_color || 'teal'); ic.setAttribute('width', 260); ic.setAttribute('height', 260);
        ic.style.strokeWidth = 1.6; cart.appendChild(ic);
      }
      if (a.bubble) {
        const bw = a.bubble.icon ? 190 : Math.min(760, 60 + (a.bubble.text || '').length * 28);
        const bx = info.x + (a.flip ? -1 : 1) * (bw / 2 + 90);
        bubble(front, Math.min(1900 - bw / 2, Math.max(bw / 2 + 20, bx)), Math.max(150, info.headTopY - 10), a.bubble,
               t0 + (a.bubble.at ?? .4) * (t1 - t0), t1);
      }
      return;
    }
    const actor = makeActor(front, a);
    const x0 = (a.x ?? .5) * 1920, x1 = (a.to ?? a.x ?? .5) * 1920;
    const switchAt = a.then ? t0 + (t1 - t0) * (a.switch ?? .55) : t1;
    // entrance: walk in or pop up
    if (a.to != null && a.to !== a.x) {
      const walkEnd = a.then ? switchAt : t1;
      anim(actor.root, [{transform: `translate(${x0}px, ${GROUND}px)`}, {transform: `translate(${x1}px, ${GROUND}px)`}], t0, walkEnd - t0, {easing: 'linear'});
      setPose(actor, 'walkA', t0, .01);
      const step = .32, n = Math.max(1, Math.floor((walkEnd - t0) / step));
      ['la', 'lf', 'ra', 'rf', 'll', 'lk', 'rl', 'rk'].forEach(k => {
        anim(actor.limbs[k], [{transform: `rotate(${POSES.walkA[k]}deg)`}, {transform: `rotate(${POSES.walkB[k]}deg)`}],
             t0, step, {iterations: n, direction: 'alternate', easing: 'ease-in-out'});
      });
      anim(actor.bob, [{transform: 'translateY(0)'}, {transform: 'translateY(-14px)'}], t0, step / 2,
           {iterations: n * 2, direction: 'alternate', easing: 'ease-out'});
      actor.cur = POSES.walkB;
      if (a.then) setPose(actor, a.then, walkEnd, .35);
    } else {
      anim(actor.root, [{transform: `translate(${x0}px, ${GROUND + 500}px)`}, {transform: `translate(${x0}px, ${GROUND}px)`}],
           t0 + i * .12, .5, {easing: OVERSHOOT});
      setPose(actor, a.pose || 'stand', t0, .01);
      setPose(actor, a.pose || 'stand', t0 + .2, .4);
      if (a.then) setPose(actor, a.then, switchAt, .35);
      // idle sway so nobody freezes
      anim(actor.bob, [{transform: 'translateY(0) rotate(0deg)'}, {transform: 'translateY(-6px) rotate(1.5deg)'}], t0 + .6, 1.1,
           {iterations: Math.max(1, Math.ceil((t1 - t0) / 1.1)), direction: 'alternate', easing: 'ease-in-out'});
    }
    const e1 = a.expr || 'happy';
    if (a.then_expr) { setFace(actor, e1, t0, switchAt); setFace(actor, a.then_expr, switchAt, t1); }
    else setFace(actor, e1, t0, t1);
    if (a.talk) talk(actor, t0 + .3, t1 - .2);
    blink(actor, t0, t1);
    if (a.prop) {
      const holder = sv('foreignObject', {x: -45, y: L.lowerArm - 30, width: 90, height: 90}, actor.rightHand);
      const ic = icon(a.prop, a.prop_color || 'yellow'); ic.setAttribute('width', 90); ic.setAttribute('height', 90); holder.appendChild(ic);
    }
    if (a.cart) {
      const cart = sv('foreignObject', {x: a.flip ? -330 : 90, y: -230, width: 240, height: 240}, actor.bob);
      const ic = icon('shopping-cart', a.cart_color || 'teal'); ic.setAttribute('width', 240); ic.setAttribute('height', 240);
      ic.style.strokeWidth = 1.6; cart.appendChild(ic);
    }
    if (a.bubble) {
      const sc = a.scale || 1.35;
      const bw = a.bubble.icon ? 190 : Math.min(760, 60 + (a.bubble.text || '').length * 28);
      const bx = (a.to != null ? x1 : x0) + (a.flip ? -1 : 1) * (bw / 2 + 60);
      const by = GROUND - 470 * sc + 10;
      bubble(front, Math.min(1900 - bw / 2, Math.max(bw / 2 + 20, bx)), Math.max(150, by), a.bubble,
             t0 + (a.bubble.at ?? .4) * (t1 - t0), t1);
    }
  });
  (s.items || []).forEach((it, i) => {
    const d = h('div', 'tile'); const size = it.size || 200;
    d.style.cssText += `;position:absolute;width:${size}px;height:${size}px;left:${it.x * 1920 - size / 2}px;top:${it.y * 880 - size / 2}px`;
    const ic = icon(it.icon, it.color || PALETTE[i % 4]); ic.style.width = ic.style.height = (size * .58) + 'px'; d.appendChild(ic);
    if (it.label) { const l = h('div', 'label', it.label); l.style.cssText = 'position:absolute;top:100%;margin-top:14px;font-size:44px;white-space:nowrap'; d.appendChild(l); }
    stage.appendChild(d);
    const at = t0 + (it.at ?? (.25 + i * .2)) * (it.at != null ? (t1 - t0) : 1);
    if (it.fall) anim(d, [{transform: 'translateY(-900px) rotate(-30deg)'}, {transform: 'translateY(0) rotate(0)'}], at, .55, {easing: 'cubic-bezier(.5,0,.75,1.4)'});
    else popIn(d, at);
    float(d, at + .6, t1, 8);
  });
  if (s.panel) {   // motion-graphics panel beside the characters
    const p = h('section'); p.style.cssText = 'position:absolute;opacity:1;left:auto;right:0;width:1100px;height:880px;transform-origin:center;';
    p.style.right = s.panel_side === 'left' ? 'auto' : '0'; if (s.panel_side === 'left') p.style.left = '0';
    stage.appendChild(p);
    const card = h('div'); card.style.cssText = 'position:absolute;inset:60px 40px;border-radius:48px;background:var(--tile);box-shadow:0 30px 80px rgba(0,0,0,.5),inset 0 0 0 4px rgba(255,255,255,.06)';
    if (!['receipt'].includes(s.panel.type)) { p.appendChild(card); popIn(card, t0 + (s.panel_at ?? .3) * (t1 - t0) - .1); }
    const inner = h('div'); inner.style.cssText = 'position:relative;transform:scale(.78);display:flex;align-items:center;justify-content:center;width:100%;height:100%';
    p.appendChild(inner);
    (BUILD[s.panel.type] || BUILD.icons)(inner, s.panel, t0 + (s.panel_at ?? .3) * (t1 - t0), t1);
  }
  // camera: slow push in (or out), optional punch on the beat
  const cam = s.camera || 'in';
  const fromS = cam === 'out' ? 1.1 : 1, toS = cam === 'out' ? 1 : 1.08;
  anim(stage, [{transform: `scale(${fromS})`}, {transform: `scale(${toS})`}], t0, t1 - t0, {easing: 'linear'});
  if (s.punch != null) {
    const pt = t0 + s.punch * (t1 - t0);
    anim(sec, [{scale: '1'}, {scale: '1.12'}, {scale: '1.06'}], pt, .35, {easing: OVERSHOOT});
  }
};
