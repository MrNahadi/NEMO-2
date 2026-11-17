import { Box, ChevronDown, Download, FileSpreadsheet, FileText, ListTree, Loader2, Package, Pencil, RotateCcw, Scissors } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api, bundleUrl, fileUrl, reportUrl } from "../api";
import { useFusion, useFusionRecords } from "../components/Fusion";
import { MoreMenu } from "../components/Menu";
import { ReportViewer } from "../components/ReportViewer";
import { StageList, stagesFrom, StageView, type StageKey } from "../components/Engineering";
import { Banner, CheckList, Segmented, formatKg, formatKn } from "../components/ui";
import { MeshModel } from "../three/MeshModel";
import { frameOf } from "../three/frame";
import { StressModel } from "../three/StressModel";
import { Viewer } from "../three/Viewer";
import { PART_NAMES, PartModel, partFrame } from "../three/PartModel";
import type { BracketDesign, FinDesign, Job, PartId, DesignResult, EngEvent, FusionRecords, Project, StressSurface, SurfaceMesh } from "../types";

type View = "model" | "stress" | "mesh";

export function Results({ project, onEdit, onRunAgain }: { project: Project; onEdit: () => void; onRunAgain: () => void }) {
  const results = project.results!;
  const run = project.latest_run!;
  const [key, setKey] = useState(results.designs[0].key);
  const [view, setView] = useState<View>("model");
  const [check, setCheck] = useState<string | null>(null);
  const [log, setLog] = useState<EngEvent[] | null>(null);
  const [stage, setStage] = useState<StageKey>("search");
  const [showReport, setShowReport] = useState(false);
  const closeReport = useCallback(() => setShowReport(false), []);
  const design = results.designs.find((d) => d.key === key) ?? results.designs[0];
  const fusion = useFusion();
  const { records, reload } = useFusionRecords(project.id, run, design.key, !!fusion.status?.connected);
  const [fusionMessage, setFusionMessage] = useState<{ kind: "info" | "error"; text: string } | null>(null);
  const fusionBusy = fusion.busy === `${project.id}/${run}/${design.key}`;

  async function openFusion() {
    setFusionMessage(null);
    try {
      const model = await fusion.openInFusion(project.id, run, design.key);
      if (!model) return; // the setup dialog was shown instead
      const diff = model.volume_difference;
      setFusionMessage({
        kind: "info",
        text: `Opened in Fusion as a ${model.parametric ? "parametric" : "fixed"} model.${diff !== null ? ` Fusion's volume matches NEMO's to ${(Math.abs(diff) * 100).toFixed(3)}%.` : ""} Use Check in NEMO in Fusion after changing dimensions.`,
      });
      reload();
    } catch (e) {
      setFusionMessage({ kind: "error", text: e instanceof Error ? e.message : String(e) });
    }
  }

  useEffect(() => {
    setLog(null);
    if (results.files?.engineering_log) api.engineeringLog(project.id, run).then(setLog).catch(() => setLog([]));
  }, [project.id, run, results.files?.engineering_log]);

  const part = (results.part ?? "padeye") as PartId;
  const names = PART_NAMES[part];
  const mesh = log?.find((e) => e.kind === "mesh" && e.target === design.key && e.surface)?.surface as SurfaceMesh | undefined;

  return (
    <div className="page page-wide">
      <div className="step-label">{project.name}</div>
      <h1 className="title">Your {names.noun} designs</h1>
      <p className="lead">
        {results.designs.length} design{results.designs.length === 1 ? "" : "s"} {jobSummary(results.job)}.{" "}
        {results.designs.every((d) => d.check_report.passed) ? "Each passes every required check." : "Read the failing checks below."} Pick one to see its working.
      </p>

      <div className="design-tabs mt-6">
        {results.designs.map((d) => (
          <button key={d.key} className="design-tab" aria-pressed={d.key === key} onClick={() => setKey(d.key)}>
            <span className="caption">{d.label}</span>
            <span className="mass">{formatKg(d.check_report.mass_kg)}</span>
            <span className="caption">{tabCaption(part, d)}</span>
          </button>
        ))}
      </div>

      <div className="split">
        <div className="stack gap-6">
          <Summary design={design} part={part} />
          <section className="stack gap-2">
            <h2 className="section-title">Design checks</h2>
            <p className="caption">
              Select a check to see its calculation, step by step{part === "padeye" ? ", and where it acts on the padeye in the 3D view" : ""}.
            </p>
            <CheckList checks={design.check_report.checks} selected={check} onSelect={(id) => { setCheck(id); if (id) setView("model"); }} />
          </section>
          {design.fea && <FeaSummary design={design} part={part} />}
          <section className="stack gap-2">
            <h2 className="section-title">Calculation report and files</h2>
            <div className="downloads">
              <button className="btn btn-primary" onClick={() => setShowReport(true)}>
                <FileText aria-hidden /> View calculation report
              </button>
              {part === "padeye" && (
                <button className="btn" onClick={openFusion} disabled={fusionBusy}>
                  {fusionBusy ? <Loader2 className="spin" aria-hidden /> : <Box aria-hidden />}
                  {fusionBusy ? "Building in Fusion" : "Open in Fusion"}
                </button>
              )}
              <MoreMenu
                label="Download files"
                align="left"
                triggerClassName="btn"
                trigger={<><Download aria-hidden /> Download files <ChevronDown aria-hidden /></>}
                items={[
                  { label: "Everything", hint: "ZIP", icon: <Package aria-hidden />, onSelect: () => download(bundleUrl(project.id, run, design.key)) },
                  { label: "Calculation report", hint: "PDF", icon: <FileText aria-hidden />, separated: true, onSelect: () => download(reportUrl(project.id, run, design.key, true)) },
                  { label: "3D model", hint: "STEP", icon: <Box aria-hidden />, onSelect: () => download(fileUrl(project.id, run, design.files.step)) },
                  { label: "Cutting profile", hint: "DXF", icon: <Scissors aria-hidden />, onSelect: () => download(fileUrl(project.id, run, design.files.dxf)) },
                  ...(results.files
                    ? [
                        { label: "Engineering log", hint: "JSON", icon: <ListTree aria-hidden />, separated: true, onSelect: () => download(fileUrl(project.id, run, results.files!.engineering_log)) },
                        { label: "Every design tried", hint: "CSV", icon: <FileSpreadsheet aria-hidden />, onSelect: () => download(fileUrl(project.id, run, results.files!.designs_evaluated)) },
                      ]
                    : []),
                ]}
              />
            </div>
            <p className="caption">
              The report has a fabrication drawing, every calculation and the stress results{part === "padeye" ? ", with a Fusion cross-check sheet" : ""}.
              "Everything" puts the report, 3D model, cutting profile and the run's records in one ZIP file, ready to send.
            </p>
            {fusionMessage && <Banner kind={fusionMessage.kind}>{fusionMessage.text}</Banner>}
          </section>
          {part === "padeye" && <FusionSection records={records} />}
        </div>

        <div className="stack gap-2 sticky">
          <ResultViewer projectId={project.id} run={run} design={design} view={view} check={check} mesh={mesh} part={part} slingAngle={results.job.part === "padeye" ? results.job.lift.sling_angle_deg : 60} />
          <Segmented
            label="What the 3D view shows"
            value={view}
            onChange={(v) => { setView(v); if (v !== "model") setCheck(null); }}
            options={[
              { value: "model", label: "Model" },
              { value: "mesh", label: "Mesh" },
              { value: "stress", label: "Stress" },
            ]}
          />
          {check && view === "model" && part === "padeye" && (
            <p className="caption">
              Highlighted in blue: the part of the padeye the selected check is about.
            </p>
          )}
        </div>
      </div>

      {log && log.length > 0 && (
        <section className="mt-8 stack gap-3">
          <div>
            <h2 className="section-title">How NEMO got here</h2>
            <p className="caption">The record of this run for the {design.label.split(" (")[0].toLowerCase()} design, step by step.</p>
          </div>
          <div className="run-grid">
            <StageList stages={stagesFrom(log, true, false)} selected={stage} onSelect={setStage} />
            <section className="live-panel">
              <StageView stage={stage} events={log} target={["search", "cad", "mesh", "solve", "verify"].includes(stage) ? design.key : undefined} />
            </section>
          </div>
          <p className="caption">
            The engineering log and a spreadsheet of all {results.search.evaluations.toLocaleString()} designs the search tried are in the
            Download files menu above, so anyone can check the choice.
          </p>
        </section>
      )}

      <div className="actions">
        <button className="btn" onClick={onEdit}>
          <Pencil aria-hidden /> Change the answers
        </button>
        <button className="btn btn-ghost" onClick={onRunAgain}>
          <RotateCcw aria-hidden /> Run again
        </button>
      </div>
      {showReport && (
        <ReportViewer
          title={`${project.name}: ${design.label.split(" (")[0]} design`}
          subtitle={`Calculation report, ${formatKg(design.check_report.mass_kg)} ${names.noun}`}
          viewUrl={reportUrl(project.id, run, design.key)}
          downloadUrl={reportUrl(project.id, run, design.key, true)}
          onClose={closeReport}
        />
      )}
      <div className="mt-4">
        <Banner kind="info">
          A competent engineer must review this design{part === "padeye" ? ", the structure it is welded to and the lifting arrangement" : " and the structure it is fitted to"} before it is made or used.
        </Banner>
      </div>
    </div>
  );
}

