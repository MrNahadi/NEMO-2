import { AlertCircle, AlertTriangle, ArrowDown, ArrowUpDown, Check as CheckIcon, CheckCircle2, ChevronRight, CircleHelp, Info, Loader2, RotateCw } from "lucide-react";
import { Working } from "./Formula";
import {
  cloneElement,
  createContext,
  isValidElement,
  useContext,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactElement,
  type ReactNode,
} from "react";
import type { Check } from "../types";

/* ------------------------------------------------------------------ Form fields */

/** What a Field tells the controls inside it: the id of its visible question, the ids of its hint, help
 *  and error (for aria-describedby), and the question text. Controls read it so the visible question is
 *  their accessible name and the hint, help, unit and error are their description. */
interface FieldInfo {
  label: string;
  labelId: string;
  describedBy?: string;
  invalid?: boolean;
}
const FieldContext = createContext<FieldInfo | null>(null);

/** Accessible name and description for a control. Inside a Field the visible question names it; when the
 *  control's own label differs (one of several inputs under one question), that label is added after the
 *  question through a hidden span, so the name is "How heavy is the load? Load weight". */
export function useControlA11y(label: string, extraDescribedBy?: string) {
  const field = useContext(FieldContext);
  const ownId = useId();
  const describedBy = [field?.describedBy, extraDescribedBy].filter(Boolean).join(" ") || undefined;
  if (!field) return { props: { "aria-label": label, "aria-describedby": describedBy }, own: null };
  const differs = label.trim().toLowerCase() !== field.label.trim().toLowerCase();
  return {
    props: { "aria-labelledby": differs ? `${field.labelId} ${ownId}` : field.labelId, "aria-describedby": describedBy },
    own: differs ? (
      <span id={ownId} hidden>
        {label}
      </span>
    ) : null,
  };
}

