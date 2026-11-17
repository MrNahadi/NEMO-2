import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";
import type { ReactNode } from "react";
import { MeshModel } from "../three/MeshModel";
import { Viewer } from "../three/Viewer";
import type { EngEvent, PadeyeDesign, WorkingStep } from "../types";
import { ConvergenceChart, DesignSpaceChart, ForceDiagram, FrequencyChart, pointsFor, PressureChart, ResidualChart } from "./Charts";
import { frameOf } from "../three/frame";
import { Working } from "./Formula";
import { formatKn } from "./ui";

export type StageKey = "forces" | "shackle" | "search" | "cad" | "mesh" | "solve" | "verify";
export type StageState = "waiting" | "active" | "done" | "failed";

export interface Stage {
  key: StageKey;
  title: string;
  state: StageState;
  summary: ReactNode;
}

const TARGET_NAMES: Record<string, string> = { lightest: "Lightest", balanced: "Balanced", robust: "Extra margin" };
const n0 = (v: number) => v.toLocaleString(undefined, { maximumFractionDigits: 0 });
const n1 = (v: number, d = 1) => v.toLocaleString(undefined, { maximumFractionDigits: d, minimumFractionDigits: d });

const last = (events: EngEvent[], kind: string, target?: string) => {
  for (let i = events.length - 1; i >= 0; i--) if (events[i].kind === kind && (!target || events[i].target === target)) return events[i];
  return undefined;
};
const all = (events: EngEvent[], kind: string) => events.filter((e) => e.kind === kind);

/** Works out what each stage of the run has done so far, from the engine's events. */
export function partOf(events: EngEvent[]): string {
  return (last(events, "start")?.part as string | undefined) ?? "padeye";
}

export function stagesFrom(events: EngEvent[], finished: boolean, failed: boolean): Stage[] {
  const part = partOf(events);
  const loads = last(events, "loads");
  const shackles = part === "padeye" ? last(events, "shackles") : last(events, part === "stabilizer" ? "hydro" : "span");
  const searchDone = last(events, "search_done");
  const found = all(events, "design_found").filter((e) => !e.duplicate);
  const searchStart = last(events, "search_start");
  const combo = last(events, "combination");
  const samples = last(events, "samples");
  const cads = all(events, "cad");
  const meshes = all(events, "mesh");
  const solves = all(events, "solve");
  const feaDone = all(events, "fea_done");
  const expectedDesigns = searchDone?.designs?.length ?? 0;
  const solving = last(events, "solve_start");
  const state = (done: boolean, started: boolean): StageState =>
    done ? "done" : failed && started ? "failed" : started ? "active" : failed ? "failed" : "waiting";

  const evaluations = samples?.evaluations ?? combo?.evaluations ?? 0;
  return [
    {
      key: "forces",
      title: part === "padeye" ? "Forces on each padeye" : part === "stabilizer" ? "Forces on the fin" : "Forces on the bracket",
      state: state(!!loads, true),
      summary: !loads ? "Working out the forces" : part === "padeye" ? `Sling force F = ${formatKn(loads.sling_force_n)} (${n1(loads.sling_force_t, 2)} t)`
        : part === "stabilizer" ? `Design force F = ${formatKn(loads.design_force_n)}, twist ${n1(loads.torque_nm / 1000, 2)} kN·m` : `Down ${formatKn(loads.down_n)}, across ${formatKn(loads.across_n)}`,
    },
    {
      key: "shackle",
      title: part === "padeye" ? "Shackle" : part === "stabilizer" ? "Pressure on the foil" : "Pipe span and vibration",
      state: state(!!shackles, !!loads),
      summary: shackles && part === "pipe-bracket" ? `Pipe span ${n1(shackles.natural_hz)} Hz, ${Math.round(shackles.separation * 100)}% from ${shackles.nearest.name.toLowerCase()}`
        : shackles && part === "stabilizer" ? `Lowest pressure coefficient ${n1(shackles.cp_min, 2)}, cavitation number ${n1(shackles.cavitation_number, 2)}`
        : shackles ? `${shackles.candidates[0].label}, pin ${shackles.candidates[0].pin_diameter_mm} mm` : "Waiting for the forces",
    },
    {
      key: "search",
      title: "Design search",
      state: state(!!searchDone, !!shackles),
      summary: searchDone
        ? `${n0(searchDone.evaluations)} designs checked, ${found.length} kept`
        : searchStart
          ? `${TARGET_NAMES[searchStart.target]}: combination ${combo && combo.target === searchStart.target ? combo.index : 1} of ${combo && combo.target === searchStart.target ? combo.count : "?"}, ${n0(evaluations)} designs checked`
          : "Waiting for the shackle",
    },
    {
      key: "cad",
      title: "3D models",
      state: state(expectedDesigns > 0 && cads.length >= expectedDesigns, !!searchDone),
      summary: cads.length
        ? `${cads.length} of ${expectedDesigns || "?"} built; volume within ${n1(Math.max(...cads.map((c) => Math.abs(c.difference) * 100)), part === "stabilizer" ? 1 : 4)}% of the formula`
        : "Waiting for the designs",
    },
    {
      key: "mesh",
      title: "Mesh",
      state: state(finished && meshes.length > 0, meshes.length > 0),
      summary: meshes.length
        ? `${TARGET_NAMES[meshes[meshes.length - 1].target]}, mesh ${meshes[meshes.length - 1].level} of ${meshes[meshes.length - 1].levels}: ${n0(meshes[meshes.length - 1].elements)} elements`
        : "Waiting for the 3D models",
    },
    {
      key: "solve",
      title: "Stress solve",
      state: state(finished && solves.length > 0, !!solving),
      summary: solves.length
        ? `${n0(solves[solves.length - 1].equations)} equations solved in ${n1(solves[solves.length - 1].seconds)} s`
        : solving
          ? `Solving ${n0(solving.equations)} equations`
          : "Waiting for the mesh",
    },
    {
      key: "verify",
      title: "Checks on the result",
      state: state(expectedDesigns > 0 && feaDone.length >= expectedDesigns, feaDone.length > 0),
      summary: feaDone.length
        ? `Force balance within ${Math.max(...feaDone.flatMap((f) => f.levels.map((l: { reaction_balance_error: number }) => l.reaction_balance_error))).toExponential(0)}; mesh change ${n1(Math.max(...feaDone.map((f) => f.convergence_change * 100)), 2)}%`
        : "Waiting for the solve",
    },
  ];
}

