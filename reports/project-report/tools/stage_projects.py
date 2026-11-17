"""Make a projects folder holding the three case studies, for taking app screenshots.

Copies the run folders produced by make_report_data.py, so nothing is recalculated:
    python stage_projects.py <empty folder>
Then start NEMO on it:  set NEMO_PROJECTS_DIR=<folder>; python -m nemo.server --port 8768 --no-browser
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from nemo.projects import create_project, save_inputs

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    root = Path(sys.argv[1])
    root.mkdir(parents=True, exist_ok=True)
    cases = json.loads((DATA / "cases.json").read_text(encoding="utf-8"))
    for part, case in cases.items():
        run_dir = DATA / case["run_dir"]
        results = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
        project = create_project(case["name"], part, root)
        save_inputs(project, results["job"])
        shutil.copytree(run_dir, project.runs_dir / run_dir.name)
        print(part, "->", project.folder)


if __name__ == "__main__":
    main()
