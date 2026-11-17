import { AlertCircle, AlertTriangle, CheckCircle2, ChevronRight, CircleHelp, Info } from "lucide-react";
import { Working } from "./Formula";
import { cloneElement, isValidElement, useId, useState, type ReactElement, type ReactNode } from "react";
import type { Check } from "../types";

/* ------------------------------------------------------------------ Form fields */

/** A question: label-14 strong with an optional help toggle, the control below, an optional hint and error. */
export function Field({
  label,
  help,
  hint,
  error,
  children,
}: {
  label: string;
  help?: string;
  hint?: ReactNode;
  error?: string | null;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="field">
      <div className="field-label">
        <span>{label}</span>
        {help && (
          <button
            type="button"
            className="help-btn"
            aria-expanded={open}
            aria-label={`What does "${label}" mean?`}
            onClick={() => setOpen((o) => !o)}
          >
            <CircleHelp aria-hidden />
          </button>
        )}
      </div>
      {open && help && <div className="help-box">{help}</div>}
      <div>{children}</div>
      {hint && <div className="field-hint">{hint}</div>}
      {error && (
        <div className="field-error" role="alert">
          <AlertCircle aria-hidden />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

/** Number input with a unit suffix. Values in Geist Mono. */
export function NumberInput({
  value,
  onChange,
  unit,
  min,
  max,
  step = 1,
  invalid,
  label,
}: {
  value: number | null;
  onChange: (value: number | null) => void;
  unit?: string;
  min?: number;
  max?: number;
  step?: number;
  invalid?: boolean;
  label: string;
}) {
  const [text, setText] = useState(value === null ? "" : String(value));
  const [lastValue, setLastValue] = useState(value);
  if (value !== lastValue) {
    setLastValue(value);
    if (value !== null && Number(text) !== value) setText(String(value));
  }
  return (
    <div className={`input-wrap${invalid ? " invalid" : ""}`}>
      <input
        className="input input-num"
        inputMode="decimal"
        aria-label={label}
        aria-invalid={invalid || undefined}
        value={text}
        min={min}
        max={max}
        step={step}
        onChange={(e) => {
          const raw = e.target.value.replace(",", ".");
          setText(e.target.value);
          if (raw.trim() === "") return onChange(null);
          const n = Number(raw);
          onChange(Number.isFinite(n) ? n : null);
        }}
      />
      {unit && <span className="unit">{unit}</span>}
    </div>
  );
}

/** Geist Switch: a segmented control for a few mutually exclusive options. */
export function Segmented<T extends string | number>({
  options,
  value,
  onChange,
  label,
  size,
  mono,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
  label: string;
  size?: "small";
  /** Set for numeric options so they render in Geist Mono. */
  mono?: boolean;
}) {
  return (
    <div className={`segmented${size === "small" ? " sm" : ""}${mono ? " mono" : ""}`} role="group" aria-label={label}>
      {options.map((o) => (
        <button key={String(o.value)} type="button" aria-pressed={o.value === value} onClick={() => onChange(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

/** Geist Toggle: an on/off switch. */
export function Switch({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button type="button" role="switch" aria-checked={checked} aria-label={label} className="switch" onClick={() => onChange(!checked)}>
      <span />
    </button>
  );
}

/** Multi-select toggles for stock lists (plate thicknesses). */
export function Chips({
  options,
  selected,
  onToggle,
  format,
}: {
  options: number[];
  selected: number[];
  onToggle: (value: number) => void;
  format: (value: number) => string;
}) {
  return (
    <div className="chips">
      {options.map((o) => (
        <button key={o} type="button" className="chip" aria-pressed={selected.includes(o)} onClick={() => onToggle(o)}>
          {format(o)}
        </button>
      ))}
    </div>
  );
}

/** Geist Choicebox, single select. Arrow keys move between options (native radio group). */
export function Choicebox<T extends string>({
  name,
  legend,
  value,
  onChange,
  options,
  layout = "list",
}: {
  name: string;
  legend: string;
  value: T;
  onChange: (value: T) => void;
  options: { value: T; title: ReactNode; description?: ReactNode; meta?: ReactNode; icon?: ReactNode; disabled?: boolean }[];
  /** "list" stacks the options; "row" puts three side by side. */
  layout?: "list" | "row";
}) {
  return (
    <fieldset className={`choicebox-group${layout === "row" ? " row3" : ""}`}>
      <legend className="sr-only">{legend}</legend>
      {options.map((o) => (
        <label key={o.value} className={`choicebox${o.disabled ? " disabled" : ""}`}>
          <input type="radio" name={name} value={o.value} checked={o.value === value} disabled={o.disabled} onChange={() => onChange(o.value)} />
          {o.icon && <span className="choicebox-icon" aria-hidden>{o.icon}</span>}
          <span className="choicebox-text">
            <span className="choicebox-title">
              <span>{o.title}</span>
              {o.meta !== undefined && <span className="choicebox-meta">{o.meta}</span>}
            </span>
            {o.description && <span className="choicebox-description">{o.description}</span>}
          </span>
          <span className="choicebox-radio" aria-hidden />
        </label>
      ))}
    </fieldset>
  );
}

/* ------------------------------------------------------------------ Status and feedback */

export type Tone = "gray" | "green" | "amber" | "red" | "blue";

export function Badge({ tone = "gray", children, title }: { tone?: Tone; children: ReactNode; title?: string }) {
  return (
    <span className={`badge badge-${tone}`} title={title}>
      {children}
    </span>
  );
}

/** Status dot plus words. Colour only when the status needs attention or is a clear pass. */
export function Status({ tone = "gray", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span className="status">
      <span className={`status-dot ${tone}`} aria-hidden />
      <span>{children}</span>
    </span>
  );
}

/** Kept for screens that show a pass/advice/fail word. */
export function StatusBadge({ check }: { check: Pick<Check, "passed" | "severity"> }) {
  if (check.passed) return <Badge tone="green">Pass</Badge>;
  if (check.severity === "advice") return <Badge tone="amber">Advice</Badge>;
  return <Badge tone="red">Fail</Badge>;
}

type NoteKind = "info" | "error" | "warning" | "success";

/** Geist Note. `Banner` is the older name for the same thing. */
export function Note({
  kind = "info",
  size,
  action,
  children,
  className,
}: {
  kind?: NoteKind;
  size?: "small";
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  const Icon = kind === "error" ? AlertCircle : kind === "warning" ? AlertTriangle : kind === "success" ? CheckCircle2 : Info;
  return (
    <div
      className={`note${kind === "info" ? "" : ` note-${kind}`}${size === "small" ? " note-sm" : ""}${className ? ` ${className}` : ""}`}
      role={kind === "error" ? "alert" : undefined}
    >
      <Icon aria-hidden />
      <div className="note-body">{children}</div>
      {action && <div className="note-action">{action}</div>}
    </div>
  );
}
export function Banner({ kind, children, className }: { kind: "info" | "error"; children: ReactNode; className?: string }) {
  return (
    <Note kind={kind} className={className}>
      {children}
    </Note>
  );
}

/** Geist Progress: determinate bar. */
export function Progress({ value, max = 1, label, tone }: { value: number; max?: number; label: string; tone?: "red" | "green" }) {
  const pct = Math.max(0, Math.min(1, max > 0 ? value / max : 0));
  return (
    <div className={`progress${tone ? ` ${tone}` : ""}`} role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(pct * 100)}>
      <span style={{ width: `${pct * 100}%` }} />
    </div>
  );
}

/** Geist Skeleton: a placeholder block the size of the content that is loading. */
export function Skeleton({ width = "100%", height = 20, radius }: { width?: number | string; height?: number | string; radius?: number }) {
  return <span className="skeleton" aria-hidden style={{ width, height, borderRadius: radius }} />;
}

/** Geist Empty State. */
export function EmptyState({ icon, title, description, action }: { icon: ReactNode; title: string; description: ReactNode; action?: ReactNode }) {
  return (
    <div className="empty-state">
      <span className="empty-state-icon" aria-hidden>{icon}</span>
      <h2 className="empty-state-title">{title}</h2>
      <p className="empty-state-description">{description}</p>
      {action && <div className="actions">{action}</div>}
    </div>
  );
}

/** Geist Tooltip: opens on hover and keyboard focus. Use it to explain why, not what. */
export function Tooltip({ text, children, side = "top" }: { text: ReactNode; children: ReactNode; side?: "top" | "bottom" }) {
  const id = useId();
  return (
    <span className="tooltip-root">
      {isValidElement(children) ? cloneElement(children as ReactElement<{ "aria-describedby"?: string }>, { "aria-describedby": id }) : children}
      <span role="tooltip" id={id} className={`tooltip${side === "bottom" ? " bottom" : ""}`}>
        {text}
      </span>
    </span>
  );
}

/* ------------------------------------------------------------------ Design checks */

/** Use of the limit as a 64 px bar. The track end is 100 %. Gray; amber at >= 90 %; red over 100 %. */
export function UseBar({ utilization }: { utilization: number; advice?: boolean }) {
  const pct = Math.min(Math.max(utilization, 0), 1);
  const cls = utilization > 1 ? " over" : utilization >= 0.9 ? " near" : "";
  return (
    <div className={`bar${cls}`} aria-hidden>
      <span style={{ width: `${pct * 100}%` }} />
    </div>
  );
}

function checkStatus(c: Check): "pass" | "advice" | "fail" {
  return c.passed ? "pass" : c.severity === "advice" ? "advice" : "fail";
}

export function CheckList({
  checks,
  compact = false,
  selected,
  onSelect,
}: {
  checks: Check[];
  compact?: boolean;
  /** The check whose working is open (and whose region is marked on the 3D model). */
  selected?: string | null;
  onSelect?: (id: string | null) => void;
}) {
  const [localOpen, setLocalOpen] = useState<string | null>(null);
  const open = selected === undefined ? localOpen : selected;
  const setOpen = onSelect ?? setLocalOpen;
  const ordered = [...checks].sort((a, b) => {
    const rank = (c: Check) => (c.severity === "required" && c.category === "strength" ? 0 : c.severity === "required" ? 1 : 2);
    return rank(a) - rank(b) || b.utilization - a.utilization;
  });
  return (
    <div className={`check-list${compact ? " compact" : ""}`}>
      <div className="check-head" aria-hidden>
        <span />
        <span>Check</span>
        {!compact && <span>Source</span>}
        <span className="use-head">Use of limit</span>
      </div>
      {ordered.map((c) => {
        const isOpen = open === c.id;
        const status = checkStatus(c);
        const pct = Math.round(c.utilization * 100);
        const tone = c.utilization > 1 ? " over" : c.utilization >= 0.9 ? " near" : "";
        return (
          <div key={c.id} className={isOpen ? "check open" : "check"}>
            <button
              type="button"
              className="check-row"
              aria-expanded={isOpen}
              aria-label={`${c.title}, ${pct}% of the limit${status === "pass" ? ", passes" : status === "advice" ? ", advice" : ", fails"}`}
              onClick={() => setOpen(isOpen ? null : c.id)}
            >
              <ChevronRight aria-hidden className="check-chevron" />
              <span className="check-title" title={c.title}>{c.title}</span>
              {!compact ? (
                <span className="check-detail" title={c.source}>
                  {status !== "pass" && <Badge tone={status === "fail" ? "red" : "amber"}>{status === "fail" ? "Fail" : "Advice"}</Badge>}
                  <span className="check-source">{c.source}</span>
                </span>
              ) : (
                <span>{status !== "pass" && <Badge tone={status === "fail" ? "red" : "amber"}>{status === "fail" ? "Fail" : "Advice"}</Badge>}</span>
              )}
              <UseBar utilization={c.utilization} />
              <span className={`check-pct${tone}`}>{pct}%</span>
            </button>
            {isOpen && (
              <div className="check-body">
                {compact && <p className="caption">{c.source}</p>}
                <p className="muted">{c.explanation}</p>
                <Working
                  steps={c.working ?? []}
                  verdict={
                    <>
                      Demand {formatValue(c.demand, c.unit)} against capacity {formatValue(c.capacity, c.unit)}: use{" "}
                      <b>{(c.utilization * 100).toFixed(1)}%</b> <StatusBadge check={c} />
                    </>
                  }
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ Formatting */

export function formatValue(value: number, unit: string): string {
  if (unit === "N") return formatKn(value);
  if (unit === "ratio") return value.toFixed(3);
  if (unit === "t") return `${value.toFixed(2)} t`;
  return `${value.toLocaleString(undefined, { maximumFractionDigits: 1 })} ${unit}`;
}
export function formatKn(newtons: number): string {
  return `${(newtons / 1000).toLocaleString(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 2 })} kN`;
}

export function formatKg(kg: number): string {
  return kg < 10 ? `${kg.toFixed(2)} kg` : `${kg.toFixed(1)} kg`;
}
