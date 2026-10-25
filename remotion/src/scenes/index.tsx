import type React from "react";
import type {SceneProps} from "./common";
import {Bars, Brands, Chain, Donut, Empire, Ledger, LineChart, Timeline, Waffle} from "./graphics";
import {Chapter, Quote, Stat, Text, Title, Versus} from "./cards";
import {Clip, Collage, Photo} from "./media";
import {MapScene} from "./map";

const SCENES: Record<string, (p: SceneProps) => React.ReactElement> = {
  photo: Photo,
  clip: Clip,
  collage: Collage,
  title: Title,
  chapter: Chapter,
  text: Text,
  stat: Stat,
  quote: Quote,
  versus: Versus,
  brands: Brands,
  empire: Empire,
  chain: Chain,
  ledger: Ledger,
  bars: Bars,
  waffle: Waffle,
  donut: Donut,
  line: LineChart,
  timeline: Timeline,
  map: MapScene,
};

export const SCENE_TYPES = Object.keys(SCENES);

export const SceneView = ({scene, index}: SceneProps) => {
  const Comp = SCENES[scene.type] || Text;
  return <Comp scene={scene} index={index} />;
};
