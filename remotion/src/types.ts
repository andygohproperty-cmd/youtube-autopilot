export type Word = {text: string; start: number; end: number};   // seconds from the video start

export type Scene = {
  start: number;          // seconds
  end: number;
  type: string;           // see scenes/index.tsx
  words: Word[];          // narration spoken during this scene
  [key: string]: any;     // the scene's own fields (photo, value, items...)
};

export type DocProps = {
  fps: number;
  width: number;
  height: number;
  duration: number;       // seconds
  title: string;
  channel: string;
  hookEnd: number;        // big kinetic captions until here
  noCaptions: [number, number][];   // spans with no captions (title and chapter cards)
  scenes: Scene[];
  words: Word[];
  cuts: number[];         // times of hard cuts that get a flash/whoosh treatment
};
