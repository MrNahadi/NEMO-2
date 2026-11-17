import { Download, ExternalLink, Loader2, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

/**
 * The calculation report shown inside NEMO, as a Geist fullscreen material (radius 16, 24px inset),
 * with its own Download PDF and Open in new tab. The PDF is generated the first time it is opened,
 * so it can take a few seconds: the loading state stays until the frame has loaded.
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
  const [loaded, setLoaded] = useState(false);
  const closeBtn = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    closeBtn.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, [onClose]);

  return (
    <div className="report-overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="report-viewer" role="dialog" aria-modal="true" aria-label={title}>
        <div className="report-bar">
          <div className="report-title">
            <span className="report-name">{title}</span>
            <span className="report-subtitle">{subtitle}</span>
          </div>
          <a className="btn btn-sm" href={downloadUrl}>
            <Download aria-hidden /> Download PDF
          </a>
          <a className="btn btn-ghost btn-sm" href={viewUrl} target="_blank" rel="noreferrer">
            <ExternalLink aria-hidden /> Open in new tab
          </a>
          <button ref={closeBtn} type="button" className="icon-btn" aria-label="Close the report" onClick={onClose}>
            <X aria-hidden />
          </button>
        </div>
        <div className="report-body">
          {!loaded && (
            <div className="report-loading">
              <span className="row">
                <Loader2 className="spin" aria-hidden /> Preparing the report
              </span>
            </div>
          )}
          <iframe className="report-frame" src={viewUrl} title={title} onLoad={() => setLoaded(true)} />
        </div>
      </div>
    </div>
  );
}
