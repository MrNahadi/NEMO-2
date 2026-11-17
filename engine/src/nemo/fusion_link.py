"""Link between NEMO and the NEMO Connector add-in running inside Autodesk Fusion.

The add-in calls NEMO on this computer (127.0.0.1). It says hello when Fusion
starts, then asks for work every couple of seconds. Each call counts as a
heartbeat, so NEMO always knows whether Fusion is connected.

Jobs live only in memory and expire if no connector picks them up quickly.
Nothing is written to a shared request file, so opening Fusion or NEMO never
builds a model on its own.
"""

from __future__ import annotations

import json
import os
import shutil
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

CONNECTOR_NAME = "NEMOConnector"
CONNECTOR_VERSION = "1.0.0"
HEARTBEAT_TIMEOUT_S = 8.0
JOB_PICKUP_TIMEOUT_S = 45.0
JOB_RUN_TIMEOUT_S = 180.0


def connector_source() -> Path:
    override = os.environ.get("NEMO_CONNECTOR_SOURCE")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "fusion" / CONNECTOR_NAME


def fusion_addins_dir() -> Path:
    override = os.environ.get("NEMO_FUSION_ADDINS_DIR")
    if override:
        return Path(override)
    appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(appdata) / "Autodesk" / "Autodesk Fusion 360" / "API" / "AddIns"


@dataclass
class FusionJob:
    id: str
    kind: str
    payload: dict
    created: float = field(default_factory=time.time)
    state: str = "waiting"  # waiting, sent, done, failed, expired
    sent: float | None = None
    result: dict | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return {"id": self.id, "kind": self.kind, "state": self.state, "result": self.result, "error": self.error,
                "created": self.created}


class FusionLink:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.session: str | None = None
        self.connected_since: float | None = None
        self.last_seen: float | None = None
        self.fusion_version: str | None = None
        self.connector_version: str | None = None
        self.jobs: dict[str, FusionJob] = {}
        self.activity: list[dict] = []

    # ------------------------------------------------------------- connector
    def hello(self, session: str, connector_version: str, fusion_version: str) -> dict:
        with self._lock:
            now = time.time()
            if session != self.session:
                self.session = session
                self.connected_since = now
                # A new Fusion session never inherits work queued for an old one.
                for job in self.jobs.values():
                    if job.state in ("waiting", "sent"):
                        job.state, job.error = "expired", "Fusion restarted before the model was built."
            self.last_seen = now
            self.fusion_version = fusion_version
            self.connector_version = connector_version
            self._note("connected", f"Fusion {fusion_version} connected")
        return {"ok": True, "server_time": now, "nemo_connector_version": CONNECTOR_VERSION}

    def poll(self, session: str) -> dict | None:
        with self._lock:
            if session != self.session:
                return {"kind": "hello_again"}
            now = time.time()
            self.last_seen = now
            self._expire(now)
            for job in sorted(self.jobs.values(), key=lambda j: j.created):
                if job.state == "waiting" and job.created >= (self.connected_since or now):
                    job.state, job.sent = "sent", now
                    return {"id": job.id, "kind": job.kind, "payload": job.payload}
        return None

    def finish(self, job_id: str, ok: bool, result: dict | None, error: str | None) -> FusionJob:
        with self._lock:
            job = self.jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)
            job.state = "done" if ok else "failed"
            job.result, job.error = result, error
            self._note("model" if ok else "error", error or "Model built in Fusion")
            return job

    # ------------------------------------------------------------------- app
    @property
    def connected(self) -> bool:
        return self.last_seen is not None and time.time() - self.last_seen < HEARTBEAT_TIMEOUT_S

    def submit(self, kind: str, payload: dict) -> FusionJob:
        with self._lock:
            if not self.connected:
                raise ConnectionError("Fusion is not connected. Start Fusion with the NEMO Connector, then try again.")
            job = FusionJob(id=uuid.uuid4().hex, kind=kind, payload=payload)
            self.jobs[job.id] = job
            return job

    def job(self, job_id: str) -> FusionJob:
        with self._lock:
            self._expire(time.time())
            return self.jobs[job_id]

    def note(self, kind: str, message: str, **data) -> None:
        with self._lock:
            self._note(kind, message, **data)

    def status(self) -> dict:
        installed = (fusion_addins_dir() / CONNECTOR_NAME / f"{CONNECTOR_NAME}.manifest").exists()
        installed_version = None
        if installed:
            try:
                manifest = json.loads((fusion_addins_dir() / CONNECTOR_NAME / f"{CONNECTOR_NAME}.manifest").read_text(encoding="utf-8"))
                installed_version = manifest.get("version")
            except (OSError, ValueError):
                pass
        return {
            "installed": installed,
            "installed_version": installed_version,
            "current_version": CONNECTOR_VERSION,
            "update_available": installed and installed_version != CONNECTOR_VERSION,
            "connected": self.connected,
            "seconds_since_seen": None if self.last_seen is None else round(time.time() - self.last_seen, 1),
            "fusion_version": self.fusion_version,
            "connector_version": self.connector_version,
            "addins_folder": str(fusion_addins_dir()),
            "activity": list(self.activity[-8:]),
        }

    # -------------------------------------------------------------- internals
    def _expire(self, now: float) -> None:
        for job in self.jobs.values():
            if job.state == "waiting" and now - job.created > JOB_PICKUP_TIMEOUT_S:
                job.state, job.error = "expired", "Fusion did not pick up the request. Check that Fusion is open and not busy."
            elif job.state == "sent" and job.sent and now - job.sent > JOB_RUN_TIMEOUT_S:
                job.state, job.error = "expired", "Fusion took too long to build the model. Look in Fusion for a message."

    def _note(self, kind: str, message: str, **data) -> None:
        self.activity.append({"kind": kind, "message": message, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **data})
        del self.activity[:-40]


def install_connector(server_url: str) -> Path:
    """Copy the add-in into Fusion's add-ins folder and point it at this NEMO."""
    source = connector_source()
    if not (source / f"{CONNECTOR_NAME}.py").exists():
        raise FileNotFoundError(f"The connector files are missing from {source}. Reinstall NEMO.")
    target = fusion_addins_dir() / CONNECTOR_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.log"))
    (target / "config.json").write_text(json.dumps({"server": server_url}, indent=2), encoding="utf-8")
    return target