function FusionSection({ records }: { records: FusionRecords | null }) {
  if (!records || (!records.model && !records.checks.length && !records.crosscheck)) return null;
  const pct = (d: number | null | undefined, digits = 1) => (d === null || d === undefined ? "-" : `${d >= 0 ? "+" : ""}${(d * 100).toFixed(digits)}%`);
  const num = (v: number | null | undefined, digits: number) => (v === null || v === undefined ? "-" : v.toFixed(digits));
  const last = records.checks[records.checks.length - 1];
  const xc = records.crosscheck;
  return (
    <section className="stack gap-2">
      <h2 className="section-title">Fusion</h2>
      {records.model && (
        <div className="fusion-card">
          <h3>Model built in Fusion</h3>
          <dl className="kv">
            <dt>Model type</dt>
            <dd>{records.model.parametric ? "Parametric (dimensions are Fusion parameters)" : "Fixed geometry"}</dd>
            <dt>Volume, Fusion against NEMO</dt>
            <dd>
              {Math.round(records.model.volume_mm3).toLocaleString()} mm³ against {Math.round(records.model.nemo_volume_mm3).toLocaleString()} mm³ ({pct(records.model.volume_difference, 2)})
            </dd>
            <dt>Fusion material</dt>
            <dd>
              {records.model.fusion_material ?? "Not assigned"}
              {records.model.material_matches
                ? `: yield ${Math.round(records.model.fusion_yield_mpa ?? 0)} MPa, matches NEMO`
                : records.model.fusion_material
                  ? ". Its strength does not match NEMO's. Set the material values by hand before solving (see the cross-check sheet)."
                  : ""}
            </dd>
          </dl>
        </div>
      )}
      {last && (
        <div className="fusion-card">
          <h3>Last check from Fusion</h3>
          <p>
            {last.passed ? <span className="text-pass">Passes every required check.</span> : <span className="text-fail">Does not pass every required check.</span>}{" "}
            Highest use: {last.governing.title.toLowerCase()}, {Math.round(last.governing.use * 100)}%. Plate mass {formatKg(last.mass_kg)} (NEMO design {formatKg(last.nemo_mass_kg)}).
          </p>
          {Object.keys(last.changed).length > 0 && (
            <p className="caption">
              Changed in Fusion:{" "}
              {Object.entries(last.changed)
                .map(([k, v]) => `${k.replace("_mm", "").replace(/_/g, " ")} ${v.from} to ${v.to} mm`)
                .join("; ")}
            </p>
          )}
          <p className="caption">Checked {new Date(last.checked_at).toLocaleString()}. {records.checks.length} check{records.checks.length === 1 ? "" : "s"} sent from Fusion so far.</p>
        </div>
      )}
      {xc && (
        <div className="fusion-card">
          <h3>Fusion stress cross-check</h3>
          <p className={xc.agrees ? "text-pass" : "text-fail"}>{xc.agrees ? "Agrees with NEMO's stress check." : "Differs from NEMO's stress check. Review the Fusion study set-up."}</p>
          <table className="data">
            <thead>
              <tr><th>Result</th><th className="r">Fusion</th><th className="r">NEMO</th><th className="r">Difference</th></tr>
            </thead>
            <tbody>
              <tr><td>Reaction</td><td className="r">{xc.reaction_n !== null ? formatKn(xc.reaction_n) : "-"}</td><td className="r">{xc.nemo_reaction_n ? formatKn(xc.nemo_reaction_n) : "-"}</td><td className="r">{pct(xc.reaction_difference)}</td></tr>
              <tr><td>Peak stress</td><td className="r">{num(xc.peak_stress_mpa, 1)} MPa</td><td className="r">{num(xc.nemo_peak_stress_mpa, 1)} MPa</td><td className="r">{pct(xc.stress_difference)}</td></tr>
              <tr><td>Movement</td><td className="r">{num(xc.max_displacement_mm, 3)} mm</td><td className="r">{num(xc.nemo_max_displacement_mm, 3)} mm</td><td className="r">{pct(xc.displacement_difference)}</td></tr>
            </tbody>
          </table>
          <p className="caption">
            They agree when the reaction is within 2% and the peak stress within 15%. Movement is shown for information only, because it
            depends on how each program models the weld and the support.
          </p>
          <p className="caption">Recorded {new Date(xc.recorded_at).toLocaleString()}{xc.checked_by ? ` by ${xc.checked_by}` : ""}. The calculation report includes it.</p>
        </div>
      )}
    </section>
  );
}

