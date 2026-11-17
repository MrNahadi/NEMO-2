"""Fusion study sheet: a small page shown in a panel inside Fusion.

It lists every value needed to set up the Static Stress cross-check study, and
has a form to send the Fusion results back to NEMO, which compares them with
its own stress check.
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from html import escape
from pathlib import Path


def _kn(n: float) -> str:
    return f"{n / 1000:,.2f} kN"


def render_sheet(run_dir: Path, design_key: str, *, project_id: str, project_name: str, run_name: str) -> str:
    results = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    entry = next(d for d in results["designs"] if d["key"] == design_key)
    report = entry["check_report"]
    material = results["material"]
    loads = results["loads"]
    lift = results["job"]["lift"]
    fea = entry.get("fea") or {}
    level = (fea.get("levels") or [{}])[-1]
    applied = level.get("applied_force_n") or [loads["horizontal_n"], loads["side_n"], loads["vertical_n"]]
    total = math.sqrt(sum(v * v for v in applied))
    yield_mpa = report["values"]["yield_main_mpa"]
    previous_path = run_dir / "designs" / design_key / "fusion-crosscheck.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else None

    steps = [
        ("Study", "New Simulation Study, Static Stress", None),
        ("Material", f"{material['name']}: E {material['elastic_modulus_gpa']:g} GPa, Poisson 0.30, "
                     f"density {material['density_kg_m3']:g} kg/m³, yield {yield_mpa:g} MPa",
         "Check the numbers, not only the name."),
        ("Constraint", "Fixed, on the flat base face (all directions)", "NEMO tags it nemo / fixed_support."),
        ("Load", f"Bearing Load on the hole face, total {_kn(loads['sling_force_n'])} at {lift['sling_angle_deg']:g}° "
                 "from the base, in the plane of the plate", "NEMO tags it nemo / pin_bearing. Enter the total, not force per face."),
        ("Components", f"X {_kn(applied[0])}, Y {_kn(applied[2])} (up), Z {_kn(applied[1])} (through the plate)",
         "Fusion's Y axis points up in this model."),
        ("Mesh", "Local mesh control on the hole; at least 3 elements through the thickness", None),
        ("After solving", f"Reaction should be {_kn(total)}, within 2%. Peak stress near the hole within 15% of "
                          f"{fea.get('head_von_mises_mpa', 0):.1f} MPa.", None),
    ]
    rows = "".join(
        f"<li><span class='k'>{escape(k)}</span><span class='v'>{escape(v)}</span>"
        + (f"<span class='n'>{escape(n)}</span>" if n else "") + "</li>"
        for k, v, n in steps
    )
    prev_html = ""
    if previous:
        verdict = "Agrees with NEMO" if previous.get("agrees") else "Differs from NEMO: review the study set-up"
        try:
            when = datetime.fromisoformat(previous["recorded_at"]).astimezone().strftime("%d %b %Y, %H:%M")
        except (KeyError, TypeError, ValueError):
            when = str(previous.get("recorded_at", ""))
        prev_html = f"<p class='prev'>Last recorded {escape(when)}: {escape(verdict)}.</p>"

    ids = json.dumps({"project_id": project_id, "run": run_name, "design": design_key})
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>NEMO study sheet</title>
<meta name="viewport" content="width=device-width, initial-scale=1"><style>
:root {{ color-scheme: light dark; --bg:#fff; --fg:#1a1a1a; --mut:#5c5c5c; --rule:#e5e5e5; --card:#f6f6f6; --acc:#0a6fd6; --ok:#1a7f4b; --bad:#c0341d; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#1f1f1f; --fg:#eee; --mut:#a8a8a8; --rule:#333; --card:#2a2a2a; --acc:#5aa9ff; --ok:#4cc38a; --bad:#ff6b57; }} }}
* {{ box-sizing: border-box; }}
body {{ margin:0; padding:16px; background:var(--bg); color:var(--fg); font:14px/1.5 "Inter","Segoe UI",system-ui,sans-serif; font-variant-numeric:tabular-nums; }}
h1 {{ font-size:17px; margin:0 0 2px; }} h2 {{ font-size:14px; margin:20px 0 8px; }}
.sub {{ color:var(--mut); font-size:12px; margin:0 0 12px; }}
ol {{ list-style:none; padding:0; margin:0; counter-reset:s; }}
li {{ counter-increment:s; padding:10px 0 10px 28px; border-top:1px solid var(--rule); position:relative; }}
li::before {{ content:counter(s); position:absolute; left:0; top:10px; width:20px; height:20px; border-radius:50%; background:var(--card); font-size:11px; display:grid; place-items:center; color:var(--mut); }}
.k {{ display:block; font-weight:600; }} .v {{ display:block; }} .n {{ display:block; font-size:12px; color:var(--mut); }}
label {{ display:block; font-weight:500; margin-top:12px; }}
input {{ width:100%; height:40px; margin-top:4px; padding:0 10px; border-radius:8px; border:1px solid var(--rule); background:var(--card); color:var(--fg); font:inherit; }}
button {{ margin-top:16px; height:44px; width:100%; border:0; border-radius:8px; background:var(--fg); color:var(--bg); font:inherit; font-weight:600; cursor:pointer; }}
.out {{ margin-top:14px; padding:12px; border-radius:8px; background:var(--card); display:none; }}
.ok {{ color:var(--ok); font-weight:600; }} .bad {{ color:var(--bad); font-weight:600; }} .prev {{ color:var(--mut); font-size:12px; }}
table {{ width:100%; border-collapse:collapse; margin-top:8px; font-size:13px; }} td {{ padding:4px 0; }} td.r {{ text-align:right; }}
</style></head><body>
<h1>Fusion cross-check</h1>
<p class="sub">{escape(project_name)}, {escape(entry['label'].split(' (')[0].lower())} design. Set up the study with these values.</p>
<ol>{rows}</ol>
<h2>Enter the Fusion results</h2>
{prev_html}
<form id="f">
<label>Reaction force, total (N)<input name="reaction_n" inputmode="decimal" placeholder="{total:.0f}"></label>
<label>Peak von Mises stress near the hole (MPa)<input name="peak_stress_mpa" inputmode="decimal"></label>
<label>Largest displacement (mm)<input name="max_displacement_mm" inputmode="decimal"></label>
<label>Checked by<input name="checked_by" autocomplete="name"></label>
<button type="submit">Send to NEMO</button>
</form>
<div class="out" id="out" role="status"></div>
<script>
const ids = {ids};
const num = v => {{ v = (v || "").replace(",", ".").trim(); return v === "" ? null : Number(v); }};
const pct = d => d === null || d === undefined ? "-" : (d >= 0 ? "+" : "") + (d * 100).toFixed(1) + "%";
document.getElementById("f").addEventListener("submit", async e => {{
  e.preventDefault();
  const f = new FormData(e.target), out = document.getElementById("out");
  const body = {{ ...ids, reaction_n: num(f.get("reaction_n")), peak_stress_mpa: num(f.get("peak_stress_mpa")),
    max_displacement_mm: num(f.get("max_displacement_mm")), checked_by: f.get("checked_by") || "" }};
  out.style.display = "block"; out.textContent = "Sending...";
  try {{
    const r = await fetch("/api/fusion/crosscheck", {{ method: "POST", headers: {{ "Content-Type": "application/json" }}, body: JSON.stringify(body) }});
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || "NEMO could not save the results.");
    out.innerHTML = `<div class="${{d.agrees ? "ok" : "bad"}}">${{d.agrees ? "Agrees with NEMO" : "Differs from NEMO: check the study set-up"}}</div>
      <table><tr><td>Reaction</td><td class="r">${{pct(d.reaction_difference)}}</td></tr>
      <tr><td>Peak stress</td><td class="r">${{pct(d.stress_difference)}}</td></tr>
      <tr><td>Displacement</td><td class="r">${{pct(d.displacement_difference)}}</td></tr></table>
      <p class="prev">Saved. The calculation report now includes these results.</p>`;
  }} catch (err) {{ out.innerHTML = `<span class="bad">${{err.message}}</span>`; }}
}});
</script></body></html>"""
