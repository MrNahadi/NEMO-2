"""Local web server: the engine's API plus the built app.

Runs on this computer only (127.0.0.1). Nothing is calculated until the app
asks for it: opening the app or a project only reads files.
"""

from __future__ import annotations

import argparse
import json
import os
import threading
import uuid
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import __version__
from .data import materials, plate_stock, shackles
from .parts.padeye.pipeline import EngineeringLog, run_padeye_job
from .parts.padeye.sizing import NoFeasibleDesign, PadeyeJob
from .parts.registry import get_part, reference_extras
from .projects import (
    Project,
    create_project,
    default_projects_root,
    delete_project,
    duplicate_project,
    find_project,
    list_projects,
    new_run_dir,
    rename_project,
    save_inputs,
)
from .fusion_link import FusionLink, install_connector
from .fusion_sheet import render_sheet
from .parts.padeye import fusion as padeye_fusion
from .report_pdf import build_report_pdf
from .rules import PART_RULE_SETS, RULE_SETS
from . import verification

FEA_LEVELS: tuple[float, ...] | None = None  # tests set fewer mesh levels
APP_DIR = Path(os.environ.get("NEMO_APP_DIR", Path(__file__).resolve().parents[3] / "app" / "dist"))


# ------------------------------------------------------------------ runs
@dataclass
class RunStatus:
    id: str
    project_id: str
    state: str = "queued"  # queued, running, done, failed
    message: str = "Waiting to start"
    fraction: float = 0.0
    run_name: str | None = None
    error: str | None = None
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    log: EngineeringLog = field(default_factory=EngineeringLog, repr=False)
    result: dict | None = None

    def to_dict(self, since: int = 0) -> dict:
        events = self.log.since(since)
        return {
            "events": events,
            "next": since + len(events),
            "id": self.id,
            "project_id": self.project_id,
            "state": self.state,
            "message": self.message,
            "fraction": self.fraction,
            "run_name": self.run_name,
            "error": self.error,
        }


class RunManager:
    def __init__(self) -> None:
        self._runs: dict[str, RunStatus] = {}
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="nemo-run")

    def start(self, project: Project, job) -> RunStatus:
        status = RunStatus(id=uuid.uuid4().hex, project_id=project.id)
        self._runs[status.id] = status
        self._pool.submit(self._execute, status, project, job)
        return status

    def start_verification(self, store: Path) -> RunStatus:
        status = RunStatus(id=uuid.uuid4().hex, project_id="verification")
        self._runs[status.id] = status

        def work() -> None:
            status.state, status.message = "running", "Running the benchmarks"
            try:
                result = verification.run_all(status.log.emit)
                store.parent.mkdir(parents=True, exist_ok=True)
                store.write_text(json.dumps(result, indent=2), encoding="utf-8")
                status.result = result
                status.state, status.message, status.fraction = "done", "Verification finished", 1.0
            except Exception as exc:  # noqa: BLE001
                status.state, status.error, status.message = "failed", f"Verification could not finish: {exc}", "Failed"

        self._pool.submit(work)
        return status

    def busy(self, project_id: str) -> bool:
        return any(r.project_id == project_id and r.state in ("queued", "running") for r in self._runs.values())

    def get(self, run_id: str) -> RunStatus:
        try:
            return self._runs[run_id]
        except KeyError as exc:
            raise HTTPException(404, "That calculation was not found. It may have been from an earlier session.") from exc

    def _execute(self, status: RunStatus, project: Project, job) -> None:
        def progress(message: str, fraction: float) -> None:
            with status.lock:
                status.message, status.fraction = message, max(status.fraction, fraction)

        status.state = "running"
        try:
            run_dir = new_run_dir(project)
            status.run_name = run_dir.name
            options = {"fea_levels": FEA_LEVELS} if FEA_LEVELS else {}
            if project.part == "padeye":
                run_padeye_job(job, run_dir, project_name=project.name, progress=progress, log=status.log, **options)
            else:
                get_part(project.part).run(job, run_dir, project_name=project.name, progress=progress, log=status.log, **options)
            status.state, status.message, status.fraction = "done", "Designs ready", 1.0
        except NoFeasibleDesign as exc:
            status.state, status.error, status.message = "failed", str(exc), "No design found"
        except Exception as exc:  # noqa: BLE001 - report any failure to the user
            status.state, status.error, status.message = "failed", f"We couldn't finish the calculation: {exc}", "Failed"


