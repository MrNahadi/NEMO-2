import { AlertCircle, CheckCircle2, ChevronRight, CircleHelp, Info, TriangleAlert, XCircle } from "lucide-react";
import { Working } from "./Formula";
import { useState, type ReactNode } from "react";
import type { Check } from "../types";

export function Field({
  label,
  help,
  error,
  children,
}: {
  label: string;
  help?: string;
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
            <CircleHelp />
          </button>
        )}
      </div>
      {open && help && <div className="help-box">{help}</div>}
      <div>{children}</div>
      {error && <div className="field-error">{error}</div>}
    </div>
  );
}

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
        className="input"
        inputMode="decimal"
        aria-label={label}
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

export function Segmented<T extends string | number>({
  options,
  value,
  onChange,
  label,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
  label: string;
}) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map((o) => (
        <button key={String(o.value)} type="button" aria-pressed={o.value === value} onClick={() => onChange(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Switch({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button type="button" role="switch" aria-checked={checked} aria-label={label} className="switch" onClick={() => onChange(!checked)}>
      <span />
    </button>
  );
}

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

export function StatusBadge({ check }: { check: Pick<Check, "passed" | "severity"> }) {
  if (check.passed)
    return (
      <span className="badge badge-pass">
        <CheckCircle2 aria-hidden /> Pass
      </span>
    );
  if (check.severity === "advice")
    return (
      <span className="badge badge-advice">
        <TriangleAlert aria-hidden /> Advice
      </span>
    );
  return (
    <span className="badge badge-fail">
      <XCircle aria-hidden /> Fail
    </span>
  );
}

export function Banner({ kind, children }: { kind: "info" | "error"; children: ReactNode }) {
  return (
    <div className={`banner banner-${kind}`} role={kind === "error" ? "alert" : undefined}>
      {kind === "error" ? <AlertCircle aria-hidden /> : <Info aria-hidden />}
      <div>{children}</div>
    </div>
  );
}

export function UseBar({ utilization, advice }: { utilization: number; advice?: boolean }) {
  const pct = Math.min(utilization, 1.2) / 1.2;
  const cls = utilization > 1 ? (advice ? " advice" : " over") : "";
  return (
    <div className={`bar${cls}`} aria-hidden>
      <span style={{ width: `${pct * 100}%` }} />
    </div>
  );
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
    <div className="check-list">
      {ordered.map((c) => {
        const isOpen = open === c.id;
        return (
          <div key={c.id} className={isOpen ? "check open" : "check"}>
            <button type="button" className="check-row" aria-expanded={isOpen} onClick={() => setOpen(isOpen ? null : c.id)}>
              <span className="check-main">
                <span className="check-title">
                  <ChevronRight aria-hidden className="check-chevron" />
                  {c.title}
                </span>
                {!compact && <span className="check-detail">{c.source}</span>}
              </span>
              <UseBar utilization={c.utilization} advice={c.severity === "advice"} />
              <span className="num">{Math.round(c.utilization * 100)}%</span>
              <span className="check-badge">
                <StatusBadge check={c} />
              </span>
            </button>
            {isOpen && (
              <div className="check-body">
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
