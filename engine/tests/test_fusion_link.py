"""Fusion connector protocol, tested by acting as the add-in."""

from __future__ import annotations

import functools
import json
import time

import pytest
from fastapi.testclient import TestClient

import nemo.fusion_link as fusion_link
import nemo.server as server
from nemo.parts.padeye.pipeline import run_padeye_job

JOB = {"lift": {"lifted_mass_kg": 3000, "lift_points": 2, "sling_angle_deg": 60}}


@pytest.fixture(scope="module")
def setup(tmp_path_factory):
    root = tmp_path_factory.mktemp("projects")
    mp = pytest.MonkeyPatch()
    mp.setattr(server, "run_padeye_job", functools.partial(run_padeye_job, fea_levels=(1.0,)))
    mp.setenv("NEMO_FUSION_ADDINS_DIR", str(tmp_path_factory.mktemp("addins")))
    client = TestClient(server.create_app(projects_root=root))
    project = client.post("/api/projects", json={"name": "Fusion test"}).json()
    started = client.post(f"/api/projects/{project['id']}/runs", json={"job": JOB}).json()
    for _ in range(240):
        if client.get(f"/api/runs/{started['id']}").json()["state"] in ("done", "failed"):
            break
        time.sleep(0.5)
    detail = client.get(f"/api/projects/{project['id']}").json()
    yield client, project, detail["latest_run"], detail["results"]["designs"][0]["key"]
    mp.undo()


def connect(client, session="s1"):
    return client.post("/api/fusion/hello", json={"session": session, "connector_version": "1.0.0", "fusion_version": "2.0.test"})


def test_install_copies_the_add_in_and_points_it_at_nemo(setup):
    client, *_ = setup
    status = client.get("/api/fusion/status").json()
    assert status["installed"] is False and status["connected"] is False
    installed = client.post("/api/fusion/install").json()
    assert installed["installed"] is True
    folder = fusion_link.fusion_addins_dir() / "NEMOConnector"
    assert (folder / "NEMOConnector.py").exists()
    manifest = json.loads((folder / "NEMOConnector.manifest").read_text(encoding="utf-8"))
    assert manifest["runOnStartup"] is True and manifest["version"] == fusion_link.CONNECTOR_VERSION
    assert json.loads((folder / "config.json").read_text(encoding="utf-8"))["server"].startswith("http")
    assert (folder / "resources" / "NEMOConnectorCheck" / "16x16.png").exists()


def test_open_needs_a_connected_fusion(setup):
    client, project, run, design = setup
    response = client.post("/api/fusion/open", json={"project_id": project["id"], "run": run, "design": design})
    assert response.status_code == 409
    assert "not connected" in response.json()["detail"]


def test_open_design_round_trip(setup):
    client, project, run, design = setup
    assert connect(client).status_code == 200
    assert client.get("/api/fusion/status").json()["connected"] is True
    assert client.get("/api/fusion/poll?session=s1").json()["job"] is None  # nothing runs on connect

    job = client.post("/api/fusion/open", json={"project_id": project["id"], "run": run, "design": design}).json()
    sent = client.get("/api/fusion/poll?session=s1").json()["job"]
    assert sent["id"] == job["id"] and sent["kind"] == "open_design"
    names = {p["name"] for p in sent["payload"]["parameters"]}
    assert {"nemo_t", "nemo_R", "nemo_Dh", "nemo_L", "nemo_h", "nemo_tc", "nemo_Rc"} <= names
    assert "/fusion/sheet?" in sent["payload"]["sheet_url"]
    assert client.get("/api/fusion/poll?session=s1").json()["job"] is None  # handed out once only

    volume = sent["payload"]["nemo_volume_mm3"] * 1.0004
    material = sent["payload"]["material"]
    assert material["yield_strength_mpa"] > 207 and material["tensile_strength_mpa"] > material["yield_strength_mpa"]
    assert material["elastic_modulus_gpa"] == 210 and "(NEMO" in material["fusion_name"]
    done = client.post(f"/api/fusion/jobs/{job['id']}/result",
                       json={"ok": True, "result": {"volume_mm3": volume, "fusion_mass_kg": 0.3, "parametric": True,
                                                    "fusion_material": material["fusion_name"],
                                                    "fusion_yield_mpa": material["yield_strength_mpa"],
                                                    "fusion_tensile_mpa": material["tensile_strength_mpa"],
                                                    "fusion_modulus_gpa": material["elastic_modulus_gpa"]}}).json()
    assert done["state"] == "done"
    assert done["result"]["volume_difference"] == pytest.approx(0.0004, rel=1e-6)
    assert done["result"]["material_matches"] is True
    records = client.get(f"/api/projects/{project['id']}/runs/{run}/fusion?design={design}").json()
    assert records["model"]["parametric"] is True
    sheet = client.get(f"/fusion/sheet?project={project['id']}&run={run}&design={design}").text
    assert "Set by the connector" in sheet


