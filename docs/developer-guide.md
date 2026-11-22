# Developer guide

For programmers working on NEMO. Users never need this page.

## Layout

| Path | Contents |
| --- | --- |
| `engine/src/nemo/data/` | Materials, plate stock, shackle tables (JSON) and loaders |
| `engine/src/nemo/rules/` | Design rule sets. `asme_bth1.py` is the default; add others with the same methods |
| `engine/src/nemo/loads.py` | Lift description to padeye forces |
| `engine/src/nemo/checks.py` | `CheckResult`, shared by every part |
| `engine/src/nemo/parts/padeye/` | Geometry, checks, CAD, DXF, FEA, sizing, full pipeline |
| `engine/src/nemo/parts/bracket/` | Pipe support bracket: job and loads, pipe span analysis, checks, CAD and DXF, FEA, sizing, pipeline |
| `engine/src/nemo/parts/stabilizer/` | Stabilizer fin: foil loads, structure geometry, UR S10 checks, CAD and rib DXF, stock FEA, sizing, pipeline |
| `engine/src/nemo/parts/registry.py` | Every part and the functions the server needs from it |
| `engine/src/nemo/hydro.py` | NACA sections, Hess-Smith panel method, low-aspect-ratio lift |
| `engine/src/nemo/fea_study.py` | Three-mesh stress study shared by the bracket and the fin stock |
| `engine/src/nemo/runlog.py` | Engineering event log and stress-plot export, shared by every part |
| `engine/src/nemo/report_parts.py` | PDF report for the bracket and the fin (same page frame as the padeye) |
| `engine/src/nemo/fea/` | Gmsh meshing and scikit-fem linear elasticity |
| `engine/src/nemo/optimize/` | Bounded Nelder-Mead |
| `engine/src/nemo/projects.py` | One folder per project; nothing runs on open |
| `engine/src/nemo/report_pdf.py` | PDF calculation package (ReportLab and Matplotlib; Inter fonts in `nemo/data/fonts`) |
| `engine/src/nemo/parts/padeye/working.py` | Hand-calculation working for every check and the loads |
| `engine/src/nemo/verification.py` | Benchmarks used by the tests and the Verification page |
| `engine/src/nemo/working.py` | `Step` record and number formatting for working |
| `engine/src/nemo/server.py` | FastAPI app on 127.0.0.1; serves `app/dist` |
| `engine/src/nemo/fusion_link.py` | Fusion connector link: connection state, one-use request queue, connector install |
| `engine/src/nemo/fusion_sheet.py` | Cross-check sheet page shown in a Fusion panel (`/fusion/sheet`) |
| `engine/src/nemo/parts/padeye/fusion.py` | What Fusion needs to build a padeye, edited-dimension checks, cross-check records |
| `fusion/NEMOConnector/` | The Fusion add-in. NEMO copies it into Fusion's add-ins folder |
| `tools/make_connector_icons.py` | Draws the add-in's toolbar icons |
| `app/` | React + TypeScript + three.js front end (`app/src/styles/tokens.css` committed) |
| `reports/project-report/` | JKUAT LaTeX project report, regeneration tools and compiled `main.pdf` |
| `.agents/skills/` | Workspace skills (`nemo-report-updates` with `verify_report.py`, and vendored `teach`) |
| `tools/install.ps1` | Windows installer used by `Install NEMO.bat` |

## Set up

```powershell
cd engine
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]" -c constraints.txt
.\.venv\Scripts\python.exe -m pytest -q

cd ..\app
npm ci
npm run build
```

Node.js is only needed here, to rebuild the app. Users do not need it: the built
app in `app/dist` is committed, and the installer serves it as it is. Rebuild and
commit `app/dist` after every change in `app/src`.

`engine/constraints.txt` holds the exact package versions the tests pass with.
The installer installs with it, so every user gets the tested versions. To move
to newer versions, upgrade them in `engine\.venv`, run the full test suite, then
regenerate the file with
`uv pip freeze --python engine\.venv\Scripts\python.exe` (drop the `nemo-engine`
line and keep the header).

Run the engine and the app with live reload in two terminals:

```powershell
cd engine; .\.venv\Scripts\python.exe -m nemo.server --no-browser
cd app; npm run dev   # http://localhost:5173, forwards /api to the engine
```

