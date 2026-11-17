import { ArrowLeft, Search } from "lucide-react";
import { PreviewPanel, usePreview } from "../components/PreviewPanel";
import { Select } from "../components/Select";
import { Banner, Field, NumberInput, Segmented, Switch } from "../components/ui";
import { HELP } from "../help";
import type { PadeyeJob, Reference } from "../types";
import { isValid, problems } from "../validate";

export function Assumptions({
  job,
  reference,
  onChange,
  onRun,
  onBack,
  starting,
  error,
}: {
  job: PadeyeJob;
  reference: Reference;
  onChange: (job: PadeyeJob) => void;
  onRun: () => void;
  onBack: () => void;
  starting: boolean;
  error: string | null;
}) {
  const issues = problems(job);
  const valid = isValid(job);
  const { preview, error: previewError, busy } = usePreview(job, valid);

  return (
    <div className="page">
      <div className="step-label">Step 2 of 3</div>
      <h1 className="title">Check the assumptions</h1>
      <p className="lead">These are the safety settings NEMO designs to. The defaults suit most lifts at sea or on deck.</p>

      <div className="split">
        <div className="form">
          <Field label="Design rules">
            <Select
              label="Design rules"
              value={job.rule_set_id}
              onChange={(id) => onChange({ ...job, rule_set_id: id })}
              options={reference.rule_sets.map((r) => ({ value: r.id, label: r.name }))}
            />
            <p className="field-help" style={{ marginTop: 8 }}>
              The vessel's classification society (DNV, Bureau Veritas, Lloyd's Register, ABS) or your lift plan may
              require different rules. Those will be added as options.
            </p>
          </Field>

          <Field label="How predictable is this lift?" help={HELP.category}>
            <Segmented
              label="Design category"
              value={job.design_category}
              onChange={(v) => onChange({ ...job, design_category: v })}
              options={[
                { value: "B", label: "Uncertain or rough (B)" },
                { value: "A", label: "Predictable (A)" },
              ]}
            />
          </Field>

          <Field label="How often will it be used at full load?" help={HELP.serviceClass}>
            <Select
              label="Service class"
              value={job.service_class}
              width={320}
              onChange={(v) => onChange({ ...job, service_class: v })}
              options={[
                { value: 0, label: "Up to 20,000 lifts", hint: "Service class 0" },
                { value: 1, label: "20,000 to 100,000 lifts", hint: "Service class 1" },
                { value: 2, label: "100,000 to 500,000 lifts", hint: "Service class 2" },
                { value: 3, label: "500,000 to 2,000,000 lifts", hint: "Service class 3" },
                { value: 4, label: "More than 2,000,000 lifts", hint: "Service class 4" },
              ]}
            />
          </Field>

          <Field label="Extra dynamic factor" help={HELP.dynamic} error={issues.dynamic}>
            <div style={{ width: 160 }}>
              <NumberInput
                label="Dynamic factor"
                value={job.lift.dynamic_factor}
                step={0.05}
                invalid={!!issues.dynamic}
                onChange={(v) => onChange({ ...job, lift: { ...job.lift, dynamic_factor: v ?? 0 } })}
              />
            </div>
          </Field>

          <Field label="Keep the padeye at least 60% as thick as the shackle jaw" help={HELP.fill}>
            <div className="switch-row" style={{ maxWidth: 420 }}>
              <span className="muted">Recommended</span>
              <Switch label="Fill the shackle jaw" checked={job.fill_shackle_jaw} onChange={(v) => onChange({ ...job, fill_shackle_jaw: v })} />
            </div>
          </Field>

          {error && <Banner kind="error">{error}</Banner>}
          <div className="actions" style={{ marginTop: 16 }}>
            <button className="btn btn-primary" onClick={onRun} disabled={!valid || starting}>
              <Search aria-hidden /> Find designs
            </button>
            <button className="btn btn-ghost" onClick={onBack}>
              <ArrowLeft aria-hidden /> Back
            </button>
          </div>
          <p className="caption">Takes about one to two minutes. It finds three designs, builds their 3D models and runs a stress check on each.</p>
        </div>

        <PreviewPanel job={job} preview={preview} error={previewError} busy={busy} />
      </div>
    </div>
  );
}
