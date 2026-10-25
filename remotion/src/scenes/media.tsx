import {AbsoluteFill, Img, OffthreadVideo, interpolate, spring} from "remotion";
import {C, F} from "../theme";
import {clamp, inOut, prog, seeded} from "../util";
import {Bg, Credit, GRADE, SceneProps, Tag, src, useScene} from "./common";

// [scale from, scale to, x from, y from, x to, y to] (x/y in % of the frame)
const MOVES: Record<string, number[]> = {
  in: [1.04, 1.16, 0, 0, 0, 0],
  out: [1.18, 1.05, 0, 0, 0, 0],
  left: [1.14, 1.14, 3, 0, -3, 0],
  right: [1.14, 1.14, -3, 0, 3, 0],
  up: [1.14, 1.14, 0, 3, 0, -3],
};

/** A real photo: full-frame Ken Burns, or framed on a blurred copy of itself when it isn't wide. */
export const Photo = ({scene, index}: SceneProps) => {
  const {t, dur, fps, frame} = useScene(scene);
  const move = scene.move || ["in", "right", "out", "left"][index % 4];
  const [s0, s1, x0, y0, x1, y1] = MOVES[move] || MOVES.in;
  const k = interpolate(t, [0, dur], [0, 1], {...clamp, easing: inOut});
  const wide = (scene.pw || 16) / (scene.ph || 9) >= 1.45;
  const framed = scene.frame ?? !wide;
  const img = src(scene.photo);
  const focus = scene.focus || "50% 50%";

  if (!framed) {
    return (
      <AbsoluteFill style={{backgroundColor: C.bg, overflow: "hidden"}}>
        <AbsoluteFill
          style={{
            scale: interpolate(k, [0, 1], [s0, s1]),
            translate: `${x0 + (x1 - x0) * k}% ${y0 + (y1 - y0) * k}%`,
            filter: GRADE,
          }}
        >
          <Img src={img} style={{width: "100%", height: "100%", objectFit: "cover", objectPosition: focus}} />
        </AbsoluteFill>
        <AbsoluteFill style={{background: "linear-gradient(180deg, rgba(0,0,0,0.35) 0%, transparent 25%, transparent 60%, rgba(0,0,0,0.6) 100%)"}} />
        {scene.tag && <Tag text={scene.tag} t={t} />}
        <Credit text={scene.credit} />
      </AbsoluteFill>
    );
  }

  const enter = spring({frame, fps, config: {damping: 18, stiffness: 120}});
  const rot = scene.rot ?? (index % 2 ? 1.4 : -1.2);
  const ar = (scene.pw || 4) / (scene.ph || 3);
  const h = ar < 1 ? 820 : Math.min(780, 1500 / ar);
  return (
    <AbsoluteFill style={{backgroundColor: C.bg, overflow: "hidden"}}>
      <AbsoluteFill style={{scale: 1.15 + k * 0.05, filter: `blur(22px) ${GRADE} brightness(0.5)`}}>
        <Img src={img} style={{width: "100%", height: "100%", objectFit: "cover"}} />
      </AbsoluteFill>
      <AbsoluteFill style={{justifyContent: "center", alignItems: "center"}}>
        <div
          style={{
            height: h,
            aspectRatio: `${ar}`,
            border: "12px solid #f1ede4",
            boxShadow: "0 40px 90px rgba(0,0,0,0.7)",
            overflow: "hidden",
            rotate: `${interpolate(enter, [0, 1], [rot * 3, rot])}deg`,
            translate: `0px ${interpolate(enter, [0, 1], [120, -20])}px`,
            opacity: interpolate(enter, [0, 0.3], [0, 1], clamp),
          }}
        >
          <Img src={img} style={{width: "100%", height: "100%", objectFit: "cover", scale: 1 + k * 0.08, filter: GRADE, objectPosition: focus}} />
        </div>
      </AbsoluteFill>
      {scene.tag && <Tag text={scene.tag} t={t} />}
      <Credit text={scene.credit} />
    </AbsoluteFill>
  );
};

