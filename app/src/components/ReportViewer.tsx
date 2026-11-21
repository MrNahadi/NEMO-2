import { Download, ExternalLink, Loader2, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useModal } from "./Menu";
import { ErrorState } from "./ui";

type ReportState = { kind: "loading" } | { kind: "ready"; url: string } | { kind: "error"; message: string };

/**
 * The calculation report shown inside NEMO, as a Geist fullscreen material (radius 16, 24 px inset). The
 * header carries the title, Download PDF, Open in new tab and Close; the PDF sits below it as a framed
 * document, so the browser's own PDF toolbar reads as part of the document, not as NEMO's chrome.
 *
 * The PDF is fetched first (the engine writes it the first time it is opened, which takes a few seconds),
 * so loading and failure are NEMO's own states: a failure shows the engine's message with Try again (which
 * asks the same address again) and Download PDF.
 *
 * Keyboard: the browser's PDF viewer swallows every key once it has focus (Escape included), so it is kept
 * out of the Tab order: Tab and Shift+Tab cycle through the header, and Escape always closes. A mouse user
 * who clicks into the PDF gets focus handed back to the dialog when the pointer leaves the document. For
 * keyboard reading, Open in new tab gives the browser's full viewer.
 */
export function ReportViewer({
  title,
  subtitle,
  viewUrl,
  downloadUrl,
  onClose,
}: {
  title: string;
  subtitle: string;
  viewUrl: string;
  downloadUrl: string;
  onClose: () => void;
}) {
  const [state, setState] = useState<ReportState>({ kind: "loading" });
  const [shown, setShown] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const closeBtn = useRef<HTMLButtonElement>(null);
  const box = useRef<HTMLDivElement>(null);
  const frame = useRef<HTMLIFrameElement>(null);
  // Same modal behaviour as every dialog: inert background, focus kept inside, Escape closes, focus returns
  // to View report.
  useModal(box, onClose, () => closeBtn.current);

  useEffect(() => {
    let cancelled = false;
    let objectUrl: string | null = null;
    setState({ kind: "loading" });
    setShown(false);
    (async () => {
      let response: Response;
      try {
        response = await fetch(viewUrl);
      } catch {
        if (!cancelled) setState({ kind: "error", message: "We couldn't reach the NEMO engine. Check that the NEMO window is still open." });
        return;
      }
      if (!response.ok) {
        let message = `Something went wrong (${response.status}).`;
        try {
          const body = await response.json();
          if (typeof body.detail === "string") message = body.detail;
        } catch {
          /* keep the generic message */
        }
        if (!cancelled) setState({ kind: "error", message });
        return;
      }
      const blob = await response.blob();
      if (cancelled) return;
      objectUrl = URL.createObjectURL(blob.type === "application/pdf" ? blob : new Blob([blob], { type: "application/pdf" }));
      setState({ kind: "ready", url: objectUrl });
    })();
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [viewUrl, attempt]);

  // After a failed attempt, put focus on Try again so a keyboard user lands on the way forward.
  useEffect(() => {
    if (state.kind === "error" && box.current?.contains(document.activeElement))
      box.current.querySelector<HTMLButtonElement>(".report-state .btn")?.focus();
  }, [state.kind]);

  const handBack = useCallback(() => {
    if (document.activeElement === frame.current) box.current?.focus({ preventScroll: true });
  }, []);

  return createPortal(
    <div className="report-overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="report-viewer" role="dialog" aria-modal="true" aria-label={title} ref={box} tabIndex={-1}>
        <div className="report-bar">
          <div className="report-title">
            <span className="report-name">{title}</span>
            <span className="report-subtitle">{subtitle}</span>
          </div>
          <a className="btn btn-ghost btn-sm" href={viewUrl} target="_blank" rel="noreferrer">
            <ExternalLink aria-hidden /> Open in new tab
          </a>
          <a className="btn btn-sm" href={downloadUrl}>
            <Download aria-hidden /> Download PDF
          </a>
          <span className="report-bar-sep" aria-hidden />
          <button ref={closeBtn} type="button" className="icon-btn" aria-label="Close the report" onClick={onClose}>
            <X aria-hidden />
          </button>
        </div>
        <div className="report-body" onMouseLeave={handBack} aria-busy={state.kind === "loading" || (state.kind === "ready" && !shown)}>
          {(state.kind === "loading" || (state.kind === "ready" && !shown)) && (
            <div className="report-state" role="status">
              <span className="row">
                <Loader2 className="spin" aria-hidden /> Preparing the report
              </span>
              <span className="caption">NEMO writes the PDF the first time it is opened. This can take a few seconds.</span>
            </div>
          )}
          {state.kind === "error" && (
            <div className="report-state">
              <ErrorState
                size="compact"
                title="The report could not be opened"
                message={state.message}
                onRetry={() => setAttempt((a) => a + 1)}
                extra={
                  <a className="btn btn-ghost btn-sm" href={downloadUrl}>
                    <Download aria-hidden /> Download PDF
                  </a>
                }
              />
            </div>
          )}
          {state.kind === "ready" && (
            <iframe
              ref={frame}
              className={shown ? "report-frame shown" : "report-frame"}
              src={state.url}
              title={`${title}, PDF document`}
              tabIndex={-1}
              onLoad={() => setShown(true)}
            />
          )}
        </div>
      </div>
    </div>,
    document.body,
  );
}
