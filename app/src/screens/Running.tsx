import { ArrowLeft } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api";
import { activeStage, StageList, stagesFrom, StageView, type StageKey } from "../components/Engineering";
import { Banner } from "../components/ui";
import type { EngEvent, RunStatus } from "../types";

export function Running({ runId, onDone, onBack, title }: { runId: string; onDone: () => void; onBack: () => void; title: string }) {
  const [status, setStatus] = useState<RunStatus | null>(null);
  const [events, setEvents] = useState<EngEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [pinned, setPinned] = useState<StageKey | null>(null);
  const [now, setNow] = useState(Date.now());
  const started = useRef(Date.now());
  const next = useRef(0);

  useEffect(() => {
    let stop = false;
    async function poll() {
      try {
        const s = await api.runStatus(runId, next.current);
        if (stop) return;
        next.current = s.next;
        if (s.events.length) setEvents((prev) => prev.concat(s.events));
        setStatus(s);
        if (s.state === "done") {
          window.setTimeout(onDone, 1200);
          return;
        }
        if (s.state === "failed") return;
      } catch (e) {
        if (!stop) setError(e instanceof ApiError ? e.message : String(e));
        return;
      }
      window.setTimeout(poll, 500);
    }
    poll();
    const tick = window.setInterval(() => setNow(Date.now()), 1000);
    return () => {
      stop = true;
      window.clearInterval(tick);
    };
  }, [runId, onDone]);

  const failed = status?.state === "failed";
  const finished = status?.state === "done";
  const stages = stagesFrom(events, finished, failed);
  const current = activeStage(stages);
  const shown = pinned ?? current;
  const seconds = Math.round((now - started.current) / 1000);
  const shownStage = stages.find((s) => s.key === shown)!;

  return (
    <div className="page page-wide">
      <div className="step-label">Step 3 of 3</div>
      <div className="title-row">
        <h1 className="title">{failed ? "No design found" : finished ? "Designs ready" : "Finding designs"}</h1>
        <span className="elapsed" aria-live="off">{Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}</span>
      </div>
      <p className="lead">{title}. Each step below shows the numbers NEMO is working with. Select a step to see its working.</p>

      {(failed || error) && (
        <div className="stack gap-2 mt-4">
          <Banner kind="error">{status?.error ?? error}</Banner>
          <div className="actions" style={{ marginTop: 0 }}>
            <button className="btn btn-primary" onClick={onBack}>
              <ArrowLeft aria-hidden /> Change the answers
            </button>
          </div>
        </div>
      )}

      <div className="run-grid">
        <div className="stack gap-2">
          <StageList stages={stages} selected={shown} onSelect={(k) => setPinned(k === current && !finished ? null : k)} />
          {pinned && !finished && (
            <button className="btn btn-ghost" onClick={() => setPinned(null)}>
              Follow the live step
            </button>
          )}
        </div>
        <section className="live-panel" aria-live="polite" aria-label={`${shownStage.title}: details`}>
          <div className="live-head">
            <h2 className="section-title">{shownStage.title}</h2>
            <span className="caption">{shownStage.state === "active" ? "Running now" : shownStage.state === "done" ? "Done" : shownStage.state === "failed" ? "Stopped" : "Not started"}</span>
          </div>
          <StageView stage={shown} events={events} />
        </section>
      </div>
    </div>
  );
}
