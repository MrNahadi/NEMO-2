import { ArrowLeft } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api";
import { activeStage, StageList, stagesFrom, StageView, type StageKey } from "../components/Engineering";
import { Page, PageHeader, StickyAside } from "../components/Page";
import { Note, Progress } from "../components/ui";
import type { EngEvent, RunStatus } from "../types";

/** True when the engine's message says the search found no design that satisfied the checks (as against a
 *  connection or solve failure). The server marks that case with the message "No design found". */
function noDesignPassed(status: RunStatus | null, message: string): boolean {
  return status?.message === "No design found" || /passed every check|no design (meets|satisfied)/i.test(message);
}

export function Running({
  runId,
  onDone,
  onBack,
  onStopped,
  title,
}: {
  runId: string;
  onDone: () => void;
  onBack: () => void;
  /** Call once when the run has stopped for good (engine state "failed" or the status request failed): the
   *  app stops the busy tab underline and makes the other tabs available again. */
  onStopped?: () => void;
  title: string;
}) {
  const [status, setStatus] = useState<RunStatus | null>(null);
  const [events, setEvents] = useState<EngEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [pinned, setPinned] = useState<StageKey | null>(null);
  const [now, setNow] = useState(Date.now());
  // Set once when the run stops: the elapsed timer freezes at this moment.
  const [frozenAt, setFrozenAt] = useState<number | null>(null);
  const started = useRef(Date.now());
  const stoppedRef = useRef(false);
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
    const tick = window.setInterval(() => {
      // Once the run has stopped the timer holds its value instead of advancing over the failure.
      if (!stoppedRef.current) setNow(Date.now());
    }, 1000);
    return () => {
      stop = true;
      window.clearInterval(tick);
    };
  }, [runId, onDone]);

  const failed = status?.state === "failed";
  const finished = status?.state === "done";
  const stopped = failed || !!error;
  useEffect(() => {
    if (!stopped) return;
    stoppedRef.current = true;
    setFrozenAt((f) => f ?? Date.now());
    // The pinned step's "Not started" detail makes no sense once the run has stopped: clear it.
    setPinned(null);
    onStopped?.();
  }, [stopped, onStopped]);

  const message = status?.error ?? error ?? "";
  const failTitle = noDesignPassed(status, message) ? "No design passed every check" : "The run stopped";
  const seconds = Math.round(((frozenAt ?? now) - started.current) / 1000);

  return (
    <Page>
      <PageHeader
        title={stopped ? failTitle : finished ? "Designs ready" : "Finding designs"}
        description={
          stopped ? `${title}.` : `${title}. Each step shows the numbers NEMO is working with. Select a step to see its working.`
        }
        actions={
          <span className="run-elapsed text-label-16-mono" role="timer" aria-label="Elapsed time">
            {Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}
          </span>
        }
      />

      {stopped ? (
        /* A stopped run is a terminal state: the progress bar, the step list and the live detail panel go
           away (so the live announcements stop too) and one clear failure panel carries the engine's
           message and the way back. */
        <Note
          kind="error"
          className="run-fail"
          action={
            <button className="btn btn-primary" onClick={onBack}>
              <ArrowLeft aria-hidden /> Change the answers
            </button>
          }
        >
          {message || "The run stopped before it finished."}
        </Note>
      ) : (
        <RunningBody
          events={events}
          finished={finished}
          failed={failed}
          pinned={pinned}
          onPin={setPinned}
        />
      )}
    </Page>
  );
}

function RunningBody({
  events,
  finished,
  failed,
  pinned,
  onPin,
}: {
  events: EngEvent[];
  finished: boolean;
  failed: boolean;
  pinned: StageKey | null;
  onPin: (k: StageKey | null) => void;
}) {
  const stages = stagesFrom(events, finished, failed);
  const current = activeStage(stages);
  const shown = pinned ?? current;
  const shownStage = stages.find((s) => s.key === shown)!;
  const doneCount = stages.filter((s) => s.state === "done").length;
  const stateWord =
    shownStage.state === "active" ? "Running now" : shownStage.state === "done" ? "Done" : shownStage.state === "failed" ? "Stopped" : "Not started";

  return (
    <>
      <div className="run-progress">
        <Progress value={doneCount} max={stages.length} label={`${doneCount} of ${stages.length} steps done`} tone={failed ? "red" : undefined} />
      </div>

      <div className="workspace">
        <div className="workspace-main">
          <StageList stages={stages} selected={shown} onSelect={(k) => onPin(k === current && !finished ? null : k)} />
          {pinned && !finished && (
            <button className="btn btn-ghost btn-sm run-follow" onClick={() => onPin(null)}>
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
    </>
  );
}
