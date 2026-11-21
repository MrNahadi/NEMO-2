import { useEffect, useRef } from "react";
import type { EngEvent } from "../types";

function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || "#888";
}

const MONO = "'Geist Mono Variable', 'Geist Mono', ui-monospace, monospace";
const SANS = "'Geist Sans Variable', 'Geist Sans', system-ui, sans-serif";
const tickFont = `12px ${MONO}`;
const strongFont = `600 12px ${MONO}`;
const axisFont = `12px ${SANS}`;

const fmt = (v: number, d = 1) => v.toLocaleString(undefined, { maximumFractionDigits: d, minimumFractionDigits: d });

/** Every design the optimizer tried: plate mass against the highest check use. The engineering limit
 *  (100%) is always drawn and labelled in gray-1000; the search target (70% / 85%), when the engine searched to
 *  one, is a labelled gray dashed line. Red dots are real limit exceedances only (use over 100%), faint
 *  4 px dots, so red stays rare and meaningful. */
export function DesignSpaceChart({
  points,
  limit = 1,
  target,
  chosen,
  height = 320,
}: {
  points: [number, number, boolean][];
  /** The engineering limit as a ratio (1 = 100%). Always drawn and labelled. */
  limit?: number;
  /** The search target (0.7 / 0.85) when the engine searched to one: a labelled gray dashed line. */
  target?: number;
  chosen?: { mass: number; use: number; label: string }[];
  height?: number;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const wrap = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const c = canvas.current;
    const w = wrap.current;
    if (!c || !w) return;
    const draw = () => {
      const width = w.clientWidth;
      const dpr = window.devicePixelRatio || 1;
      c.width = width * dpr;
      c.height = height * dpr;
      c.style.width = `${width}px`;
      c.style.height = `${height}px`;
      const ctx = c.getContext("2d")!;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, width, height);
      // Geist tokens: points gray, failures faint red, the chosen design blue; labels mono gray-900,
      // gridlines gray-400. The target line is gray so only the limit is red.
      const ink = cssVar("--ds-gray-700");
      const inkStrong = cssVar("--ds-gray-1000");
      const fail = cssVar("--ds-red-700");
      const rule = cssVar("--ds-gray-400");
      const label = cssVar("--ds-gray-900");
      const targetInk = cssVar("--ds-gray-600");
      const accent = cssVar("--ds-blue-700");
      const bg = cssVar("--ds-background-100");
      const targetLine = target !== undefined && target < limit - 1e-9 ? target : null;
      const pad = { l: 68, r: 16, t: 14, b: 40 };
      const plotW = width - pad.l - pad.r;
      const plotH = height - pad.t - pad.b;
      const masses = points.map((p) => p[0]).sort((a, b) => a - b);
      // Fit the x axis to the data (not from 0): just below the bulk of the tried masses (3rd percentile)
      // to just above the heavy end (97th percentile), on a nice step. The few outlier batches beyond the
      // edges are left out, as before.
      const massAt = (q: number) =>
        masses.length ? masses[Math.min(masses.length - 1, Math.max(0, Math.floor(masses.length * q)))] : 0;
      const chosenMasses = (chosen ?? []).map((c) => c.mass);
      const xLo = Math.max(0, Math.min(massAt(0.03), ...chosenMasses) * 0.92);
      const xHi = Math.max(massAt(0.97) * 1.15, ...chosenMasses.map((m) => m * 1.3), 0.1);
      const xAxis = niceRange(xLo, xHi);
      // Fit the y range to the data with the limit and target lines always visible: from just below the
      // bulk (3rd percentile) to just above the larger of the lines and the bulk (97th percentile), on a
      // nice step. The few outliers outside it clamp to the edge.
      const uses = points.map((p) => p[1]).sort((a, b) => a - b);
      const at = (q: number) => (uses.length ? uses[Math.min(uses.length - 1, Math.max(0, Math.floor(uses.length * q)))] : limit);
      const chosenUses = (chosen ?? []).map((c) => c.use);
      const hiRaw = Math.max(limit * 1.05, at(0.97) * 1.03, ...chosenUses.map((u) => u * 1.03), ...(targetLine ? [targetLine * 1.05] : []));
      const loRaw = Math.max(0, Math.min(at(0.03), ...chosenUses, limit, ...(targetLine ? [targetLine] : [])) * 0.95);
      const span = hiRaw - loRaw;
      const yStep = span <= 0.3 ? 0.05 : span <= 0.6 ? 0.1 : span <= 1.2 ? 0.25 : 0.5;
      const yMin = Math.max(0, Math.floor(loRaw / yStep - 1e-9) * yStep);
      const yMax = Math.ceil(hiRaw / yStep - 1e-9) * yStep;
      const yTicks: number[] = [];
      for (let v = yMin; v <= yMax + yStep / 2; v += yStep) yTicks.push(Math.round(v / yStep) * yStep);
      const X = (m: number) => pad.l + ((m - xAxis.min) / (xAxis.max - xAxis.min)) * plotW;
      const Y = (u: number) => pad.t + plotH - ((Math.min(Math.max(u, yMin), yMax) - yMin) / (yMax - yMin)) * plotH;

      ctx.font = tickFont;
      ctx.fillStyle = label;
      ctx.strokeStyle = rule;
      ctx.lineWidth = 1;
      for (const u of yTicks) {
        const y = Math.round(Y(u)) + 0.5;
        ctx.beginPath();
        ctx.moveTo(pad.l, y);
        ctx.lineTo(width - pad.r, y);
        ctx.stroke();
        ctx.textAlign = "right";
        ctx.fillText(`${Math.round(u * 100)}%`, pad.l - 8, y + 4);
      }
      for (const m of xAxis.ticks) {
        ctx.textAlign = "center";
        ctx.fillText(fmt(m, xAxis.digits), X(m), height - pad.b + 18);
      }
      ctx.font = axisFont;
      ctx.fillText("Plate mass (kg)", pad.l + plotW / 2, height - 6);
      ctx.save();
      ctx.translate(13, pad.t + plotH / 2);
      ctx.rotate(-Math.PI / 2);
      ctx.textAlign = "center";
      ctx.fillText("Highest check use", 0, 0);
      ctx.restore();
      ctx.font = tickFont;

      // Dots: gray for every candidate at or under the limit (5 px), faint red 4 px dots only for a real
      // limit exceedance (over 100%). Missing the search target is not a failure, so the engine's flag is
      // not used for colour. A 1 px background-100 stroke keeps overlapping dots separate.
      ctx.lineWidth = 1;
      for (const [m, u] of points) {
        if (m < xAxis.min || m > xAxis.max) continue;
        const over = u > limit + 1e-9;
        ctx.beginPath();
        ctx.arc(X(m), Y(u), over ? 2 : 2.5, 0, Math.PI * 2);
        if (over) ctx.globalAlpha = 0.45;
        ctx.fillStyle = over ? fail : ink;
        ctx.fill();
        ctx.strokeStyle = bg;
        ctx.stroke();
        ctx.globalAlpha = 1;
      }
      // The 100% limit: always drawn and labelled, in gray-1000 (red is kept for dots that exceed it).
      ctx.strokeStyle = inkStrong;
      ctx.setLineDash([5, 4]);
      ctx.beginPath();
      ctx.moveTo(pad.l, Math.round(Y(limit)) + 0.5);
      ctx.lineTo(width - pad.r, Math.round(Y(limit)) + 0.5);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = inkStrong;
      ctx.font = strongFont;
      ctx.textAlign = "right";
      ctx.fillText(`Limit ${Math.round(limit * 100)}%`, width - pad.r, Y(limit) - 7);
      ctx.font = tickFont;
      // The search target, when the engine searched to one: a labelled gray dashed line.
      if (targetLine) {
        ctx.strokeStyle = targetInk;
        ctx.setLineDash([5, 4]);
        ctx.beginPath();
        ctx.moveTo(pad.l, Math.round(Y(targetLine)) + 0.5);
        ctx.lineTo(width - pad.r, Math.round(Y(targetLine)) + 0.5);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = label;
        ctx.font = axisFont;
        ctx.textAlign = "right";
        ctx.fillText(`Search target ${Math.round(targetLine * 100)}%`, width - pad.r, Y(targetLine) + 15);
        ctx.font = tickFont;
      }

      for (const c of chosen ?? []) {
        const cx = X(c.mass);
        const cy = Y(c.use);
        ctx.strokeStyle = accent;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(cx, cy, 7, 0, Math.PI * 2);
        ctx.stroke();
        // Offset callout: the label sits at the end of a leader, away from the point, on whichever side
        // (above or below, right or left) has the fewest dots under it, with a background halo so it
        // stays readable where dots are dense.
        ctx.font = strongFont;
        const labelW = ctx.measureText(c.label).width;
        const dir = cx + 52 + labelW <= width - pad.r ? 1 : -1;
        const crowd = (ly: number) => {
          const x0 = dir === 1 ? cx + 40 : cx - 40 - labelW;
          let n = 0;
          for (const [m, u] of points) {
            const px = X(m);
            const py = Y(u);
            if (px >= x0 - 4 && px <= x0 + labelW + 4 && py >= ly - 12 && py <= ly + 8) n += 1;
          }
          return n;
        };
        const upY = cy - 36;
        const downY = cy + 36;
        const upOk = upY - 12 > pad.t;
        const downOk = downY + 8 < pad.t + plotH;
        const up = upOk && (!downOk || crowd(upY) <= crowd(downY));
        const ly = up ? upY : downY;
        ctx.strokeStyle = accent;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(cx + dir * 5, up ? cy - 5 : cy + 5);
        ctx.lineTo(cx + dir * 28, ly);
        ctx.lineTo(cx + dir * 36, ly);
        ctx.stroke();
        ctx.textAlign = dir === 1 ? "left" : "right";
        ctx.lineJoin = "round";
        ctx.lineWidth = 4;
        ctx.strokeStyle = bg;
        ctx.strokeText(c.label, cx + dir * 40, ly + 4);
        ctx.fillStyle = inkStrong;
        ctx.fillText(c.label, cx + dir * 40, ly + 4);
        ctx.font = tickFont;
      }
    };
    draw();
    const ro = new ResizeObserver(draw);
    ro.observe(w);
    const mo = new MutationObserver(draw);
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => {
      ro.disconnect();
      mo.disconnect();
    };
  }, [points, limit, target, chosen, height]);

  return (
    <div ref={wrap} className="chart" role="img"
      aria-label={`Chart of ${points.length} designs tried, plate mass against highest check use, with the limit at ${Math.round(limit * 100)}%${
        target !== undefined && target < limit - 1e-9 ? ` and a search target at ${Math.round(target * 100)}%` : ""
      }.`}>
      <canvas ref={canvas} />
      <div className="chart-legend">
        <span><i className="dot dot-pass" /> Within the limit</span>
        <span><i className="dot dot-fail" /> Over the limit (fails a check)</span>
        {chosen?.length ? <span><i className="dot dot-chosen" /> Design chosen</span> : null}
      </div>
    </div>
  );
}

