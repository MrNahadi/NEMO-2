import { ArrowLeft, Loader2, Search } from "lucide-react";
import type { ReactNode } from "react";
import { PageHeader, Workspace } from "../components/Page";
import { PreviewPanel, usePreview } from "../components/PreviewPanel";
import { Select } from "../components/Select";
import { Chips, Field, Note, NumberInput, Segmented, Switch } from "../components/ui";
import { HELP_BRACKET as HB, HELP_FIN as HF } from "../help";
import type { BracketJob, FinJob, Reference } from "../types";

interface StepProps<J> {
  job: J;
  reference: Reference;
  onChange: (job: J) => void;
  onNext: () => void;
  onBack: () => void;
  starting?: boolean;
  error?: string | null;
}

export interface FormSection {
  title?: string;
  content: ReactNode;
}

/** A step's form column: one or more titled groups separated by hairlines. */
export function FormSections({ sections }: { sections: FormSection[] }) {
  return (
    <div className="form-stack">
      {sections.map((s, i) => (
        <section key={s.title ?? i} className="form-section">
          {s.title && <h2 className="section-title">{s.title}</h2>}
          <div className="form">{s.content}</div>
        </section>
      ))}
    </div>
  );
}

/** Single number question at the standard 160 px width. */
function Num({ label, value, unit, onChange, help, step }: {
  label: string; value: number; unit?: string; onChange: (v: number) => void; help?: string; step?: number;
}) {
  return (
    <Field label={label} help={help}>
      <div className="w-num">
        <NumberInput label={label} value={value} unit={unit} step={step} onChange={(v) => onChange(v ?? 0)} />
      </div>
    </Field>
  );
}

/** Number question that fills its .field-grid cell (used for related numbers on one row). */
function NumCell({ label, value, unit, onChange, help, step }: {
  label: string; value: number; unit?: string; onChange: (v: number) => void; help?: string; step?: number;
}) {
  return (
    <Field label={label} help={help}>
      <NumberInput label={label} value={value} unit={unit} step={step} onChange={(v) => onChange(v ?? 0)} />
    </Field>
  );
}

/** Captioned small input for rows of related numbers inside a .field-grid. Takes the cell width. The
 *  visible caption names the control (the Field's question is prepended automatically). */
function Mini({ caption, value, unit, step, onChange }: {
  caption: string; value: number; unit?: string; step?: number; onChange: (v: number) => void;
}) {
  return (
    <div className="mini-field">
      <span className="caption">{caption}</span>
      <NumberInput label={caption} value={value} unit={unit} step={step} onChange={(v) => onChange(v ?? 0)} />
    </div>
  );
}

/** Template B workspace for the bracket and fin Describe/Assumptions steps. */
function Layout({ title, lead, sections, job, footer, error }: {
  title: string; lead: string; sections: FormSection[]; job: BracketJob | FinJob; footer: ReactNode; error?: string | null;
}) {
  const { preview, error: previewError, busy } = usePreview(job, true);
  return (
    <Workspace
      header={<PageHeader title={title} description={lead} />}
      aside={<PreviewPanel job={job} preview={preview} error={previewError} busy={busy} />}
      asideLabel="3D preview"
      footer={footer}
    >
      <FormSections sections={sections} />
      {error && (
        <Note kind="error" className="mt-6">
          {error}
        </Note>
      )}
    </Workspace>
  );
}

function NextFooter({ onNext, onBack, disabled, label }: { onNext: () => void; onBack: () => void; disabled?: boolean; label: string }) {
  return (
    <>
      <button className="btn btn-ghost" onClick={onBack}>
        <ArrowLeft aria-hidden /> Back
      </button>
      <button className="btn btn-primary" onClick={onNext} disabled={disabled}>
        {label}
      </button>
    </>
  );
}

function RunFooter({ onRun, onBack, starting, note }: { onRun: () => void; onBack: () => void; starting?: boolean; note: string }) {
  return (
    <>
      <button className="btn btn-ghost" onClick={onBack}>
        <ArrowLeft aria-hidden /> Back
      </button>
      <p className="footer-bar-note">{note}</p>
      <button className="btn btn-primary" onClick={onRun} disabled={starting}>
        {starting ? <Loader2 className="spin" aria-hidden /> : <Search aria-hidden />} Find designs
      </button>
    </>
  );
}

