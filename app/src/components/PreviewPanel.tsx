import { Loader2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api";
import { PartModel, partFrame } from "../three/PartModel";
import { Viewer } from "../three/Viewer";
import type { BracketDesign, CheckReport, FinDesign, Job, PadeyeDesign, PartId, Preview } from "../types";
import { formatKg, formatKn, Note, Skeleton } from "./ui";

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

interface Chip {
  label: string;
  value: string;
  /** Pure numbers with units render in Geist Mono; phrases stay in Sans. */
  mono?: boolean;
  wide?: boolean;
}

function Chips({ part, report }: { part: PartId; report: CheckReport }) {
  const worst = report.checks.find((c) => c.id === report.governing);
  const chips: Chip[] = [];
  if (part === "padeye") {
    const d = report.design;
    const cheeks = d.cheek_thickness_mm > 0;
    chips.push(
      { label: "Plate mass", value: formatKg(report.mass_kg), mono: true },
      { label: "Plate", value: `${d.main_thickness_mm} mm${cheeks ? ` + 2 × ${d.cheek_thickness_mm} mm cheeks` : ""}`, mono: !cheeks },
      { label: "Shackle", value: `${report.shackle.wll_t} t`, mono: true },
    );
  } else if (part === "pipe-bracket") {
    const d = report.design as unknown as BracketDesign;
    chips.push(
      { label: "Steel mass", value: formatKg(report.mass_kg), mono: true },
      { label: "Seat / knees", value: `${d.seat_thickness_mm} / ${d.knee_thickness_mm} mm`, mono: true },
      { label: "U-bolt", value: report.ubolt?.thread ?? "", mono: true },
    );
    if (report.span) chips.push({ label: "Pipe span frequency", value: `${report.span.natural_hz.toFixed(1)} Hz`, mono: true });
  } else {
    const d = report.design as unknown as FinDesign;
    chips.push(
      { label: "Mass", value: formatKg(report.mass_kg), mono: true },
      { label: "Skin / webs", value: `${d.skin_mm} / ${d.web_mm} mm`, mono: true },
      { label: "Stock", value: `Ø${d.stock_diameter_mm} mm`, mono: true },
      { label: "Ribs", value: `${report.ribs} at ${Math.round(report.rib_pitch_mm ?? 0)} mm` },
    );
  }
  if (worst) chips.push({ label: "Closest to its limit", value: `${worst.title}, ${Math.round(worst.utilization * 100)}%`, wide: true });
  return (
    <>
      {chips.map((c) => (
        <div key={c.label} className={`viewer-chip${c.wide ? " wide" : ""}`}>
          {c.label}
          <b className={c.mono ? "mono" : undefined} title={c.value}>
            {c.value}
          </b>
        </div>
      ))}
    </>
  );
}

/** The readout strip while there is no feasible preview yet: the same cells with the same labels, so the
 *  panel height never changes between loading and loaded. Quiet skeleton values while sizing, "-" when the
 *  sizing came back infeasible. */
function ReservedChips({ part, infeasible }: { part: PartId; infeasible: boolean }) {
  const labels =
    part === "padeye"
      ? ["Plate mass", "Plate", "Shackle"]
      : part === "pipe-bracket"
        ? ["Steel mass", "Seat / knees", "U-bolt"]
        : ["Mass", "Skin / webs", "Stock", "Ribs"];
  const value = (wide: boolean) =>
    infeasible ? "-" : <Skeleton width={wide ? 128 : 56} height={12} radius={4} />;
  return (
    <>
      {labels.map((label) => (
        <div key={label} className="viewer-chip">
          {label}
          <b aria-hidden>{value(false)}</b>
        </div>
      ))}
      <div className="viewer-chip wide">
        Closest to its limit
        <b aria-hidden>{value(true)}</b>
      </div>
    </>
  );
}

/** The workspace aside content: the 3D viewer fills the height, then messages and the caption.
 *  Returns a fragment; the Workspace aside is already sticky and a flex column. */
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
    <>
      <Viewer
        size={frame.size}
        centreY={frame.centreY}
        top={
          <span className="legend">
            {busy ? <Loader2 size={14} className="spin" aria-hidden /> : null}
            {busy ? "Sizing…" : "Provisional design"}
          </span>
        }
        overlay={feasible ? <Chips part={part} report={feasible} /> : <ReservedChips part={part} infeasible={!!preview && !preview.feasible} />}
      >
        <PartModel part={part} report={{ design, shackle: feasible?.shackle ?? (undefined as never) }}
          slingAngleDeg={job.part === "padeye" ? job.lift.sling_angle_deg : 60} />
      </Viewer>
      {preview && !preview.feasible && <Note kind="error" size="small">{preview.reason}</Note>}
      {error && <Note kind="error" size="small">{error}</Note>}
      {preview && (
        <p className="caption">
          {caption} This preview updates as you answer. Press "Find designs" for the final sizes, the 3D models and the stress check.
        </p>
      )}
    </>
  );
}
