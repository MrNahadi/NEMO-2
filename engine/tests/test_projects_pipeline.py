"""Project folders and the full padeye run."""

from __future__ import annotations

import json

import pytest

from nemo.loads import LiftScenario
from nemo.parts.padeye.pipeline import run_padeye_job
from nemo.parts.padeye.sizing import PadeyeJob
from nemo.projects import create_project, find_project, list_projects, load_project, new_run_dir, save_inputs


def test_each_project_gets_its_own_folder(tmp_path):
    a = create_project("Engine lift", root=tmp_path)
    b = create_project("Engine lift", root=tmp_path)
    assert a.folder != b.folder
    assert a.id != b.id
    assert {p.id for p in list_projects(tmp_path)} == {a.id, b.id}


def test_new_project_is_empty_and_runs_nothing(tmp_path):
    project = create_project("Fresh", root=tmp_path)
    assert project.inputs is None
    assert project.runs() == []
    assert project.latest_results() is None
    assert sorted(p.name for p in project.folder.iterdir()) == ["project.json"]


def test_inputs_are_saved_and_reloaded(tmp_path):
    project = create_project("Saved", root=tmp_path)
    job = PadeyeJob(LiftScenario(3000, 2, 60))
    save_inputs(project, job.to_dict())
    reloaded = load_project(project.folder)
    assert PadeyeJob.from_dict(reloaded.inputs) == job
    assert find_project(project.id, tmp_path).name == "Saved"


def test_unknown_part_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        create_project("Fin", part="rudder", root=tmp_path)


def test_full_run_writes_results_and_files(tmp_path):
    project = create_project("Pipeline", root=tmp_path)
    run_dir = new_run_dir(project)
    messages = []
    summary = run_padeye_job(
        PadeyeJob(LiftScenario(3000, 2, 60)),
        run_dir,
        project_name=project.name,
        progress=lambda m, f: messages.append((m, f)),
        fea_levels=(1.0,),
    )
    assert messages[-1] == ("Done", 1.0)
    assert [f for _, f in messages] == sorted(f for _, f in messages)
    saved = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    assert saved["designs"][0]["key"] == "lightest"
    for design in saved["designs"]:
        assert design["check_report"]["passed"]
        assert design["fea"]["levels"][0]["reaction_balance_error"] < 1e-6
        for key in ("step", "stl", "dxf", "stress_surface"):
            assert (run_dir / design["files"][key]).stat().st_size > 0
        surface = json.loads((run_dir / design["files"]["stress_surface"]).read_text(encoding="utf-8"))
        assert len(surface["positions"]) == 3 * len(surface["von_mises"])
        assert max(surface["triangles"]) < len(surface["von_mises"])
    latest = project.latest_results()
    assert [d["key"] for d in latest["designs"]] == [d["key"] for d in summary["designs"]]
    assert [d["check_report"]["mass_kg"] for d in latest["designs"]] == [
        d["check_report"]["mass_kg"] for d in summary["designs"]
    ]


def test_duplicate_copies_answers_but_not_results(tmp_path):
    from nemo.projects import duplicate_project

    original = save_inputs(create_project("Crane", root=tmp_path), PadeyeJob(LiftScenario(2000, 2, 60)).to_dict())
    new_run_dir(original)
    copy = duplicate_project(original)
    assert copy.id != original.id
    assert copy.name == "Copy of Crane"
    assert copy.inputs == original.inputs
    assert copy.runs() == []


def test_delete_moves_the_folder_away(tmp_path, monkeypatch):
    import sys
    import types

    from nemo.projects import delete_project

    # Use the fallback path so the test does not touch the real Recycle Bin.
    fake = types.ModuleType("send2trash")

    def refuse(path):
        raise OSError("no recycle bin in tests")

    fake.send2trash = refuse
    monkeypatch.setitem(sys.modules, "send2trash", fake)
    project = create_project("Old job", root=tmp_path)
    where = delete_project(project)
    assert not project.folder.exists()
    assert (tmp_path / "_deleted").exists() and where.startswith(str(tmp_path / "_deleted"))
    assert all(p.id != project.id for p in list_projects(tmp_path))
