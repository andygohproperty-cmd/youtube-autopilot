import {Composition} from "remotion";
import {Doc} from "./Doc";
import type {DocProps} from "./types";

const demo: DocProps = {
  fps: 30, width: 1920, height: 1080, duration: 6, title: "Demo", channel: "HOW IT MAKES MONEY",
  hookEnd: 6, noCaptions: [], cuts: [], words: [],
  scenes: [{start: 0, end: 6, type: "text", lines: ["IT ISN'T."], words: []}],
};

// Props come from the Python pipeline: `remotion render src/index.ts Doc out.mp4 --props=props.json`.
export const Root = () => (
  <Composition
    id="Doc"
    component={Doc}
    defaultProps={demo}
    fps={30}
    width={1920}
    height={1080}
    durationInFrames={180}
    calculateMetadata={({props}) => ({
      fps: props.fps,
      width: props.width,
      height: props.height,
      durationInFrames: Math.max(1, Math.round(props.duration * props.fps)),
    })}
  />
);