# ---------------------------------------------------------------- models
class NewProject(BaseModel):
    name: str
    part: str = "padeye"


class Rename(BaseModel):
    name: str


class JobPayload(BaseModel):
    job: dict[str, Any]


class FusionHello(BaseModel):
    session: str
    connector_version: str = ""
    fusion_version: str = ""


class FusionResult(BaseModel):
    ok: bool
    result: dict[str, Any] | None = None
    error: str | None = None


class DesignRef(BaseModel):
    project_id: str
    run: str
    design: str


class FusionCheck(DesignRef):
    parameters: dict[str, float]


class CrossCheck(DesignRef):
    reaction_n: float | None = None
    peak_stress_mpa: float | None = None
    max_displacement_mm: float | None = None
    checked_by: str = ""
    notes: str = ""


def create_app(projects_root: Path | None = None) -> FastAPI:
    root = Path(projects_root) if projects_root else default_projects_root()
    runs = RunManager()
    fusion = FusionLink()
    app = FastAPI(title="NEMO", version=__version__)

    def project_or_404(project_id: str) -> Project:
        try:
            return find_project(project_id, root)
        except KeyError as exc:
            raise HTTPException(404, "That design could not be found.") from exc

    def parse_job(data: dict, part: str = "padeye"):
        try:
            return get_part(part).job_from_dict(data)
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(422, f"Some answers are missing or not numbers: {exc}") from exc

    def run_dir_or_404(project_id: str, run_name: str, design: str) -> tuple[Project, Path]:
        project = project_or_404(project_id)
        run_dir = (project.runs_dir / run_name).resolve()
        if project.runs_dir.resolve() not in run_dir.parents or not (run_dir / "results.json").exists():
            raise HTTPException(404, "Those results were not found.")
        if not design.isalpha() or not (run_dir / "designs" / design).is_dir():
            raise HTTPException(404, "That design is not in these results.")
        return project, run_dir

    # ------------------------------------------------------------ Fusion
    @app.post("/api/fusion/hello")
    def fusion_hello(body: FusionHello) -> dict:
        return fusion.hello(body.session, body.connector_version, body.fusion_version)

    @app.get("/api/fusion/poll")
    def fusion_poll(session: str) -> dict:
        return {"job": fusion.poll(session)}

    @app.post("/api/fusion/jobs/{job_id}/result")
    def fusion_job_result(job_id: str, body: FusionResult) -> dict:
        try:
            job = fusion.finish(job_id, body.ok, body.result, body.error)
        except KeyError as exc:
            raise HTTPException(404, "That Fusion request is no longer known.") from exc
        if job.kind == "open_design" and body.ok and body.result:
            p = job.payload
            try:
                _, run_dir = run_dir_or_404(p["project_id"], p["run"], p["design_key"])
                job.result = padeye_fusion.record_model(
                    run_dir, p["design_key"], {"fusion_version": fusion.fusion_version, **body.result})
            except HTTPException:
                pass
        return job.to_dict()

    @app.post("/api/fusion/check")
    def fusion_check(body: FusionCheck) -> dict:
        project, run_dir = run_dir_or_404(body.project_id, body.run, body.design)
        summary = padeye_fusion.check_edited(run_dir, body.design, body.parameters)
        if summary["ok"]:
            verdict = "passes every check" if summary["passed"] else "fails a check"
            gov = summary["governing"]
            fusion.note("check", f"{project.name}: edited design {verdict} ({gov['title']}, {gov['use'] * 100:.0f}%)",
                        project_id=project.id, run=body.run, design=body.design, passed=summary["passed"])
        return summary

    @app.get("/api/fusion/status")
    def fusion_status() -> dict:
        return fusion.status()

    @app.post("/api/fusion/install")
    def fusion_install(request: Request) -> dict:
        server_url = str(request.base_url).rstrip("/")
        try:
            target = install_connector(server_url)
        except (OSError, FileNotFoundError) as exc:
            raise HTTPException(500, f"The connector could not be installed: {exc}") from exc
        fusion.note("installed", "NEMO Connector installed in Fusion")
        return {"folder": str(target), **fusion.status()}

    @app.post("/api/fusion/open")
    def fusion_open(body: DesignRef, request: Request) -> dict:
        project, run_dir = run_dir_or_404(body.project_id, body.run, body.design)
        if project.part != "padeye":
            raise HTTPException(422, "Open in Fusion builds padeyes for now. Open this design's STEP file in Fusion instead.")
        base = str(request.base_url).rstrip("/")
        sheet = f"{base}/fusion/sheet?project={project.id}&run={body.run}&design={body.design}"
        payload = padeye_fusion.build_request(run_dir, body.design, project_id=project.id, project_name=project.name,
                                              run_name=body.run, sheet_url=sheet)
        try:
            return fusion.submit("open_design", payload).to_dict()
        except ConnectionError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/api/fusion/jobs/{job_id}")
    def fusion_job(job_id: str) -> dict:
        try:
            return fusion.job(job_id).to_dict()
        except KeyError as exc:
            raise HTTPException(404, "That Fusion request is no longer known.") from exc

    @app.get("/api/projects/{project_id}/runs/{run_name}/fusion")
    def fusion_records(project_id: str, run_name: str, design: str) -> dict:
        _, run_dir = run_dir_or_404(project_id, run_name, design)
        folder = run_dir / "designs" / design

        def read(name: str):
            path = folder / name
            return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

        return {"model": read("fusion-model.json"), "checks": read("fusion-checks.json") or [],
                "crosscheck": read("fusion-crosscheck.json")}

    @app.post("/api/fusion/crosscheck")
    def fusion_crosscheck(body: CrossCheck) -> dict:
        project, run_dir = run_dir_or_404(body.project_id, body.run, body.design)
        if body.peak_stress_mpa is None and body.reaction_n is None:
            raise HTTPException(422, "Enter at least the peak stress or the reaction force from Fusion.")
        record = padeye_fusion.record_crosscheck(
            run_dir, body.design, reaction_n=body.reaction_n, peak_stress_mpa=body.peak_stress_mpa,
            max_displacement_mm=body.max_displacement_mm, checked_by=body.checked_by, notes=body.notes)
        fusion.note("crosscheck", f"{project.name}: Fusion cross-check recorded", project_id=project.id)
        return record

    @app.get("/fusion/sheet", response_class=HTMLResponse)
    def fusion_sheet(project: str, run: str, design: str) -> str:
        proj, run_dir = run_dir_or_404(project, run, design)
        return render_sheet(run_dir, design, project_id=proj.id, project_name=proj.name, run_name=run)

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True, "version": __version__, "projects_folder": str(root)}

    @app.get("/api/reference")
    def reference() -> dict:
        return {
            "materials": [
                {
                    "id": m.id,
                    "name": m.name,
                    "family": m.family,
                    "source": m.source,
                    "tensile_strength_mpa": m.tensile_strength_mpa,
                    "yield_bands": [b.__dict__ for b in m.yield_bands],
                }
                for m in materials().values()
            ],
            "plates": plate_stock(),
            "shackles": [s.__dict__ for s in shackles()],
            "rule_sets": [{"id": rid, "name": cls.full_name} for rid, cls in RULE_SETS.items()],
            "part_rule_sets": {part: list(ids) for part, ids in PART_RULE_SETS.items()},
            "default_job": PadeyeJob.from_dict({"lift": {"lifted_mass_kg": 5000}}).to_dict(),
            **reference_extras(),
        }

    @app.get("/api/projects")
    def projects() -> list[dict]:
        return [p.to_dict() for p in list_projects(root)]

    @app.post("/api/projects")
    def new_project(body: NewProject) -> dict:
        try:
            return create_project(body.name, body.part, root).to_dict()
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/api/projects/{project_id}")
    def get_project(project_id: str) -> dict:
        project = project_or_404(project_id)
        data = project.to_dict()
        data["results"] = project.latest_results()
        data["latest_run"] = project.runs()[-1].name if project.runs() else None
        return data

    @app.patch("/api/projects/{project_id}")
    def rename(project_id: str, body: Rename) -> dict:
        return rename_project(project_or_404(project_id), body.name).to_dict()

    @app.delete("/api/projects/{project_id}")
    def remove(project_id: str) -> dict:
        project = project_or_404(project_id)
        if runs.busy(project_id):
            raise HTTPException(409, "This design is still calculating. Wait for it to finish, then delete it.")
        where = delete_project(project)
        return {"deleted": project_id, "moved_to": where}

    @app.post("/api/projects/{project_id}/duplicate")
    def duplicate(project_id: str) -> dict:
        return duplicate_project(project_or_404(project_id), root).to_dict()

    @app.post("/api/projects/{project_id}/reveal")
    def reveal(project_id: str) -> dict:
        folder = project_or_404(project_id).folder
        if not hasattr(os, "startfile"):
            raise HTTPException(501, f"Open this folder yourself: {folder}")
        os.startfile(str(folder))  # noqa: S606 - local app, opens File Explorer on this computer
        return {"folder": str(folder)}

    @app.put("/api/projects/{project_id}/inputs")
    def put_inputs(project_id: str, body: JobPayload) -> dict:
        project = project_or_404(project_id)
        job = parse_job(body.job, project.part)
        return save_inputs(project, job.to_dict()).to_dict()

    def run_preview(part: str, raw: dict) -> dict:
        try:
            spec = get_part(part)
        except KeyError as exc:
            raise HTTPException(404, str(exc)) from exc
        job = parse_job(raw, part)
        issues = spec.problems(job)
        if issues:
            raise HTTPException(422, " ".join(issues))
        try:
            data = spec.preview(job)
        except NoFeasibleDesign as exc:
            return {"feasible": False, "reason": str(exc), "loads": job.loads.to_dict()}
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        data["feasible"] = True
        return data

    @app.post("/api/padeye/preview")
    def preview(body: JobPayload) -> dict:
        return run_preview("padeye", body.job)

    @app.post("/api/parts/{part}/preview")
    def part_preview(part: str, body: JobPayload) -> dict:
        return run_preview(part, body.job)

    @app.post("/api/projects/{project_id}/runs")
    def start_run(project_id: str, body: JobPayload) -> dict:
        project = project_or_404(project_id)
        job = parse_job(body.job, project.part)
        issues = get_part(project.part).problems(job)
        if issues:
            raise HTTPException(422, " ".join(issues))
        project = save_inputs(project, job.to_dict())
        return runs.start(project, job).to_dict()

    @app.get("/api/runs/{run_id}")
    def run_status(run_id: str, since: int = 0) -> dict:
        status = runs.get(run_id)
        data = status.to_dict(max(since, 0))
        if status.result is not None:
            data["result"] = status.result
        return data

    verification_store = root / "_verification" / "latest.json"

    @app.get("/api/verification")
    def verification_latest() -> dict:
        if verification_store.exists():
            return {"latest": json.loads(verification_store.read_text(encoding="utf-8")),
                    "benchmarks": [{"id": b[0], "title": b[1], "description": b[2], "source": b[3]} for b in verification.BENCHMARKS]}
        return {"latest": None,
                "benchmarks": [{"id": b[0], "title": b[1], "description": b[2], "source": b[3]} for b in verification.BENCHMARKS]}

    @app.post("/api/verification/runs")
    def verification_start() -> dict:
        return runs.start_verification(verification_store).to_dict()

    @app.get("/api/projects/{project_id}/runs/{run_name}/files/{file_path:path}")
    def run_file(project_id: str, run_name: str, file_path: str):
        project = project_or_404(project_id)
        run_dir = (project.runs_dir / run_name).resolve()
        target = (run_dir / file_path).resolve()
        if run_dir not in target.parents or not target.is_file() or project.runs_dir.resolve() not in run_dir.parents:
            raise HTTPException(404, "File not found.")
        download_name = f"{project.name} - {target.parent.name} - {target.name}"
        return FileResponse(target, filename=download_name)

    @app.get("/api/projects/{project_id}/runs/{run_name}/bundle.zip")
    def bundle(project_id: str, run_name: str, design: str = "lightest"):
        """Everything for one design in one file: report, models, cutting profile, log and search data."""
        import io
        import zipfile

        from fastapi.responses import Response

        project = project_or_404(project_id)
        run_dir = (project.runs_dir / run_name).resolve()
        if project.runs_dir.resolve() not in run_dir.parents or not (run_dir / "results.json").exists():
            raise HTTPException(404, "Those results were not found.")
        if not design.isalpha() or not (run_dir / "designs" / design).is_dir():
            raise HTTPException(404, "That design is not in these results.")
        report_pdf = run_dir / "designs" / design / "calculation-report.pdf"
        if not report_pdf.exists():
            build_report_pdf(run_dir, design, project_name=project.name, run_name=run_name, target=report_pdf)
        safe = "".join(ch if ch.isalnum() or ch in " -_" else "_" for ch in project.name).strip() or "design"
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted((run_dir / "designs" / design).iterdir()):
                if path.is_file() and path.suffix in (".pdf", ".step", ".stl", ".dxf"):
                    archive.write(path, f"{safe}/{path.name}")
            for name in ("results.json", "engineering-log.json", "designs-evaluated.csv"):
                if (run_dir / name).exists():
                    archive.write(run_dir / name, f"{safe}/run-data/{name}")
        return Response(
            buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{safe} - {design}.zip"'},
        )

    @app.get("/api/projects/{project_id}/runs/{run_name}/report.pdf")
    def report(project_id: str, run_name: str, design: str = "lightest", download: bool = False):
        project = project_or_404(project_id)
        run_dir = (project.runs_dir / run_name).resolve()
        if project.runs_dir.resolve() not in run_dir.parents or not (run_dir / "results.json").exists():
            raise HTTPException(404, "Those results were not found.")
        if not design.isalpha():
            raise HTTPException(404, "That design is not in these results.")
        target = run_dir / "designs" / design / "calculation-report.pdf"
        if not target.exists():
            try:
                build_report_pdf(run_dir, design, project_name=project.name, run_name=run_name, target=target)
            except KeyError as exc:
                raise HTTPException(404, "That design is not in these results.") from exc
        return FileResponse(target, media_type="application/pdf", filename=f"{project.name} - {design} - calculation.pdf",
                            content_disposition_type="attachment" if download else "inline")

    if APP_DIR.exists():
        app.mount("/", _AppFiles(directory=APP_DIR, html=True), name="app")

    return app


class _AppFiles(StaticFiles):
    """Serves the built app. The start page is never cached, so an updated NEMO loads its new files."""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if path in ("", ".", "index.html") or not path.startswith("assets"):
            response.headers["Cache-Control"] = "no-cache"
        else:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(description="Start NEMO on this computer.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser automatically.")
    args = parser.parse_args()
    url = f"http://127.0.0.1:{args.port}/"
    if not args.no_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    print(f"NEMO is running at {url}  (close this window to stop NEMO)")
    uvicorn.run(create_app(), host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
