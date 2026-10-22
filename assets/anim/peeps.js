// Hand-drawn cartoon people (Open Peeps by Pablo Stanley, CC0) for "scene" visuals.
// An actor with a `cast` (or `body`) key is drawn as a peep instead of a stick figure.
// Library (window.PEEPS): bodies {kind/name: {viewBox, svg, neck:[x,y]}}, heads, faces, hair_offsets.

const HEAD_FROM_NECK = [-271, -449];   // hair/head origin relative to the neck (from Open Peeps' Effigy layout)
const FACE_FROM_NECK = [-82, -273];
const SKIN = '#D08B5B', TEE = '#FFCF77', PANTS = '#9DDADB', JACKET = '#BA98DE';

// Recurring characters so every video has the same faces.
const CAST = {
  you:    {head: 'ShortOne', skin: '#E0A879', top: '#FFC93C', pants: '#4D7CFE', outfit: 'Tee'},
  friend: {head: 'LongCurly', skin: '#8D5A3B', top: '#2EC4B6', pants: '#1D2852', outfit: 'Tee'},
  exec:   {head: 'GrayShort', skin: '#F1C7A5', top: '#4D6BD8', jacket: '#33406E', outfit: 'Blazer'},
  expert: {head: 'MediumStraight', skin: '#C68A62', top: '#FF5E5B', pants: '#1D2852', outfit: 'Tee'},
};
// Pose names -> body art. Open Peeps' "ColorTee"/"ColorPants" names are not reliable, so each
// pose names the exact variant whose top carries the accent colour (pointing has no such variant).
const PEEP_POSES = {
  stand: 'standing/RestingColorPants', walk: 'standing/WalkingColorTee', point: 'standing/PointingFingerColorPants',
  cross: 'standing/CrossArmColorTee', easy: 'standing/EasingColorTee', shrug: 'standing/EasingColorTee',
  blazer: 'standing/BlazerColorTee', shirt: 'standing/ShirtColorTee',
  sit: 'sitting/MidColorTee', explain: 'effigy/Explaining', coffee: 'effigy/Coffee', laptop: 'effigy/Computer',
  paper: 'effigy/Paper', idea: 'effigy/PointingUp', arms: 'effigy/TeeArmsCrossed', whatever: 'effigy/Whatever',
};
const PEEP_FACES = {
  happy: 'Smile', grin: 'BigSmile', laugh: 'SmileLOL', shock: 'Awe', fear: 'ConcernedFear', worried: 'Concerned',
  sad: 'Solemn', tired: 'Tired', smug: 'Cheeky', angry: 'Angry', rage: 'Rage', think: 'Suspicious', neutral: 'Calm',
  talk: 'Explaining', love: 'LoveGrinTeeth', serious: 'Serious', driven: 'Driven', blank: 'Blank', cute: 'Cute',
};

function bodyKey(pose, look) {
  let k = PEEP_POSES[pose] || pose || 'standing/RestingColorPants';
  const lib = window.PEEPS.bodies;
  if (look.outfit === 'Blazer' && (pose || 'stand') === 'stand') return 'standing/BlazerColorTee';
  if (lib[k]) return k;
  const pref = [];
  const order = look.outfit === 'Tee' ? ['ColorTee', 'ColorPants'] : ['ColorPants', 'ColorTee'];
  for (const cand of [...pref, ...order.map(o => k + o), k + 'Tee', k + 'Pants'])
    if (lib[cand]) return cand;
  return 'standing/RestingColorPants';
}
function recolor(svg, look) {
  // Open Peeps uses its two accent colours inconsistently across poses, so both become the
  // character's signature colour; that keeps a character recognisable from pose to pose.
  return svg.replaceAll(SKIN, look.skin || SKIN).replaceAll(TEE, look.top || TEE)
            .replaceAll(PANTS, look.top || PANTS).replaceAll(JACKET, look.jacket || '#2B3A67');
}
function nested(parent, part, x, y, look) {
  const [, , w, hgt] = part.viewBox.split(' ').map(Number);
  const s = sv('svg', {x, y, width: w, height: hgt, viewBox: part.viewBox, overflow: 'visible'}, parent);
  s.innerHTML = recolor(part.svg, look);
  return s;
}

// Builds a peep whose neck sits at (0,0) of the returned group. Returns handles for animation.
function makePeep(parent, look, poses, faces) {
  const lib = window.PEEPS;
  const root = sv('g', {}, parent);
  const bodies = {};
  for (const p of poses) {
    const key = bodyKey(p, look); const b = lib.bodies[key];
    const g = sv('g', {opacity: 0}, root);
    nested(g, b, -b.neck[0], -b.neck[1], look);
    bodies[p] = {g, key, part: b};
  }
  const head = sv('g', {}, root); head.style.transformBox = 'view-box'; head.style.transformOrigin = '0px 0px';
  const hair = lib.heads[look.head] || lib.heads.ShortOne; const off = lib.hair_offsets[look.head] || [0, 0];
  nested(head, hair, HEAD_FROM_NECK[0] + off[0], HEAD_FROM_NECK[1] + off[1], look);
  const faceEls = {};
  for (const f of faces) {
    const part = lib.faces[PEEP_FACES[f] || f] || lib.faces.Smile;
    const g = sv('g', {opacity: 0}, head); nested(g, part, FACE_FROM_NECK[0], FACE_FROM_NECK[1], look);
    faceEls[f] = g;
  }
  return {root, head, bodies, faceEls};
}