/** Stock footage, graded to the channel look, with a slow push in. */
export const Clip = ({scene}: SceneProps) => {
  const {t, dur} = useScene(scene);
  if (!scene.clip) return <Bg scene={scene} />;
  return (
    <AbsoluteFill style={{backgroundColor: C.bg, overflow: "hidden"}}>
      <AbsoluteFill style={{scale: interpolate(t, [0, dur], [1.03, 1.1]), filter: `${GRADE} ${scene.bw ? "grayscale(1)" : ""}`}}>
        <OffthreadVideo muted src={src(scene.clip)} style={{width: "100%", height: "100%", objectFit: "cover"}} />
      </AbsoluteFill>
      <AbsoluteFill style={{background: "linear-gradient(180deg, transparent 55%, rgba(0,0,0,0.55) 100%)"}} />
      {scene.tag && <Tag text={scene.tag} t={t} />}
    </AbsoluteFill>
  );
};

/** Hook collage: photos pinned one by one onto a red grid board as they are mentioned. */
export const Collage = ({scene, index}: SceneProps) => {
  const {t, at, fps} = useScene(scene);
  const items: any[] = scene.items || [];
  const rnd = seeded(index * 31 + 7);
  const slots = [
    [-470, -170], [430, -190], [-430, 230], [460, 220], [0, 10], [-20, -260],
  ];
  return (
    <AbsoluteFill style={{overflow: "hidden"}}>
      <AbsoluteFill style={{backgroundColor: "#2a0b0a"}} />
      <AbsoluteFill
        style={{
          backgroundImage: "linear-gradient(rgba(255,80,60,0.18) 2px, transparent 2px), linear-gradient(90deg, rgba(255,80,60,0.18) 2px, transparent 2px)",
          backgroundSize: "96px 96px",
          scale: 1 + t * 0.01,
        }}
      />
      <AbsoluteFill style={{background: "radial-gradient(ellipse at center, transparent 30%, rgba(0,0,0,0.75) 100%)"}} />
      {items.map((it, i) => {
        const start = at(it.at, i * 0.6);
        const s = spring({frame: Math.round((t - start) * fps), fps, config: {damping: 14, stiffness: 160}});
        const [x, y] = it.pos || slots[i % slots.length];
        const rot = it.rot ?? (rnd() - 0.5) * 12;
        const ar = (it.pw || 4) / (it.ph || 3);
        const h = it.h || 400;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: 960 + x - (h * ar) / 2,
              top: 540 + y - h / 2,
              height: h,
              width: h * ar,
              border: "10px solid #f1ede4",
              boxShadow: "0 30px 60px rgba(0,0,0,0.6)",
              overflow: "hidden",
              opacity: t >= start ? 1 : 0,
              scale: interpolate(s, [0, 1], [1.6, 1]),
              rotate: `${interpolate(s, [0, 1], [rot * 2.5, rot])}deg`,
              backgroundColor: "#111",
            }}
          >
            {it.photo ? (
              <Img src={src(it.photo)} style={{width: "100%", height: "100%", objectFit: "cover", filter: GRADE}} />
            ) : (
              <div style={{display: "flex", width: "100%", height: "100%", alignItems: "center", justifyContent: "center", fontFamily: F.display, fontSize: h / 4, color: C.ink}}>
                {it.label}
              </div>
            )}
            {it.label && it.photo && (
              <div style={{position: "absolute", left: 0, bottom: 0, backgroundColor: C.red, color: "#fff", fontFamily: F.sans, fontWeight: 900, fontSize: 30, padding: "6px 16px", letterSpacing: 2}}>
                {it.label}
              </div>
            )}
          </div>
        );
      })}
      {scene.stamp && (() => {
        const s = spring({frame: Math.round((t - at(scene.stamp.at, 1)) * fps), fps, config: {damping: 10, stiffness: 200}});
        return (
          <AbsoluteFill style={{justifyContent: "center", alignItems: "center"}}>
            <div
              style={{
                fontFamily: F.display,
                fontSize: 170,
                color: "#fff",
                backgroundColor: C.red,
                padding: "10px 50px",
                rotate: "-4deg",
                opacity: s > 0.01 ? 1 : 0,
                scale: interpolate(s, [0, 1], [2.2, 1]),
                boxShadow: "0 30px 80px rgba(0,0,0,0.7)",
              }}
            >
              {scene.stamp.text}
            </div>
          </AbsoluteFill>
        );
      })()}
    </AbsoluteFill>
  );
};