function PlateChips({ job, reference, onChange }: { job: BracketJob | FinJob; reference: Reference; onChange: (t: number[]) => void }) {
  return (
    <Chips
      options={reference.plates.steel_mm.filter((t) => t <= 50)}
      selected={job.plate_thicknesses_mm}
      format={(t) => `${t} mm`}
      onToggle={(t) =>
        onChange(job.plate_thicknesses_mm.includes(t) ? job.plate_thicknesses_mm.filter((x) => x !== t) : [...job.plate_thicknesses_mm, t].sort((a, b) => a - b))
      }
    />
  );
}

const steelOptions = (reference: Reference, families: string[]) =>
  reference.materials.filter((m) => families.includes(m.family)).map((m) => ({
    value: m.id, label: m.name, hint: `Yield ${m.yield_bands[0].yield_strength_mpa} MPa, tensile ${m.tensile_strength_mpa} MPa`,
  }));

// ------------------------------------------------------------------ bracket
export function DescribeBracket({ job, reference, onChange, onNext, onBack }: StepProps<BracketJob>) {
  const set = (patch: Partial<BracketJob>) => onChange({ ...job, ...patch });
  const pipes = reference.piping.pipes;
  const insulated = job.insulation_id !== "none";
  const insulationSelect = (
    <Select label="Insulation" value={job.insulation_id} width={520}
      onChange={(v) => set({ insulation_id: v, insulation_thickness_mm: v === "none" ? 0 : job.insulation_thickness_mm || 50 })}
      options={reference.piping.insulation.map((f) => ({ value: f.id, label: f.name }))} />
  );
  return (
    <Layout title="Describe the pipe" lead="Answer a few questions about the pipe and where it runs. The bracket on the right resizes as you go." job={job}
      sections={[
        {
          title: "The pipe",
          content: (
            <>
              <Field label="Pipe size" help={HB.pipe}>
                <div className="field-grid">
                  <div className="mini-field">
                    <span className="caption">Size</span>
                    <Select label="Pipe size" value={job.pipe_nps}
                      options={pipes.map((p) => ({ value: p.nps, label: `NPS ${p.nps} (DN ${p.dn})`, hint: `${p.od_mm} mm outside` }))}
                      onChange={(v) => set({ pipe_nps: v })} />
                  </div>
                  <div className="mini-field">
                    <span className="caption">Wall</span>
                    <Segmented label="Wall" value={job.schedule} onChange={(v) => set({ schedule: v })}
                      options={[{ value: "STD", label: "Standard" }, { value: "XS", label: "Extra strong" }]} />
                  </div>
                </div>
              </Field>
              <Field label="Pipe material">
                <Select label="Pipe material" value={job.pipe_material_id} width={520} onChange={(v) => set({ pipe_material_id: v })}
                  options={reference.piping.pipe_materials.map((m) => ({ value: m.id, label: m.name }))} />
              </Field>
              <Field label="What is in the pipe?" help={HB.contents}>
                <Select label="Pipe contents" value={job.fluid_id} width={520} onChange={(v) => set({ fluid_id: v })}
                  options={reference.piping.fluids.map((f) => ({ value: f.id, label: f.name, hint: f.density_kg_m3 ? `${f.density_kg_m3} kg/m³` : undefined }))} />
              </Field>
              <Field label="Insulation" help={HB.insulation}>
                {insulated ? (
                  <div className="field-grid">
                    {insulationSelect}
                    <Mini caption="Thickness" value={job.insulation_thickness_mm} unit="mm"
                      onChange={(v) => set({ insulation_thickness_mm: v })} />
                  </div>
                ) : (
                  insulationSelect
                )}
              </Field>
              <Num label="Distance to the next supports" value={job.span_m} unit="m" step={0.1} help={HB.span} onChange={(v) => set({ span_m: v })} />
              <Field label="Which way does the pipe run?" help={HB.direction}>
                <Segmented label="Pipe direction" value={job.pipe_direction} onChange={(v) => set({ pipe_direction: v })}
                  options={[{ value: "fore_aft", label: "Fore and aft" }, { value: "athwartships", label: "Athwartships" }]} />
              </Field>
            </>
          ),
        },
        {
          title: "The bracket",
          content: (
            <>
              <Num label="Gap between the bulkhead and the pipe" value={job.gap_mm} unit="mm" help={HB.gap} onChange={(v) => set({ gap_mm: v })} />
              <Field label="Bracket material" help={HB.material}>
                <Select label="Bracket material" value={job.material_id} width={520} onChange={(v) => set({ material_id: v })} options={steelOptions(reference, ["steel", "stainless"])} />
              </Field>
              <Field label="Which plate thicknesses does your workshop have?" help={HB.plates}>
                <PlateChips job={job} reference={reference} onChange={(t) => set({ plate_thicknesses_mm: t })} />
              </Field>
              <details className="more">
                <summary>More about the support</summary>
                <div className="form">
                  <div className="field-grid">
                    <NumCell label="Continuity factor" value={job.continuity_factor} step={0.05} help={HB.continuity} onChange={(v) => set({ continuity_factor: v })} />
                    <NumCell label="Friction between pipe and bracket" value={job.friction} step={0.05} help={HB.friction} onChange={(v) => set({ friction: v })} />
                  </div>
                  <Field label="U-bolt material" help={HB.ubolt}>
                    <Select label="U-bolt material" value={job.ubolt_grade_id} width={520} onChange={(v) => set({ ubolt_grade_id: v })}
                      options={reference.piping.ubolt_grades.map((g) => ({ value: g.id, label: g.name }))} />
                  </Field>
                </div>
              </details>
            </>
          ),
        },
      ]}
      footer={<NextFooter onNext={onNext} onBack={onBack} disabled={job.plate_thicknesses_mm.length === 0} label="Next: ship motion and vibration" />}
    />
  );
}

