/** Robot-specific shot list; the oriented assembly is three scene units high. */
export const chapterIds = [
  "home",
  "companion",
  "intelligence",
  "hardware-explorer",
  "pcb-design",
  "wiring",
  "development",
  "live",
  "about",
] as const;
export interface Shot {
  azimuth: number;
  elevation: number;
  distance: number;
  targetY: number;
  x: number;
  y: number;
  visible: number;
}
const desktop: readonly Shot[] = [
  {
    azimuth: 0.18,
    elevation: 0.08,
    distance: 6.1,
    targetY: 1.5,
    x: 0.29,
    y: -0.02,
    visible: 1,
  },
  {
    azimuth: -0.16,
    elevation: 0.03,
    distance: 4.0,
    targetY: 2.05,
    x: -0.48,
    y: 0,
    visible: 1,
  },
  {
    azimuth: 0.04,
    elevation: 0.015,
    distance: 2.5,
    targetY: 2.36,
    x: 0.48,
    y: 0.04,
    visible: 1,
  },
  {
    azimuth: 1.08,
    elevation: 0.16,
    distance: 6.3,
    targetY: 1.5,
    x: -0.48,
    y: 0,
    visible: 1,
  },
  {
    azimuth: 2.2,
    elevation: 0.18,
    distance: 7,
    targetY: 1.5,
    x: -0.7,
    y: 0,
    visible: 0,
  },
  {
    azimuth: 3.6,
    elevation: 0.1,
    distance: 7,
    targetY: 1.5,
    x: -0.7,
    y: 0,
    visible: 0,
  },
  {
    azimuth: 5.72,
    elevation: 0.1,
    distance: 6.7,
    targetY: 1.5,
    x: 0.5,
    y: -0.08,
    visible: 1,
  },
  {
    azimuth: 6.48,
    elevation: 0.025,
    distance: 4.8,
    targetY: 1.8,
    x: -0.48,
    y: 0,
    visible: 1,
  },
  {
    azimuth: 6.48,
    elevation: 0.025,
    distance: 6.5,
    targetY: 1.5,
    x: -0.65,
    y: 0,
    visible: 0,
  },
];
const mobile: readonly Shot[] = desktop.map((shot, index) => ({
  ...shot,
  distance: index === 2 ? 3.4 : index === 1 ? 5.8 : 10.3,
  targetY: index === 2 ? 2.35 : index === 1 ? 2 : 1.5,
  x: 0,
  y: 0.25,
}));
const smooth = (t: number) => t * t * (3 - 2 * t);
export function resolveShot(
  progress: number,
  compact: boolean,
  reduced: boolean,
  out: Shot,
): Shot {
  const p = Number.isFinite(progress)
    ? Math.max(0, Math.min(chapterIds.length - 1, progress))
    : 0;
  const stops = compact ? mobile : desktop;
  const i = Math.floor(p),
    j = Math.min(i + 1, stops.length - 1);
  const t = reduced ? (p - i < 0.5 ? 0 : 1) : smooth(p - i);
  for (const key of Object.keys(out) as (keyof Shot)[])
    out[key] = stops[i][key] + (stops[j][key] - stops[i][key]) * t;
  if (reduced) {
    out.azimuth = 0.18;
    out.elevation = 0.06;
    out.distance = compact ? 8 : 6.6;
    out.targetY = 1.5;
  }
  return out;
}
export function emptyShot(): Shot {
  return { ...desktop[0] };
}
