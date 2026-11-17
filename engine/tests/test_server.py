"""Local API used by the app."""

from __future__ import annotations

import functools
import time

import pytest
from fastapi.testclient import TestClient

import nemo.server as server
from nemo.parts.padeye.pipeline import run_padeye_job

JOB = {"lift": {"lifted_mass_kg": 3000, "lift_points": 2, "sling_angle_deg": 60}}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "run_padeye_job", functools.partial(run_padeye_job, fea_levels=(1.0,)))
    return TestClient(server.create_app(projects_root=tmp_path))


def test_health_and_reference(client):
    assert client.get("/api/health").json()["ok"] is True
    ref = client.get("/api/reference").json()
    assert {m["id"] for m in ref["materials"]} >= {"S355", "AH36", "AL5083_H111"}
    assert ref["rule_sets"][0]["id"] == "asme-bth-1"
    assert ref["default_job"]["lift"]["lifted_mass_kg"] == 5000


def test_start_page_is_not_cached(client):
    response = client.get("/")
    if response.status_code == 200:  # only when the app has been built
        assert response.headers["cache-control"] == "no-cache"


def test_new_project_starts_empty(client):
    created = client.post("/api/projects", json={"name": "Generator lift"}).json()
    project = client.get(f"/api/projects/{created['id']}").json()
    assert project["inputs"] is None
    assert project["results"] is None
    assert project["latest_run"] is None


def test_preview_returns_a_design_quickly(client):
    start = time.perf_counter()
    data = client.post("/api/padeye/preview", json={"job": JOB}).json()
    assert time.perf_counter() - start < 1.5
    assert data["feasible"] is True
    assert data["passed"] is True
    assert all(c["working"] for c in data["checks"])
    assert data["load_steps"][2]["symbol"] == "F"
    assert len(data["outline"]) > 10


def test_preview_explains_impossible_jobs(client):
    data = client.post("/api/padeye/preview", json={"job": {"lift": {"lifted_mass_kg": 500000}}}).json()
    assert data["feasible"] is False
    assert "shackle" in data["reason"]


def test_preview_rejects_bad_answers(client):
    response = client.post("/api/padeye/preview", json={"job": {"lift": {"lifted_mass_kg": 1000, "sling_angle_deg": 5}}})
    assert response.status_code == 422
    assert "Sling angle" in response.json()["detail"]


def test_full_run_report_and_files(client):
    project = client.post("/api/projects", json={"name": "Run test"}).json()
    started = client.post(f"/api/projects/{project['id']}/runs", json={"job": JOB}).json()
    for _ in range(240):
        status = client.get(f"/api/runs/{started['id']}").json()
        if status["state"] in ("done", "failed"):
            break
        time.sleep(0.5)
    assert status["state"] == "done", status
    detail = client.get(f"/api/projects/{project['id']}").json()
    assert detail["inputs"]["lift"]["lifted_mass_kg"] == 3000
    run = detail["latest_run"]
    design = detail["results"]["designs"][0]

    report = client.get(f"/api/projects/{project['id']}/runs/{run}/report.pdf?design={design['key']}")
    assert report.status_code == 200
    assert report.headers["content-type"] == "application/pdf"
    assert report.content.startswith(b"%PDF")

    events = client.get(f"/api/runs/{started['id']}?since=0").json()["events"]
    kinds = {e["kind"] for e in events}
    assert {"loads", "shackles", "samples", "design_found", "cad", "mesh", "solve", "fea_done", "done"} <= kinds
    assert [e["seq"] for e in events] == list(range(len(events)))
    later = client.get(f"/api/runs/{started['id']}?since={len(events) - 2}").json()
    assert len(later["events"]) == 2

    log = client.get(f"/api/projects/{project['id']}/runs/{run}/files/engineering-log.json")
    assert log.status_code == 200
    csv_file = client.get(f"/api/projects/{project['id']}/runs/{run}/files/designs-evaluated.csv")
    assert csv_file.text.startswith("target,shackle_wll_t")

    step = client.get(f"/api/projects/{project['id']}/runs/{run}/files/{design['files']['step']}")
    assert step.status_code == 200 and len(step.content) > 1000

    escape = client.get(f"/api/projects/{project['id']}/runs/{run}/files/..%2F..%2Fproject.json")
    assert escape.status_code == 404

    import io
    import zipfile

    bundle = client.get(f"/api/projects/{project['id']}/runs/{run}/bundle.zip?design={design['key']}")
    assert bundle.status_code == 200 and bundle.headers["content-type"] == "application/zip"
    names = zipfile.ZipFile(io.BytesIO(bundle.content)).namelist()
    for expected in ("calculation-report.pdf", "padeye.step", "padeye-cutting.dxf", "run-data/engineering-log.json",
                     "run-data/designs-evaluated.csv"):
        assert any(n.endswith(expected) for n in names), expected
    assert client.get(f"/api/projects/{project['id']}/runs/{run}/bundle.zip?design=..").status_code == 404


def test_project_menu_actions(client, tmp_path, monkeypatch):
    import sys
    import types

    fake = types.ModuleType("send2trash")
    fake.send2trash = lambda path: (_ for _ in ()).throw(OSError("no recycle bin in tests"))
    monkeypatch.setitem(sys.modules, "send2trash", fake)

    project = client.post("/api/projects", json={"name": "Deck crane"}).json()
    client.put(f"/api/projects/{project['id']}/inputs", json={"job": JOB})
    renamed = client.patch(f"/api/projects/{project['id']}", json={"name": "Deck crane 2"}).json()
    assert renamed["name"] == "Deck crane 2"

    copy = client.post(f"/api/projects/{project['id']}/duplicate").json()
    assert copy["name"] == "Copy of Deck crane 2"
    assert copy["inputs"]["lift"]["lifted_mass_kg"] == 3000
    assert copy["runs"] == []

    gone = client.delete(f"/api/projects/{project['id']}")
    assert gone.status_code == 200
    ids = [p["id"] for p in client.get("/api/projects").json()]
    assert project["id"] not in ids and copy["id"] in ids
    assert client.get(f"/api/projects/{project['id']}").status_code == 404
