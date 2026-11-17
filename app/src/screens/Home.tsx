import { Anchor, Box, Copy, FileText, FolderOpen, FolderSearch, Pencil, Plus, Search, Ship, Trash2, Wrench, type LucideIcon } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError, reportUrl } from "../api";
import { useFusion } from "../components/Fusion";
import { Dialog, MoreMenu } from "../components/Menu";
import { Page, PageHeader } from "../components/Page";
import { EmptyState, Note, Skeleton, Status } from "../components/ui";
import { PART_NAMES } from "../three/PartModel";
import type { PartId, Project } from "../types";

type Pending = { kind: "rename"; project: Project; name: string } | { kind: "delete"; project: Project } | null;

const PART_ICONS: Record<string, LucideIcon> = { padeye: Anchor, "pipe-bracket": Wrench, stabilizer: Ship };

export function Home({ onNew, onOpen }: { onNew: () => void; onOpen: (p: Project) => void }) {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [pending, setPending] = useState<Pending>(null);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
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

  const q = query.trim().toLowerCase();
  const filtered = projects ? (q ? projects.filter((p) => p.name.toLowerCase().includes(q)) : projects) : null;
  const count = filtered
    ? q
      ? `${filtered.length} of ${projects!.length} design${projects!.length === 1 ? "" : "s"}`
      : `${filtered.length} design${filtered.length === 1 ? "" : "s"}`
    : "";

  return (
    <Page>
      <PageHeader
        title="Designs"
        description="Each design keeps its own inputs, results and files."
        actions={
          <button className="btn btn-primary" onClick={onNew}>
            <Plus aria-hidden /> New design
          </button>
        }
      />

      {(notice || error) && (
        <div className="home-notices">
          {notice && (
            <Note
              kind="success"
              action={
                <button className="btn btn-tertiary btn-sm" onClick={() => setNotice(null)}>
                  Dismiss
                </button>
              }
            >
              {notice}
            </Note>
          )}
          {error && <Note kind="error">{error}</Note>}
        </div>
      )}

      {projects && projects.length === 0 ? (
        <>
          <EmptyState
            icon={<FolderOpen aria-hidden />}
            title="No designs yet"
            description="Your designs will appear here after you create one."
            action={
              <button className="btn btn-primary" onClick={onNew}>
                <Plus aria-hidden /> New design
              </button>
            }
          />
          <div className="mt-4">
            <Note size="small">
              NEMO is a design aid. A competent engineer must review every design, the structure it is welded to and the lifting
              arrangement before anything is made or used.
            </Note>
          </div>
        </>
      ) : (
        <>
          <div className="list-toolbar">
            <div className="input-wrap sm home-search">
              <span className="input-prefix">
                <Search aria-hidden />
              </span>
              <input
                className="input"
                aria-label="Search designs"
                placeholder="Search designs"
                value={query}
                disabled={!projects}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            {filtered ? <span className="list-count">{count}</span> : <Skeleton width={72} height={14} />}
          </div>

          <div className="table-wrap menus">
            <table className="table designs-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Part</th>
                  <th>Status</th>
                  <th className="saved">Saved</th>
                  <th className="menu-h">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {!filtered &&
                  [0, 1, 2, 3].map((i) => (
                    <tr key={i} aria-hidden>
                      <td>
                        <div className="design-cell">
                          <Skeleton width={28} height={28} radius={6} />
                          <Skeleton width={200} height={16} />
                        </div>
                      </td>
                      <td>
                        <Skeleton width={110} height={14} />
                      </td>
                      <td>
                        <Skeleton width={80} height={14} />
                      </td>
                      <td className="saved">
                        <span className="sk-right">
                          <Skeleton width={56} height={14} />
                        </span>
                      </td>
                      <td className="menu-cell" />
                    </tr>
                  ))}
                {filtered?.map((p) => {
                  const run = p.runs[p.runs.length - 1];
                  const PartIcon = PART_ICONS[p.part] ?? FolderOpen;
                  return (
                    <tr key={p.id} className="row-link" onClick={() => onOpen(p)}>
                      <td className="cell-truncate">
                        <div className="design-cell">
                          <span className="part-tile" aria-hidden>
                            <PartIcon />
                          </span>
                          <button
                            type="button"
                            className="design-name"
                            title={p.name}
                            onClick={(e) => {
                              e.stopPropagation();
                              onOpen(p);
                            }}
                          >
                            {p.name}
                          </button>
                        </div>
                      </td>
                      <td className="part">{PART_NAMES[p.part as PartId]?.title ?? "Design"}</td>
                      <td>
                        {p.runs.length === 0 ? (
                          <Status tone="gray">
                            <span className="text-secondary">Not run yet</span>
                          </Status>
                        ) : (
                          <Status tone="gray">
                            {p.runs.length} result{p.runs.length === 1 ? "" : "s"}
                          </Status>
                        )}
                      </td>
                      <td className="saved">{relative(p.updated_at ?? p.created_at)}</td>
                      <td className="menu-cell">
                        <MoreMenu
                          label={`More options for ${p.name}`}
                          items={[
                            { label: "Open", icon: <FolderOpen aria-hidden />, onSelect: () => onOpen(p) },
                            {
                              label: "Rename…",
                              icon: <Pencil aria-hidden />,
                              onSelect: () => setPending({ kind: "rename", project: p, name: p.name }),
                            },
                            {
                              label: "Duplicate",
                              icon: <Copy aria-hidden />,
                              onSelect: () =>
                                act(async () => `Made "${(await api.duplicateProject(p.id)).name}" with the same answers. It has no results until you run it.`),
                            },
                            {
                              label: "View report",
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
                              onSelect: () =>
                                act(async () => {
                                  await api.revealProject(p.id);
                                }),
                            },
                            {
                              label: "Delete…",
                              icon: <Trash2 aria-hidden />,
                              danger: true,
                              separated: true,
                              onSelect: () => setPending({ kind: "delete", project: p }),
                            },
                          ]}
                        />
                      </td>
                    </tr>
                  );
                })}
                {filtered && filtered.length === 0 && (
                  <tr className="designs-empty">
                    <td colSpan={5}>No designs match “{query.trim()}”.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {projects && (
            <div className="mt-4">
              <Note size="small">
                NEMO is a design aid. A competent engineer must review every design, the structure it is welded to and the lifting
                arrangement before anything is made or used.
              </Note>
            </div>
          )}
        </>
      )}

      {pending?.kind === "rename" && (
        <Dialog
          title="Rename design"
          description={`Give “${pending.project.name}” a new name.`}
          onClose={close}
          actions={
            <>
              <button className="btn" onClick={close}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                disabled={busy || !pending.name.trim()}
                onClick={() =>
                  act(async () => {
                    await api.renameProject(pending.project.id, pending.name.trim());
                  })
                }
              >
                Rename design
              </button>
            </>
          }
        >
          <div className="input-wrap">
            <input
              className="input"
              aria-label="Design name"
              value={pending.name}
              onChange={(e) => setPending({ ...pending, name: e.target.value })}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !busy && pending.name.trim())
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
          title="Delete design"
          description={`You are about to delete “${pending.project.name}”.`}
          initialFocus="#delete-cancel"
          onClose={close}
          actions={
            <>
              <button id="delete-cancel" className="btn" onClick={close}>
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
    </Page>
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