/** Solver error falling towards zero, on a log scale. */
export function ResidualChart({ residuals, height = 200 }: { residuals: number[]; height?: number }) {
  const w = 520;
  const pad = { l: 48, r: 12, t: 12, b: 30 };
  if (residuals.length < 2) return null;
  const lo = Math.min(...residuals.filter((r) => r > 0), 1e-12);
  const decades = Math.max(1, Math.ceil(-Math.log10(lo)));
  const X = (i: number) => pad.l + (i / (residuals.length - 1)) * (w - pad.l - pad.r);
  const Y = (r: number) => pad.t + (Math.min(-Math.log10(Math.max(r, 1e-30)), decades) / decades) * (height - pad.t - pad.b);
  const d = residuals.map((r, i) => `${i ? "L" : "M"}${X(i).toFixed(1)},${Y(r).toFixed(1)}`).join("");
  return (
    <svg className="svg-chart" viewBox={`0 0 ${w} ${height}`} role="img" aria-label="Solver error against iteration, on a log scale">
      {Array.from({ length: decades + 1 }, (_, k) => k).filter((k) => k % Math.ceil(decades / 5) === 0).map((k) => (
        <g key={k}>
          <line x1={pad.l} x2={w - pad.r} y1={Y(10 ** -k)} y2={Y(10 ** -k)} className="grid" />
          <text x={pad.l - 6} y={Y(10 ** -k) + 4} textAnchor="end" className="tick">
            {k === 0 ? "1" : `1e-${k}`}
          </text>
        </g>
      ))}
      <path d={d} className="line" />
      <text x={(w + pad.l) / 2} y={height - 6} textAnchor="middle" className="tick">
        Solver iteration ({residuals.length - 1} shown)
      </text>
    </svg>
  );
}