function showFor(el, at, end) {
  anim(el, [{opacity: 1}, {opacity: 1, offset: .995}, {opacity: 0}], at, Math.max(.05, end - at), {easing: 'linear', fill: 'forwards'});
}

// Height of a peep from head top to feet (in its own units), used to scale it to the scene.
function peepHeight(part) { const vb = part.viewBox.split(' ').map(Number); return vb[3] - part.neck[1] + 449; }

window.buildPeepActor = function (front, a, i, t0, t1) {
  const look = {...(CAST[a.cast] || CAST.you), ...(a.look || {})};
  const walking = a.to != null && a.to !== a.x;
  const pose1 = walking ? 'walk' : (a.pose || 'stand');
  const pose2 = a.then || null;
  const face1 = a.expr || 'happy', face2 = a.then_expr || null;
  const poses = [pose1, ...(pose2 ? [pose2] : [])];
  const faces = [face1, ...(face2 ? [face2] : []), ...(a.talk ? ['talk'] : [])];
  const x0 = (a.x ?? .5) * 1920, x1 = (a.to ?? a.x ?? .5) * 1920;
  const switchAt = pose2 || face2 ? t0 + (t1 - t0) * (a.switch ?? .55) : t1;

  const pos = sv('g', {}, front);                        // world position
  const hop = sv('g', {}, pos);                          // bounce / squash
  hop.style.transformBox = 'view-box'; hop.style.transformOrigin = '0px 0px';
  const flip = sv('g', {transform: a.flip ? 'scale(-1,1)' : ''}, hop);
  const bust = PEEP_POSES[pose1]?.startsWith('effigy');
  const ref = window.PEEPS.bodies[bodyKey(pose1, look)];
  const targetH = (a.size || 1) * (bust ? 700 : 660);
  const k = targetH / (bust ? 1229 : peepHeight(ref));
  const scaled = sv('g', {transform: `scale(${k})`}, flip);
  // anchor: feet on the ground for standing peeps; bust bottom at the frame bottom
  const neckY = bust ? 880 - 780 * k : GROUND - (peepHeight(ref) - 449) * k;
  const peep = makePeep(scaled, look, poses, faces);

  // bodies and faces over time
  showFor(peep.bodies[pose1].g, t0, pose2 ? switchAt : t1);
  if (pose2) {
    showFor(peep.bodies[pose2].g, switchAt, t1);
    anim(hop, [{transform: 'scale(1.04, .94)'}, {transform: 'scale(1,1)'}], switchAt, .3, {easing: OVERSHOOT, fill: 'none'});
  }
  showFor(peep.faceEls[face1], t0, face2 ? switchAt : t1);
  if (face2) showFor(peep.faceEls[face2], switchAt, t1);
  if (a.talk) {   // alternate to the open-mouth face while speaking
    const n = Math.max(1, Math.floor((t1 - t0 - .5) / .28));
    anim(peep.faceEls.talk, [{opacity: 0}, {opacity: 1}, {opacity: 0}], t0 + .3, .28, {iterations: n, easing: 'steps(2, jump-none)', fill: 'none'});
  }

  if (walking) {
    const walkEnd = pose2 ? switchAt : t1;
    anim(pos, [{transform: `translate(${x0}px, ${neckY}px)`}, {transform: `translate(${x1}px, ${neckY}px)`}], t0, walkEnd - t0, {easing: 'linear'});
    const step = .3, n = Math.max(1, Math.floor((walkEnd - t0) / step));
    anim(hop, [{transform: 'translateY(0) rotate(-2deg)'}, {transform: 'translateY(-18px) rotate(2deg)'}], t0, step,
         {iterations: n, direction: 'alternate', easing: 'ease-in-out'});
  } else {
    anim(pos, [{transform: `translate(${x0}px, ${neckY + 700}px)`}, {transform: `translate(${x0}px, ${neckY}px)`}], t0 + i * .12, .5, {easing: OVERSHOOT});
    anim(hop, [{transform: 'scale(1,1)'}, {transform: 'scale(1.012, .988)'}], t0 + .6, 1.2,
         {iterations: Math.max(1, Math.ceil((t1 - t0) / 1.2)), direction: 'alternate', easing: 'ease-in-out'});
  }
  // head life: small nods and tilts
  anim(peep.head, [{transform: 'rotate(-2.5deg)'}, {transform: 'rotate(3deg)'}], t0 + .2, a.talk ? .6 : 1.4,
       {iterations: Math.max(1, Math.ceil((t1 - t0) / (a.talk ? .6 : 1.4))), direction: 'alternate', easing: 'ease-in-out'});
  if (a.react === 'jump') anim(hop, [{transform: 'translateY(0)'}, {transform: 'translateY(-120px)'}, {transform: 'translateY(0)'}], switchAt, .45, {easing: 'ease-out', fill: 'none'});
  if (a.react === 'shake') anim(hop, [{transform: 'translateX(0)'}, {transform: 'translateX(-16px)'}, {transform: 'translateX(16px)'}, {transform: 'translateX(0)'}],
                                switchAt, .12, {iterations: 4, easing: 'linear', fill: 'none'});

  const headTopY = neckY - 449 * k;
  return {x: walking ? x1 : x0, headTopY, pos, scale: k, neckY};
};
