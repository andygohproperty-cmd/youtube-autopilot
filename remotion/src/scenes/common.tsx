import React from "react";
import {AbsoluteFill, Img, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {C, F} from "../theme";
import type {Scene} from "../types";
import {clamp, prog, whenSaid} from "../util";

export type SceneProps = {scene: Scene; index: number};

/** Scene-relative seconds, scene length, and a helper for "when is this word said". */
export const useScene = (scene: Scene) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const dur = scene.end - scene.start;
  const at = (key: string | number | undefined, fallback = 0) =>
    typeof key === "number" ? key : whenSaid(scene.words, scene.start, key, fallback);
  return {t, dur, at, frame, fps};
};

export const src = (p: string) => (/^https?:/.test(p) ? p : staticFile(p));

export const GRADE = "contrast(1.1) saturate(0.82) brightness(0.92)";

/** Dark textured backdrop with a slowly drifting red glow and a faint grid. */
export const Backdrop = ({tint = C.red, grid = true}: {tint?: string; grid?: boolean}) => {
  const frame = useCurrentFrame();
  const x = 50 + Math.sin(frame / 90) * 18;
  const y = 40 + Math.cos(frame / 120) * 12;
  return (
    <AbsoluteFill style={{backgroundColor: C.bg}}>
      <AbsoluteFill
        style={{background: `radial-gradient(circle at ${x}% ${y}%, ${tint}33 0%, ${tint}10 30%, transparent 62%)`}}
      />
      {grid && (
        <AbsoluteFill
          style={{
            backgroundImage: `linear-gradient(${C.line}55 1px, transparent 1px), linear-gradient(90deg, ${C.line}55 1px, transparent 1px)`,
            backgroundSize: "80px 80px",
            backgroundPosition: `${(frame * 0.25) % 80}px 0px`,
            maskImage: "radial-gradient(ellipse at center, black 30%, transparent 80%)",
          }}
        />
      )}
    </AbsoluteFill>
  );
};

/** Background for cards: a blurred, darkened photo or clip, or the plain backdrop. */
export const Bg = ({scene, dim = 0.72}: {scene: Scene; dim?: number}) => {
  const frame = useCurrentFrame();
  const scale = 1.08 + frame * 0.0004;
  if (scene.bgPhoto || scene.bgClip) {
    return (
      <AbsoluteFill style={{backgroundColor: C.bg}}>
        <AbsoluteFill style={{scale, filter: `blur(14px) ${GRADE}`}}>
          {scene.bgPhoto ? (
            <Img src={src(scene.bgPhoto)} style={{width: "100%", height: "100%", objectFit: "cover"}} />
          ) : (
            <OffthreadVideo muted src={src(scene.bgClip)} style={{width: "100%", height: "100%", objectFit: "cover"}} />
          )}
        </AbsoluteFill>
        <AbsoluteFill style={{backgroundColor: `rgba(8,8,10,${dim})`}} />
      </AbsoluteFill>
    );
  }
  return <Backdrop tint={scene.tint === "gold" ? C.gold : C.red} />;
};

/** Small caps tag with a red bar, e.g. "MILAN · 1935". */
export const Tag = ({text, t, at = 0.15, style}: {text: string; t: number; at?: number; style?: React.CSSProperties}) => {
  const p = prog(t, at, 0.5);
  return (
    <div
      style={{
        position: "absolute",
        left: 110,
        top: 96,
        display: "flex",
        alignItems: "center",
        gap: 18,
        opacity: p,
        translate: `${interpolate(p, [0, 1], [-30, 0])}px 0px`,
        ...style,
      }}
    >
      <div style={{width: 10, height: 46, backgroundColor: C.red}} />
      <div
        style={{
          fontFamily: F.sans,
          fontWeight: 800,
          fontSize: 34,
          letterSpacing: 6,
          color: C.ink,
          textTransform: "uppercase",
          textShadow: "0 2px 10px rgba(0,0,0,0.8)",
        }}
      >
        {text}
      </div>
    </div>
  );
};

export const Credit = ({text}: {text?: string}) =>
  text ? (
    <div
      style={{
        position: "absolute",
        right: 28,
        top: 22,
        fontFamily: F.sans,
        fontWeight: 500,
        fontSize: 17,
        color: "rgba(255,255,255,0.5)",
        maxWidth: 700,
        textAlign: "right",
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis",
      }}
    >
      {text}
    </div>
  ) : null;

/** Text with *starred* words in the accent colour. */
export const Marked = ({text, color = C.gold}: {text: string; color?: string}) => (
  <>
    {text.split(/(\*[^*]+\*)/).map((part, i) =>
      part.startsWith("*") ? (
        <span key={i} style={{color}}>
          {part.slice(1, -1)}
        </span>
      ) : (
        <React.Fragment key={i}>{part}</React.Fragment>
      ),
    )}
  </>
);

export const fadeOut = (t: number, dur: number) => interpolate(t, [dur - 0.25, dur], [1, 0.0], clamp);