/** Peak stress against mesh size: flat means the answer does not depend on the mesh. */
export function ConvergenceChart({ levels, height = 200 }: { levels: { elements: number; head_von_mises_mpa: number }[]; height?: number }) {
  const w = 520;
  const pad = { l: 56, r: 24, t: 24, b: 30 };
  if (!levels.length) return null;
  const xs = levels.map((l) => Math.log10(l.elements));
  const ys = levels.map((l) => l.head_von_mises_mpa);
  const xMin = Math.min(...xs) - 0.15;
  const xMax = Math.max(...xs) + 0.15;
  const mid = ys.reduce((a, b) => a + b, 0) / ys.length;
  const half = Math.max((Math.max(...ys) - Math.min(...ys)) * 1.5, mid * 0.1);
  const X = (x: number) => pad.l + ((x - xMin) / (xMax - xMin || 1)) * (w - pad.l - pad.r);
  const Y = (y: number) => pad.t + (1 - (y - (mid - half)) / (2 * half)) * (height - pad.t - pad.b);
  return (
    <svg className="svg-chart" viewBox={`0 0 ${w} ${height}`} role="img" aria-label="Peak stress against number of elements">
      {[mid - half, mid, mid + half].map((y) => (
        <g key={y}>
          <line x1={pad.l} x2={w - pad.r} y1={Y(y)} y2={Y(y)} className="grid" />
          <text x={pad.l - 6} y={Y(y) + 4} textAnchor="end" className="tick">
            {fmt(y, 0)}
          </text>
        </g>
      ))}
      <path d={levels.map((_, i) => `${i ? "L" : "M"}${X(xs[i])},${Y(ys[i])}`).join("")} className="line" />
      {levels.map((l, i) => (
        <g key={i}>
          <circle cx={X(xs[i])} cy={Y(ys[i])} r={4} className="point" />
          <text x={X(xs[i])} y={Y(ys[i]) - 10} textAnchor="middle" className="tick strong">
            {fmt(l.head_von_mises_mpa, 1)} MPa
          </text>
          <text x={X(xs[i])} y={height - 8} textAnchor="middle" className="tick">
            {l.elements.toLocaleString()} el.
          </text>
        </g>
      ))}
    </svg>
  );
}

