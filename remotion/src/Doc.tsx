import {AbsoluteFill, Sequence, useVideoConfig} from "remotion";
import {C} from "./theme";
import type {DocProps} from "./types";
import {SceneView} from "./scenes";
import {Captions} from "./overlays/Captions";
import {Grain, Vignette, CutFlash} from "./overlays/Film";

const FADE = 4; // frames each scene overlaps the next, so cuts never show a black frame

export const Doc = (props: DocProps) => {
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{backgroundColor: C.bg}}>
      {props.scenes.map((s, i) => {
        const from = Math.round(s.start * fps);
        const len = Math.max(1, Math.round(s.end * fps) - from) + (i < props.scenes.length - 1 ? FADE : 0);
        return (
          <Sequence key={i} from={from} durationInFrames={len} name={`${i} ${s.type}`}>
            <SceneView scene={s} index={i} />
          </Sequence>
        );
      })}
      <Vignette />
      <Grain />
      <CutFlash cuts={props.cuts} />
      <Captions words={props.words} hookEnd={props.hookEnd} hidden={props.noCaptions} />
    </AbsoluteFill>
  );
};
