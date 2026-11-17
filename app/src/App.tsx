import { Moon, ShieldCheck, Sun } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "./api";
import { FusionLight, FusionProvider } from "./components/Fusion";
import { Banner } from "./components/ui";
import { Assumptions } from "./screens/Assumptions";
import { DescribeLift } from "./screens/DescribeLift";
import { Home } from "./screens/Home";
import { NewDesign } from "./screens/NewDesign";
import { BracketAssumptions, DescribeBracket, DescribeFin, FinAssumptions } from "./screens/PartForms";
import { Results } from "./screens/Results";
import { Running } from "./screens/Running";
import { Verification } from "./screens/Verification";
import type { Job, PartId, Project, Reference } from "./types";

type Screen =
  | { name: "home" }
  | { name: "new" }
  | { name: "describe" }
  | { name: "assumptions" }
  | { name: "running"; runId: string }
  | { name: "results" }
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
    window.scrollTo(0, 0);
    document.querySelector(".panel")?.scrollTo(0, 0);
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
      <div className="page page-narrow">
        <Banner kind="error">{fatal}</Banner>
      </div>
    );
  } else if (!reference) {
    body = <div className="page page-narrow muted">Starting NEMO…</div>;
  } else if (screen.name === "home") {
    body = <Home onNew={() => setScreen({ name: "new" })} onOpen={openProject} />;
  } else if (screen.name === "new") {
    body = <NewDesign onCreated={openProject} onCancel={() => setScreen({ name: "home" })} />;
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
  } else if (project && screen.name === "results" && project.results) {
    body = <Results project={project} onEdit={() => setScreen({ name: "describe" })} onRunAgain={startRun} />;
  }

  return (
    <FusionProvider>
    <div className="shell">
      <header className="topbar">
        <button className="brand" onClick={() => setScreen({ name: "home" })} aria-label="NEMO home">
          <span className="brand-mark">N</span> NEMO
        </button>
        <div className="topbar-meta">
          {project && !["home", "new", "verification"].includes(screen.name) && <span>{project.name}</span>}
          <FusionLight />
          <button
            className="btn btn-ghost nav-btn"
            aria-pressed={screen.name === "verification"}
            onClick={() => setScreen({ name: "verification" })}
          >
            <ShieldCheck aria-hidden /> Verification
          </button>
          <button
            className="btn btn-ghost"
            style={{ height: 36, padding: "0 10px" }}
            aria-label={theme === "light" ? "Switch to dark theme" : "Switch to light theme"}
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
          >
            {theme === "light" ? <Moon aria-hidden /> : <Sun aria-hidden />}
          </button>
        </div>
      </header>
      <main className="panel">{body}</main>
    </div>
    </FusionProvider>
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