import { Loader2, Moon, Sun } from "lucide-react";
import { Fragment, useCallback, useEffect, useState } from "react";
import { api, ApiError } from "./api";
import { FusionLight, FusionProvider } from "./components/Fusion";
import { Logo } from "./components/Logo";
import { Page } from "./components/Page";
import { Note, Skeleton, Tooltip } from "./components/ui";
import { Assumptions } from "./screens/Assumptions";
import { DescribeLift } from "./screens/DescribeLift";
import { Home } from "./screens/Home";
import { NewDesign } from "./screens/NewDesign";
import { BracketAssumptions, DescribeBracket, DescribeFin, FinAssumptions } from "./screens/PartForms";
import { Results } from "./screens/Results";
import { Running } from "./screens/Running";
import { Verification } from "./screens/Verification";
import type { Job, PartId, Project, Reference } from "./types";
import { isValid } from "./validate";

type Screen =
  | { name: "home" }
  | { name: "new" }
  | { name: "describe" }
  | { name: "assumptions" }
  | { name: "running"; runId: string }
  | { name: "results" }
  | { name: "runlog" }
  | { name: "verification" };

export function App() {
  const [reference, setReference] = useState<Reference | null>(null);
  const [fatal, setFatal] = useState<string | null>(null);
  const [screen, setScreen] = useState<Screen>({ name: "home" });
  const [project, setProject] = useState<Project | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [starting, setStarting] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [theme, setTheme] = useState<"light" | "dark">(() => (localStorage.getItem("nemo-theme") as "light" | "dark") ?? "light");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("nemo-theme", theme);
  }, [theme]);

  useEffect(() => {
    api.reference().then(setReference).catch((e) => setFatal(e instanceof ApiError ? e.message : String(e)));
  }, []);

  useEffect(() => {
    if (screen.name !== "new") window.scrollTo(0, 0);
  }, [screen.name]);

  const openProject = useCallback(
    async (p: Project) => {
      if (!reference) return;
      const full = await api.project(p.id);
      setProject(full);
      const part = (full.part as PartId) ?? "padeye";
      const base = reference.parts?.[part]?.default_job ?? reference.default_job;
      setJob(full.inputs ? ({ ...structuredClone(base), ...full.inputs } as Job) : structuredClone(base));
      setScreen(full.results ? { name: "results" } : { name: "describe" });
    },
    [reference],
  );

  const saveDraft = useCallback(async () => {
    if (project && job) {
      try {
        await api.saveInputs(project.id, job);
      } catch {
        /* drafts are saved again when the run starts */
      }
    }
  }, [project, job]);

  async function startRun() {
    if (!project || !job) return;
    setStarting(true);
    setRunError(null);
    try {
      const status = await api.startRun(project.id, job);
      setScreen({ name: "running", runId: status.id });
    } catch (e) {
      setRunError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setStarting(false);
    }
  }

  const finishRun = useCallback(async () => {
    if (!project) return;
    setProject(await api.project(project.id));
    setScreen({ name: "results" });
  }, [project]);

  let body: React.ReactNode = null;
  if (fatal) {
    body = (
      <Page>
        <div className="page-header" />
        <Note kind="error">{fatal}</Note>
      </Page>
    );
  } else if (!reference) {
    body = (
      <Page>
        <div className="page-header" aria-busy="true" aria-label="Starting NEMO">
          <div className="stack gap-2">
            <Skeleton width={160} height={32} />
            <Skeleton width={360} height={20} />
          </div>
        </div>
        <Skeleton height={240} radius={12} />
      </Page>
    );
  } else if (screen.name === "home" || screen.name === "new") {
    body = (
      <>
        <Home onNew={() => setScreen({ name: "new" })} onOpen={openProject} />
        {screen.name === "new" && <NewDesign onCreated={openProject} onCancel={() => setScreen({ name: "home" })} />}
      </>
    );
  } else if (project && job && job.part === "pipe-bracket" && (screen.name === "describe" || screen.name === "assumptions")) {
    body = screen.name === "describe" ? (
      <DescribeBracket job={job} reference={reference} onChange={setJob}
        onNext={() => { saveDraft(); setScreen({ name: "assumptions" }); }} onBack={() => { saveDraft(); setScreen({ name: "home" }); }} />
    ) : (
      <BracketAssumptions job={job} reference={reference} onChange={setJob} onNext={startRun} onBack={() => setScreen({ name: "describe" })}
        starting={starting} error={runError} />
    );
  } else if (project && job && job.part === "stabilizer" && (screen.name === "describe" || screen.name === "assumptions")) {
    body = screen.name === "describe" ? (
      <DescribeFin job={job} reference={reference} onChange={setJob}
        onNext={() => { saveDraft(); setScreen({ name: "assumptions" }); }} onBack={() => { saveDraft(); setScreen({ name: "home" }); }} />
    ) : (
      <FinAssumptions job={job} reference={reference} onChange={setJob} onNext={startRun} onBack={() => setScreen({ name: "describe" })}
        starting={starting} error={runError} />
    );
  } else if (project && job && job.part === "padeye" && screen.name === "describe") {
    body = (
      <DescribeLift
        job={job}
        reference={reference}
        onChange={setJob}
        onNext={() => {
          saveDraft();
          setScreen({ name: "assumptions" });
        }}
        onBack={() => {
          saveDraft();
          setScreen({ name: "home" });
        }}
      />
    );
  } else if (project && job && job.part === "padeye" && screen.name === "assumptions") {
    body = (
      <Assumptions
        job={job}
        reference={reference}
        onChange={setJob}
        onRun={startRun}
        onBack={() => setScreen({ name: "describe" })}
        starting={starting}
        error={runError}
      />
    );
  } else if (project && screen.name === "running") {
    body = (
      <Running
        runId={screen.runId}
        onDone={finishRun}
        onBack={() => setScreen({ name: "describe" })}
        title={runTitle(project.name, job)}
      />
    );
  } else if (screen.name === "verification") {
    body = <Verification />;
  } else if (project && (screen.name === "results" || screen.name === "runlog") && project.results) {
    body = (
      <Results
        project={project}
        view={screen.name === "runlog" ? "log" : "results"}
        onEdit={() => setScreen({ name: "describe" })}
        onRunAgain={startRun}
        onShowLog={() => setScreen({ name: "runlog" })}
      />
    );
  }

  const inDesign = !!project && !["home", "new", "verification"].includes(screen.name);
  const go = (s: Screen) => setScreen(s);
  const running = screen.name === "running";
  const hasResults = !!project?.results;
  const answered = !!job && (job.part === "padeye" ? isValid(job) : job.plate_thicknesses_mm.length > 0);
  const whileRunning = "Available when the run finishes.";
  const tabs: { key: string; label: string; current: boolean; enabled: boolean; why: string; busy?: boolean; open: () => void }[] = [
    {
      key: "describe", label: "Describe", current: screen.name === "describe", enabled: !running, why: whileRunning,
      open: () => go({ name: "describe" }),
    },
    {
      key: "assumptions", label: "Assumptions", current: screen.name === "assumptions", enabled: !running && answered,
      why: running ? whileRunning : "Answer the questions on Describe first.",
      open: () => {
        if (screen.name === "describe") saveDraft();
        go({ name: "assumptions" });
      },
    },
    {
      key: "results", label: "Results", current: screen.name === "results" || running, enabled: hasResults || running, busy: running,
      why: "Results appear after you press Find designs.",
      open: () => go({ name: "results" }),
    },
    {
      key: "runlog", label: "Run log", current: screen.name === "runlog", enabled: hasResults && !running,
      why: running ? whileRunning : "The run log appears after a run.",
      open: () => go({ name: "runlog" }),
    },
  ];

  useEffect(() => {
    const where = screen.name === "verification" ? "Verification" : inDesign && project ? project.name : "Designs";
    document.title = `${where} - NEMO`;
  }, [screen.name, inDesign, project]);

  return (
    <FusionProvider>
      <div className={inDesign ? "app has-tabs" : "app"}>
        <header className="app-header">
          <div className="frame app-header-bar">
            <nav className="crumbs" aria-label="Breadcrumb">
              <button className="brand" onClick={() => go({ name: "home" })} aria-label="NEMO, go to Designs">
                <span className="brand-mark" aria-hidden>
                  <Logo size={16} />
                </span>
                <span>NEMO</span>
              </button>
              <Slash />
              {screen.name === "verification" ? (
                <span className="crumb" aria-current="page">Verification</span>
              ) : inDesign && project ? (
                <>
                  <button className="crumb" onClick={() => go({ name: "home" })}>Designs</button>
                  <Slash />
                  <span className="crumb" aria-current="page" title={project.name}>
                    <span className="crumb-text">{project.name}</span>
                  </span>
                </>
              ) : (
                <span className="crumb" aria-current="page">Designs</span>
              )}
            </nav>
            <div className="header-actions">
              <FusionLight />
              <button
                className="btn btn-ghost btn-sm nav-link"
                onClick={() => go({ name: "verification" })}
                aria-current={screen.name === "verification" ? "page" : undefined}
              >
                Verification
              </button>
              <Tooltip text={theme === "light" ? "Dark theme" : "Light theme"} side="bottom">
                <button
                  className="icon-btn"
                  aria-label={theme === "light" ? "Switch to dark theme" : "Switch to light theme"}
                  onClick={() => setTheme(theme === "light" ? "dark" : "light")}
                >
                  {theme === "light" ? <Moon aria-hidden /> : <Sun aria-hidden />}
                </button>
              </Tooltip>
            </div>
          </div>
          {inDesign && (
            <div className="frame">
              <nav className="app-tabs" aria-label="Design steps">
                {tabs.map((t) => {
                  const button = (
                    <button
                      className="tab"
                      aria-current={t.current ? "page" : undefined}
                      aria-disabled={!t.enabled || undefined}
                      onClick={() => t.enabled && !t.current && t.open()}
                    >
                      {t.busy && <Loader2 className="spin" aria-hidden />}
                      <span>{t.label}</span>
                      {t.busy && <span className="sr-only">(running)</span>}
                    </button>
                  );
                  return t.enabled ? (
                    <Fragment key={t.key}>{button}</Fragment>
                  ) : (
                    <Tooltip key={t.key} text={t.why} side="bottom">
                      {button}
                    </Tooltip>
                  );
                })}
              </nav>
            </div>
          )}
        </header>
        <main>{body}</main>
      </div>
    </FusionProvider>
  );
}

/** Geist breadcrumb separator: a thin slanted slash. */
function Slash() {
  return (
    <svg className="crumb-sep" viewBox="0 0 16 24" aria-hidden focusable="false">
      <path d="M11 4 5 20" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" fill="none" />
    </svg>
  );
}

function runTitle(name: string, job: Job | null): string {
  if (!job) return name;
  if (job.part === "padeye") {
    const lift = job.lift;
    return `${name}: ${(lift.lifted_mass_kg / 1000).toLocaleString(undefined, { maximumFractionDigits: 2 })} t on ${lift.lift_points} padeyes, slings at ${lift.sling_angle_deg}\u00b0`;
  }
  if (job.part === "pipe-bracket") return `${name}: NPS ${job.pipe_nps} pipe on supports every ${job.span_m} m`;
  return `${name}: ${job.span_m} × ${job.chord_m} m fin at ${job.speed_kn} knots, up to ${job.max_angle_deg}\u00b0`;
}