export function StageList({ stages, selected, onSelect }: { stages: Stage[]; selected: StageKey; onSelect: (k: StageKey) => void }) {
  return (
    <ol className="stages">
      {stages.map((s, i) => (
        <li key={s.key}>
          <button type="button" className={`stage stage-${s.state}`} aria-pressed={selected === s.key} onClick={() => onSelect(s.key)}>
            <span className="stage-icon" aria-hidden>
              {s.state === "done" ? <CheckCircle2 /> : s.state === "active" ? <Loader2 className="spin" /> : s.state === "failed" ? <XCircle /> : <Circle />}
            </span>
            <span className="stage-text">
              <span className="stage-title">
                <span className="stage-number">{i + 1}</span>
                {s.title}
              </span>
              <span className="stage-summary">{s.summary}</span>
            </span>
          </button>
        </li>
      ))}
    </ol>
  );
}

// ---------------------------------------------------------------- 2D outline
function tangent(px: number, py: number, cy: number, r: number, side: 1 | -1) {
  const d = Math.max(Math.hypot(px, py - cy), r + 1e-6);
  return Math.atan2(py - cy, px) + side * Math.acos(r / d);
}

export function outline2d(d: PadeyeDesign, segments = 64): [number, number][] {
  const half = d.base_length_mm / 2;
  const h = d.hole_height_mm;
  const r = d.head_radius_mm;
  const a0 = tangent(half, 0, h, r, 1);
  let a1 = tangent(-half, 0, h, r, -1);
  while (a1 < a0) a1 += Math.PI * 2;
  const pts: [number, number][] = [[-half, 0], [half, 0]];
  for (let i = 0; i <= segments; i++) {
    const a = a0 + ((a1 - a0) * i) / segments;
    pts.push([r * Math.cos(a), h + r * Math.sin(a)]);
  }
  return pts;
}

const GENERIC: PadeyeDesign = {
  main_thickness_mm: 20, head_radius_mm: 45, hole_diameter_mm: 26, base_length_mm: 200, hole_height_mm: 90,
  weld_leg_mm: 8, cheek_thickness_mm: 0, cheek_radius_mm: 0, cheek_weld_leg_mm: 0,
};