## Rules

- Units inside the engine: mm, N, MPa, kg, degrees.
- Formula strings use a small markup: `X_t` or `X_{eff}` for subscripts, `x^2` for superscripts. `app/src/components/Formula.tsx` and `report_pdf.markup` render it.
- Long-running work reports progress as events through `EngineeringLog.emit`; the run screen polls `/api/runs/{id}?since=n`.
- Every check returns a `CheckResult` with a plain-language title and
  explanation, its source, `basis` (rule or practice), `severity` (required or
  advice) and `category` (strength or fit).
- Rule sets supply capacities; parts never hard-code a code's factors. Each part has its own: ASME BTH-1 (padeye), AISC 360 ASD (bracket), IACS UR S10 (fin).
- Loads with a target moment instead of a force (`SurfaceLoad.total_moment_nmm`) and loads that absorb the net force of earlier ones (`absorb=True`) are supported by the solver.
- Opening a project must never start a calculation.
- Gmsh is single-threaded: all meshing goes through the lock in `fea/mesh.py`.
- The app's colours come from `design-system/graphite/project/tokens.json` via
  `app/scripts/build-tokens.mjs`. Spacing and sizes live in `app/src/styles/nemo.css`.

## Fusion connector

The add-in (`fusion/NEMOConnector/NEMOConnector.py`) runs inside Fusion and
talks to NEMO over HTTP on 127.0.0.1. No files are shared, so there is no stale
request to pick up.

1. On start it calls `POST /api/fusion/hello` with a new session id, then polls
   `GET /api/fusion/poll?session=` every 1.5 s. If NEMO is not
   running it retries quietly every 5 s.
2. `POST /api/fusion/open` (from the app) queues an `open_design` job. A job is
   handed out once. It expires if not picked up within 45 s or not finished
   within 180 s, and a new `hello` expires every older job.
3. The add-in builds the model on Fusion's main thread (custom event), then posts
   `POST /api/fusion/jobs/{id}/result`. The app waits on `GET /api/fusion/jobs/{id}`.
4. **Check in NEMO** posts the `nemo_*` user parameters (converted from cm to mm)
   to `POST /api/fusion/check`.
5. The sheet palette loads `GET /fusion/sheet?project=&run=&design=` and posts
   `POST /api/fusion/crosscheck`.

Other routes: `GET /api/fusion/status` (the app's light), `POST /api/fusion/install`
(copies the add-in and writes `config.json` with the server address) and
`GET /api/projects/{id}/runs/{run}/fusion?design=` (the records shown on the
results page).

Environment variables for testing: `NEMO_FUSION_ADDINS_DIR` (install target
instead of `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns`) and
`NEMO_PROJECTS_DIR`. When the add-in changes, bump `CONNECTOR_VERSION` in
`fusion_link.py`, `VERSION` in `NEMOConnector.py` and `version` in
`NEMOConnector.manifest` together; the app then offers **Update connector**.

The Fusion API calls are not covered by the test suite, which acts as the add-in
over HTTP (`tests/test_fusion_link.py`). Test changes to the add-in in Fusion.

## Adding a rule set

1. Add `engine/src/nemo/rules/<name>.py` with the same methods as `ASMEBTH1`.
2. Register it in `RULE_SETS` in `rules/__init__.py`.
3. Add tests that reproduce a published example for that rule set.

## Adding a part

1. `parts/<part>/`: a job with `from_dict`, `to_dict`, `problems` and `loads`; geometry; checks returning a
   `PartCheckReport`; CAD and DXF; FEA through `fea_study.run_study`; sizing; a pipeline that writes the
   same run folder as the padeye (`results.json` with `part`, the engineering log, `designs-evaluated.csv`).
2. Register it in `parts/registry.py` (`PARTS`), `projects.py` (`PARTS`) and `rules/__init__.py` (`PART_RULE_SETS`).
3. Report: a branch in `report_parts.py`.
4. App: a job type in `types.ts`, input screens (see `screens/PartForms.tsx`), a 3D model in `three/`, and
   entries in `three/PartModel.tsx`. The run screen and results read the shared event and result keys.
5. Tests: hand calculation, behaviour, CAD volume, FEA balance, and a server run (`tests/test_server_parts.py`).