def test_material_left_at_fusion_steel_is_flagged(setup):
    client, project, run, design = setup
    connect(client, "s9")
    job = client.post("/api/fusion/open", json={"project_id": project["id"], "run": run, "design": design}).json()
    client.get("/api/fusion/poll?session=s9")
    done = client.post(f"/api/fusion/jobs/{job['id']}/result",
                       json={"ok": True, "result": {"volume_mm3": 1000.0, "fusion_material": "Steel",
                                                    "fusion_yield_mpa": 207.0, "fusion_tensile_mpa": 345.0,
                                                    "fusion_modulus_gpa": 210.0}}).json()
    assert done["result"]["material_matches"] is False
    sheet = client.get(f"/fusion/sheet?project={project['id']}&run={run}&design={design}").text
    assert "207 MPa" in sheet and "Manage Physical Materials" in sheet and "legend" in sheet


def test_a_new_fusion_session_drops_old_requests(setup):
    client, project, run, design = setup
    connect(client, "s2")
    job = client.post("/api/fusion/open", json={"project_id": project["id"], "run": run, "design": design}).json()
    connect(client, "s3")  # Fusion restarted before picking it up
    assert client.get("/api/fusion/poll?session=s3").json()["job"] is None
    assert client.get(f"/api/fusion/jobs/{job['id']}").json()["state"] == "expired"
    assert client.get("/api/fusion/poll?session=s2").json()["job"]["kind"] == "hello_again"


def test_check_in_nemo_with_edited_dimensions(setup):
    client, project, run, design = setup
    detail = client.get(f"/api/projects/{project['id']}").json()
    original = detail["results"]["designs"][0]["check_report"]["design"]
    same = client.post("/api/fusion/check", json={"project_id": project["id"], "run": run, "design": design,
                                                  "parameters": {"nemo_t": original["main_thickness_mm"]}}).json()
    assert same["ok"] and same["passed"] and same["changed"] == {}

    thinner = client.post("/api/fusion/check", json={"project_id": project["id"], "run": run, "design": design,
                                                     "parameters": {"nemo_R": original["head_radius_mm"] * 0.75,
                                                                    "nemo_L": original["base_length_mm"] * 0.5}}).json()
    assert thinner["ok"]
    assert thinner["mass_kg"] < same["mass_kg"]
    assert "head_radius_mm" in thinner["changed"]
    assert thinner["governing"]["use"] > same["governing"]["use"]

    broken = client.post("/api/fusion/check", json={"project_id": project["id"], "run": run, "design": design,
                                                    "parameters": {"nemo_Dh": original["head_radius_mm"] * 3}}).json()
    assert broken["ok"] is False and broken["problems"]

    activity = client.get("/api/fusion/status").json()["activity"]
    assert any(a["kind"] == "check" for a in activity)


def test_cross_check_is_recorded_and_goes_into_the_report(setup):
    client, project, run, design = setup
    sheet = client.get(f"/fusion/sheet?project={project['id']}&run={run}&design={design}")
    assert sheet.status_code == 200 and "Bearing Load" in sheet.text

    detail = client.get(f"/api/projects/{project['id']}").json()
    fea = detail["results"]["designs"][0]["fea"]
    reaction = sum(v * v for v in fea["levels"][-1]["applied_force_n"]) ** 0.5
    record = client.post("/api/fusion/crosscheck", json={
        "project_id": project["id"], "run": run, "design": design, "reaction_n": reaction,
        "peak_stress_mpa": fea["head_von_mises_mpa"] * 1.08, "max_displacement_mm": 0.02, "checked_by": "A. Engineer"}).json()
    assert record["agrees"] is True
    assert record["stress_difference"] == pytest.approx(0.08, rel=1e-6)

    pdf = client.get(f"/api/projects/{project['id']}/runs/{run}/report.pdf?design={design}")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    assert client.post("/api/fusion/crosscheck", json={"project_id": project["id"], "run": run,
                                                       "design": design}).status_code == 422

    wrong = client.post("/api/fusion/crosscheck", json={
        "project_id": project["id"], "run": run, "design": design, "reaction_n": reaction * 0.05,
        "peak_stress_mpa": fea["head_von_mises_mpa"], "checked_by": "A. Engineer"})
    assert wrong.status_code == 422 and "Reaction Force" in wrong.json()["detail"]
    kept = client.get(f"/api/projects/{project['id']}/runs/{run}/fusion?design={design}").json()["crosscheck"]
    assert kept["agrees"] is True  # the rejected entry did not replace the earlier record
