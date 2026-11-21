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

/** The step-by-step calculation: a numbered list; each step shows its formula, the same formula
 *  with the numbers in it, and the result, all in Geist Mono. The verdict line sits at the end. */
export function Working({ steps, verdict }: { steps: WorkingStep[]; verdict?: ReactNode }) {
  if (!steps.length) return null;
  return (
    <div className="working">
      <ol className="working-steps" aria-label="Calculation, step by step">
        {steps.map((s, i) => (
          <li className="working-step" key={i}>
            <span className="working-num" aria-hidden>
              {i + 1}
            </span>
            <span className="working-label">
              {s.label}
              {s.note && (
                <span className="working-note">
                  <Formula text={s.note} />
                </span>
              )}
            </span>
            <span className="working-formula">
              {s.formula && <Formula text={s.formula} />}
              {s.formula && s.substituted ? " = " : ""}
              {s.substituted && <Formula text={s.substituted} />}
              {(s.formula || s.substituted) && s.result ? " = " : ""}
              {s.result && (
                <span className="working-result">
                  <Formula text={s.result} />
                </span>
              )}
            </span>
          </li>
        ))}
      </ol>
      {verdict && <div className="working-verdict">{verdict}</div>}
    </div>
  );
}