function download(url: string) {
  const a = document.createElement("a");
  a.href = url;
  a.rel = "noreferrer";
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function jobSummary(job: Job): string {
  if (job.part === "padeye") {
    const t = (job.lift.lifted_mass_kg / 1000).toLocaleString(undefined, { maximumFractionDigits: 2 });
    return `for a ${t} t lift on ${job.lift.lift_points} point${job.lift.lift_points === 1 ? "" : "s"}`;
  }
  if (job.part === "pipe-bracket") return `for an NPS ${job.pipe_nps} pipe on supports every ${job.span_m} m`;
  return `for a ${job.span_m} × ${job.chord_m} m fin at ${job.speed_kn} knots`;
}

function tabCaption(part: PartId, d: DesignResult): string {
  const r = d.check_report;
  if (part === "pipe-bracket") {
    const b = r.design as unknown as BracketDesign;
    return `${b.seat_thickness_mm} mm seat, 2 × ${b.knee_thickness_mm} mm knees, ${r.ubolt?.thread} U-bolt`;
  }
  if (part === "stabilizer") {
    const f = r.design as unknown as FinDesign;
    return `${f.skin_mm} mm skin, ${r.ribs} ribs, Ø${f.stock_diameter_mm} mm stock`;
  }
  return `${r.design.main_thickness_mm} mm plate${r.design.cheek_thickness_mm > 0 ? " with cheek plates" : ""}, ${r.shackle.wll_t} t shackle`;
}

function Summary({ design, part }: { design: DesignResult; part: PartId }) {
  const r = design.check_report;
  const governing = r.checks.find((c) => c.id === r.governing);
  let rows: [string, string][];
  let force: [string, string];
  if (part === "pipe-bracket") {
    const b = r.design as unknown as BracketDesign;
    force = [formatKn(r.loads.sling_force_n), "Downward design force"];
    rows = [
      ["Pipe", r.pipe?.label ?? ""],
      ["Seat plate", `${b.seat_length_mm} × ${b.seat_width_mm} × ${b.seat_thickness_mm} mm`],
      ["Knees (2)", `${b.knee_thickness_mm} mm, ${b.knee_depth_mm} mm deep at the bulkhead`],
      ["Pipe centre from the bulkhead", `${Math.round(b.pipe_offset_mm)} mm`],
      ["U-bolt", r.ubolt?.label ?? ""],
      ["Welds", `${b.root_weld_mm} mm to the bulkhead, ${b.knee_weld_mm} mm knees to seat`],
    ];
    if (r.span) {
      rows.push(["Pipe span frequency", `${r.span.natural_hz.toFixed(1)} Hz, ${Math.round(r.span.separation * 100)}% from ${r.span.nearest.name.toLowerCase()} (${r.span.nearest.hz.toFixed(1)} Hz)`]);
      rows.push(["Longest support spacing", `${r.span.recommended_m.toFixed(1)} m (stress ${r.span.spans_m.stress.toFixed(1)}, sag ${r.span.spans_m.sag.toFixed(1)}, vibration ${r.span.spans_m.frequency.toFixed(1)} m)`]);
    }
  } else if (part === "stabilizer") {
    const f = r.design as unknown as FinDesign;
    const m = r.masses_kg ?? {};
    force = [formatKn(r.loads.sling_force_n), "Design force on the fin"];
    rows = [
      ["Foil", `${f.span_mm} mm span × ${f.chord_mm} mm chord, NACA 00${Math.round(f.thickness_ratio * 100)}`],
      ["Skin", `${f.skin_mm} mm`],
      ["Spars and ribs", `${f.web_mm} mm; spars at ${Math.round(f.front_spar * 100)}% and ${Math.round(f.rear_spar * 100)}% chord`],
      ["Ribs", `${r.ribs} at ${Math.round(r.rib_pitch_mm ?? 0)} mm`],
      ["Stock", `Ø${f.stock_diameter_mm} mm ${r.stock_material?.name ?? ""}`],
      ["Mass", `structure ${formatKg((m.total ?? 0) - (m.stock ?? 0))}, stock ${formatKg(m.stock ?? 0)}`],
    ];
  } else {
    const d = r.design;
    force = [formatKn(r.loads.sling_force_n), "Sling force per padeye"];
    rows = [
      ["Main plate", `${d.main_thickness_mm} mm`],
      ["Head radius", `${d.head_radius_mm} mm`],
      ["Hole diameter", `${d.hole_diameter_mm} mm`],
      ["Hole height above base", `${d.hole_height_mm} mm`],
      ["Base length", `${d.base_length_mm} mm`],
      ["Base weld", `${d.weld_leg_mm} mm fillet, both sides`],
    ];
    if (d.cheek_thickness_mm > 0) {
      rows.push(["Cheek plates (2)", `${d.cheek_thickness_mm} mm, radius ${d.cheek_radius_mm} mm`]);
      rows.push(["Cheek welds", `${d.cheek_weld_leg_mm} mm fillet all round`]);
    }
    rows.push(["Shackle", r.shackle.label]);
  }
  return (
    <section className="stack gap-3">
      <div className="stat-grid">
        <div className="stat">
          <div className="value">{formatKg(r.mass_kg)}</div>
          <div className="label">{part === "padeye" ? "Plate mass" : "Steel mass"}</div>
        </div>
        <div className="stat">
          <div className="value">{force[0]}</div>
          <div className="label">{force[1]}</div>
        </div>
        <div className="stat">
          <div className="value">{governing ? `${Math.round(governing.utilization * 100)}%` : "–"}</div>
          <div className="label">Highest use: {governing?.title.toLowerCase()}</div>
        </div>
      </div>
      <dl className="kv">
        {rows.map(([k, v]) => (
          <div key={k} style={{ display: "contents" }}>
            <dt>{k}</dt>
            <dd>{v}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function FeaSummary({ design, part }: { design: DesignResult; part: PartId }) {
  const f = design.fea!;
  const ok = f.factor_of_safety_on_yield >= 1 && f.converged;
  const what =
    part === "padeye"
      ? "The built-in simulation pulled on the hole with the full sling force and held the base fixed. The highest stress near the hole is"
      : part === "pipe-bracket"
        ? "The built-in simulation pushed on the seat where the pipe sits, with the design forces, and held the bracket fixed at the bulkhead. The highest stress away from the bulkhead face is"
        : "The fin body is a thin box checked by hand calculation; the built-in simulation checks the stock, fixed at the outer bearing and loaded with the fin force and twist. Its highest stress is";
  return (
    <section className="stack gap-2">
      <h2 className="section-title">Stress check</h2>
      <p className="muted">
        {what} <b>{f.head_von_mises_mpa.toFixed(0)} MPa</b>, against a yield strength of {f.yield_strength_mpa.toFixed(0)} MPa, so the most
        stressed point has a safety factor of <b>{f.factor_of_safety_on_yield.toFixed(2)}</b> before it would start to bend permanently.
      </p>
      <p className="caption">
        Checked on {f.levels.length} meshes; the result changed by {(f.convergence_change * 100).toFixed(1)}% on the finest. The support forces
        balance the load to within {Math.max(...f.levels.map((l) => l.reaction_balance_error)).toExponential(0)}.
        {f.hand_stress_mpa ? ` Hand calculation for the same place (${f.hand_label}): ${f.hand_stress_mpa.toFixed(0)} MPa.` : ""}{" "}
        {ok ? "Result: pass." : "Result: needs an engineer's review."}
      </p>
    </section>
  );
}

function ResultViewer({
  projectId,
  run,
  design,
  view,
  check,
  mesh,
  part,
  slingAngle,
}: {
  projectId: string;
  run: string;
  design: DesignResult;
  view: View;
  check: string | null;
  mesh?: SurfaceMesh;
  part: PartId;
  slingAngle: number;
}) {
  const [surface, setSurface] = useState<StressSurface | null>(null);
  const path = design.files.stress_surface;
  useEffect(() => {
    setSurface(null);
    if (view === "stress" && path) api.stressSurface(projectId, run, path).then(setSurface).catch(() => setSurface(null));
  }, [projectId, run, path, view]);
  const yieldMpa = design.fea?.yield_strength_mpa ?? 1;
  const checkTitle = check && part === "padeye" ? design.check_report.checks.find((c) => c.id === check)?.title : null;
  const frame = view === "stress" && surface ? frameOf(surface.positions) : view === "mesh" && mesh ? frameOf(mesh.positions) : partFrame(part, design.check_report.design);
  return (
    <Viewer
      size={frame.size}
      centreY={frame.centreY}
      top={
        view === "stress" ? (
          <span className="legend">
            0 <span className="ramp" /> {yieldMpa.toFixed(0)} MPa (yield){part === "stabilizer" ? ", stock" : ""}
          </span>
        ) : view === "mesh" ? (
          <span className="legend">Coarsest of the 3 meshes solved{part === "stabilizer" ? " (stock)" : ""}</span>
        ) : checkTitle ? (
          <span className="legend legend-accent">{checkTitle}</span>
        ) : undefined
      }
    >
      {view === "stress" && surface ? (
        <StressModel surface={surface} scaleMax={yieldMpa} />
      ) : view === "mesh" && mesh ? (
        <MeshModel mesh={mesh} />
      ) : (
        <PartModel
          part={part}
          report={design.check_report}
          slingAngleDeg={slingAngle}
          showExtras={view === "model" && (!check || check.startsWith("shackle") || part !== "padeye")}
          highlight={part === "padeye" ? check : null}
        />
      )}
    </Viewer>
  );
}