// ---------------------------------------------------------------- stage views
export function StageView({ stage, events, target }: { stage: StageKey; events: EngEvent[]; target?: string }) {
  const loads = last(events, "loads");
  const designFor = (t?: string) => (last(events, "design_found", t)?.design as PadeyeDesign | undefined);
  const part = partOf(events);

  if (part !== "padeye" && stage === "forces") {
    if (!loads) return <Waiting />;
    return (
      <div className="stack gap-3">
        <p className="muted">
          {part === "stabilizer"
            ? "The lift on the fin at full speed and its largest angle comes from published low-aspect-ratio foil data, and is compared with the IACS rudder formula. The larger is used for the structure."
            : "The pipe span's weight, with its contents and insulation, is multiplied by the ship's motion. These forces act on the bracket where the pipe sits."}
        </p>
        <Working steps={loads.steps as WorkingStep[]} />
      </div>
    );
  }

  if (part === "pipe-bracket" && stage === "shackle") {
    const s = last(events, "span");
    if (!s) return <Waiting />;
    return (
      <div className="stack gap-3">
        <p className="muted">
          The pipe between two supports can vibrate like a guitar string. Its natural frequency must stay clear of the frequencies the propeller
          and engine shake the ship at, or it resonates and cracks its welds.
        </p>
        <FrequencyChart natural={s.natural_hz} excitations={s.excitations} margin={0.2} />
        <Working steps={s.steps as WorkingStep[]} />
      </div>
    );
  }

  if (part === "stabilizer" && stage === "shackle") {
    const h = last(events, "hydro");
    if (!h) return <Waiting />;
    return (
      <div className="stack gap-3">
        <p className="muted">
          NEMO's panel method works out the pressure all round the foil section at the angle that gives the same lift. The suction peak near the
          nose sets where cavitation starts.
        </p>
        <PressureChart upper={h.upper} lower={h.lower} cavitation={h.cavitation_number} />
        <dl className="kv">
          <dt>Lowest pressure coefficient</dt><dd>{n1(h.cp_min, 2)}</dd>
          <dt>Cavitation number at the fin depth</dt><dd>{n1(h.cavitation_number, 2)}</dd>
          <dt>Section angle for the same lift</dt><dd>{n1(h.section_angle_deg)}°</dd>
        </dl>
      </div>
    );
  }

  if (stage === "forces") {
    if (!loads) return <Waiting />;
    const d = designFor(target) ?? designFor() ?? GENERIC;
    return (
      <div className="stack gap-3">
        <div className="view-split">
          <ForceDiagram outline={outline2d(d)} holeHeight={d.hole_height_mm} holeDiameter={d.hole_diameter_mm}
            angle={loads.sling_angle_deg} F={loads.sling_force_n} V={loads.vertical_n} H={loads.horizontal_n} />
          <p className="muted">
            The weight of the load is shared between the lifting points, then the sling angle turns the vertical share into a
            larger force along each sling. That force, F, is what every check on the padeye has to carry.
          </p>
        </div>
        <Working steps={loads.steps as WorkingStep[]} />
      </div>
    );
  }

  if (stage === "shackle") {
    const s = last(events, "shackles");
    if (!s) return <Waiting />;
    return (
      <div className="stack gap-2">
        <p className="muted">{s.rule} The sling force on each padeye is {n1(s.sling_force_t, 2)} t.</p>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr><th>Shackle</th><th className="r">Rated (WLL)</th><th className="r">Pin</th><th className="r">Jaw</th><th className="r">Hole drilled</th></tr>
            </thead>
            <tbody>
              {s.candidates.map((c: { label: string; wll_t: number; pin_diameter_mm: number; jaw_width_mm: number; hole_mm: number }, i: number) => (
                <tr key={c.label} className={i === 0 ? "row-strong" : undefined}>
                  <td>{c.label}{i === 0 ? " (smallest that covers the load)" : ""}</td>
                  <td className="r">{c.wll_t} t</td>
                  <td className="r">{c.pin_diameter_mm} mm</td>
                  <td className="r">{c.jaw_width_mm} mm</td>
                  <td className="r">{c.hole_mm} mm</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="caption">Hole = pin + the larger of 1 mm and 4%, rounded up to 0.5 mm. Larger shackles are tried only if the smallest cannot give a design.</p>
      </div>
    );
  }

  if (stage === "search") {
    const start = target ? last(events, "search_start", target) : last(events, "search_start");
    const key = target ?? start?.target;
    if (!key) return <Waiting />;
    const found = last(events, "design_found", key);
    const combos = events.filter((e) => e.kind === "combination" && e.target === key).slice(-6).reverse();
    const points = pointsFor(events, key);
    return (
      <div className="stack gap-2">
        <p className="muted">
          {TARGET_NAMES[key]} design: every check at or below {Math.round((start?.max_use ?? 1) * 100)}% of its limit.{" "}
          {part === "padeye" ? "For each plate and cheek combination, a Nelder-Mead search varies the head radius, base length and cheek radius to find the least steel."
            : part === "pipe-bracket" ? "For each pair of seat and knee plates, a Nelder-Mead search varies the knee depth and seat width to find the least steel."
            : "For each pair of skin and web plates, NEMO tries every rib spacing from 150 to 1000 mm and sizes the stock to the rules."}{" "}
          Each dot is one design it tried.
        </p>
        <DesignSpaceChart points={points} limit={start?.max_use ?? 1}
          chosen={found ? [{ mass: found.mass_kg, use: found.max_use, label: `${n1(found.mass_kg, 2)} kg` }] : undefined} />
        {combos.length > 0 && (
          <div className="table-wrap">
            <table className="data">
              <thead><tr><th>Combination</th><th>{part === "padeye" ? "Plate" : part === "pipe-bracket" ? "Seat" : "Skin"}</th><th>{part === "padeye" ? "Cheeks" : part === "pipe-bracket" ? "Knees" : "Webs"}</th>{part === "padeye" && <th className="r">Shackle</th>}<th>Outcome</th></tr></thead>
              <tbody>
                {combos.map((c) => (
                  <tr key={c.seq} className={c.outcome === "best" ? "row-strong" : undefined}>
                    <td>{c.index} of {c.count}</td>
                    <td>{c.plate_mm} mm</td>
                    <td>{part !== "padeye" ? `2 × ${c.cheek_mm} mm` : c.cheek_mm ? `2 × ${c.cheek_mm} mm` : "None"}</td>
                    {part === "padeye" && <td className="r">{c.shackle_wll_t} t</td>}
                    <td>{c.outcome === "best" ? `Best so far, ${n1(c.mass_kg, 2)} kg` : c.outcome === "passed" ? `${n1(c.mass_kg, 2)} kg, heavier` : c.outcome === "skipped" ? "Skipped: cannot beat the best" : "No design passes"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  }

  if (stage === "cad") {
    const cads = all(events, "cad").filter((c) => !target || c.target === target);
    if (!cads.length) return <Waiting />;
    return (
      <div className="stack gap-2">
        <p className="muted">
          Each design is built as an exact solid with the OpenCASCADE geometry kernel, the same model exported as STEP. Its
          volume is compared with the formula the mass came from.
        </p>
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>Design</th><th className="r">Solid volume</th><th className="r">Formula volume</th><th className="r">Difference</th><th className="r">Mass</th></tr></thead>
            <tbody>
              {cads.map((c) => (
                <tr key={c.seq}>
                  <td>{TARGET_NAMES[c.target]}</td>
                  <td className="r">{n0(c.volume_mm3)} mm³</td>
                  <td className="r">{n0(c.formula_volume_mm3)} mm³</td>
                  <td className="r">{Math.abs(c.difference * 100) >= 0.01 ? `${n1(c.difference * 100, 2)}%` : `${(c.difference * 100).toExponential(1)}%`}</td>
                  <td className="r">{n1(c.mass_kg, 2)} kg</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (stage === "mesh") {
    const meshes = all(events, "mesh").filter((m) => !target || m.target === target);
    const withSurface = [...meshes].reverse().find((m) => m.surface);
    if (!meshes.length) return <Waiting />;
    const frame = withSurface ? frameOf(withSurface.surface.positions) : null;
    return (
      <div className="stack gap-2">
        {withSurface && frame && (
          <Viewer size={frame.size} centreY={frame.centreY}
            top={<span className="legend">{TARGET_NAMES[withSurface.target]}, coarsest mesh: {n0(withSurface.elements)} elements</span>}>
            <MeshModel mesh={withSurface.surface} />
          </Viewer>
        )}
        <p className="muted">The solid is split into small four-sided elements{part === "padeye" ? ", finer around the hole where the stress changes fastest" : part === "pipe-bracket" ? ", finer next to the bulkhead" : ""}. Each design is solved on three meshes, each finer than the last.</p>
        <MeshTable events={meshes} />
      </div>
    );
  }

  if (stage === "solve") {
    const solves = all(events, "solve").filter((s) => !target || s.target === target);
    const running = last(events, "solve_start", target);
    const s = solves[solves.length - 1];
    if (!s) return running ? <p className="muted">Solving {n0(running.equations)} equations…</p> : <Waiting />;
    return (
      <div className="stack gap-2">
        <p className="muted">
          The stiffness of every element is assembled into one system of {n0(s.equations)} equations, K·u = f, and solved for the
          movement u of every node. The line shows the solver's error shrinking with each iteration ({s.method} solver).
        </p>
        {s.residuals.length > 1 ? <ResidualChart residuals={s.residuals} /> : <p className="muted">Solved directly in one step.</p>}
        <dl className="kv">
          <dt>Design, mesh</dt><dd>{TARGET_NAMES[s.target]}, mesh {s.level}</dd>
          <dt>Equations</dt><dd>{n0(s.equations)}</dd>
          <dt>Iterations</dt><dd>{s.iterations || 1}</dd>
          <dt>Final error, |K·u − f| / |f|</dt><dd>{s.relative_residual.toExponential(1)}</dd>
          <dt>Solve time</dt><dd>{n1(s.seconds)} s</dd>
          <dt>{part === "padeye" ? "Peak stress near the hole" : "Peak stress in the assessed region"}</dt><dd>{n1(s.head_von_mises_mpa)} MPa</dd>
        </dl>
      </div>
    );
  }

  // verify
  const fea = all(events, "fea_done").filter((f) => !target || f.target === target);
  const f = fea[fea.length - 1];
  if (!f) return <Waiting />;
  const lvl = f.levels[f.levels.length - 1];
  const ap = lvl.applied_force_n as number[];
  const re = lvl.reaction_force_n as number[];
  return (
    <div className="stack gap-3">
      <div>
        <h3 className="view-heading">Does the answer depend on the mesh?</h3>
        <p className="muted">
          {part === "padeye" ? "Peak stress near the hole" : "Peak stress"} on each mesh. It changed by <b>{n1(f.convergence_change * 100, 2)}%</b> between the two finest
          meshes; under 5% means the mesh is fine enough.
        </p>
        <ConvergenceChart levels={f.levels} />
      </div>
      <div>
        <h3 className="view-heading">Do the support forces balance the load?</h3>
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th /><th className="r">Along the base</th><th className="r">Through the plate</th><th className="r">Up</th></tr></thead>
            <tbody>
              <tr><td>{part === "padeye" ? "Load applied to the hole" : "Load applied"}</td>{ap.map((v, i) => <td key={i} className="r">{formatKn(v)}</td>)}</tr>
              <tr><td>{part === "padeye" ? "Reaction at the base" : "Reaction at the support"}</td>{re.map((v, i) => <td key={i} className="r">{formatKn(v)}</td>)}</tr>
              <tr className="row-strong"><td>Sum</td>{ap.map((v, i) => <td key={i} className="r">{formatKn(Math.abs(v + re[i]) < 0.5 ? 0 : v + re[i])}</td>)}</tr>
            </tbody>
          </table>
        </div>
        <p className="caption mt-3">Balance error {lvl.reaction_balance_error.toExponential(1)}. The load in the model is the force calculated in step 1.</p>
      </div>
      <p>
        Peak stress {n1(f.head_von_mises_mpa)} MPa against yield {n0(f.yield_strength_mpa)} MPa: safety factor on yield{" "}
        <b>{n1(f.factor_of_safety_on_yield, 2)}</b>.{f.hand_stress_mpa ? `  Hand calculation for the same place: ${n1(f.hand_stress_mpa)} MPa (${f.hand_label}).` : ""}
      </p>
    </div>
  );
}

function MeshTable({ events }: { events: EngEvent[] }) {
  return (
    <div className="table-wrap">
      <table className="data">
        <thead><tr><th>Design</th><th className="r">Mesh</th><th className="r">Element size at hole</th><th className="r">Nodes</th><th className="r">Elements</th></tr></thead>
        <tbody>
          {events.map((m) => (
            <tr key={m.seq}>
              <td>{TARGET_NAMES[m.target]}</td>
              <td className="r">{m.level} of {m.levels}</td>
              <td className="r">{n1(m.hole_size_mm, 2)} mm</td>
              <td className="r">{n0(m.nodes)}</td>
              <td className="r">{n0(m.elements)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Waiting() {
  return <p className="muted">This step has not started yet.</p>;
}

/** The stage the run is working on now, for the live view to follow. */
export function activeStage(stages: Stage[]): StageKey {
  const active = stages.find((s) => s.state === "active");
  if (active) return active.key;
  const done = [...stages].reverse().find((s) => s.state === "done");
  return done?.key ?? "forces";
}