/** Padeye outline with the sling force and its parts, drawn to scale. */
export function ForceDiagram({
  outline,
  holeHeight,
  holeDiameter,
  angle,
  F,
  V,
  H,
}: {
  outline: [number, number][];
  holeHeight: number;
  holeDiameter: number;
  angle: number;
  F: number;
  V: number;
  H: number;
}) {
  const xs = outline.map((p) => p[0]);
  const ys = outline.map((p) => p[1]);
  const span = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys)) || 1;
  const size = 300;
  const s = (size * 0.55) / span;
  const ox = size * 0.4;
  const oy = size * 0.86;
  const P = (x: number, y: number) => `${(ox + x * s).toFixed(1)},${(oy - y * s).toFixed(1)}`;
  const cx = ox;
  const cy = oy - holeHeight * s;
  const a = (angle * Math.PI) / 180;
  const L = size * 0.42;
  const ex = cx + L * Math.cos(a);
  const ey = cy - L * Math.sin(a);
  const kn = (n: number) => `${fmt(n / 1000, 2)} kN`;
  return (
    <svg className="svg-chart force" viewBox={`0 0 ${size} ${size}`} role="img"
      aria-label={`Sling force ${kn(F)} at ${angle} degrees, vertical part ${kn(V)}, horizontal part ${kn(H)}`}>
      <defs>
        <marker id="arrow-accent" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" className="arrowhead-accent" />
        </marker>
        <marker id="arrow-muted" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" className="arrowhead-muted" />
        </marker>
        <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="6" className="hatch" />
        </pattern>
      </defs>
      <rect x={ox - (span * s) / 2 - 20} y={oy} width={span * s + 40} height={10} fill="url(#hatch)" />
      <line x1={ox - (span * s) / 2 - 20} x2={ox + (span * s) / 2 + 40} y1={oy} y2={oy} className="ground" />
      <polygon points={outline.map(([x, y]) => P(x, y)).join(" ")} className="part" />
      <circle cx={cx} cy={cy} r={(holeDiameter / 2) * s} className="hole" />
      <line x1={cx} y1={cy} x2={ex} y2={cy} className="component" markerEnd="url(#arrow-muted)" />
      <line x1={ex} y1={cy} x2={ex} y2={ey} className="component" markerEnd="url(#arrow-muted)" />
      <line x1={cx} y1={cy} x2={ex} y2={ey} className="force-line" markerEnd="url(#arrow-accent)" />
      <text x={ex + 8} y={ey - 2} className="label accent">F = {kn(F)}</text>
      <text x={(cx + ex) / 2} y={cy + 16} textAnchor="middle" className="label">H = {kn(H)}</text>
      <text x={ex + 8} y={(cy + ey) / 2 + 4} className="label">V = {kn(V)}</text>
      <text x={cx + 22} y={cy - 6} className="label">{angle}°</text>
    </svg>
  );
}

