# Writing brief for the NEMO project report

This file is shared by everyone writing chapters of the report, so the chapters agree.

## The report

- JKUAT final-year project report, BSc Marine Engineering, Department of Marine Engineering and
  Maritime Operations. LaTeX, `report` class, chapters in `structure/`, IEEE citations through
  `references.bib` (`\bibliographystyle{IEEEtran}`).
- Authors: Amina Ahmed Bwana (ENM241-0087/2022) and Mboje Abdullah (ENM241-0088/2022).
  Submission March 2027. Write as "this project" or "we".
- Audience: final-year BSc Marine Engineering defence panel (marine engineering lecturers). Let core
  marine engineering principles (shipboard load paths, marine codes, ship-motion accelerations,
  machinery-space vibration, foil hydrodynamics and cavitation, and shipyard plate stock) anchor the
  discussion naturally without overstatement.
- Title: *NEMO: A Rule-Based, Verified Design Tool for Marine Steelwork: Lifting Padeyes,
  Pipe Support Brackets and Stabilizer Fins*.
- The macro `\NEMO{}` prints the name. Treat the project as an independent engineering work (do not
  refer to it as "NEMO 2" or "the second phase"); earlier prototype trials may be cited briefly only
  as preliminary testing context. Use `\code{...}` for file and function names.

## Chapter plan and labels (use these exact labels for cross-references)

| File | Chapter | Label |
| --- | --- | --- |
| `01-introduction.tex` | Introduction | `chap:introduction` |
| `02-literature-review.tex` | Literature review | `chap:literature` |
| `03-methodology.tex` | Methodology | `chap:methodology` |
| `04-results.tex` | Results and discussion | `chap:results` |
| `05-workplan.tex` | Project workplan | `chap:workplan` |
| `06-budget.tex` | Project budget | `chap:budget` |
| `07-conclusion.tex` | Conclusions and recommendations | `chap:conclusion` |

## Objectives (use exactly these, in this order)

General objective: to develop and verify a rule-based marine structural design tool (\NEMO{}) that sizes lifting
padeyes, machinery-space pipe support brackets and roll-stabilizer fin internal structures from
available shipyard plate stock, confirms each design through automated three-dimensional finite
element analysis, and issues a traceable engineering calculation package and fabrication files for
review.

Specific objectives:

1. Formulate and implement code-based structural check and stock-aware sizing models for three
   shipboard details (lifting padeyes to ASME BTH-1, pipe support brackets to AISC 360-16 with
   machinery-space pipe-span vibration screening, and roll-stabilizer fin internal structures to
   IACS UR S10 with independent foil-load and cavitation models) that search available shipyard plate
   thicknesses and deliver buildable designs with full hand-calculation working, STEP and DXF outputs,
   and a reviewable PDF calculation package through a local desktop interface.
2. Establish an automated open-source geometry and quadratic tetrahedral finite element pipeline
   (build123d on OpenCASCADE, Gmsh, scikit-fem and PyAMG) with three-level mesh refinement and
   automatic force and moment equilibrium checks, and verify the structural, geometric and
   hydrodynamic solvers against hand calculations, closed-form theory, published reference solutions
   and automated regression tests.
3. Evaluate the verified tool across representative vessel case studies and operating-envelope
   parameter sweeps (load, sling inclination and obliquity, pipe nominal size and support spacing,
   ship speed and stock bearing arrangement) to determine the structural, catalogue, vibration and
   hydrodynamic limits that govern each marine detail in practice.

Research questions:

1. How can rule-based structural checks, shipyard plate-stock constraints and traceable
   hand-calculation working be unified across structurally distinct marine details without obscuring
   code provisions or engineering assumptions?
2. How closely do the automated solid-geometry, quadratic finite element and potential-flow foil
   solvers agree with hand calculations, closed-form elasticity and beam theory, and published
   reference data?
3. Across realistic shipboard operating envelopes, which structural, catalogue, vibration and
   hydrodynamic limits govern lifting padeyes, machinery-space pipe brackets and stabilizer fins in
   practice?

## What the project is (short version; full detail in the sources below)