export function BracketAssumptions({ job, reference, onChange, onNext, onBack, starting, error }: StepProps<BracketJob>) {
  const set = (patch: Partial<BracketJob>) => onChange({ ...job, ...patch });
  const rules = reference.rule_sets.filter((r) => (reference.part_rule_sets["pipe-bracket"] ?? []).includes(r.id));
  return (
    <Layout title="Ship motion and vibration" lead="How the ship moves and shakes where this pipe runs. Replace the starting values with the ones for your vessel." job={job} error={error}
      sections={[
        {
          title: "Motion and vibration",
          content: (
            <>
              <Field label="Ship-motion accelerations" help={HB.accel}>
                <div className="field-grid field-grid-3">
                  <Mini caption="Vertical, extra" value={job.accel_vertical_g} unit="g" step={0.1} onChange={(v) => set({ accel_vertical_g: v })} />
                  <Mini caption="Athwartships" value={job.accel_transverse_g} unit="g" step={0.1} onChange={(v) => set({ accel_transverse_g: v })} />
                  <Mini caption="Fore and aft" value={job.accel_longitudinal_g} unit="g" step={0.1} onChange={(v) => set({ accel_longitudinal_g: v })} />
                </div>
              </Field>
              <Field label="Propeller" help={HB.propeller}>
                <div className="field-grid">
                  <Mini caption="Speed" value={job.propeller_rpm} unit="rpm" onChange={(v) => set({ propeller_rpm: v })} />
                  <Mini caption="Blades" value={job.propeller_blades} unit="blades" onChange={(v) => set({ propeller_blades: Math.round(v) })} />
                </div>
              </Field>
              <Field label="Main engine" help={HB.engine}>
                <div className="field-grid">
                  <Mini caption="Speed" value={job.engine_rpm} unit="rpm" onChange={(v) => set({ engine_rpm: v })} />
                  <Mini caption="Cylinders" value={job.engine_cylinders} unit="cyl." onChange={(v) => set({ engine_cylinders: Math.round(v) })} />
                  <div className="mini-field grid-span">
                    <span className="caption">Engine type</span>
                    <Segmented label="Engine type" value={job.engine_stroke} onChange={(v) => set({ engine_stroke: v })}
                      options={[{ value: 4, label: "4-stroke" }, { value: 2, label: "2-stroke" }]} />
                  </div>
                </div>
              </Field>
            </>
          ),
        },
        {
          title: "Limits and rules",
          content: (
            <>
              <Num label="Keep the pipe's frequency this far from every excitation" value={Math.round(job.frequency_margin * 100)} unit="%" help={HB.margin}
                onChange={(v) => set({ frequency_margin: v / 100 })} />
              <Num label="Largest bracket deflection" value={job.deflection_limit_mm} unit="mm" step={0.1} help={HB.deflection} onChange={(v) => set({ deflection_limit_mm: v })} />
              <Field
                label="Design rules"
                hint="ASME BTH-1 is for lifting devices, so pipe supports use the AISC 360 steel rules. Class rules (DNV, BV, LR, ABS) can be added the same way."
              >
                <Select label="Design rules" value={job.rule_set_id} width={520} onChange={(v) => set({ rule_set_id: v })} options={rules.map((r) => ({ value: r.id, label: r.name }))} />
              </Field>
              <details className="more">
                <summary>Advanced settings</summary>
                <div className="form">
                  <Field label="Allow for the bracket bending in the vibration check" help={HB.flexibility}>
                    <div className="switch-row">
                      <span className="muted">Pipe and brackets checked together</span>
                      <Switch label="Pipe and brackets checked together" checked={job.include_bracket_flexibility ?? true}
                        onChange={(v) => set({ include_bracket_flexibility: v })} />
                    </div>
                  </Field>
                </div>
              </details>
            </>
          ),
        },
      ]}
      footer={
        <RunFooter onRun={onNext} onBack={onBack} starting={starting}
          note="Takes about half a minute." />
      }
    />
  );
}

