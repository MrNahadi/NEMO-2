"""Project folders.

Every "New design" gets its own folder, so projects never share files:

    <projects root>/<slug>-<short id>/
        project.json          name, part type, saved inputs
        runs/<run id>/        one folder per "Find designs" press
            results.json
            designs/<key>/    STEP, STL, DXF and stress-plot data per design

Nothing here starts a calculation. Opening a project only reads files.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

PROJECT_FILE = "project.json"
PARTS = ("padeye", "pipe-bracket", "stabilizer")


def default_projects_root() -> Path:
    override = os.environ.get("NEMO_PROJECTS_DIR")
    if override:
        return Path(override)
    return Path.home() / "Documents" / "NEMO Projects"


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    part: str
    created_at: str
    folder: Path
    inputs: dict | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "part": self.part,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "inputs": self.inputs,
            "runs": [r.name for r in self.runs()],
        }

    @property
    def runs_dir(self) -> Path:
        return self.folder / "runs"

    def runs(self) -> list[Path]:
        if not self.runs_dir.exists():
            return []
        return sorted((p for p in self.runs_dir.iterdir() if (p / "results.json").exists()), key=lambda p: p.name)

    def latest_results(self) -> dict | None:
        runs = self.runs()
        if not runs:
            return None
        return json.loads((runs[-1] / "results.json").read_text(encoding="utf-8"))


def create_project(name: str, part: str = "padeye", root: Path | None = None) -> Project:
    if part not in PARTS:
        raise ValueError(f"NEMO cannot design '{part}' yet.")
    clean = name.strip() or "Untitled design"
    base = Path(root) if root else default_projects_root()
    project_id = uuid.uuid4().hex
    folder = base / f"{_slug(clean)}-{project_id[:6]}"
    folder.mkdir(parents=True, exist_ok=False)
    project = Project(project_id, clean, part, _now(), folder)
    _write(project)
    return project


def load_project(folder: Path) -> Project:
    data = json.loads((Path(folder) / PROJECT_FILE).read_text(encoding="utf-8"))
    return Project(
        id=data["id"],
        name=data["name"],
        part=data["part"],
        created_at=data["created_at"],
        folder=Path(folder),
        inputs=data.get("inputs"),
        updated_at=data.get("updated_at"),
    )


def list_projects(root: Path | None = None) -> list[Project]:
    base = Path(root) if root else default_projects_root()
    if not base.exists():
        return []
    found = []
    for child in base.iterdir():
        if (child / PROJECT_FILE).exists():
            try:
                found.append(load_project(child))
            except (OSError, ValueError, KeyError):
                continue
    return sorted(found, key=lambda p: p.updated_at or p.created_at, reverse=True)


def find_project(project_id: str, root: Path | None = None) -> Project:
    for project in list_projects(root):
        if project.id == project_id:
            return project
    raise KeyError(f"No project with id {project_id}")


def save_inputs(project: Project, inputs: dict) -> Project:
    updated = Project(project.id, project.name, project.part, project.created_at, project.folder, inputs, _now())
    _write(updated)
    return updated


def rename_project(project: Project, name: str) -> Project:
    updated = Project(project.id, name.strip() or project.name, project.part, project.created_at, project.folder,
                      project.inputs, _now())
    _write(updated)
    return updated


def new_run_dir(project: Project) -> Path:
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = project.runs_dir / run_id
    path.mkdir(parents=True, exist_ok=False)
    return path


def duplicate_project(project: Project, root: Path | None = None) -> Project:
    """A new, empty project with the same answers. Results are not copied, so the copy starts fresh."""
    copy = create_project(f"Copy of {project.name}", project.part, root or project.folder.parent)
    return save_inputs(copy, project.inputs) if project.inputs else copy


def delete_project(project: Project) -> str:
    """Move a project folder to the Recycle Bin. Returns where it went.

    Falls back to a ``_deleted`` folder next to the projects if the Recycle Bin
    is not available, so nothing is ever erased outright.
    """
    folder = project.folder.resolve()
    if not (folder / PROJECT_FILE).exists():
        raise ValueError("That folder is not a NEMO design.")
    try:
        from send2trash import send2trash

        send2trash(str(folder))
        return "recycle_bin"
    except Exception:  # noqa: BLE001 - any Recycle Bin failure falls back to a safe move
        target = folder.parent / "_deleted" / f"{folder.name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(folder, target)
        return str(target)


def _write(project: Project) -> None:
    payload = {
        "id": project.id,
        "name": project.name,
        "part": project.part,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "inputs": project.inputs,
        "nemo_project_version": 1,
    }
    target = project.folder / PROJECT_FILE
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, target)


def _slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:40] or "design"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
