# Writing brief for the NEMO 2 project report

This file is shared by everyone writing chapters of the report, so the chapters agree.

## The report

- JKUAT final-year project report, BSc Marine Engineering, Department of Marine Engineering and
  Maritime Operations. LaTeX, `report` class, chapters in `structure/`, IEEE citations through
  `references.bib` (`\bibliographystyle{IEEEtran}`).
- Authors: Amina Ahmed Bwana (ENM241-0087/2022) and Mboje Abdullah (ENM241-0088/2022).
  Submission March 2027. Write as "this project" or "we".
- Title: *NEMO 2: A Rule-Based, Verified Design Tool for Marine Steelwork: Lifting Padeyes,
  Pipe Support Brackets and Stabilizer Fins*.
- The macro `\NEMO{}` prints the name. Use `\code{...}` for file and function names.

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

## Aim and objectives (use exactly these, in this order)

Aim: to develop and verify a desktop design tool that sizes three marine structural details from a
plain description of the job, checks each design against published design rules, confirms it with a
built-in finite element analysis, and issues a traceable calculation package that an engineer without
programming knowledge can produce and review.

Objectives:

1. Implement rule-based check models, each with its hand-calculation working: ASME BTH-1 for the
   lifting padeye, AISC 360-16 with a pipe-span vibration check for the pipe support bracket, and
   IACS UR S10 with an independent foil load model for the stabilizer fin.
2. Develop a stock-aware sizing method that searches the plate thicknesses a workshop holds, sizes
   the continuous dimensions with a bounded Nelder-Mead search, rounds to buildable sizes and offers
   three designs at different reserve margins.
3. Build an open-source geometry and stress-analysis pipeline (build123d on OpenCASCADE, Gmsh,
   scikit-fem) that meshes every design at three refinements and checks force balance and mesh
   convergence automatically.
4. Verify the engine against hand calculations, closed-form theory and published solutions through a
   reproducible benchmark suite and automated tests.
5. Deliver an interface and outputs that need no programming: a local browser application with a live
   3D preview and a live record of the engineering steps, a PDF calculation package, STEP and DXF
   files, and an optional link to Autodesk Fusion.
6. Apply the tool to one case study for each part, examine how the designs respond to the main inputs,
   and state the limits of the results.

Research questions:

1. Can one tool cover three structurally different marine details while keeping every check traceable
   to a named rule or a stated practice?
2. How closely do the built-in stress solver, geometry kernel and foil solver agree with closed-form and
   published reference results?
3. What governs each part in practice, and what does that imply for how such details are designed?
4. Can a non-programmer run the full workflow, from job description to calculation package, unaided?

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
