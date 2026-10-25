import {geoInterpolate, geoMercator, geoPath} from "d3-geo";
import {feature} from "topojson-client";
import world from "world-atlas/countries-50m.json";
import {AbsoluteFill, interpolate, spring} from "remotion";
import {C, F} from "../theme";
import {inOut, prog} from "../util";
import {SceneProps, Tag, useScene} from "./common";

const countries: any[] = (feature(world as any, (world as any).objects.countries) as any).features;

// Named camera positions: map centre (lon, lat) and Mercator scale at 1920x1080.
const VIEWS: Record<string, {center: [number, number]; scale: number}> = {
  world: {center: [10, 25], scale: 300},
  europe: {center: [10, 49], scale: 1150},
  italy: {center: [11.5, 44.5], scale: 4200},
  north_italy: {center: [10.8, 45.8], scale: 9000},
  usa: {center: [-97, 38.5], scale: 1150},
  atlantic: {center: [-35, 42], scale: 520},
  australia: {center: [134, -27], scale: 900},
  france_italy: {center: [6, 46.5], scale: 2600},
};

const view = (v: any) => (typeof v === "string" ? VIEWS[v] || VIEWS.world : v || VIEWS.world);

export const MapScene = ({scene}: SceneProps) => {
  const {t, at, dur, fps} = useScene(scene);
  const a = view(scene.from || scene.view), b = view(scene.view);
  const k = prog(t, 0, Math.min(2.4, dur * 0.7), inOut);
  const center: [number, number] = [a.center[0] + (b.center[0] - a.center[0]) * k, a.center[1] + (b.center[1] - a.center[1]) * k];
  const scale = Math.exp(Math.log(a.scale) + (Math.log(b.scale) - Math.log(a.scale)) * k) * (1 + t * 0.006);
  const proj = geoMercator().center(center).scale(scale).translate([960, 520]).clipExtent([[-50, -50], [1970, 1130]]);
  const path = geoPath(proj);
  const hl = new Set<string>((scene.highlight || []).map(String));
  const points: any[] = scene.points || [];
  return (
    <AbsoluteFill style={{backgroundColor: "#07080a"}}>
      <svg width={1920} height={1080}>
        <defs>
          <radialGradient id="sea" cx="50%" cy="45%" r="70%">
            <stop offset="0%" stopColor="#11141a" />
            <stop offset="100%" stopColor="#050506" />
          </radialGradient>
        </defs>
        <rect width={1920} height={1080} fill="url(#sea)" />
        {countries.map((c, i) => {
          const d = path(c);
          if (!d) return null;
          const on = hl.has(String(c.id));
          return <path key={i} d={d} fill={on ? `${C.red}cc` : C.land} stroke={on ? C.red : C.landEdge} strokeWidth={on ? 2.5 : 1} />;
        })}
        {scene.route &&
          points.slice(1).map((p, i) => {
            const q = points[i];
            const start = at(p.at ?? p.name?.split(" ")[0], 0.8 + i * 0.8) - 0.2;
            const kk = prog(t, start, 1.0, inOut);
            if (kk <= 0) return null;
            const ip = geoInterpolate([q.lon, q.lat], [p.lon, p.lat]);
            const line = {type: "LineString", coordinates: Array.from({length: 41}, (_, j) => ip((j / 40) * kk))};
            return <path key={`r${i}`} d={path(line as any) || ""} fill="none" stroke={C.gold} strokeWidth={5} strokeDasharray="2 12" strokeLinecap="round" />;
          })}
        {points.map((p, i) => {
          const xy = proj([p.lon, p.lat]);
          if (!xy) return null;
          const start = at(p.at ?? p.name?.split(" ")[0], 0.6 + i * 0.8);
          const s = spring({frame: Math.round((t - start) * fps), fps, config: {damping: 12}});
          const pulse = ((t - start) % 1.4) / 1.4;
          if (t < start) return null;
          return (
            <g key={i} transform={`translate(${xy[0]},${xy[1]})`}>
              <circle r={14 + pulse * 46} fill="none" stroke={C.gold} strokeWidth={3} opacity={1 - pulse} />
              <circle r={14 * s} fill={C.gold} stroke="#000" strokeWidth={3} />
            </g>
          );
        })}
      </svg>
      {points.map((p, i) => {
        const xy = proj([p.lon, p.lat]);
        if (!xy || !p.name) return null;
        const start = at(p.at ?? p.name.split(" ")[0], 0.6 + i * 0.8);
        const s = prog(t, start + 0.1, 0.5);
        const left = p.side === "left";
        return (
          <div
            key={`l${i}`}
            style={{
              position: "absolute",
              left: xy[0] + (left ? -34 : 34),
              top: xy[1] - 34,
              translate: left ? "-100% 0" : "0 0",
              fontFamily: F.sans,
              fontWeight: 900,
              fontSize: 40,
              letterSpacing: 2,
              color: "#111",
              backgroundColor: C.ink,
              padding: "6px 16px",
              textTransform: "uppercase",
              whiteSpace: "nowrap",
              opacity: s,
              scale: interpolate(s, [0, 1], [0.8, 1]),
            }}
          >
            {p.name}
            {p.sub && <span style={{color: C.red, marginLeft: 12}}>{p.sub}</span>}
          </div>
        );
      })}
      {scene.tag && <Tag text={scene.tag} t={t} />}
    </AbsoluteFill>
  );
};
