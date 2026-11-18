import { ArrowLeft } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api";
import { activeStage, StageList, stagesFrom, StageView, type StageKey } from "../components/Engineering";
import { Page, PageHeader, StickyAside } from "../components/Page";
import { Note, Progress } from "../components/ui";
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
  const doneCount = stages.filter((s) => s.state === "done").length;
  const stateWord =
    shownStage.state === "active" ? "Running now" : shownStage.state === "done" ? "Done" : shownStage.state === "failed" ? "Stopped" : "Not started";

  return (
    <Page>
      <PageHeader
        title={failed ? "No design found" : finished ? "Designs ready" : "Finding designs"}
        description={`${title}. Each step shows the numbers NEMO is working with. Select a step to see its working.`}
        actions={
          <span className="run-elapsed text-label-16-mono" role="timer" aria-label="Elapsed time">
            {Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}
          </span>
        }
      />
      <div className="run-progress">
        <Progress value={doneCount} max={stages.length} label={`${doneCount} of ${stages.length} steps done`} tone={failed ? "red" : undefined} />
      </div>

      {(failed || error) && (
        <Note
          kind="error"
          className="run-fail"
          action={
            <button className="btn" onClick={onBack}>
              <ArrowLeft aria-hidden /> Change the answers
            </button>
          }
        >
          {status?.error ?? error}
        </Note>
      )}

      <div className="workspace">
        <div className="workspace-main">
          <StageList stages={stages} selected={shown} onSelect={(k) => setPinned(k === current && !finished ? null : k)} />
          {pinned && !finished && (
            <button className="btn btn-ghost btn-sm run-follow" onClick={() => setPinned(null)}>
              Follow the live step
            </button>
          )}
        </div>
        <StickyAside className="workspace-aside-scroll run-panel" live="polite" label={`${shownStage.title}: details`}>
          <div className="run-panel-head">
            <h2 className="section-title">{shownStage.title}</h2>
            <span className="caption">{stateWord}</span>
          </div>
          <StageView stage={shown} events={events} state={shownStage.state} />
        </StickyAside>
      </div>
    </Page>
  );
}
