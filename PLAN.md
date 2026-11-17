# NEMO 2: Rebuild Plan

Status: scope agreed 16 Nov 2026. Nothing has been built yet.
Source reviewed: `C:\Users\muigu\Desktop\SIDE\NEMO` (5 commits, latest `c8d632c Project Report`).
The original project is not modified by this plan.

Purpose: final-year project submission and defence at JKUAT (Department of
Marine Engineering and Maritime Operations), due about end of March 2027.
Main user: engineers at shipyards and marine contractors.

---

## 1. What the current NEMO is

NEMO is a JKUAT Marine Engineering final-year project. It tries to make three
marine parts lighter while keeping them strong enough:

| Part | Material | Load | Pass rule |
| --- | --- | --- | --- |
| Equipment bracket | Aluminium 6061-T6 | 1,471.5 N | FOS >= 2.5, deflection <= 0.5 mm |
| Lifting padeye | S275 steel | 14,715 N (500 kg x 3) | FOS >= 2.5, deflection <= 0.5 mm |
| Stabilizer fin | Aluminium 6061-T6 | 11,808 N (assumed) | FOS >= 2.5, tip deflection <= 5 mm |

How it works today:

1. Each part is described in a JSON file (dimension names, min/max, material, load).
2. A short Python formula estimates mass, stress and deflection for any set of dimensions.
3. A hand-written Nelder-Mead optimizer searches for the lightest set that passes.
4. Results go to CSV files and a Streamlit dashboard.
5. The best few designs are sent to Autodesk Fusion through `request.json` /
   `response.json` files. A Fusion add-in builds the 3D model and exports STEP.
6. A person then runs the stress simulation (FEA) in Fusion by hand, about 20
   steps per design, and types the results into a Markdown checklist.

### What is good and worth keeping

- Part definitions live in data files, not in code. Adding a part is mostly data.
- A bad design never crashes a run. It is logged as failed and the search continues.
- The project is honest about evidence: estimate, CAD mass and FEA result are kept
  separate, and it never calls a design "safe".
- The Fusion generators were tested on 21 shapes per part and all built.
- Analytical mass and CAD mass agreed within 3.8%, so the volume formulas are sound.

### What holds it back

1. **The strength numbers cannot be traced to any standard.** The formulas use
   tuning factors with no source (for example bracket rib section x 0.65, padeye
   stress factor `1.8 + 0.020 / fillet_radius`, padeye side load fixed at 25%).
   A shipyard engineer or surveyor has no basis to accept them.
2. **The loop never closes.** Fusion's Python API cannot start a stress
   simulation or read its results (documented in `docs/API_SPIKE_LOG.md`), so the
   "validated design" step is always manual and, per the report, was never
   completed. The two bracket studies were rejected because one used 1.472 N
   instead of 1,472 N. That error came from typing loads by hand.
3. **Setup is heavy.** A user needs Python, a virtual environment, Fusion with a
   Simulation licence, a Hybrid Design, a linked add-in, correct relative paths,
   and must never move the folder. The README is 49 KB. `quick-start.md` points at
   `Documents\Projects\NEMO`, but the project lives in `Desktop\SIDE\NEMO`.
4. **The user cannot describe their own job.** The load is fixed inside the JSON
   (500 kg x 3). Nobody can say "I need to lift a 3-tonne generator with a
   4-leg sling at 60 degrees" and get an answer.
5. **Answers are not buildable.** The optimizer returns values like 11.37 mm
   plate. Yards buy 6, 8, 10, 12, 15, 20 mm plate. Several optimum values sit on
   their lower bounds, which suggests the real limits (stock sizes, weld size,
   minimum edge distance) are missing.
6. **Materials are not the usual marine ones.** 6061-T6 loses a large share of its
   strength next to a weld. Welded marine aluminium is normally 5083 or 6082 with a
   welded-strength reduction. Ship steel is normally grade A / AH36.
7. **No document comes out that someone else can check.** The output is CSV, JSON
   and an empty checklist, not a calculation report.