/** Collects the design-space points sent so far for one search target. */
export function pointsFor(events: EngEvent[], target?: string): [number, number, boolean][] {
  const out: [number, number, boolean][] = [];
  for (const e of events) if (e.kind === "samples" && (!target || e.target === target)) out.push(...(e.points as [number, number, boolean][]));
  return out;
}

/** The pipe span's natural frequency against the excitation frequencies, each with its keep-clear band. */
export function FrequencyChart({ natural, excitations, margin, height = 170 }: {
  natural: number; excitations: { name: string; hz: number }[]; margin: number; height?: number;
}) {
  const w = 560;
  const pad = { l: 16, r: 16, t: 14, b: 34 };
  const max = Math.max(natural, ...excitations.map((e) => e.hz)) * 1.3;
  const X = (f: number) => pad.l + (f / max) * (w - pad.l - pad.r);
  const ticks = Array.from({ length: 6 }, (_, i) => (max / 5) * i);
  return (
    <svg className="svg-chart" viewBox={`0 0 ${w} ${height}`} role="img"
      aria-label={`Pipe span natural frequency ${fmt(natural)} Hz against ${excitations.length} excitation frequencies`}>
      {ticks.map((f) => (
        <g key={f}>
          <line x1={X(f)} x2={X(f)} y1={pad.t} y2={height - pad.b} className="grid" />
          <text x={X(f)} y={height - pad.b + 16} textAnchor="middle" className="tick">{fmt(f, 0)}</text>
        </g>
      ))}
      {excitations.map((e, i) => (
        <g key={e.name}>
          <rect x={X(e.hz * (1 - margin))} width={X(e.hz * (1 + margin)) - X(e.hz * (1 - margin))} y={pad.t} height={height - pad.t - pad.b} className="band" />
          <line x1={X(e.hz)} x2={X(e.hz)} y1={pad.t} y2={height - pad.b} className="danger-line" />
          <text x={X(e.hz) + 4} y={pad.t + 12 + (i % 3) * 14} className="tick">{e.name} {fmt(e.hz)} Hz</text>
        </g>
      ))}
      <line x1={X(natural)} x2={X(natural)} y1={pad.t} y2={height - pad.b} className="force-line" />
      <text x={X(natural) + 4} y={height - pad.b - 8} className="label accent">Pipe span {fmt(natural)} Hz</text>
      <text x={w / 2} y={height - 4} textAnchor="middle" className="tick">Frequency (Hz). Shaded: within {Math.round(margin * 100)}% of an excitation</text>
    </svg>
  );
}

