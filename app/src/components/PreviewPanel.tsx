import { Loader2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api";
import { PartModel, partFrame } from "../three/PartModel";
import { Viewer } from "../three/Viewer";
import type { BracketDesign, CheckReport, FinDesign, Job, PadeyeDesign, PartId, Preview } from "../types";
import { Banner, formatKg, formatKn } from "./ui";

const PADEYE: PadeyeDesign = {
  main_thickness_mm: 20, head_radius_mm: 45, hole_diameter_mm: 24, base_length_mm: 180, hole_height_mm: 90,
  weld_leg_mm: 8, cheek_thickness_mm: 0, cheek_radius_mm: 0, cheek_weld_leg_mm: 0,
};
const BRACKET: BracketDesign = {
  seat_length_mm: 200, seat_width_mm: 120, seat_thickness_mm: 10, knee_depth_mm: 120, knee_thickness_mm: 8,
  pipe_offset_mm: 110, pipe_od_mm: 114.3, ubolt_diameter_mm: 12, root_weld_mm: 5, knee_weld_mm: 5,
};
const FIN: FinDesign = {
  span_mm: 1400, chord_mm: 1200, thickness_ratio: 0.2, stock_position: 0.35, front_spar: 0.15, rear_spar: 0.65,
  skin_mm: 10, web_mm: 10, rib_spacing_mm: 350, stock_diameter_mm: 160, bearing_gap_mm: 200,
};

export function placeholder(part: PartId): CheckReport["design"] {
  return (part === "pipe-bracket" ? BRACKET : part === "stabilizer" ? FIN : PADEYE) as unknown as CheckReport["design"];
}

/** Re-sizes the part from the current answers (debounced) and returns the latest result. */
export function usePreview(job: Job | null, valid: boolean) {
  const [preview, setPreview] = useState<Preview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const key = job ? JSON.stringify(job) : "";

  useEffect(() => {
    if (!job || !valid) return;
    const timer = window.setTimeout(async () => {
      controller.current?.abort();
      const c = new AbortController();
      controller.current = c;
      setBusy(true);
      try {
        const result = await api.preview(job, c.signal);
        if (!c.signal.aborted) {
          setPreview(result);
          setError(null);
        }
      } catch (e) {
        if (!c.signal.aborted) setError(e instanceof ApiError ? e.message : "We couldn't size the part.");
      } finally {
        if (!c.signal.aborted) setBusy(false);
      }
    }, 280);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, valid]);

  return { preview, error, busy };
}

function Chips({ part, report }: { part: PartId; report: CheckReport }) {
  const worst = report.checks.find((c) => c.id === report.governing);
  const chips: [string, string][] = [];
  if (part === "padeye") {
    const d = report.design;
    chips.push(["Plate mass", formatKg(report.mass_kg)],
      ["Plate", `${d.main_thickness_mm} mm${d.cheek_thickness_mm > 0 ? ` + 2 × ${d.cheek_thickness_mm} mm cheeks` : ""}`],
      ["Shackle", `${report.shackle.wll_t} t`]);
  } else if (part === "pipe-bracket") {
    const d = report.design as unknown as BracketDesign;
    chips.push(["Steel mass", formatKg(report.mass_kg)], ["Seat / knees", `${d.seat_thickness_mm} / ${d.knee_thickness_mm} mm`],
      ["U-bolt", report.ubolt?.thread ?? ""]);
    if (report.span) chips.push(["Pipe span frequency", `${report.span.natural_hz.toFixed(1)} Hz`]);
  } else {
    const d = report.design as unknown as FinDesign;
    chips.push(["Mass", formatKg(report.mass_kg)], ["Skin / webs", `${d.skin_mm} / ${d.web_mm} mm`],
      ["Stock", `Ø${d.stock_diameter_mm} mm`], ["Ribs", `${report.ribs} at ${Math.round(report.rib_pitch_mm ?? 0)} mm`]);
  }
  if (worst) chips.push(["Closest to its limit", `${worst.title}, ${Math.round(worst.utilization * 100)}%`]);
  return (
    <>
      {chips.map(([label, value]) => (
        <div key={label} className="viewer-chip">
          {label}
          <b>{value}</b>
        </div>
      ))}
    </>
  );
}

export function PreviewPanel({ job, preview, error, busy }: { job: Job; preview: Preview | null; error: string | null; busy: boolean }) {
  const part = job.part;
  const feasible = preview?.feasible ? preview : null;
  const design = feasible?.design ?? placeholder(part);
  const frame = partFrame(part, design);
  const force = preview?.loads.sling_force_n;
  const caption =
    part === "padeye"
      ? `Each padeye takes a sling force of ${force ? formatKn(force) : "-"}.`
      : part === "pipe-bracket"
        ? `Each bracket carries a downward design force of ${force ? formatKn(force) : "-"}.`
        : `The fin is designed for a force of ${force ? formatKn(force) : "-"} at its largest angle.`;
  return (
    <div className="stack gap-2 sticky preview-panel">
      <Viewer
        size={frame.size}
        centreY={frame.centreY}
        top={
          <span className="legend">
            {busy ? <Loader2 size={14} className="spin" aria-hidden /> : null}
            {busy ? "Sizing…" : "Provisional design"}
          </span>
        }
        overlay={feasible ? <Chips part={part} report={feasible} /> : null}
      >
        <PartModel part={part} report={{ design, shackle: feasible?.shackle ?? (undefined as never) }}
          slingAngleDeg={job.part === "padeye" ? job.lift.sling_angle_deg : 60} />
      </Viewer>
      {preview && !preview.feasible && <Banner kind="error">{preview.reason}</Banner>}
      {error && <Banner kind="error">{error}</Banner>}
      {preview && (
        <p className="caption">
          {caption} This preview updates as you answer. Press "Find designs" for the final sizes, the 3D models and the stress check.
        </p>
      )}
    </div>
  );
}