// ---------------------------------------------------------------------- fin
export function DescribeFin({ job, reference, onChange, onNext, onBack }: StepProps<FinJob>) {
  const set = (patch: Partial<FinJob>) => onChange({ ...job, ...patch });
  return (
    <Layout title="Describe the fin" lead="The outer shape of the fin and how it is used. NEMO designs the structure inside it." job={job}
      sections={[
        {
          title: "The fin",
          content: (
            <>
              <Num label="Ship speed" value={job.speed_kn} unit="knots" help={HF.speed} onChange={(v) => set({ speed_kn: v })} />
              <Field label="Fin size" help={HF.size}>
                <div className="field-grid">
                  <Mini caption="Span" value={job.span_m} unit="m" step={0.1} onChange={(v) => set({ span_m: v })} />
                  <Mini caption="Chord" value={job.chord_m} unit="m" step={0.1} onChange={(v) => set({ chord_m: v })} />
                </div>
              </Field>
              <Field label="Foil thickness" help={HF.thickness} hint="NACA 00 series section, thickness as a share of the chord.">
                <Segmented mono label="Foil thickness" value={Math.round(job.thickness_ratio * 100)} onChange={(v) => set({ thickness_ratio: v / 100 })}
                  options={[12, 15, 18, 20, 25].map((t) => ({ value: t, label: `${t}%` }))} />
              </Field>
              <div className="field-grid">
                <NumCell label="Largest fin angle" value={job.max_angle_deg} unit="deg" help={HF.angle} onChange={(v) => set({ max_angle_deg: v })} />
                <NumCell label="Stock position" value={Math.round(job.stock_position * 100)} unit="% chord" help={HF.stock}
                  onChange={(v) => set({ stock_position: v / 100 })} />
              </div>
              <Field label="Depth and draught" hint={`${HF.depth} ${HF.draught}`}>
                <div className="field-grid">
                  <Mini caption="Fin depth below water" value={job.depth_m} unit="m" step={0.5} onChange={(v) => set({ depth_m: v })} />
                  <Mini caption="Ship draught" value={job.draught_m} unit="m" step={0.5} onChange={(v) => set({ draught_m: v })} />
                </div>
              </Field>
              <Num label="Fin root to the outer stock bearing" value={job.bearing_gap_mm} unit="mm" help={HF.gap} onChange={(v) => set({ bearing_gap_mm: v })} />
            </>
          ),
        },
        {
          title: "Materials and stock",
          content: (
            <>
              <Field label="Materials" help={HF.material}>
                <div className="stack gap-3">
                  <div className="mini-field">
                    <span className="caption" aria-hidden>Skin, spars and ribs</span>
                    <Select label="Skin, spars and ribs" value={job.material_id} width={520} onChange={(v) => set({ material_id: v })} options={steelOptions(reference, ["steel"])} />
                  </div>
                  <div className="mini-field">
                    <span className="caption" aria-hidden>Stock</span>
                    <Select label="Stock" value={job.stock_material_id} width={520} onChange={(v) => set({ stock_material_id: v })} options={steelOptions(reference, ["forging", "steel"])} />
                  </div>
                </div>
              </Field>
              <Field label="Which plate thicknesses does your workshop have?" help={HB.plates}>
                <PlateChips job={job} reference={reference} onChange={(t) => set({ plate_thicknesses_mm: t })} />
              </Field>
            </>
          ),
        },
      ]}
      footer={<NextFooter onNext={onNext} onBack={onBack} disabled={job.plate_thicknesses_mm.length === 0} label="Next: check the assumptions" />}
    />
  );
}