8. **Stale requests rebuild on connect.** The bridge starts with
   `LAST_MTIME = None` (`NEMOBridge.py` line 53), so a `request.json` left from an
   earlier session builds a model as soon as the bridge connects.
9. **The stabilizer case is weak.** Its load is a guess because there is no
   hydrodynamic model, so its "optimum" cannot mean much.

---

## 2. The real problem to solve

Problem statement (to confirm with your supervisor and, ideally, one yard or
rigging contractor in Mombasa):

> Small and mid-size yards, fabricators and marine contractors routinely need
> lifting padeyes for one-off jobs (engine and generator swaps, deck cranes, pump
> installs, module lifts) and pipe support brackets by the hundred on every new
> build or refit. These are often sized by rule of thumb or copied from an old
> drawing. Writing a proper calculation for each one takes an engineer's time;
> over-sizing wastes steel and welding hours; under-sizing risks a dropped load or
> a cracked pipe. There is no simple, free tool that takes the job description and
> returns a code-checked, buildable design with a report and cutting files.

What NEMO 2 does about it:

> Answer a short form about the job (plain-language questions, numbers and
> dropdowns; no AI involved). NEMO sizes the part from standard plate and pin
> sizes, checks it against a published design method, confirms it with an
> automatic built-in stress simulation, and gives you a PDF calculation report, a
> 3D model, a cutting profile for the plasma or laser table, and a native Fusion
> model if you want one.

### Components, in order

1. **Lifting padeye (main case).** The most common, highest-consequence detail,
   with well-published check methods.
   - Inputs: load to lift, number of padeyes, sling angle, out-of-plane angle,
     dynamic factor, shackle size, material, available plate thicknesses.
   - Checks: tension across the hole, double-plane shear-out, fracture beyond the
     hole, pin bearing, cheek plates if used, weld throat, and out-of-plane bending.
   - Shackle table so the pin hole and plate thickness fit a real shackle.
2. **Pipe support bracket (second case).** Replaces the general bracket. A ship
   carries hundreds of them, so a small saving per bracket adds up, and
   pipe-support failures (cracked welds, pipe fatigue) usually come from vibration,
   which the old version ignored.
   - Inputs: pipe size and schedule, pipe material, fluid (water, fuel oil,
     seawater, empty), insulation, support spacing, bracket style (welded angle
     bracket, plate with U-bolt), where it sits on the vessel.
   - Loads: pipe + fluid + insulation weight over the span, multiplied by ship
     motion accelerations (vertical, side, fore-aft), not one fixed number.
   - Checks: bracket plate and leg bending, weld throat, U-bolt or clamp capacity,
     bracket deflection, and natural frequency of the pipe span on its supports
     kept away from engine and propeller excitation frequencies.
   - Extra output: recommended maximum support spacing for that pipe.
3. **Stabilizer fin (third case, required).** Built after the padeye and pipe
   bracket are complete. It must not repeat the old guessed load, so it gets its
   own load model first:
   - Inputs: vessel speed, fin area and span, maximum fin angle, foil section
     (NACA 0015 by default), where the fin sits on the hull.
   - Loads: lift from the fin's area, speed and angle using published
     low-aspect-ratio foil data (lift slope and stall angle), spread along the span;
     twisting moment from the centre of pressure relative to the fin stock.
   - Checks: root bending and shear, stock and flange, skin panel buckling,
     tip deflection, and a cavitation warning from foil pressure at speed.
   - Optimizes the internal structure (skin, spars, ribs, root insert); the outer
     foil shape stays fixed, as in the original NEMO.

---

## 3. Technical approach

### 3.1 Built-in engine, with Fusion kept

Two tools, each doing what it is good at.

**Built-in engine (does the automatic work).** Runs on any Windows laptop from
free packages, so a yard engineer without a Fusion licence still gets a full
result:

