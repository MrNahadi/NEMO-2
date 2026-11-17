import { CheckCircle2, Loader2, Plug, RefreshCw } from "lucide-react";
import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { api, ApiError } from "../api";
import type { FusionJob, FusionModel, FusionRecords, FusionStatus } from "../types";
import { Dialog } from "./Menu";
import { Banner } from "./ui";

interface FusionContextValue {
  status: FusionStatus | null;
  refresh: () => void;
  openSetup: () => void;
  /** Ask Fusion to build a design. Resolves when Fusion has built it. */
  openInFusion: (projectId: string, run: string, design: string) => Promise<FusionModel | null>;
  busy: string | null;
}

const FusionContext = createContext<FusionContextValue | null>(null);

export function useFusion(): FusionContextValue {
  const value = useContext(FusionContext);
  if (!value) throw new Error("useFusion must be used inside FusionProvider");
  return value;
}

export function FusionProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<FusionStatus | null>(null);
  const [setup, setSetup] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);

  const refresh = useCallback(() => {
    api.fusionStatus().then(setStatus).catch(() => undefined);
  }, []);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 3000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const openInFusion = useCallback(
    async (projectId: string, run: string, design: string) => {
      const current = await api.fusionStatus().catch(() => null);
      if (current) setStatus(current);
      if (!current?.connected) {
        setSetup(true);
        return null;
      }
      setBusy(`${projectId}/${run}/${design}`);
      try {
        let job: FusionJob = await api.openInFusion(projectId, run, design);
        while (job.state === "waiting" || job.state === "sent") {
          await new Promise((r) => setTimeout(r, 800));
          job = await api.fusionJob(job.id);
        }
        if (job.state !== "done") throw new ApiError(job.error ?? "Fusion did not build the model.");
        return job.result;
      } finally {
        setBusy(null);
      }
    },
    [],
  );

  return (
    <FusionContext.Provider value={{ status, refresh, openSetup: () => setSetup(true), openInFusion, busy }}>
      {children}
      {setup && <FusionSetup status={status} onClose={() => setSetup(false)} onChanged={setStatus} />}
    </FusionContext.Provider>
  );
}

/** The light in the top bar. */
export function FusionLight() {
  const { status, openSetup } = useFusion();
  const state = !status ? "unknown" : status.connected ? "connected" : status.installed ? "waiting" : "missing";
  const label = { unknown: "Fusion", connected: "Fusion connected", waiting: "Fusion not running", missing: "Connect to Fusion" }[state];
  return (
    <button className={`btn btn-ghost btn-sm fusion-light fusion-${state}`} onClick={openSetup} aria-label={`${label}. Open Fusion connector settings.`}>
      <span className="fusion-dot" aria-hidden />
      <span className="fusion-label">{label}</span>
    </button>
  );
}

function FusionSetup({ status, onClose, onChanged }: { status: FusionStatus | null; onClose: () => void; onChanged: (s: FusionStatus) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [justInstalled, setJustInstalled] = useState(false);
  const close = useRef(onClose);
  close.current = onClose;
  const stableClose = useCallback(() => close.current(), []);

  async function install() {
    setBusy(true);
    setError(null);
    try {
      onChanged(await api.installFusion());
      setJustInstalled(true);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  const connected = !!status?.connected;
  const installed = !!status?.installed;
  const steps: { done: boolean; title: string; text: ReactNode }[] = [
    {
      done: installed && !status?.update_available,
      title: "Install the NEMO Connector",
      text: installed
        ? status?.update_available
          ? `Installed version ${status.installed_version}. Version ${status.current_version} is available.`
          : "Installed in Fusion's add-ins folder. It starts by itself with Fusion."
        : "NEMO copies a small add-in into Fusion's add-ins folder and sets it to start with Fusion.",
    },
    {
      done: connected,
      title: justInstalled ? "Restart Fusion" : "Start Fusion",
      text: connected
        ? `Connected to Fusion ${status?.fusion_version ?? ""}.`
        : justInstalled
          ? "Close Fusion completely if it is open, then start it again. The light turns green within a few seconds."
          : "Open Fusion. The connector links to NEMO by itself within a few seconds.",
    },
    {
      done: false,
      title: "Use it",
      text: (
        <>
          On a design's results, choose <b>Open in Fusion</b>. In Fusion, the NEMO panel on the Solid tab has <b>Check in NEMO</b> and the
          <b> NEMO cross-check sheet</b>.
        </>
      ),
    },
  ];

  return (
    <Dialog
      title="Fusion connector"
      description="Fusion is optional. With the connector, NEMO designs open in Fusion as parametric models you can edit, and Fusion can send edited dimensions back to NEMO to be checked."
      onClose={stableClose}
      actions={
        <>
          <button className="btn" onClick={stableClose}>
            Close
          </button>
          <button className="btn btn-primary" onClick={install} disabled={busy}>
            {busy ? <Loader2 className="spin" aria-hidden /> : installed ? <RefreshCw aria-hidden /> : <Plug aria-hidden />}
            {installed ? (status?.update_available ? "Update connector" : "Reinstall connector") : "Install connector"}
          </button>
        </>
      }
    >
      <ol className="setup-steps">
        {steps.map((s, i) => (
          <li key={s.title} className={s.done ? "done" : ""}>
            <span className="setup-mark" aria-hidden>
              {s.done ? <CheckCircle2 /> : i + 1}
            </span>
            <span className="sr-only">{s.done ? "Done: " : `Step ${i + 1}: `}</span>
            <span className="stack">
              <span className="setup-title">{s.title}</span>
              <span className="caption">{s.text}</span>
            </span>
          </li>
        ))}
      </ol>
      {error && <Banner kind="error">{error}</Banner>}
      {status && status.activity.length > 0 && (
        <details className="more">
          <summary>Recent activity</summary>
          <ul className="activity">
            {[...status.activity].reverse().map((a, i) => (
              <li key={i}>
                <span>{a.message}</span>
                <span className="caption mono">{new Date(a.at).toLocaleTimeString()}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </Dialog>
  );
}

/** Fusion records for one design: the model built, checks sent from Fusion, and the stress cross-check. */
export function useFusionRecords(projectId: string, run: string, design: string, live: boolean) {
  const [records, setRecords] = useState<FusionRecords | null>(null);
  const load = useCallback(() => {
    api.fusionRecords(projectId, run, design).then(setRecords).catch(() => undefined);
  }, [projectId, run, design]);
  useEffect(() => {
    setRecords(null);
    load();
    if (!live) return;
    const timer = window.setInterval(load, 4000);
    return () => window.clearInterval(timer);
  }, [load, live]);
  return { records, reload: load };
}
