"""Every part NEMO can design, with the few functions the server needs from each.

Adding a part means adding an entry here; the server, the run manager and the
report find it by the project's ``part``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ..data import piping


@dataclass(frozen=True)
class PartSpec:
    id: str
    title: str
    job_from_dict: Callable[[dict], Any]
    default_job: Callable[[], dict]
    problems: Callable[[Any], list[str]]
    run: Callable[..., dict]
    preview: Callable[[Any], dict]


# ------------------------------------------------------------------ padeye
def _padeye_from_dict(data: dict):
    from .padeye.sizing import PadeyeJob

    return PadeyeJob.from_dict(data)


def _padeye_default() -> dict:
    return _padeye_from_dict({"lift": {"lifted_mass_kg": 5000}}).to_dict()


def _padeye_run(job, run_dir, **kwargs) -> dict:
    from .padeye.pipeline import run_padeye_job

    return run_padeye_job(job, run_dir, **kwargs)


def _padeye_preview(job) -> dict:
    from .padeye.sizing import size_padeye
    from .padeye.working import explain, load_steps

    report = size_padeye(job, quick=True)
    data = explain(report).to_dict()
    data["load_steps"] = [s.to_dict() for s in load_steps(job.scenario, job.loads)]
    data["outline"] = report.design.outline_polyline(arc_segments=48)
    return data


# ----------------------------------------------------------------- bracket
def _bracket_from_dict(data: dict):
    from .bracket.job import BracketJob

    return BracketJob.from_dict(data)


def _bracket_run(job, run_dir, **kwargs) -> dict:
    from .bracket.pipeline import run_bracket_job

    return run_bracket_job(job, run_dir, **kwargs)


def _bracket_preview(job) -> dict:
    from .bracket.checks import check_bracket
    from .bracket.job import load_steps
    from .bracket.sizing import size_bracket

    rough = size_bracket(job, quick=True)
    report = check_bracket(rough.design, job, job.loads, _span(job), working=True)
    data = report.to_dict()
    data["load_steps"] = [s.to_dict() for s in load_steps(job, job.loads)]
    return data


def _span(job):
    from .bracket.job import span_analysis

    return span_analysis(job, job.loads)


# -------------------------------------------------------------- stabilizer
def _fin_from_dict(data: dict):
    from .stabilizer.job import FinJob

    return FinJob.from_dict(data)


def _fin_run(job, run_dir, **kwargs) -> dict:
    from .stabilizer.pipeline import run_fin_job

    return run_fin_job(job, run_dir, **kwargs)


def _fin_preview(job) -> dict:
    from .stabilizer.job import load_steps
    from .stabilizer.sizing import size_fin

    report = size_fin(job, quick=True)
    data = report.to_dict()
    data["load_steps"] = [s.to_dict() for s in load_steps(job, job.loads)]
    data["outline"] = report.design.outline(61)
    return data


PARTS: dict[str, PartSpec] = {
    "padeye": PartSpec("padeye", "Lifting padeye", _padeye_from_dict, _padeye_default,
                       lambda job: job.scenario.problems(), _padeye_run, _padeye_preview),
    "pipe-bracket": PartSpec("pipe-bracket", "Pipe support bracket", _bracket_from_dict,
                             lambda: _bracket_from_dict({}).to_dict(), lambda job: job.problems(), _bracket_run, _bracket_preview),
    "stabilizer": PartSpec("stabilizer", "Stabilizer fin", _fin_from_dict, lambda: _fin_from_dict({}).to_dict(),
                           lambda job: job.problems(), _fin_run, _fin_preview),
}


def get_part(part_id: str) -> PartSpec:
    try:
        return PARTS[part_id]
    except KeyError as exc:
        raise KeyError(f"NEMO cannot design '{part_id}'.") from exc


def reference_extras() -> dict:
    data = piping()
    return {
        "parts": {pid: {"title": spec.title, "default_job": spec.default_job()} for pid, spec in PARTS.items()},
        "piping": {
            "pipes": data["pipes"],
            "pipe_materials": data["pipe_materials"],
            "fluids": data["fluids"],
            "insulation": data["insulation"],
            "ubolt_grades": data["ubolts"]["grades"],
        },
    }
