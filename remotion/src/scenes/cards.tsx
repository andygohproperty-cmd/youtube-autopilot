import {AbsoluteFill, interpolate, spring} from "remotion";
import {C, F} from "../theme";
import {clamp, prog} from "../util";
import {Backdrop, Bg, Marked, SceneProps, useScene} from "./common";

export const Title = ({scene}: SceneProps) => {
  const {t, dur} = useScene(scene);
  const lines: string[] = scene.lines || [scene.title];
  return (
    <AbsoluteFill>
      <Bg scene={scene} dim={0.8} />
      <AbsoluteFill style={{justifyContent: "center", alignItems: "center", scale: interpolate(t, [0, dur], [1, 1.05])}}>
        <div style={{fontFamily: F.sans, fontWeight: 800, letterSpacing: 10, fontSize: 30, color: C.gold, opacity: prog(t, 0.1)}}>
          {scene.channel}
        </div>
        <div style={{height: 6, width: interpolate(prog(t, 0.2, 0.8), [0, 1], [0, 520]), backgroundColor: C.red, margin: "26px 0 34px"}} />
        {lines.map((l, i) => {
          const p = prog(t, 0.25 + i * 0.18, 0.7);
          return (
            <div
              key={i}
              style={{
                fontFamily: F.display,
                fontSize: 150,
                lineHeight: 1.05,
                color: C.ink,
                textTransform: "uppercase",
                opacity: p,
                translate: `0px ${interpolate(p, [0, 1], [50, 0])}px`,
                textShadow: "0 10px 40px rgba(0,0,0,0.8)",
              }}
            >
              <Marked text={l} />
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Chapter = ({scene}: SceneProps) => {
  const {t, dur} = useScene(scene);
  const p = prog(t, 0, 0.7);
  const out = interpolate(t, [dur - 0.3, dur], [1, 0], clamp);
  return (
    <AbsoluteFill style={{opacity: out}}>
      <Backdrop />
      <AbsoluteFill style={{justifyContent: "center", paddingLeft: 200}}>
        <div
          style={{
            fontFamily: F.display,
            fontSize: 420,
            lineHeight: 0.9,
            color: "transparent",
            WebkitTextStroke: `4px ${C.red}`,
            opacity: p,
            translate: `${interpolate(p, [0, 1], [-80, 0])}px 0px`,
          }}
        >
          {String(scene.number).padStart(2, "0")}
        </div>
        <div style={{height: 8, width: interpolate(prog(t, 0.2, 0.8), [0, 1], [0, 900]), backgroundColor: C.red, margin: "20px 0 30px"}} />
        <div
          style={{
            fontFamily: F.display,
            fontSize: 140,
            textTransform: "uppercase",
            color: C.ink,
            opacity: prog(t, 0.3, 0.6),
            translate: `${interpolate(prog(t, 0.3, 0.8), [0, 1], [60, 0])}px 0px`,
          }}
        >
          {scene.title}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** Kinetic typography: each line lands when its `at` word is spoken. */
export const Text = ({scene}: SceneProps) => {
  const {t, at, fps} = useScene(scene);
  const lines: any[] = (scene.lines || []).map((l: any) => (typeof l === "string" ? {text: l} : l));
  return (
    <AbsoluteFill>
      <Bg scene={scene} />
      <AbsoluteFill style={{justifyContent: "center", alignItems: "center", paddingBottom: 60}}>
        {lines.map((l, i) => {
          const start = i === 0 ? 0 : at(l.at, i * 0.5);   // never open on an empty screen
          const s = spring({frame: Math.round((t - start) * fps), fps, config: {damping: 15, stiffness: 180}});
          return (
            <div
              key={i}
              style={{
                fontFamily: l.serif ? F.serif : F.display,
                fontStyle: l.serif ? "italic" : "normal",
                fontSize: l.size || 170,
                lineHeight: 1.05,
                textTransform: l.serif ? "none" : "uppercase",
                color: l.color === "red" ? C.red : C.ink,
                opacity: t >= start ? 1 : 0,
                scale: interpolate(s, [0, 1], [1.25, 1]),
                textShadow: "0 10px 40px rgba(0,0,0,0.8)",
                textAlign: "center",
                maxWidth: 1600,
              }}
            >
              <Marked text={l.text} color={l.mark === "red" ? C.red : C.gold} />
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** "€26.5 BILLION" -> prefix, number, decimals, suffix */
const parseValue = (v: string) => {
  const m = v.match(/^([^0-9]*)([0-9][0-9,]*\.?[0-9]*)(.*)$/);
  if (!m) return null;
  const num = parseFloat(m[2].replace(/,/g, ""));
  const decimals = (m[2].split(".")[1] || "").length;
  return {pre: m[1], num, decimals, post: m[3], comma: m[2].includes(",")};
};

const fmt = (n: number, decimals: number, comma: boolean) => {
  const s = n.toFixed(decimals);
  return comma ? Number(s).toLocaleString("en-US", {minimumFractionDigits: decimals}) : s;
};

/** Big number that counts up, with a label and a sweeping underline. */
export const Stat = ({scene}: SceneProps) => {
  const {t, at, dur} = useScene(scene);
  const start = at(scene.at, 0.1);
  const early = Math.min(start, 0.6);   // never hold an empty screen waiting for the keyword
  const pv = parseValue(scene.value || "");
  const k = prog(t, early, Math.max(start + 0.9 - early, 0.6));   // counts up, landing as the keyword is said
  const shown = pv ? `${pv.pre}${fmt(pv.num * k, pv.decimals, pv.comma)}${pv.post}` : scene.value;
  const pop = prog(t, early, 0.35);
  return (
    <AbsoluteFill>
      <Bg scene={scene} />
      <AbsoluteFill style={{justifyContent: "center", alignItems: "center", paddingBottom: 80, scale: interpolate(t, [0, dur], [1, 1.04])}}>
        {scene.label && (
          <div style={{fontFamily: F.sans, fontWeight: 800, fontSize: 40, letterSpacing: 8, color: C.muted, textTransform: "uppercase", opacity: prog(t, 0, 0.5), marginBottom: 10}}>
            {scene.label}
          </div>
        )}
        <div
          style={{
            fontFamily: F.display,
            fontSize: scene.size || 250,
            lineHeight: 1,
            color: scene.color === "red" ? C.red : C.gold,
            opacity: pop,
            scale: interpolate(pop, [0, 1], [0.8, 1]),
            textShadow: "0 14px 50px rgba(0,0,0,0.8)",
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {shown}
        </div>
        <div style={{height: 10, width: interpolate(prog(t, start + 0.2, 0.9), [0, 1], [0, 760]), backgroundColor: C.red, marginTop: 18}} />
        {scene.sub && (
          <div style={{fontFamily: F.sans, fontWeight: 700, fontSize: 46, color: C.ink, marginTop: 26, opacity: prog(t, start + 0.5, 0.5)}}>
            {scene.sub}
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** A sourced quote on a paper card, the key phrase swept with a highlighter. */
export const Quote = ({scene}: SceneProps) => {
  const {t, at, dur} = useScene(scene);
  const p = prog(t, 0, 0.6);
  const hl = prog(t, at(scene.hlAt, 1.0), 0.8);
  const parts = (scene.text as string).split(/(\*[^*]+\*)/);
  return (
    <AbsoluteFill>
      <Bg scene={scene} dim={0.82} />
      <AbsoluteFill style={{justifyContent: "center", alignItems: "center", paddingBottom: 90}}>
        <div
          style={{
            width: 1360,
            backgroundColor: "#efe9dc",
            padding: "70px 90px",
            boxShadow: "0 40px 100px rgba(0,0,0,0.7)",
            rotate: "-1deg",
            opacity: p,
            translate: `0px ${interpolate(p, [0, 1], [80, 0])}px`,
            scale: interpolate(t, [0, dur], [1, 1.03]),
          }}
        >
          {scene.kicker && (
            <div style={{fontFamily: F.sans, fontWeight: 900, fontSize: 28, letterSpacing: 6, color: C.red, marginBottom: 24}}>
              {scene.kicker}
            </div>
          )}
          <div style={{fontFamily: F.serif, fontWeight: 700, fontSize: scene.size || 76, lineHeight: 1.25, color: "#1a1a1a"}}>
            {parts.map((part, i) =>
              part.startsWith("*") ? (
                <span
                  key={i}
                  style={{
                    backgroundImage: `linear-gradient(${C.gold}, ${C.gold})`,
                    backgroundRepeat: "no-repeat",
                    backgroundSize: `${hl * 100}% 88%`,
                    backgroundPosition: "0 60%",
                    padding: "0 6px",
                  }}
                >
                  {part.slice(1, -1)}
                </span>
              ) : (
                <span key={i}>{part}</span>
              ),
            )}
          </div>
          {scene.who && (
            <div style={{fontFamily: F.sans, fontWeight: 700, fontSize: 32, color: "#555", marginTop: 36}}>— {scene.who}</div>
          )}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** Two sides facing off. */
export const Versus = ({scene}: SceneProps) => {
  const {t, at, fps} = useScene(scene);
  const side = (s: any, dir: number, start: number) => {
    const k = spring({frame: Math.round((t - start) * fps), fps, config: {damping: 16}});
    return (
      <div
        style={{
          width: 700,
          textAlign: "center",
          opacity: t >= start ? 1 : 0,
          translate: `${interpolate(k, [0, 1], [dir * 300, 0])}px 0px`,
        }}
      >
        <div style={{fontFamily: s.serif ? F.serif : F.display, fontStyle: s.serif ? "italic" : "normal", fontSize: s.name.length > 10 ? 96 : 130, color: s.color === "red" ? C.red : C.ink, whiteSpace: "nowrap", textTransform: s.serif ? "none" : "uppercase"}}>
          {s.name}
        </div>
        <div style={{fontFamily: F.sans, fontWeight: 700, fontSize: 38, color: C.muted, marginTop: 10}}>{s.sub}</div>
      </div>
    );
  };
  const vs = prog(t, at(scene.vsAt, 0.6), 0.4);
  return (
    <AbsoluteFill>
      <Bg scene={scene} />
      <AbsoluteFill style={{flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 60, paddingBottom: 80}}>
        {side(scene.left, -1, 0)}
        <div style={{fontFamily: F.display, fontSize: 110, color: C.gold, opacity: vs, scale: interpolate(vs, [0, 1], [2, 1])}}>{scene.vs || "VS"}</div>
        {side(scene.right, 1, at(scene.right.at, 0.3))}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