- **Previous phase (NEMO 1).** The first version of this final-year project (report in
  `C:\Users\muigu\Desktop\SIDE\NEMO\reports\project-report\`) optimized three parts (aluminium bracket,
  S275 padeye, aluminium stabilizer fin) with first-order screening equations, Latin-hypercube
  sampling and Nelder-Mead, and built CAD in Autodesk Fusion through a file-based bridge. Its weak
  points (from `PLAN.md` section 1): Fusion's Python API cannot set up or solve Simulation studies, so
  the analysis loop never closed; the two Fusion stress studies of the bracket had to be rejected
  (one used 1.472 N instead of 1472 N, the other had no traceable load definition); several equations
  used tuning factors with no source; the stabilizer load was assumed, not derived; there were no
  design-code checks; setup needed Python, a virtual environment and Fusion, so non-programmers could
  not use it; the bridge rebuilt a stale request on connect.
- **This phase (NEMO 2).** Rebuilt from scratch. Three parts: lifting padeye (ASME BTH-1), pipe
  support bracket (seat plate, two knees, U-bolt; AISC 360-16 ASD; pipe span natural frequency against
  propeller and engine excitation), stabilizer fin internal structure (skin, two spars, ribs, solid
  stock; Whicker-Fehlner low-aspect-ratio lift and IACS UR S10 rudder force, the larger used; Hess-Smith
  panel method for pressure and cavitation; UR S10 stock, blade and plating checks). Sizing over the
  yard's plate stock. Built-in CAD (build123d/OpenCASCADE), mesh (Gmsh), FEA (scikit-fem, quadratic
  tetrahedra, multigrid-preconditioned conjugate gradients) on three meshes with force balance and
  convergence checks. Local FastAPI server and React/three.js browser app with a live 3D preview, a
  live run screen showing every engineering step, per-check hand-calculation working, a Verification
  page, PDF calculation package (ReportLab), STEP, STL, DXF, ZIP bundle, Fusion connector add-in for
  padeyes (parametric model, re-check of edited dimensions, recording a Fusion cross-check). Windows
  installer; plain-language user documentation.
- **Key numbers** are in `data/facts.md` (generated from real runs). Quote numbers only from there.

## Sources to read

- `C:\Users\muigu\Desktop\SIDE\NEMO2\PLAN.md` (why and what), `README.md`
- `C:\Users\muigu\Desktop\SIDE\NEMO2\docs\engineering-manual.md` (every equation and source)
- `C:\Users\muigu\Desktop\SIDE\NEMO2\docs\pipe-support-brackets.md`, `stabilizer-fins.md`, `user-guide.md`
- `C:\Users\muigu\Desktop\SIDE\NEMO2\reports\project-report\data\facts.md` (results)
- The NEMO 1 report chapters and `references.bib` in `C:\Users\muigu\Desktop\SIDE\NEMO\reports\project-report\`
  (reuse their verified references where they fit; keep the same BibTeX keys)

## Style (required)

Formal academic register, but plain. Follow these rules, taken from the "unslop" skill:

- No em dashes or en dashes used as dashes. No parentheses used as a dash substitute. Use full stops
  and commas.
- No AI vocabulary: additionally, crucial, delve, enduring, enhance, fostering, garner, interplay,
  intricate, landscape, pivotal, showcase, tapestry, testament, underscore, vibrant, leverage, utilize,
  facilitate, robust, seamless, comprehensive, paradigm, holistic, cutting-edge, game-changing.
- No "serves as", "stands as", "boasts". Say "is" or "has".
- No "not just X, but Y", no forced groups of three, no "from X to Y" false ranges.
- No vague attributions ("studies show", "experts agree"). Name the source and cite it.
- No filler ("it is important to note that", "in order to"), no stacked hedges, no generic endings.
- Prefer active voice and the concrete mechanism or number over an impression.
- Sentence case for section headings. One idea per sentence; vary sentence length.
- Do not over-use bold. No colons as mid-sentence connectors.
- Every chapter starts with a short paragraph saying what it covers.

## LaTeX conventions

- `\chapter{}`, `\section{}`, `\subsection{}` with `\label{sec:...}`; figures `[H]`, `\centering`,
  `\label{fig:...}`; tables use `booktabs` and `tabularx`, caption above, `\label{tab:...}`.
- Escape `% & $ # _ { } ~ ^`. Units with a thin space: `28.3~kN`, `355~MPa`.
- Citations `\cite{key}`. Every reference you add must be real and checked online (DOI or official
  page). Never invent a reference or a page number. If you cannot verify a source, do not cite it.
- Put new BibTeX entries in `references-lit.bib` (the main author merges them). Reuse keys from the
  NEMO 1 `references.bib` where the source is the same.
