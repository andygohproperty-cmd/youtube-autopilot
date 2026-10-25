import {Easing, interpolate} from "remotion";
import type {Word} from "./types";

export const clamp = {extrapolateLeft: "clamp", extrapolateRight: "clamp"} as const;
export const outExpo = Easing.bezier(0.16, 1, 0.3, 1);
export const inOut = Easing.bezier(0.65, 0, 0.35, 1);

/** 0→1 over `dur` seconds starting at `at` (seconds, scene-relative). */
export const prog = (t: number, at: number, dur = 0.6, ease = outExpo) =>
  interpolate(t, [at, at + dur], [0, 1], {...clamp, easing: ease});

const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9€$%]/g, "");

/** Scene-relative time the narration says `key` (a word or the start of a phrase); `fallback` if never. */
export const whenSaid = (words: Word[], sceneStart: number, key: string | undefined, fallback: number): number => {
  if (!key) return fallback;
  const parts = key.split(/\s+/).map(norm).filter(Boolean);
  for (let i = 0; i < words.length; i++) {
    if (parts.every((p, j) => words[i + j] && norm(words[i + j].text).startsWith(p))) {
      return Math.max(0, words[i].start - sceneStart);
    }
  }
  return fallback;
};

export const seeded = (seed: number) => {
  let s = seed % 2147483647 || 1;
  return () => (s = (s * 16807) % 2147483647) / 2147483647;
};
