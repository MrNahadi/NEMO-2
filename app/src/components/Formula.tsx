import { Fragment, type ReactNode } from "react";
import type { WorkingStep } from "../types";

/** Renders the engine's formula markup: X_t or X_{eff} as subscripts, x^2 as superscripts. */
export function Formula({ text }: { text: string }) {
  const parts: ReactNode[] = [];
  const pattern = /([A-Za-zα-ωΑ-Ω])_\{([^}]*)\}|([A-Za-zα-ωΑ-Ω])_([A-Za-z0-9])|\^\{([^}]*)\}|\^([0-9])/g;
  let last = 0;
  let match: RegExpExecArray | null;
  let key = 0;
  while ((match = pattern.exec(text))) {
    if (match.index > last) parts.push(text.slice(last, match.index));
    if (match[1] || match[3]) {
      parts.push(
        <Fragment key={key++}>
          {match[1] ?? match[3]}
          <sub>{match[2] ?? match[4]}</sub>
        </Fragment>,
      );
    } else {
      parts.push(<sup key={key++}>{match[5] ?? match[6]}</sup>);
    }
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return <span className="formula">{parts}</span>;
}

/** The calculation sheet: quantity, formula, the same formula with numbers, result. */
export function Working({ steps, verdict }: { steps: WorkingStep[]; verdict?: ReactNode }) {
  if (!steps.length) return null;
  return (
    <div className="sheet-wrap">
    <div className="sheet" role="table" aria-label="Calculation">
      <div className="sheet-row sheet-head" role="row">
        <span role="columnheader">Quantity</span>
        <span role="columnheader">Formula</span>
        <span role="columnheader">With the numbers</span>
        <span role="columnheader" className="sheet-result">
          Result
        </span>
      </div>
      {steps.map((s, i) => (
        <div className="sheet-row" role="row" key={i}>
          <span role="cell" className="sheet-label">
            {s.label}
            {s.note && (
              <span className="sheet-note">
                <Formula text={s.note} />
              </span>
            )}
          </span>
          <span role="cell">
            <Formula text={s.formula} />
          </span>
          <span role="cell" className="sheet-sub">
            <Formula text={s.substituted} />
          </span>
          <span role="cell" className="sheet-result">
            <Formula text={s.result} />
          </span>
        </div>
      ))}
      {verdict && <div className="sheet-verdict">{verdict}</div>}
    </div>
    </div>
  );
}