/** Pressure coefficient round the foil section; the dashed line is where cavitation starts. */
export function PressureChart({ upper, lower, cavitation, height = 220 }: {
  upper: [number, number][]; lower: [number, number][]; cavitation: number; height?: number;
}) {
  const w = 520;
  const pad = { l: 48, r: 14, t: 12, b: 32 };
  const all = [...upper, ...lower].map((p) => p[1]);
  const lo = Math.min(...all, -cavitation) - 0.2;
  const hi = Math.max(...all, 1) + 0.1;
  const X = (x: number) => pad.l + x * (w - pad.l - pad.r);
  const Y = (cp: number) => pad.t + ((cp - lo) / (hi - lo)) * (height - pad.t - pad.b); // suction (negative) at the top
  const path = (pts: [number, number][]) => pts.map(([x, c], i) => `${i ? "L" : "M"}${X(x).toFixed(1)},${Y(c).toFixed(1)}`).join("");
  const ticks = [Math.ceil(lo), 0, 1].filter((v, i, a) => a.indexOf(v) === i);
  return (
    <svg className="svg-chart" viewBox={`0 0 ${w} ${height}`} role="img" aria-label="Pressure coefficient round the foil section">
      {ticks.map((c) => (
        <g key={c}>
          <line x1={pad.l} x2={w - pad.r} y1={Y(c)} y2={Y(c)} className="grid" />
          <text x={pad.l - 6} y={Y(c) + 4} textAnchor="end" className="tick">{fmt(c, 1)}</text>
        </g>
      ))}
      <line x1={pad.l} x2={w - pad.r} y1={Y(-cavitation)} y2={Y(-cavitation)} className="danger-line dashed" />
      <text x={w - pad.r} y={Y(-cavitation) - 4} textAnchor="end" className="tick danger">Cavitation starts</text>
      <path d={path(upper)} className="line" />
      <path d={path(lower)} className="line muted-line" />
      <text x={(w + pad.l) / 2} y={height - 6} textAnchor="middle" className="tick">Along the chord, leading edge to trailing edge. Upper line: suction side</text>
    </svg>
  );
}

/** Round axis fitted to a data range: a 1, 2, 2.5 or 5 x 10^n step giving about four intervals. The low
 *  end snaps down to a half step, so a range that sits away from 0 (plate masses of 0.3 kg and up) never
 *  restarts the axis at 0; the high end snaps up to a step. Ticks are whole steps inside the range. */
function niceRange(lo: number, hi: number, count = 4): { min: number; max: number; ticks: number[]; digits: number } {
  const raw = Math.max(hi - lo, 1e-9) / count;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const norm = raw / mag;
  const step = (norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 2.5 ? 2.5 : norm <= 5 ? 5 : 10) * mag;
  const min = lo <= 0 ? 0 : Math.max(0, Math.floor(lo / (step / 2) + 1e-9) * (step / 2));
  const max = Math.ceil(hi / step - 1e-9) * step;
  const ticks: number[] = [];
  for (let v = Math.ceil(min / step - 1e-9) * step; v <= max + step / 2; v += step) ticks.push(Math.round(v / step) * step);
  const digits = step >= 1 ? 0 : Math.min(3, Math.ceil(-Math.log10(step) - 1e-9) + (norm > 2 && norm <= 2.5 ? 1 : 0));
  return { min, max, ticks, digits };
}
