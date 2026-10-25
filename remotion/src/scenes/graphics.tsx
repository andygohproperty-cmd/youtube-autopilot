import {AbsoluteFill, interpolate, spring} from "remotion";
import {C, F} from "../theme";
import {clamp, inOut, outExpo, prog} from "../util";
import {Bg, SceneProps, Tag, useScene} from "./common";

const FONTS = [F.serif, F.display, F.sans, F.serif, F.display, F.sans];

/** Brand names as tiles, each landing when it's said; optional `converge` pulls them all into one owner. */
export const Brands = ({scene}: SceneProps) => {
  const {t, at, fps} = useScene(scene);
  const items: any[] = scene.items.map((i: any) => (typeof i === "string" ? {name: i} : i));
  const cols = scene.cols || Math.min(4, items.length);
  const rows = Math.ceil(items.length / cols);
  const cw = 380, ch = 170, gap = 34;
  const conv = scene.converge ? prog(t, at(scene.converge.at, 99), 0.9, inOut) : 0;
  const owner = scene.converge ? spring({frame: Math.round((t - at(scene.converge.at, 99) - 0.6) * fps), fps, config: {damping: 12}}) : 0;
  return (
    <AbsoluteFill>
      <Bg scene={scene} />
      {scene.tag && <Tag text={scene.tag} t={t} />}
      {items.map((it, i) => {
        const r = Math.floor(i / cols), c = i % cols;
        const inRow = r === rows - 1 ? items.length - r * cols : cols;
        const x = 960 + (c - (inRow - 1) / 2) * (cw + gap);
        const y = 500 + (r - (rows - 1) / 2) * (ch + gap);
        const start = at(it.at ?? it.name.split(" ")[0], i * 0.35);
        const s = spring({frame: Math.round((t - start) * fps), fps, config: {damping: 14, stiffness: 170}});
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: interpolate(conv, [0, 1], [x, 960]) - cw / 2,
              top: interpolate(conv, [0, 1], [y, 500]) - ch / 2,
              width: cw,
              height: ch,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: C.panel,
              border: `2px solid ${C.line}`,
              boxShadow: "0 20px 50px rgba(0,0,0,0.5)",
              opacity: (t >= start ? 1 : 0) * interpolate(conv, [0.6, 1], [1, 0], clamp),
              scale: interpolate(s, [0, 1], [0.6, 1]) * interpolate(conv, [0, 1], [1, 0.4]),
              rotate: `${conv * (i % 2 ? 8 : -8)}deg`,
            }}
          >
            <div
              style={{
                fontFamily: it.font === "serif" ? F.serif : it.font === "sans" ? F.sans : FONTS[i % FONTS.length],
                fontWeight: 800,
                fontStyle: FONTS[i % FONTS.length] === F.serif ? "italic" : "normal",
                fontSize: it.name.length > 10 ? 48 : 64,
                letterSpacing: FONTS[i % FONTS.length] === F.sans ? 4 : 1,
                color: C.ink,
                textTransform: FONTS[i % FONTS.length] === F.serif ? "none" : "uppercase",
                textAlign: "center",
              }}
            >
              {it.name}
            </div>
          </div>
        );
      })}
      {scene.converge && (
        <AbsoluteFill style={{justifyContent: "center", alignItems: "center", paddingBottom: 80}}>
          <div
            style={{
              fontFamily: F.display,
              fontSize: 150,
              color: "#fff",
              backgroundColor: C.red,
              padding: "14px 60px",
              opacity: owner > 0.02 ? 1 : 0,
              scale: interpolate(owner, [0, 1], [0.3, 1]),
              boxShadow: `0 0 120px ${C.red}88`,
            }}
          >
            {scene.converge.text}
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

/** Hub and spokes: the owner in the middle, what it owns around it, lines drawing out as each is named. */
export const Empire = ({scene}: SceneProps) => {
  const {t, at, fps, dur} = useScene(scene);
  const nodes: any[] = scene.nodes.map((n: any) => (typeof n === "string" ? {label: n} : n));
  const R = scene.radius || 360;
  const CY = scene.cy || 500;
  const RX = scene.rx || R * 1.45;
  const hub = spring({frame: Math.round(t * fps), fps, config: {damping: 14}});
  return (
    <AbsoluteFill>
      <Bg scene={scene} />
      <AbsoluteFill style={{scale: interpolate(t, [0, dur], [1, 1.06])}}>
        <svg width={1920} height={1080} style={{position: "absolute"}}>
          {nodes.map((n, i) => {
            const a = -Math.PI / 2 + (i / nodes.length) * Math.PI * 2;
            const x = 960 + Math.cos(a) * RX, y = CY + Math.sin(a) * R;
            const k = prog(t, at(n.at ?? n.label.split(" ")[0], 0.4 + i * 0.4), 0.6);
            return <line key={i} x1={960} y1={CY} x2={960 + (x - 960) * k} y2={CY + (y - CY) * k} stroke={C.red} strokeWidth={4} strokeDasharray="14 10" opacity={0.8} />;
          })}
        </svg>
        {nodes.map((n, i) => {
          const a = -Math.PI / 2 + (i / nodes.length) * Math.PI * 2;
          const x = 960 + Math.cos(a) * RX, y = CY + Math.sin(a) * R;
          const start = at(n.at ?? n.label.split(" ")[0], 0.4 + i * 0.4) + 0.3;
          const s = spring({frame: Math.round((t - start) * fps), fps, config: {damping: 13}});
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: x,
                top: y,
                translate: "-50% -50%",
                padding: "18px 34px",
                backgroundColor: C.panel,
                border: `3px solid ${C.red}`,
                fontFamily: F.sans,
                fontWeight: 900,
                fontSize: 44,
                letterSpacing: 2,
                color: C.ink,
                textTransform: "uppercase",
                whiteSpace: "nowrap",
                opacity: t >= start ? 1 : 0,
                scale: interpolate(s, [0, 1], [0.4, 1]),
              }}
            >
              {n.label}
              {n.sub && <div style={{fontWeight: 600, fontSize: 28, color: C.muted, letterSpacing: 0, textTransform: "none"}}>{n.sub}</div>}
            </div>
          );
        })}
        <div
          style={{
            position: "absolute",
            left: 960,
            top: CY,
            translate: "-50% -50%",
            padding: "26px 46px",
            backgroundColor: C.red,
            fontFamily: F.display,
            fontSize: 84,
            color: "#fff",
            whiteSpace: "nowrap",
            scale: interpolate(hub, [0, 1], [0.5, 1]),
            boxShadow: `0 0 100px ${C.red}77`,
          }}
        >
          {scene.center}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** The supply chain as steps; steps light up as "owned" (the video's recurring motif). */
export const Chain = ({scene}: SceneProps) => {
  const {t, at, fps} = useScene(scene);
  const steps: any[] = scene.steps.map((s: any) => (typeof s === "string" ? {label: s} : s));
  const w = Math.min(300, (1760 - (steps.length - 1) * 82) / steps.length);   // 82 = gaps + arrow
  return (
    <AbsoluteFill>
      <Bg scene={scene} />
      {scene.tag && <Tag text={scene.tag} t={t} />}
      <AbsoluteFill style={{flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 30, paddingBottom: 80}}>
        {steps.map((s, i) => {
          const owned = s.owned === true ? -1 : s.owned;
          const on = owned === undefined || owned === false ? 0 : prog(t, owned === -1 ? 0 : at(owned, 0.5 + i * 0.4), 0.4);
          const appear = spring({frame: Math.round((t - i * 0.12) * fps), fps, config: {damping: 16}});
          const stamp = spring({frame: Math.round((t - (owned === -1 ? -1 : at(owned, 0.5 + i * 0.4))) * fps), fps, config: {damping: 9, stiffness: 220}});
          return (
            <div key={i} style={{display: "flex", alignItems: "center", gap: 30}}>
              <div
                style={{
                  width: w,
                  height: 220,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  backgroundColor: on > 0.5 ? C.red : C.panel,
                  border: `3px solid ${on > 0.5 ? C.red : C.line}`,
                  boxShadow: on > 0.5 ? `0 0 60px ${C.red}66` : "none",
                  opacity: appear,
                  translate: `0px ${interpolate(appear, [0, 1], [60, 0])}px`,
                  position: "relative",
                }}
              >
                <div style={{fontFamily: F.sans, fontWeight: 900, fontSize: w < 200 ? 24 : w < 240 ? 30 : 38, color: C.ink, textTransform: "uppercase", letterSpacing: 2, textAlign: "center", padding: "0 10px"}}>
                  {s.label}
                </div>
                {on > 0 && owned !== undefined && owned !== false && (
                  <div
                    style={{
                      position: "absolute",
                      bottom: -26,
                      backgroundColor: "#fff",
                      color: C.red,
                      fontFamily: F.sans,
                      fontWeight: 900,
                      fontSize: 24,
                      letterSpacing: 4,
                      padding: "6px 14px",
                      scale: interpolate(stamp, [0, 1], [2, 1]),
                      opacity: stamp > 0.02 ? 1 : 0,
                    }}
                  >
                    {s.stamp || scene.ownedText || "OWNED"}
                  </div>
                )}
              </div>
              {i < steps.length - 1 && <div style={{width: 0, height: 0, borderTop: "16px solid transparent", borderBottom: "16px solid transparent", borderLeft: `22px solid ${C.muted}`, opacity: appear}} />}
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** An acquisition ledger: rows (year, name, price) stamping in as each deal is named. */
export const Ledger = ({scene}: SceneProps) => {
  const {t, at, fps} = useScene(scene);
  const rows: any[] = scene.rows;
  return (
    <AbsoluteFill>
      <Bg scene={scene} />
      <AbsoluteFill style={{justifyContent: "center", alignItems: "center", paddingBottom: 110}}>
        <div style={{width: 1300}}>
          <div style={{fontFamily: F.sans, fontWeight: 900, fontSize: 32, letterSpacing: 8, color: C.gold, marginBottom: 20, opacity: prog(t, 0)}}>
            {scene.title || "THE SHOPPING LIST"}
          </div>
          {rows.map((r, i) => {
            const start = at(r.at ?? r.name.split(" ")[0], i * 0.6);
            const s = spring({frame: Math.round((t - start) * fps), fps, config: {damping: 15, stiffness: 200}});
            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  borderBottom: `2px solid ${C.line}`,
                  padding: "18px 0",
                  opacity: t >= start ? 1 : 0.0,
                  translate: `${interpolate(s, [0, 1], [-60, 0])}px 0px`,
                }}
              >
                <div style={{fontFamily: F.display, fontSize: 64, color: C.red, width: 200}}>{r.year}</div>
                <div style={{fontFamily: F.display, fontSize: 80, color: C.ink, flex: 1, textTransform: "uppercase"}}>{r.name}</div>
                <div style={{fontFamily: F.display, fontSize: 72, color: C.gold}}>{r.price}</div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** Horizontal bars growing to their values. */
export const Bars = ({scene}: SceneProps) => {
  const {t, at} = useScene(scene);
  const items: any[] = scene.items;
  const max = scene.max || Math.max(...items.map((i) => i.value));
  return (
    <AbsoluteFill>
      <Bg scene={scene} />
      <AbsoluteFill style={{justifyContent: "center", alignItems: "center", paddingBottom: 110}}>
        <div style={{width: 1400}}>
          {scene.title && <div style={{fontFamily: F.sans, fontWeight: 900, fontSize: 36, letterSpacing: 6, color: C.gold, marginBottom: 34, opacity: prog(t, 0)}}>{scene.title}</div>}
          {items.map((it, i) => {
            const k = prog(t, at(it.at ?? it.label.split(" ")[0], 0.3 + i * 0.5), 1.0);
            return (
              <div key={i} style={{display: "flex", alignItems: "center", margin: "22px 0", opacity: interpolate(k, [0, 0.1], [0, 1], clamp)}}>
                <div style={{width: 360, fontFamily: F.sans, fontWeight: 800, fontSize: 40, color: C.ink, textTransform: "uppercase"}}>{it.label}</div>
                <div style={{flex: 1, height: 84, backgroundColor: "#ffffff10", position: "relative"}}>
                  <div style={{height: "100%", width: `${(it.value / max) * 100 * k}%`, backgroundColor: it.color === "muted" ? C.muted : it.color === "gold" ? C.gold : C.red}} />
                </div>
                <div style={{width: 200, textAlign: "right", fontFamily: F.display, fontSize: 76, color: C.ink}}>
                  {it.prefix || ""}{(it.value * k).toFixed(it.decimals || 0)}{scene.unit || ""}
                </div>
              </div>
            );
          })}
          {scene.note && <div style={{fontFamily: F.sans, fontWeight: 500, fontSize: 26, color: C.muted, marginTop: 20}}>{scene.note}</div>}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** A 10x10 grid of squares: `from` lit at the start, filling to `to` when `at` is said. */
export const Waffle = ({scene}: SceneProps) => {
  const {t, at} = useScene(scene);
  const k = prog(t, at(scene.at, 1.2), 1.4, inOut);
  const lit = Math.round(scene.from + (scene.to - scene.from) * k);
  const size = 62, gap = 10;
  return (
    <AbsoluteFill>
      <Bg scene={scene} />
      <AbsoluteFill style={{flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 120, paddingBottom: 90}}>
        <div style={{display: "grid", gridTemplateColumns: `repeat(10, ${size}px)`, gap}}>
          {Array.from({length: 100}).map((_, i) => {
            const on = i < lit;
            const appear = prog(t, i * 0.004, 0.3);
            return <div key={i} style={{width: size, height: size, backgroundColor: on ? C.red : "#ffffff14", opacity: appear, boxShadow: on ? `0 0 18px ${C.red}66` : "none"}} />;
          })}
        </div>
        <div>
          <div style={{fontFamily: F.sans, fontWeight: 800, fontSize: 40, letterSpacing: 4, color: C.muted, textTransform: "uppercase", whiteSpace: "pre-line"}}>{scene.label}</div>
          <div style={{fontFamily: F.display, fontSize: 280, lineHeight: 1, color: C.gold}}>{lit}%</div>
          <div style={{fontFamily: F.sans, fontWeight: 800, fontSize: 50, color: C.ink}}>{k < 0.5 ? scene.fromLabel : scene.toLabel}</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** One share of a whole, as a ring. */
export const Donut = ({scene}: SceneProps) => {
  const {t, at} = useScene(scene);
  const k = prog(t, at(scene.at, 0.3), 1.2);
  const r = 260, c = 2 * Math.PI * r;
  return (
    <AbsoluteFill>
      <Bg scene={scene} />
      <AbsoluteFill style={{flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 110, paddingBottom: 90}}>
        <svg width={640} height={640} viewBox="0 0 640 640">
          <circle cx={320} cy={320} r={r} fill="none" stroke="#ffffff16" strokeWidth={70} />
          <circle cx={320} cy={320} r={r} fill="none" stroke={C.red} strokeWidth={70} strokeDasharray={`${(c * scene.value * k) / 100} ${c}`} transform="rotate(-90 320 320)" />
          <text x={320} y={355} textAnchor="middle" fontFamily="Anton" fontSize={130} fill={C.ink}>
            {scene.approx ? "~" : ""}{Math.round(scene.value * k)}%
          </text>
        </svg>
        <div style={{maxWidth: 700}}>
          <div style={{fontFamily: F.display, fontSize: 110, lineHeight: 1.05, color: C.ink, textTransform: "uppercase", opacity: prog(t, 0.3)}}>{scene.title}</div>
          {scene.sub && <div style={{fontFamily: F.sans, fontWeight: 700, fontSize: 42, color: C.muted, marginTop: 20, opacity: prog(t, 0.6)}}>{scene.sub}</div>}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** A stock-style line chart that draws itself: "down" crashes, "up" climbs. */
export const LineChart = ({scene}: SceneProps) => {
  const {t, at} = useScene(scene);
  const pts: number[] = scene.points || (scene.direction === "down" ? [62, 64, 61, 66, 65, 67, 64, 40, 34, 36, 31] : [10, 14, 12, 20, 24, 22, 33, 41, 46, 58, 70]);
  const k = prog(t, at(scene.at, 0.2), scene.direction === "down" ? 2.2 : 2.6, outExpo);
  const W = 1400, H = 560;
  const max = Math.max(...pts) * 1.15;
  const xy = pts.map((v, i) => [(i / (pts.length - 1)) * W, H - (v / max) * H]);
  const n = k * (pts.length - 1);
  const shown = xy.slice(0, Math.floor(n) + 1);
  const i0 = Math.floor(n), f = n - i0;
  if (i0 < pts.length - 1) shown.push([xy[i0][0] + (xy[i0 + 1][0] - xy[i0][0]) * f, xy[i0][1] + (xy[i0 + 1][1] - xy[i0][1]) * f]);
  const d = shown.map((p, i) => `${i ? "L" : "M"}${p[0]},${p[1]}`).join(" ");
  const last = shown[shown.length - 1];
  const color = scene.direction === "down" ? C.red : "#3ddc84";
  return (
    <AbsoluteFill>
      <Bg scene={scene} />
      {scene.tag && <Tag text={scene.tag} t={t} />}
      <AbsoluteFill style={{justifyContent: "center", alignItems: "center", paddingBottom: 90}}>
        <svg width={W + 40} height={H + 40} viewBox={`-20 -20 ${W + 40} ${H + 40}`}>
          {[0, 1, 2, 3, 4].map((g) => (
            <line key={g} x1={0} x2={W} y1={(g / 4) * H} y2={(g / 4) * H} stroke="#ffffff14" strokeWidth={2} />
          ))}
          <path d={`${d} L${last[0]},${H} L0,${H} Z`} fill={color} opacity={0.12} />
          <path d={d} fill="none" stroke={color} strokeWidth={8} strokeLinejoin="round" strokeLinecap="round" />
          <circle cx={last[0]} cy={last[1]} r={16} fill={color} />
        </svg>
        {scene.label && (
          <div style={{position: "absolute", right: 170, top: 170, fontFamily: F.display, fontSize: 100, color, opacity: prog(t, at(scene.at, 0.2) + 1.2)}}>
            {scene.label}
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** A year ruler sliding from one year to another, with the year counting. */
export const Timeline = ({scene}: SceneProps) => {
  const {t, at, dur} = useScene(scene);
  const from: number = scene.from, to: number = scene.to ?? scene.from;
  const k = prog(t, at(scene.at, 0.2), Math.min(2.2, Math.max(0.8, dur - 1)), inOut);
  const year = Math.round(from + (to - from) * k);
  const span = 1 / 34; // px per year inverse: 34 px per year
  const offset = (from + (to - from) * k) * 34;
  const ticks: number[] = [];
  for (let y = Math.min(from, to) - 30; y <= Math.max(from, to) + 30; y++) ticks.push(y);
  return (
    <AbsoluteFill>
      <Bg scene={scene} />
      <AbsoluteFill style={{justifyContent: "center", alignItems: "center", paddingBottom: 120}}>
        <div style={{fontFamily: F.display, fontSize: 300, lineHeight: 1, color: C.ink, fontVariantNumeric: "tabular-nums", textShadow: "0 14px 50px rgba(0,0,0,0.8)"}}>{year}</div>
        {scene.label && <div style={{fontFamily: F.sans, fontWeight: 800, fontSize: 46, letterSpacing: 6, color: C.gold, textTransform: "uppercase", marginTop: 6, opacity: prog(t, 0.3)}}>{scene.label}</div>}
      </AbsoluteFill>
      <div style={{position: "absolute", left: 0, right: 0, top: 800, height: 90, overflow: "hidden", opacity: 0.9 + span * 0}}>
        {ticks.map((y) => (
          <div key={y} style={{position: "absolute", left: 960 + y * 34 - offset, top: 0, width: 3, height: y % 10 === 0 ? 70 : y % 5 === 0 ? 44 : 24, backgroundColor: y === year ? C.red : "#ffffff40"}}>
            {y % 10 === 0 && <div style={{position: "absolute", top: 72, left: -40, width: 80, textAlign: "center", fontFamily: F.sans, fontWeight: 700, fontSize: 22, color: C.muted}}>{y}</div>}
          </div>
        ))}
        <div style={{position: "absolute", left: 957, top: 0, width: 6, height: 90, backgroundColor: C.red}} />
      </div>
    </AbsoluteFill>
  );
};
