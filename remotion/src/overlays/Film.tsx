import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from "remotion";
import {clamp} from "../util";

/** Animated film grain: a quarter-resolution noise tile, re-seeded every other frame. */
export const Grain = () => {
  const frame = useCurrentFrame();
  const seed = Math.floor(frame / 2) % 97;
  return (
    <AbsoluteFill style={{mixBlendMode: "overlay", opacity: 0.32, pointerEvents: "none"}}>
      <svg width="100%" height="100%" viewBox="0 0 480 270" preserveAspectRatio="none">
        <filter id={`g${seed}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="1" seed={seed} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="480" height="270" filter={`url(#g${seed})`} />
      </svg>
    </AbsoluteFill>
  );
};

export const Vignette = () => (
  <AbsoluteFill
    style={{
      background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)",
      pointerEvents: "none",
    }}
  />
);

/** A short white flash on chosen hard cuts (chapter turns, reveals). */
export const CutFlash = ({cuts}: {cuts: number[]}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const near = cuts.find((c) => t >= c && t < c + 0.3);
  if (near === undefined) return null;
  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#fff",
        mixBlendMode: "screen",
        opacity: interpolate(t - near, [0, 0.04, 0.3], [0, 0.55, 0], clamp),
      }}
    />
  );
};