| Job | Tool | Why |
| --- | --- | --- |
| 3D model, STEP, STL | [build123d](https://pypi.org/project/build123d/) (OpenCASCADE kernel) | Pure Python install, same kernel class as commercial CAD |
| Mesh | Gmsh (pip wheel) | Standard open mesher, reads STEP |
| Stress simulation | [scikit-fem](https://scikit-fem.readthedocs.io/) linear elasticity on tetrahedra | Pure Python, no solver install. CalculiX can be an optional second solver |
| Cutting profile | ezdxf (DXF) | Plasma/laser tables read DXF |
| Report | HTML to PDF | Readable on any machine |

This is needed whether or not Fusion is used, because Fusion's API cannot run a
stress simulation or read its results. Without it the loop cannot close.

**Fusion (native CAD, presentation, independent check).**

- **"Open in Fusion" button.** Builds the chosen design as a native, editable
  Fusion model with named user parameters and a clean timeline, through a
  rebuilt NEMO bridge (section 3.5 rules). Students and panel members can open,
  inspect and edit it in a tool they know, and make drawings from it.
- **Independent cross-check for the defence.** For each final design, the
  Fusion Static Stress study is run once by hand and compared with the built-in
  result. Two independent solvers agreeing is stronger evidence than either
  alone. NEMO prints a one-page Fusion study sheet (material values, which faces,
  total load and direction, expected reaction) so nothing is typed from memory.
- **Optional for yard users.** Every other feature works without Fusion.

On "Fusion is the CAD standard": the exchange standard in industry is STEP
(ISO 10303). Fusion is the common tool in education; yards also use AutoCAD,
Rhino, SolidWorks, ShipConstructor and AVEVA. NEMO exports STEP for all of them,
plus the native Fusion model for Fusion users.

### 3.2 Close the loop automatically

```
Job description
   -> code check (milliseconds; screens thousands of options)
   -> optimizer over real stock sizes
   -> top 3 designs built as 3D solids
   -> automatic FEA, 3 mesh levels, loads applied from the job (no hand typing)
   -> reaction-force balance check (catches the 1.472 N type of error)
   -> report: code check and FEA side by side, with pass/fail and margins
   -> optional: open in Fusion, Fusion cross-check
```

The FEA is only trusted after it passes benchmark problems with known answers
(cantilever beam, plate with a hole stress factor about 3, pin-loaded lug). These
benchmarks ship with the tool and appear in the engineering manual.

### 3.3 Optimizer

- Plate thickness, pin and shackle size become choices from lists; lengths and
  radii stay continuous within shop-sensible limits (minimum edge distance, weld
  access, minimum fillet).
- Approach: try each allowed thickness combination, run Nelder-Mead on the
  continuous dimensions for each, keep the best. This keeps the project's
  Nelder-Mead identity while giving buildable answers. scipy's
  differential evolution with integer variables is the fallback if it is too slow.
- Goal options: lightest, cheapest (steel price per kg + weld cost per metre), or
  fewest parts. Default: lightest.
- Show a short list of 3 designs (lightest, balanced, most margin) instead of a
  single "optimum".

### 3.4 Data the tool ships with

- Materials: S235, S275, S355, grade A, AH36, 5083-H111, 6082-T6 (with welded
  strength), stainless 316L. Each with its source.
- Standard plate thicknesses (editable per yard).
- Shackle dimension table (bow and dee, common working load limits).
- Default safety factors with a plain explanation of each.

### 3.5 Every project starts fresh

- **One folder per project.** "New design" creates its own folder (inputs,
  results, models, report). Nothing is shared between projects.
- **Nothing runs on open.** Opening the app, a project, or connecting Fusion never
  starts a build. Builds start only when the user presses a button.
- **Requests are used once.** Each Fusion request carries a project ID and a
  creation time. The bridge ignores anything created before it started, and moves
  each request to a `done` folder after answering it.
- **Reopening is explicit.** "Open saved design" shows the saved results. Re-running
  is a separate "Run again" button.

### 3.6 The app and the live 3D preview

Streamlit is dropped. It reruns the whole page on every input change, offers
little control over styling, and handles interactive 3D poorly.

| Layer | Tool | Role |
| --- | --- | --- |
| Screens | React + TypeScript (Vite), styled with the design system in 3.7 | Full control over look and layout |
| Live 3D | Three.js via react-three-fiber | Part drawn in the browser, redrawn on every input change |
| Engine | Python + FastAPI, running locally | Code checks, optimizer, CAD, FEA, report, Fusion link |

The user double-clicks one shortcut. The Python engine starts in the background
and opens the app in the browser. A desktop window wrapper (Tauri) is an option
later.

Live preview, in two layers:

1. **Instant (in the browser, every keystroke).** The padeye is simple shapes: a
   plate outline with a rounded top, a hole, cheek rings, a base plate. Three.js
   draws them from the dimensions directly.
2. **Quick sizing (engine, about 0.1 to 0.5 s, after the user stops typing).** The
   code checks take milliseconds, so the engine picks a provisional design from
   stock sizes on every change. Raise the load and the plate visibly thickens and
   the hole and lug grow to suit the matching shackle.

The preview is marked "provisional" until the user presses **Find designs**, which
runs the full optimizer, builds the exact CAD solid and runs the FEA.

### 3.7 Visual design: Graphite with Apple-style spacing

Base: the user's Graphite design system (copied to `design-system/graphite/`).
Kept: monochrome palette with one blue accent (for the selected part of the model
and the main action only), hairline ring edges, Inter, Lucide icons, light and
dark themes, radius and motion tokens, and the writing rules ("calm colleague",
sentence case, verb + object buttons, status never shown by colour alone).

Changed, because Graphite is built to be dense. Spacing, sizes and hierarchy
follow Apple's habits: an 8-point rhythm, 44-point minimum targets, 17-point
reading text, one main task per screen, and the most space for the 3D part.

| Lever | Graphite default | NEMO |
| --- | --- | --- |
| Interface text | 13 / 20 px | 15 / 24 px; form questions 17 / 26 px |
| Default control height | 32 px | 44 px; main action 48 px |
| Field gap | 16 px | 24 px |
| Card padding | 16 px | 24 to 32 px |
| Section gap | 32 px | 48 px |
| Page top padding | 48 px | 64 px |
| Table row | about 32 px | 48 px |
| Layout grid | 4 px everywhere | 8 px for layout; 4 px only inside controls |
| Page titles | up to heading-4 | one large title per step (32 / 40 px) |
| Questions per row | any | one |

One sans-serif font (Inter) for the whole interface, with tabular figures for
numbers. Not used: Newsreader serif, Departure Mono, Geist Mono, decorative
backgrounds, and Apple-specific conventions (SF Pro, glass materials, iOS
navigation). The look stays plain on purpose.

Implemented as a NEMO token layer on top of Graphite's `tokens.json`, so Graphite
itself stays unchanged.

### 3.8 Design rules are swappable

- **Default:** ASME BTH-1-style pin-connected-plate equations for the padeye
  (publicly available, widely used).
- **Rule sets are separate modules.** Each check (tension, shear-out, bearing,
  weld, and so on) gets its capacities and safety factors from the selected rule
  set. Adding a new one does not change the rest of the tool.
- **Which rule set applies depends on the job.** The vessel's classification
  society (DNV, Bureau Veritas, Lloyd's Register, ABS, and others) or the lifting
  standard named in the contract decides. Planned additions: DNV-ST-0378 for
  lifting appliances, then BV, LR and ABS rules where we can get access through
  the university.
- **The report names the rule set and edition** on every page, and states that a
  different class or flag requirement can change the result.
- **Pipe support bracket:** ship-motion accelerations come from a published class
  method, chosen in phase 7 and named in the report.

---

## 4. User flow (no coding needed)

The app opens in the web browser from a desktop shortcut. No terminal is shown.

1. **Start screen.** "New design" / "Open saved design". Short note on what NEMO
   can and cannot tell you.
2. **What are you designing?** Picture cards: Lifting padeye, Pipe support bracket.
3. **Describe the job.** Plain questions with units shown and a "?" on each:
   - "How heavy is the load?" (kg or tonnes)
   - "How many lifting points?"
   - "Sling angle from horizontal?" (with a small diagram)
   - "Material?" (dropdown, defaults to S355)
   - "Which plate thicknesses does your workshop have?" (tick boxes)
   Inputs are checked as you type, with a reason when something is out of range.
   The 3D preview beside the form updates as you go.
4. **Check the assumptions.** One page listing the design rule set (default ASME
   BTH-1), safety factor and dynamic factor, each with a one-line explanation.
   Keep the defaults or change them.
5. **Find designs.** One button. A progress bar with plain stages: "Checking
   12,000 options", "Building 3 models", "Running stress check".
6. **Results.**
   - Recommended design with a turnable 3D view and a dimensioned sketch.
   - Table of checks: each one, how close to its limit, pass or fail in words.
   - "Compared with a typical design: 4.2 kg lighter, 0.6 m less weld."
   - Stress colour plot from the FEA.
7. **Download or open.** PDF calculation report, STEP model, DXF cutting profile,
   project file, and "Open in Fusion" if Fusion is installed.

Every report carries a clear statement: this is a design aid; a competent
engineer must review it before fabrication or use.

---

## 5. Installation and documentation

### Install

- One installer script: double-click `Install NEMO`, wait, a desktop shortcut
  appears. It uses `uv` to fetch the correct Python automatically, so the user does
  not install Python, create environments or type commands.
- Fusion link: one extra guided step for users who have Fusion (link the add-in,
  with screenshots). Skipped by everyone else.
- Internet is needed once at install. After that it runs offline.

### Documentation set

Written for someone who has never programmed:

| Document | Reader | Content |
| --- | --- | --- |
| Getting Started | Everyone | Install with screenshots, first padeye in 10 minutes |
| User Guide | Engineers, students, fabricators | Each screen explained, worked examples (5 t engine lift, 100 mm seawater line support) |
| Using NEMO with Fusion | Fusion users | Linking the add-in, opening a design, running the cross-check study |
| Understanding Your Results | Everyone | What each check means, what "margin" means, what to do on a fail |
| Glossary | Everyone | FOS, FEA, sling angle, WLL, DAF, etc. in plain words |
| Troubleshooting | Everyone | Organised by what you see ("The app does not open") |
| Limits and Safety | Everyone | What NEMO does not check, and when to call an engineer |
| Engineering Manual | Supervisors, surveyors, checkers | Every equation, its source and rule set, benchmarks, verification results |
| Developer Guide | Programmers only | Code layout, adding a part or rule set, running tests. Kept separate |

The same plain-language help text appears inside the app next to each input.

---

## 6. Phased roadmap

### Progress (16 Nov 2026)

| Phase | State | Evidence |
| --- | --- | --- |
| 1. Foundation | Done | 26 tests; every ASME BTH-1 padeye value matches an independent hand calculation |
| 2. Geometry | Done | CAD volume equals formula on 50 random designs; STEP re-import within 0.5%; DXF closed full-size profile |
| 3. Built-in FEA | Done | Cantilever −0.8%, bending stress +2.6%, hole K<sub>t</sub> +0.9%; padeye force balance < 1e-12; mesh convergence 0.05% |
| 4. Optimizer | Done | Stock-size search with 3-design shortlist; full padeye job with FEA in about 100 s; quick preview about 0.1 to 0.3 s |
| 5. App | Built and checked in the browser | React + three.js wizard, live 3D preview, results with stress and mesh views, themed drop-downs |
| 5a. Engineering transparency | Done | Working for every check; live run screen (forces, shackle, design-space chart, mesh, solver residuals, convergence, force balance); check regions marked on the 3D model; Verification page; engineering log and CSV of every design tried |
| 5b. PDF report | Done | ReportLab calculation package: title block on every page, fabrication drawing with parts list, design search chart, calculation sheets, FEA figures, Fusion cross-check sheet, audit trail with checksums |
| 6. Fusion link | Built; not yet run inside Fusion | NEMO Connector add-in installed from the app; connection light; "Open in Fusion" builds a parametric model (user parameters `nemo_*`, tagged faces) and compares volume; "Check in NEMO" re-checks edited dimensions; cross-check sheet panel records Fusion results (agree: reaction within 2%, peak stress within 15%) into report section 7. HTTP link with one-use, expiring requests. Protocol tested by acting as the add-in (6 tests); the Fusion API calls still need a live test in Fusion |
| 7. Pipe bracket | Built and checked in the browser | Seat plate with two knees and a U-bolt. AISC 360-16 ASD checks at 61 stations along the arm, weld group, U-bolt interaction, deflection; pipe span natural frequency against propeller and engine excitations with a recommended maximum spacing. Nelder-Mead sizing, STEP/DXF, FEA read clear of the fixed edge. Ship-motion accelerations are inputs, not yet from a class method |
| 8. Stabilizer | Built and checked in the browser | Whicker-Fehlner low-aspect-ratio lift compared with the IACS UR S10 rudder force; Hess-Smith panel method for pressure and cavitation (verified against exact flow); UR S10 stock, blade and plating checks, skin buckling, tip deflection; rib-spacing search and stock sizing; STEP/rib DXF; stock FEA against beam theory (0.2%) |
| 9. Install, docs | Written, installer not yet run on a fresh laptop | `Install NEMO.bat`, `Start NEMO.bat`, guides in `docs/` |

Open items for the padeye: verify against a published BTH-1 worked example;
test the connector inside Fusion and run a Fusion cross-check study; first
non-coder walkthrough; screenshots for the guides.

### Phases

Order of work. Each phase ends with something you can run and see. Target:
submission at JKUAT, about end of March 2027.

| Phase | Work | Done when |
| --- | --- | --- |
| 1. Foundation | Project skeleton, material/plate/shackle data, rule-set module, ASME BTH-1 padeye checks | Checks match independent hand calculations; published worked example added when a source is available |
| 2. Geometry | build123d padeye, STEP + DXF export, mass | CAD mass matches formula within 1% over 50 random designs |
| 3. Built-in FEA | Gmsh + scikit-fem, benchmark suite, padeye with pin-bearing load | Benchmarks within 5%; reactions balance applied load |
| 4. Optimizer | Stock-size search, 3-design shortlist, auto FEA of shortlist | Padeye job end to end in under 5 minutes |
| 5. App | Browser wizard, live 3D preview, results page, PDF report | A non-coder completes a padeye design unaided |
| 6. Fusion link | Rebuilt bridge with fresh-project rules, "Open in Fusion", study sheet, Fusion cross-check of final padeye | Fusion and built-in stress agree within an agreed tolerance |
| 7. Pipe bracket | Ship-motion loads, checks, vibration, support spacing, CAD, FEA | Same "done" tests as padeye |
| 8. Stabilizer | Foil load model, internal-structure checks, CAD, FEA | Same "done" tests as padeye; load model checked against published foil data |
| 9. Install, docs, report | Installer, user documents, project report chapters for the new scope | Fresh laptop to first report in under 20 minutes |

---

## 7. Decisions

| # | Decision | Answer |
| --- | --- | --- |
| 1 | Purpose | JKUAT final-year submission and defence |
| 2 | Main user | Engineers at shipyards and marine contractors |
| 3 | Parts | Padeye first, pipe support bracket second, stabilizer third (required, with its own load model) |
| 4 | Fusion | Kept: native model export and independent cross-check. Built-in engine does the automatic work |
| 5 | Design method | ASME BTH-1-style equations by default; rule sets swappable for DNV, BV, LR, ABS as required by class |
| 6 | Location | `C:\Users\muigu\Desktop\SIDE\NEMO2` |
| 7 | Design system | Graphite with Apple-style spacing, Inter only |
| 8 | Bracket type | Pipe support bracket |
| 9 | Front end | React + Three.js; no Streamlit; no AI |

Supervisor has agreed the new scope (16 Nov 2026).
