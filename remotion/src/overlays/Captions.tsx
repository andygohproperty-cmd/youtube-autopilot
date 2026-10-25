import {useMemo} from "react";
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {C, F} from "../theme";
import type {Word} from "../types";
import {clamp} from "../util";

type Page = {words: Word[]; start: number; end: number; hook: boolean};

/** Group words into short caption pages: break on pauses, sentence ends, or a word limit. */
const paginate = (words: Word[], hookEnd: number): Page[] => {
  const pages: Page[] = [];
  let cur: Word[] = [];
  const flush = () => {
    if (!cur.length) return;
    const hook = cur[0].start < hookEnd;
    pages.push({words: cur, start: cur[0].start, end: cur[cur.length - 1].end, hook});
    cur = [];
  };
  words.forEach((w, i) => {
    const hook = w.start < hookEnd;
    if (cur.length && (cur[0].start < hookEnd) !== hook) flush();
    cur.push(w);
    const next = words[i + 1];
    const max = hook ? 3 : 5;
    const len = cur.reduce((n, x) => n + x.text.length + 1, 0);
    if (!next || next.start - w.end > 0.35 || /[.!?]$/.test(w.text) || cur.length >= max || len > 30) flush();
  });
  // hold each page until the next one starts (no flicker in short gaps)
  pages.forEach((p, i) => {
    const next = pages[i + 1];
    p.end = next ? Math.min(next.start, p.end + 0.6) : p.end + 0.6;
  });
  return pages;
};

export const Captions = ({words, hookEnd, hidden}: {words: Word[]; hookEnd: number; hidden: [number, number][]}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const pages = useMemo(() => paginate(words, hookEnd), [words, hookEnd]);
  if (hidden.some(([a, b]) => t >= a && t < b)) return null;
  const page = pages.find((p) => t >= p.start && t < p.end);
  if (!page) return null;
  const local = frame - Math.round(page.start * fps);

  if (page.hook) {
    // Hook: big kinetic words that punch in as they are spoken
    return (
      <AbsoluteFill style={{justifyContent: "flex-end", alignItems: "center", paddingBottom: 150}}>
        <div style={{display: "flex", gap: "0px 34px", flexWrap: "wrap", justifyContent: "center", maxWidth: 1500}}>
          {page.words.map((w, i) => {
            const at = Math.round((w.start - page.start) * fps);
            const s = spring({frame: local - at, fps, config: {damping: 13, stiffness: 220, mass: 0.6}});
            const active = t >= w.start && t < w.end + 0.05;
            return (
              <span
                key={i}
                style={{
                  fontFamily: F.display,
                  fontSize: 132,
                  lineHeight: 1,
                  textTransform: "uppercase",
                  color: active ? C.gold : C.ink,
                  opacity: local >= at ? 1 : 0,
                  scale: interpolate(s, [0, 1], [1.18, 1]),
                  translate: `0px ${interpolate(s, [0, 1], [30, 0])}px`,
                  textShadow: "0 6px 0 rgba(0,0,0,0.85), 0 0 40px rgba(0,0,0,0.6)",
                  WebkitTextStroke: "3px rgba(0,0,0,0.9)",
                  paintOrder: "stroke fill",
                }}
              >
                {w.text}
              </span>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  const enter = interpolate(local, [0, 5], [0, 1], clamp);
  return (
    <AbsoluteFill style={{justifyContent: "flex-end", alignItems: "center", paddingBottom: 74}}>
      <div
        style={{
          display: "flex",
          gap: 14,
          padding: "10px 22px",
          opacity: enter,
          translate: `0px ${interpolate(enter, [0, 1], [12, 0])}px`,
        }}
      >
        {page.words.map((w, i) => {
          const active = t >= w.start && t < w.end + 0.05;
          const said = t >= w.start;
          return (
            <span
              key={i}
              style={{
                fontFamily: F.sans,
                fontWeight: 900,
                fontSize: 58,
                letterSpacing: -0.5,
                color: active ? "#111" : C.ink,
                backgroundColor: active ? C.gold : "transparent",
                borderRadius: 8,
                padding: "0 10px",
                opacity: said ? 1 : 0.55,
                textShadow: active ? "none" : "0 3px 12px rgba(0,0,0,0.9), 0 2px 0 rgba(0,0,0,0.9)",
              }}
            >
              {w.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