/** A question: label-14 strong with an optional help toggle right after the text, the control below, an
 *  optional hint (8 px under the control) and error. The question, help, hint and error are tied to the
 *  control inside for assistive technology. */
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
  const id = useId();
  const labelId = `${id}-label`;
  const helpId = `${id}-help`;
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const describedBy = [error ? errorId : null, hint ? hintId : null, open && help ? helpId : null].filter(Boolean).join(" ") || undefined;
  return (
    <div className="field" role="group" aria-labelledby={labelId}>
      <div className="field-label">
        <span id={labelId}>{label}</span>
        {help && (
          <button
            type="button"
            className="help-btn"
            aria-expanded={open}
            aria-controls={open ? helpId : undefined}
            aria-label={`What does "${label}" mean?`}
            onClick={() => setOpen((o) => !o)}
          >
            <CircleHelp aria-hidden />
          </button>
        )}
      </div>
      {open && help && (
        <div className="help-box" id={helpId}>
          {help}
        </div>
      )}
      <FieldContext.Provider value={{ label, labelId, describedBy, invalid: !!error }}>
        <div className="field-control">{children}</div>
      </FieldContext.Provider>
      {hint && (
        <div className="field-hint" id={hintId}>
          {hint}
        </div>
      )}
      {error && (
        <div className="field-error" role="alert" id={errorId}>
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
  const unitId = useId();
  const a11y = useControlA11y(label, unit ? unitId : undefined);
  if (value !== lastValue) {
    setLastValue(value);
    if (value !== null && Number(text) !== value) setText(String(value));
  }
  return (
    <div className={`input-wrap${invalid ? " invalid" : ""}`}>
      <input
        className="input input-num"
        inputMode="decimal"
        {...a11y.props}
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
      {unit && (
        <span className="unit" id={unitId}>
          {unit}
        </span>
      )}
      {a11y.own}
    </div>
  );
}

/** Roving focus for a group of buttons: one tab stop for the whole group, arrow keys (and Home/End) move
 *  between the items. Returns the index the key lands on, or -1 when the key is not a move. */
export function rovingIndex(e: KeyboardEvent, current: number, count: number): number {
  const prev = e.key === "ArrowLeft" || e.key === "ArrowUp";
  const next = e.key === "ArrowRight" || e.key === "ArrowDown";
  if (!prev && !next && e.key !== "Home" && e.key !== "End") return -1;
  e.preventDefault();
  if (e.key === "Home") return 0;
  if (e.key === "End") return count - 1;
  return (current + (next ? 1 : -1) + count) % count;
}

/** Geist Switch: a segmented control for a few mutually exclusive options. A radio group: one tab stop
 *  (the selected option), arrow keys move and select, as Geist's Switch does. */
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
  const a11y = useControlA11y(label);
  const root = useRef<HTMLDivElement>(null);
  const selected = Math.max(0, options.findIndex((o) => o.value === value));
  return (
    <div
      ref={root}
      className={`segmented${size === "small" ? " sm" : ""}${mono ? " mono" : ""}`}
      role="radiogroup"
      {...a11y.props}
      onKeyDown={(e) => {
        const i = rovingIndex(e, selected, options.length);
        if (i < 0) return;
        onChange(options[i].value);
        root.current?.querySelectorAll<HTMLButtonElement>("[role=radio]")[i]?.focus();
      }}
    >
      {a11y.own}
      {options.map((o, i) => (
        <button
          key={String(o.value)}
          type="button"
          role="radio"
          aria-checked={i === selected}
          tabIndex={i === selected ? 0 : -1}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

/** Geist Toggle: an on/off switch. */
export function Switch({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  const a11y = useControlA11y(label);
  return (
    <>
      <button type="button" role="switch" aria-checked={checked} {...a11y.props} className="switch" onClick={() => onChange(!checked)}>
        <span />
      </button>
      {a11y.own}
    </>
  );
}

/** Multi-select toggles for stock lists (plate thicknesses): a group of checkboxes with one tab stop.
 *  Arrow keys (and Home/End) move between chips, Space or Enter toggles the focused one. Selected chips have
 *  a gray-1000 edge and a check mark, not a solid fill, so a long list never outweighs the primary button. */
export function Chips({
  options,
  selected,
  onToggle,
  format,
  label,
}: {
  options: number[];
  selected: number[];
  onToggle: (value: number) => void;
  format: (value: number) => string;
  /** Name of the group when the chips are not inside a Field. */
  label?: string;
}) {
  const field = useContext(FieldContext);
  const [focus, setFocus] = useState(0);
  const root = useRef<HTMLDivElement>(null);
  const current = Math.min(focus, options.length - 1);
  return (
    <div
      ref={root}
      className="chips"
      role="group"
      aria-labelledby={field?.labelId}
      aria-label={field ? undefined : label}
      aria-describedby={field?.describedBy}
      onKeyDown={(e) => {
        const i = rovingIndex(e, current, options.length);
        if (i < 0) return;
        setFocus(i);
        root.current?.querySelectorAll<HTMLButtonElement>("[role=checkbox]")[i]?.focus();
      }}
    >
      {options.map((o, i) => {
        const on = selected.includes(o);
        return (
          <button
            key={o}
            type="button"
            role="checkbox"
            className="chip"
            aria-checked={on}
            tabIndex={i === current ? 0 : -1}
            onFocus={() => setFocus(i)}
            onClick={() => onToggle(o)}
          >
            {on && <CheckIcon aria-hidden className="chip-check" />}
            <span>{format(o)}</span>
          </button>
        );
      })}
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

/** Status dot plus words. Colour only when the status needs attention or is a clear pass. `hollow` draws an
 *  outline dot for "nothing yet" (Not run yet), so it reads differently from a filled dot. */
export function Status({ tone = "gray", hollow, children }: { tone?: Tone; hollow?: boolean; children: ReactNode }) {
  return (
    <span className="status">
      <span className={`status-dot ${hollow ? "hollow" : tone}`} aria-hidden />
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

/** Geist Empty State. `kind="error"` is the failure variant (red-tinted icon tile, announced as an alert);
 *  `size="compact"` drops the border and padding for use inside another surface (a table cell, a viewer). */
export function EmptyState({
  icon,
  title,
  description,
  action,
  kind,
  size,
}: {
  icon: ReactNode;
  title: string;
  description: ReactNode;
  action?: ReactNode;
  kind?: "error";
  size?: "compact";
}) {
  return (
    <div
      className={`empty-state${kind === "error" ? " error" : ""}${size === "compact" ? " compact" : ""}`}
      role={kind === "error" ? "alert" : undefined}
    >
      <span className="empty-state-icon" aria-hidden>{icon}</span>
      <h2 className="empty-state-title">{title}</h2>
      <p className="empty-state-description">{description}</p>
      {action && <div className="actions">{action}</div>}
    </div>
  );
}

/** Failure state with a way forward: the engine's message and a "Try again" button that repeats the same
 *  request. Use it wherever a load fails (Designs list, stress surface, report, preview). `busy` shows a
 *  spinner on the button while the retry is pending. */
export function ErrorState({
  title,
  message,
  onRetry,
  busy,
  size,
  extra,
}: {
  title: string;
  message: ReactNode;
  onRetry: () => void;
  busy?: boolean;
  size?: "compact";
  /** A second, quieter action after Try again (for example Download PDF). */
  extra?: ReactNode;
}) {
  return (
    <EmptyState
      kind="error"
      size={size}
      icon={<AlertCircle />}
      title={title}
      description={message}
      action={
        <>
          <button type="button" className="btn btn-sm" onClick={onRetry} disabled={busy} aria-busy={busy || undefined}>
            {busy ? <Loader2 className="spin" aria-hidden /> : <RotateCw aria-hidden />} Try again
          </button>
          {extra}
        </>
      }
    />
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

export type CheckStatus = "pass" | "advice" | "fail";

export function checkStatus(c: Pick<Check, "passed" | "severity">): CheckStatus {
  return c.passed ? "pass" : c.severity === "advice" ? "advice" : "fail";
}

/** Use of the limit as a 64 px bar; the track end is 100 %. The colour follows the check's status, not its
 *  percentage: gray for a pass (even at 98 %), amber for an advisory, red for a failure. */
export function UseBar({ utilization, status = "pass" }: { utilization: number; status?: CheckStatus }) {
  const pct = Math.min(Math.max(utilization, 0), 1);
  return (
    <div className={`bar${status === "pass" ? "" : ` ${status}`}`} aria-hidden>
      <span style={{ width: `${pct * 100}%` }} />
    </div>
  );
}

/** The status word for a check that does not pass (none for a pass: the column says "Use of limit"). */
export function CheckBadge({ status }: { status: CheckStatus }) {
  if (status === "pass") return null;
  return <Badge tone={status === "fail" ? "red" : "amber"}>{status === "fail" ? "Fail" : "Advice"}</Badge>;
}

/** Moves keyboard focus to a check row (after "Show check" opens it) and scrolls it to the top of the view,
 *  clear of the sticky header (the page's scroll-padding-top). */
export function focusCheck(id: string) {
  requestAnimationFrame(() => {
    const row = document.querySelector<HTMLElement>(`.check-row[data-check-id="${CSS.escape(id)}"]`);
    if (!row) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    row.scrollIntoView({ block: "start", behavior: reduce ? "auto" : "smooth" });
    row.focus({ preventScroll: true });
  });
}

export type CheckOrder = "attention" | "use";

export function CheckList({
  checks,
  selected,
  onSelect,
}: {
  checks: Check[];
  /** The check whose working is open (and whose region is marked on the 3D model). */
  selected?: string | null;
  onSelect?: (id: string | null) => void;
}) {
  const [localOpen, setLocalOpen] = useState<string | null>(null);
  const [order, setOrder] = useState<CheckOrder>("attention");
  const open = selected === undefined ? localOpen : selected;
  const setOpen = onSelect ?? setLocalOpen;
  // Default: anything that needs attention first (fail, then advice), then required strength, required fit
  // and practice checks, each by use. "Use of limit" header: highest use first. View only.
  const byUse = order === "use";
  const ordered = [...checks].sort((a, b) => {
    if (byUse) return b.utilization - a.utilization;
    const attention = (c: Check) => ({ fail: 0, advice: 1, pass: 2 })[checkStatus(c)];
    const rank = (c: Check) => (c.severity === "required" && c.category === "strength" ? 0 : c.severity === "required" ? 1 : 2);
    return attention(a) - attention(b) || rank(a) - rank(b) || b.utilization - a.utilization;
  });
  return (
    <div className="check-list">
      <div className="check-head">
        <span aria-hidden />
        <span>Check and source</span>
        <button
          type="button"
          className="use-head"
          aria-pressed={byUse}
          title={byUse ? "Sorted by use of limit. Select to list checks that need attention first." : "Sort by use of limit, highest first"}
          onClick={() => setOrder(byUse ? "attention" : "use")}
        >
          <span>Use of limit</span>
          {byUse ? <ArrowDown aria-hidden /> : <ArrowUpDown aria-hidden />}
          <span className="sr-only">{byUse ? ", sorted highest first" : ", sort highest first"}</span>
        </button>
      </div>
      {ordered.map((c) => {
        const isOpen = open === c.id;
        const status = checkStatus(c);
        const pct = Math.round(c.utilization * 100);
        return (
          <div key={c.id} className={`check${isOpen ? " open" : ""}${status === "pass" ? "" : ` ${status}`}`}>
            <button
              type="button"
              className="check-row"
              data-check-id={c.id}
              aria-expanded={isOpen}
              aria-label={`${c.title}, ${c.source}. ${pct}% of the limit, ${status === "pass" ? "passes" : status === "advice" ? "advice: over NEMO's recommendation" : "fails"}`}
              onClick={() => setOpen(isOpen ? null : c.id)}
            >
              <ChevronRight aria-hidden className="check-chevron" />
              <span className="check-text">
                <span className="check-title">
                  {c.title}
                  {status !== "pass" && (
                    <>
                      {" "}
                      <CheckBadge status={status} />
                    </>
                  )}
                </span>
                <span className="check-source" title={c.source}>
                  {c.source}
                </span>
              </span>
              <UseBar utilization={c.utilization} status={status} />
              <span className={`check-pct${status === "pass" ? "" : ` ${status}`}`}>{pct}%</span>
            </button>
            {isOpen && (
              <div className="check-body">
                <p className="check-source-full">
                  <span className="muted">Source: </span>
                  {c.source}
                </p>
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

export function formatKg(kg: number, extraDigit = false): string {
  return formatKgDigits(kg, (kg < 10 ? 2 : 1) + (extraDigit ? 1 : 0));
}
function formatKgDigits(kg: number, digits: number): string {
  return `${kg.toFixed(digits)} kg`;
}

/** Masses shown side by side (design choices, readouts, tables): decimals are added for all of them until
 *  masses that differ never share a label (0.305 / 0.308 / 0.313 kg, or 0.3051 / 0.3052 kg). Equal masses
 *  keep equal labels. Display only. */
export function formatKgSet(masses: number[]): string[] {
  const distinct = new Set(masses.map((m) => m.toFixed(6))).size;
  const base = masses.some((m) => m < 10) ? 2 : 1;
  for (let digits = base; digits <= base + 4; digits++) {
    const labels = masses.map((m) => formatKgDigits(m, digits));
    if (new Set(labels).size >= distinct) return labels;
  }
  return masses.map((m) => formatKgDigits(m, base + 4));
}
