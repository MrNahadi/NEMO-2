import { ArrowLeft } from "lucide-react";
import { useState } from "react";
import { PageHeader, Workspace } from "../components/Page";
import { PreviewPanel, usePreview } from "../components/PreviewPanel";
import { Select } from "../components/Select";
import { Chips, Field, NumberInput, Segmented, Switch } from "../components/ui";
import { HELP } from "../help";
import type { PadeyeJob, Reference } from "../types";
import { isValid, problems } from "../validate";
import { FormSections } from "./PartForms";

export function DescribeLift({
  job,
  reference,
  onChange,
  onNext,
  onBack,
}: {
  job: PadeyeJob;
  reference: Reference;
  onChange: (job: PadeyeJob) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  const [unit, setUnit] = useState<"kg" | "t">(job.lift.lifted_mass_kg >= 1000 ? "t" : "kg");
  const issues = problems(job);
  const valid = isValid(job);
  const { preview, error, busy } = usePreview(job, valid);
  const lift = job.lift;
  const setLift = (patch: Partial<PadeyeJob["lift"]>) => onChange({ ...job, lift: { ...lift, ...patch } });
  const material = reference.materials.find((m) => m.id === job.material_id);
  const stock = material?.family === "aluminium" ? reference.plates.aluminium_mm : reference.plates.steel_mm;
  const massShown = unit === "t" ? round(lift.lifted_mass_kg / 1000, 3) : lift.lifted_mass_kg;

  return (
    <Workspace
      header={
        <PageHeader
          title="Describe the lift"
          description="Answer a few questions. The padeye on the right resizes as you go."
        />
      }
      aside={<PreviewPanel job={job} preview={preview} error={error} busy={busy} />}
      asideLabel="3D preview"
      footer={
        <>
          <button className="btn btn-ghost" onClick={onBack}>
            <ArrowLeft aria-hidden /> Back
          </button>
          <button className="btn btn-primary" onClick={onNext} disabled={!valid}>
            Next: check the assumptions
          </button>
        </>
      }
    >
      <FormSections
        sections={[
          {
            title: "The load",
            content: (
              <>
                <Field label="How heavy is the load?" help={HELP.mass} error={issues.mass}>
                  <div className="row">
                    <div className="w-num">
                      <NumberInput
                        label="Load weight"
                        value={massShown}
                        unit={unit}
                        invalid={!!issues.mass}
                        onChange={(v) => setLift({ lifted_mass_kg: v === null ? 0 : unit === "t" ? v * 1000 : v })}
                      />
                    </div>
                    <Segmented
                      label="Weight unit"
                      value={unit}
                      onChange={setUnit}
                      options={[
                        { value: "kg", label: "kg" },
                        { value: "t", label: "tonnes" },
                      ]}
                    />
                  </div>
                </Field>

                <Field label="How many lifting points?" help={HELP.points} error={issues.points}>
                  <Segmented
                    mono
                    label="Lifting points"
                    value={lift.lift_points}
                    onChange={(n) =>
                      setLift({ lift_points: n, points_carrying: lift.points_carrying && lift.points_carrying > n ? null : lift.points_carrying })
                    }
                    options={[1, 2, 3, 4, 6, 8].map((n) => ({ value: n, label: String(n) }))}
                  />
                </Field>

                <Field label="Sling angle from horizontal" help={HELP.slingAngle} error={issues.angle}>
                  <div className="row">
                    <input
                      className="range"
                      type="range"
                      min={30}
                      max={90}
                      step={1}
                      aria-label="Sling angle from horizontal"
                      value={Math.min(Math.max(lift.sling_angle_deg, 30), 90)}
                      onChange={(e) => setLift({ sling_angle_deg: Number(e.target.value) })}
                    />
                    <div className="w-num">
                      <NumberInput
                        label="Sling angle in degrees"
                        value={lift.sling_angle_deg}
                        unit="deg"
                        invalid={!!issues.angle}
                        onChange={(v) => setLift({ sling_angle_deg: v ?? 0 })}
                      />
                    </div>
                  </div>
                </Field>
              </>
            ),
          },
          {
            title: "Material and stock",
            content: (
              <>
                <Field label="Material" help={HELP.material}>
                  <Select
                    label="Material"
                    value={job.material_id}
                    width={520}
                    options={reference.materials.map((m) => ({
                      value: m.id,
                      label: m.name,
                      hint: `Yield ${m.yield_bands[0].yield_strength_mpa} MPa, tensile ${m.tensile_strength_mpa} MPa`,
                    }))}
                    onChange={(id) => {
                      const next = reference.materials.find((m) => m.id === id);
                      const nextStock = next?.family === "aluminium" ? reference.plates.aluminium_mm : reference.plates.steel_mm;
                      onChange({
                        ...job,
                        material_id: id,
                        plate_thicknesses_mm: job.plate_thicknesses_mm.filter((t) => nextStock.includes(t)),
                      });
                    }}
                  />
                </Field>

                <Field label="Which plate thicknesses does your workshop have?" help={HELP.plates} error={issues.plates}>
                  <Chips
                    options={stock}
                    selected={job.plate_thicknesses_mm}
                    format={(t) => `${t} mm`}
                    onToggle={(t) =>
                      onChange({
                        ...job,
                        plate_thicknesses_mm: job.plate_thicknesses_mm.includes(t)
                          ? job.plate_thicknesses_mm.filter((x) => x !== t)
                          : [...job.plate_thicknesses_mm, t].sort((a, b) => a - b),
                      })
                    }
                  />
                </Field>

                <Field label="Allow cheek plates" help={HELP.cheeks}>
                  <div className="switch-row">
                    <span className="muted">Rings welded around the hole to make it thicker</span>
                    <Switch
                      label="Rings welded around the hole to make it thicker"
                      checked={job.allow_cheek_plates}
                      onChange={(v) => onChange({ ...job, allow_cheek_plates: v })}
                    />
                  </div>
                </Field>

                <details className="more">
                  <summary>Advanced settings: sling direction and load sharing</summary>
                  <div className="form">
                    <p className="field-help">Leave these alone for a simple lift with the padeyes facing their slings.</p>
                    <Field label="How many points carry the load?" help={HELP.carrying} error={issues.carrying}>
                      <Segmented
                        mono
                        label="Points carrying the load"
                        value={lift.points_carrying ?? lift.lift_points}
                        onChange={(n) => setLift({ points_carrying: n === lift.lift_points ? null : n })}
                        options={Array.from({ length: lift.lift_points }, (_, i) => i + 1).map((n) => ({
                          value: n,
                          label: n === lift.lift_points ? `All ${n}` : String(n),
                        }))}
                      />
                    </Field>
                    <Field label="Sideways pull allowance" help={HELP.side} error={issues.side}>
                      <div className="w-num">
                        <NumberInput
                          label="Sideways pull in percent"
                          value={round(lift.side_load_fraction * 100, 2)}
                          unit="%"
                          invalid={!!issues.side}
                          onChange={(v) => setLift({ side_load_fraction: (v ?? -1) / 100 })}
                        />
                      </div>
                    </Field>
                    <Field label="Angle between the sling and the padeye plate, seen from above" help={HELP.oblique} error={issues.oblique}>
                      <div className="w-num">
                        <NumberInput
                          label="Out-of-plane sling angle in degrees"
                          value={lift.out_of_plane_angle_deg ?? 0}
                          unit="deg"
                          invalid={!!issues.oblique}
                          onChange={(v) => setLift({ out_of_plane_angle_deg: v ?? 0 })}
                        />
                      </div>
                    </Field>
                  </div>
                </details>
              </>
            ),
          },
        ]}
      />
    </Workspace>
  );
}

function round(value: number, digits: number): number {
  const f = 10 ** digits;
  return Math.round(value * f) / f;
}
