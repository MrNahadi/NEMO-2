"""The API for the pipe support bracket and the stabilizer fin."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

import nemo.server as server


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "FEA_LEVELS", (1.0,))
    return TestClient(server.create_app(projects_root=tmp_path))


def test_reference_lists_every_part(client):
    ref = client.get("/api/reference").json()
    assert set(ref["parts"]) == {"padeye", "pipe-bracket", "stabilizer"}
    assert ref["parts"]["pipe-bracket"]["default_job"]["part"] == "pipe-bracket"
    assert ref["part_rule_sets"]["stabilizer"] == ["iacs-ur-s10"]
    assert any(p["nps"] == "4" for p in ref["piping"]["pipes"])


@pytest.mark.parametrize("part", ["pipe-bracket", "stabilizer"])
def test_preview(client, part):
    data = client.post(f"/api/parts/{part}/preview", json={"job": {}}).json()
    assert data["feasible"] is True
    assert data["checks"] and data["load_steps"]


def test_preview_explains_bad_answers(client):
    response = client.post("/api/parts/pipe-bracket/preview", json={"job": {"span_m": 40}})
    assert response.status_code == 422
    assert "spacing" in response.json()["detail"]
    assert client.post("/api/parts/crane/preview", json={"job": {}}).status_code == 404


@pytest.mark.parametrize("part,step", [("pipe-bracket", "bracket.step"), ("stabilizer", "fin.step")])
def test_full_run_and_report(client, part, step):
    project = client.post("/api/projects", json={"name": f"{part} test", "part": part}).json()
    assert project["part"] == part
    started = client.post(f"/api/projects/{project['id']}/runs", json={"job": {}}).json()
    for _ in range(400):
        status = client.get(f"/api/runs/{started['id']}").json()
        if status["state"] in ("done", "failed"):
            break
        time.sleep(0.5)
    assert status["state"] == "done", status
    detail = client.get(f"/api/projects/{project['id']}").json()
    assert detail["inputs"]["part"] == part
    results = detail["results"]
    assert results["part"] == part
    design = results["designs"][0]
    assert design["files"]["step"].endswith(step)
    assert design["fea"]["levels"][0]["reaction_balance_error"] < 1e-8
    run = detail["latest_run"]
    pdf = client.get(f"/api/projects/{project['id']}/runs/{run}/report.pdf?design={design['key']}")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    kinds = {e["kind"] for e in client.get(f"/api/runs/{started['id']}?since=0").json()["events"]}
    assert {"loads", "search_done", "cad", "mesh", "solve", "fea_done", "done"} <= kinds
    assert ("span" if part == "pipe-bracket" else "hydro") in kinds
    opened = client.post("/api/fusion/open", json={"project_id": project["id"], "run": run, "design": design["key"]})
    assert opened.status_code == 422
