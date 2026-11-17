import type { EngEvent, FusionJob, FusionRecords, FusionStatus, Job, Preview, Project, Reference, RunStatus, StressSurface, VerificationResult } from "./types";

export class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError("We couldn't reach the NEMO engine. Check that the NEMO window is still open.");
  }
  if (!response.ok) {
    let detail = `Something went wrong (${response.status}).`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* keep the generic message */
    }
    throw new ApiError(detail);
  }
  return response.json() as Promise<T>;
}

export const api = {
  reference: () => request<Reference>("/api/reference"),
  projects: () => request<Project[]>("/api/projects"),
  project: (id: string) => request<Project>(`/api/projects/${id}`),
  createProject: (name: string, part = "padeye") =>
    request<Project>("/api/projects", { method: "POST", body: JSON.stringify({ name, part }) }),
  renameProject: (id: string, name: string) =>
    request<Project>(`/api/projects/${id}`, { method: "PATCH", body: JSON.stringify({ name }) }),
  duplicateProject: (id: string) => request<Project>(`/api/projects/${id}/duplicate`, { method: "POST" }),
  deleteProject: (id: string) => request<{ deleted: string; moved_to: string }>(`/api/projects/${id}`, { method: "DELETE" }),
  revealProject: (id: string) => request<{ folder: string }>(`/api/projects/${id}/reveal`, { method: "POST" }),
  saveInputs: (id: string, job: Job) =>
    request<Project>(`/api/projects/${id}/inputs`, { method: "PUT", body: JSON.stringify({ job }) }),
  preview: (job: Job, signal?: AbortSignal) =>
    request<Preview>(job.part === "padeye" ? "/api/padeye/preview" : `/api/parts/${job.part}/preview`, { method: "POST", body: JSON.stringify({ job }), signal }),
  startRun: (id: string, job: Job) =>
    request<RunStatus>(`/api/projects/${id}/runs`, { method: "POST", body: JSON.stringify({ job }) }),
  runStatus: (runId: string, since = 0) => request<RunStatus>(`/api/runs/${runId}?since=${since}`),
  stressSurface: (projectId: string, run: string, path: string) =>
    request<StressSurface>(fileUrl(projectId, run, path)),
  engineeringLog: (projectId: string, run: string) => request<EngEvent[]>(fileUrl(projectId, run, "engineering-log.json")),
  verification: () =>
    request<{ latest: VerificationResult | null; benchmarks: { id: string; title: string; description: string; source: string }[] }>(
      "/api/verification",
    ),
  startVerification: () => request<RunStatus>("/api/verification/runs", { method: "POST" }),
  fusionStatus: () => request<FusionStatus>("/api/fusion/status"),
  installFusion: () => request<FusionStatus>("/api/fusion/install", { method: "POST" }),
  openInFusion: (project_id: string, run: string, design: string) =>
    request<FusionJob>("/api/fusion/open", { method: "POST", body: JSON.stringify({ project_id, run, design }) }),
  fusionJob: (id: string) => request<FusionJob>(`/api/fusion/jobs/${id}`),
  fusionRecords: (projectId: string, run: string, design: string) =>
    request<FusionRecords>(`/api/projects/${projectId}/runs/${run}/fusion?design=${design}`),
};

export function fileUrl(projectId: string, run: string, path: string): string {
  return `/api/projects/${projectId}/runs/${run}/files/${path.replace(/\\/g, "/")}`;
}

export function reportUrl(projectId: string, run: string, design: string, download = false): string {
  return `/api/projects/${projectId}/runs/${run}/report.pdf?design=${design}${download ? "&download=true" : ""}`;
}

export function bundleUrl(projectId: string, run: string, design: string): string {
  return `/api/projects/${projectId}/runs/${run}/bundle.zip?design=${design}`;
}
