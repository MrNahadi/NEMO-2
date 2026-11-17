import { Box, ChevronRight, Copy, FileText, FolderOpen, FolderSearch, Pencil, Plus, Trash2 } from "lucide-react";
import { useFusion } from "../components/Fusion";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError, reportUrl } from "../api";
import { Dialog, MoreMenu } from "../components/Menu";
import { Banner } from "../components/ui";
import { PART_NAMES } from "../three/PartModel";
import type { PartId, Project } from "../types";

type Pending = { kind: "rename"; project: Project; name: string } | { kind: "delete"; project: Project } | null;

export function Home({ onNew, onOpen }: { onNew: () => void; onOpen: (p: Project) => void }) {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [pending, setPending] = useState<Pending>(null);
  const [busy, setBusy] = useState(false);
  const fusion = useFusion();

  const load = useCallback(() => {
    api.projects().then(setProjects).catch((e) => setError(e instanceof ApiError ? e.message : String(e)));
  }, []);
  useEffect(load, [load]);

  async function act(task: () => Promise<string | void>) {
    setBusy(true);
    setError(null);
    try {
      const message = await task();
      if (message) setNotice(message);
      setPending(null);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  const close = useCallback(() => setPending(null), []);

  return (
    <div className="page page-narrow">
      <h1 className="title">Design marine steelwork</h1>
      <p className="lead">
        Lifting padeyes, pipe support brackets and stabilizer fins. Tell NEMO about the job. It picks the sizes from your stock,
        checks them against the design rules, runs a stress check, and gives you a report, a 3D model and cutting files.
      </p>
      <div className="actions">
        <button className="btn btn-primary" onClick={onNew}>
          <Plus aria-hidden /> New design
        </button>
      </div>

      <div className="mt-6 stack gap-2">
        <h2 className="section-title">Saved designs</h2>
        {notice && (
          <div className="banner banner-info" role="status">
            <span style={{ flex: 1 }}>{notice}</span>
            <button className="link" style={{ marginTop: 0 }} onClick={() => setNotice(null)}>
              Dismiss
            </button>
          </div>
        )}
        {error && <Banner kind="error">{error}</Banner>}
        {projects && projects.length === 0 && (
          <p className="muted">No saved designs yet. Your designs will appear here after you create one.</p>
        )}
        {projects && projects.length > 0 && (
          <ul className="card project-list">
            {projects.map((p) => {
              const run = p.runs[p.runs.length - 1];
              return (
                <li key={p.id} className="project-item">
                  <button className="project-row" onClick={() => onOpen(p)}>
                    <FolderOpen aria-hidden size={20} />
                    <span className="stack" style={{ flex: 1, minWidth: 0 }}>
                      <span className="project-name">{p.name}</span>
                      <span className="caption">
                        {PART_NAMES[(p.part as PartId)]?.title ?? "Design"}, {p.runs.length > 0 ? `${p.runs.length} result${p.runs.length > 1 ? "s" : ""}` : "not run yet"}, saved{" "}
                        {relative(p.updated_at ?? p.created_at)}
                      </span>
                    </span>
                    <ChevronRight aria-hidden size={18} />
                  </button>
                  <MoreMenu
                    label={`More options for ${p.name}`}
                    items={[
                      { label: "Open", icon: <FolderOpen aria-hidden />, onSelect: () => onOpen(p) },
                      { label: "Rename", icon: <Pencil aria-hidden />, onSelect: () => setPending({ kind: "rename", project: p, name: p.name }) },
                      {
                        label: "Duplicate",
                        icon: <Copy aria-hidden />,
                        onSelect: () => act(async () => `Made "${(await api.duplicateProject(p.id)).name}" with the same answers. It has no results until you run it.`),
                      },
                      {
                        label: "Open calculation report",
                        icon: <FileText aria-hidden />,
                        disabled: !run,
                        onSelect: () => window.open(reportUrl(p.id, run, "lightest"), "_blank", "noreferrer"),
                      },
                      {
                        label: "Open in Fusion",
                        icon: <Box aria-hidden />,
                        disabled: !run || p.part !== "padeye",
                        onSelect: () =>
                          act(async () => {
                            const model = await fusion.openInFusion(p.id, run, "lightest");
                            if (model) return `Opened the lightest "${p.name}" design in Fusion.`;
                          }),
                      },
                      {
                        label: "Show in folder",
                        icon: <FolderSearch aria-hidden />,
                        onSelect: () => act(async () => {
                          await api.revealProject(p.id);
                        }),
                      },
                      {
                        label: "Delete",
                        icon: <Trash2 aria-hidden />,
                        danger: true,
                        separated: true,
                        onSelect: () => setPending({ kind: "delete", project: p }),
                      },
                    ]}
                  />
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div className="mt-6">
        <Banner kind="info">
          NEMO is a design aid. A competent engineer must review every design, the structure it is welded to and the lifting
          arrangement before anything is made or used.
        </Banner>
      </div>

      {pending?.kind === "rename" && (
        <Dialog
          title="Rename this design"
          onClose={close}
          actions={
            <>
              <button className="btn btn-ghost" onClick={close}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                disabled={busy || !pending.name.trim()}
                onClick={() => act(async () => {
                  await api.renameProject(pending.project.id, pending.name.trim());
                })}
              >
                Rename design
              </button>
            </>
          }
        >
          <div className="input-wrap" style={{ maxWidth: "none" }}>
            <input
              className="input"
              aria-label="Design name"
              value={pending.name}
              onChange={(e) => setPending({ ...pending, name: e.target.value })}
              onKeyDown={(e) => {
                if (e.key === "Enter" && pending.name.trim())
                  act(async () => {
                    await api.renameProject(pending.project.id, pending.name.trim());
                  });
              }}
            />
          </div>
        </Dialog>
      )}

      {pending?.kind === "delete" && (
        <Dialog
          title={`Delete "${pending.project.name}"?`}
          onClose={close}
          actions={
            <>
              <button className="btn btn-ghost" onClick={close}>
                Cancel
              </button>
              <button
                className="btn btn-danger"
                disabled={busy}
                onClick={() =>
                  act(async () => {
                    const out = await api.deleteProject(pending.project.id);
                    return out.moved_to === "recycle_bin"
                      ? `Deleted "${pending.project.name}". It is in the Recycle Bin if you need it back.`
                      : `Deleted "${pending.project.name}". Its folder was moved to ${out.moved_to}.`;
                  })
                }
              >
                Delete design
              </button>
            </>
          }
        >
          <p className="muted">
            {pending.project.runs.length === 0
              ? "The design and its answers move to the Windows Recycle Bin. You can restore them from there."
              : `The design, its answers and its ${pending.project.runs.length === 1 ? "result" : `${pending.project.runs.length} results`} (reports, 3D models and cutting files) move to the Windows Recycle Bin. You can restore them from there.`}
          </p>
        </Dialog>
      )}
    </div>
  );
}

function relative(iso: string): string {
  const then = new Date(iso).getTime();
  const minutes = Math.round((Date.now() - then) / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}