export function FinAssumptions({ job, reference, onChange, onNext, onBack, starting, error }: StepProps<FinJob>) {
  const set = (patch: Partial<FinJob>) => onChange({ ...job, ...patch });
  const rules = reference.rule_sets.filter((r) => (reference.part_rule_sets["stabilizer"] ?? []).includes(r.id));
  return (
    <Layout title="Check the assumptions" lead="The internal layout and the limits NEMO designs to." job={job} error={error}
      sections={[
        {
          content: (
            <>
              <Field label="Spar positions" help={HF.spars}>
                <div className="field-grid">
                  <Mini caption="Front spar" value={Math.round(job.front_spar * 100)} unit="% chord" onChange={(v) => set({ front_spar: v / 100 })} />
                  <Mini caption="Rear spar" value={Math.round(job.rear_spar * 100)} unit="% chord" onChange={(v) => set({ rear_spar: v / 100 })} />
                </div>
              </Field>
              <Num label="Largest tip deflection" value={job.deflection_limit_mm} unit="mm" help={HF.deflection} onChange={(v) => set({ deflection_limit_mm: v })} />
              <Field
                label="Design rules"
                hint="A stabilizer fin turns on a stock like a spade rudder, so NEMO uses the IACS rudder requirements for its stresses and plating."
              >
                <Select label="Design rules" value={job.rule_set_id} width={520} onChange={(v) => set({ rule_set_id: v })} options={rules.map((r) => ({ value: r.id, label: r.name }))} />
              </Field>
              <details className="more">
                <summary>Advanced settings: going astern and the stock bearings</summary>
                <div className="form">
                  <p className="field-help">The defaults suit most fins. Turn on the bearing check once you know where the bearings go.</p>
                  <Field label="Check the stock going astern" help={HF.astern}>
                    <div className="switch-row">
                      <span className="muted">UR S10 astern condition</span>
                      <Switch label="UR S10 astern condition" checked={job.include_astern ?? true} onChange={(v) => set({ include_astern: v })} />
                    </div>
                  </Field>
                  {(job.include_astern ?? true) && (
                    <Num label="Astern speed (0 = half the ahead speed)" value={job.astern_speed_kn ?? 0} unit="knots" help={HF.asternSpeed}
                      onChange={(v) => set({ astern_speed_kn: v })} />
                  )}
                  <Field label="Size the stock bearings" help={HF.bearings}>
                    <div className="switch-row">
                      <span className="muted">Bearing lengths to UR S10</span>
                      <Switch label="Bearing lengths to UR S10" checked={job.check_bearings ?? false} onChange={(v) => set({ check_bearings: v })} />
                    </div>
                  </Field>
                  {job.check_bearings && (
                    <>
                      <Num label="Distance between the two stock bearings" value={job.bearing_spacing_mm ?? 800} unit="mm" help={HF.bearingSpacing}
                        onChange={(v) => set({ bearing_spacing_mm: v })} />
                      <Field label="Bearing material">
                        <Select label="Bearing material" value={job.bearing_material ?? "synthetic"} width={520} onChange={(v) => set({ bearing_material: v as FinJob["bearing_material"] })}
                          options={[
                            { value: "synthetic", label: "Synthetic, harder than 60 Shore D", hint: "5.5 N/mm²" },
                            { value: "bronze", label: "Steel or bronze", hint: "7.0 N/mm²" },
                            { value: "white_metal", label: "White metal, oil lubricated", hint: "4.5 N/mm²" },
                            { value: "lignum", label: "Lignum vitae", hint: "2.5 N/mm²" },
                          ]} />
                      </Field>
                    </>
                  )}
                </div>
              </details>
            </>
          ),
        },
      ]}
      footer={
        <RunFooter onRun={onNext} onBack={onBack} starting={starting}
          note="Takes about a minute." />
      }
    />
  );
}
