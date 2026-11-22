# NEMO Report Rules, Institutional Format, and Style Checklist

This reference consolidates the institutional JKUAT UPRO rules, NEMO's
`WRITING-BRIEF.md` contract, and lessons learned from past report regressions.

---

## 1. JKUAT UPRO Institutional Template Rules

Keep `reports/project-report/main.tex` compliant with the JKUAT University
Project Report (UPRO) template:

- **Class & geometry:** `\documentclass[12pt,a4paper]{report}`,
  `\geometry{top=2cm, bottom=2.5cm, left=1in, right=1in}`, `\onehalfspacing`,
  `\setlength{\parindent}{1.25cm}`.
- **Title page branding:** Must include `./media/HDlogo.png`, University/College/
  School/Department/Degree hierarchy (`BACHELOR OF SCIENCE IN MARINE ENGINEERING`,
  `DEPARTMENT OF MARINE ENGINEERING AND MARITIME OPERATIONS`), bold title between
  horizontal rules, project code, authors (`Amina Ahmed Bwana`, `ENM241-0087/2022`;
  `Mboje Abdullah`, `ENM241-0088/2022`), supervisor, and submission statement
  (`March 2027`).
- **Page numbering:** Roman numerals (`\pagenumbering{roman}`) for Front Matter
  (Declaration, Dedication, Acknowledgements, Abstract, ToC, LoF, LoT,
  Abbreviations and Symbols); Arabic numerals (`\pagenumbering{arabic}`) from
  Chapter 1 onward.
- **Chapter & label conventions:**
  - `structure/00-abstract.tex` — Abstract
  - `structure/01-introduction.tex` — `\label{chap:introduction}`
  - `structure/02-literature-review.tex` — `\label{chap:literature}`
  - `structure/03-methodology.tex` — `\label{chap:methodology}`
  - `structure/04-results.tex` — `\label{chap:results}`
  - `structure/05-workplan.tex` — `\label{chap:workplan}`
  - `structure/06-budget.tex` — `\label{chap:budget}`
  - `structure/07-conclusion.tex` — `\label{chap:conclusion}`
  - `structure/08-appendices.tex` — Appendices (`\appendix`)
  - Standard label prefixes: `chap:`, `sec:`, `fig:`, `tab:`, `eq:`, `lst:`.
- **Tables & figures:**
  - Tables use `booktabs` (`\toprule`, `\midrule`, `\bottomrule`) and `tabularx`,
    with caption **above** the table (`\captionsetup[table]{position=top}`).
  - Figures use `[H]`, `\centering`, and caption **below** the figure.
  - Citations use `\bibliographystyle{IEEEtran}` with `references.bib`.

---

## 2. Standalone Project Framing & Marine Engineering Lens

- **Project name:** Always use `\NEMO{}` (never `NEMO 2`, `\NEMO{}~2`, `NEMO 1`,
  or `\NEMO{}~1`).
- **No sequel framing:** Never call the project `the second phase`, `Phase 2`,
  or contrast it as a sequel to `the first phase` / `Phase 1`. Earlier prototype
  trials (e.g., manual Fusion bracket studies) may appear only briefly as
  exploratory testing motivation (`sec:early-testing`).
- **Audience (BSc Marine Engineering defense panel):** Anchor requirements,
  explanations, and conclusions naturally in naval architecture and marine
  engineering fundamentals:
  - Shipboard lifting load paths, dynamic/oblique sling effects, ASME BTH-1
  - Machinery-space piping inertia under ship-motion accelerations, AISC 360-16,
    and pipe-span resonance separation from engine firing and propeller
    blade-passing frequencies
  - Roll-stabilizer fin low-aspect-ratio hydrodynamics (Whicker–Fehlner), IACS
    UR S10 stock and blade checks, and Hess–Smith cavitation onset
  - Shipyard plate-stock inventory, catalogue shackles/U-bolts, and practical
    fillet-weld fabrication limits

---

## 3. Golden Thread: Objectives & Research Questions

Section 1.4 of `structure/01-introduction.tex` must preserve the two-tier
structure:

- **`\section{Objectives}`** (`\label{sec:aim-objectives}`)
  - **`\subsection{General objective}`** (`\label{sec:general-objective}`):
    single overarching statement of developing and verifying `\NEMO{}`.
  - **`\subsection{Specific objectives}`** (`\label{sec:specific-objectives}`):
    exactly **3** completely achieved, verifiable objectives:
    1. Code-based structural check & shipyard stock-aware sizing models (padeye,
       pipe bracket, stabilizer fin) + traceable PDF/STEP/DXF deliverables.
    2. Automated open-source CAD–FEA pipeline (build123d/OpenCASCADE, Gmsh,
       scikit-fem, PyAMG) with 3-mesh refinement, 6-DOF equilibrium, and
       multi-tier verification benchmarks + automated regression tests.
    3. Shipboard case studies and operating-envelope parameter sweeps identifying
       governing structural, catalogue, vibration, and hydrodynamic limits.
- **`\section{Research questions}`** (`\label{sec:research-questions}`): exactly
  **3** research questions mapped 1-to-1 to Specific Objectives 1–3.
- Every downstream reference in Chapter 2 (`sec:research-gap`), Chapter 4
  (`sec:requirements-summary`, `sec:research-questions-answers`), Chapter 5
  (`fig:gantt` bars tagged `O1`, `O2`, `O3`), and Chapter 7 (`sec:conclusions`)
  must match these exact 3 objectives and 3 RQs.
- Unproven extensions (physical proof load testing, formal user-usability study)
  belong strictly in Scope/Limitations and Future Work — never as an objective.

---

## 4. Prose, Punctuation, Units, and Citation Rules (`WRITING-BRIEF.md`)

- **Register:** Plain, formal academic English; active voice; one clear idea per
  sentence; sentence-case section headings; every chapter opens with a short
  overview paragraph.
- **Forbidden dashes:** No em-dashes (`—`, `---`) and no en-dashes used as prose
  dashes (` -- `, ` – `). Use commas or full stops. (TikZ `--` path operators and
  numeric/compound ranges like `CAD--FEA` or `1--10` are valid LaTeX.)
- **Forbidden AI vocabulary & filler:** Never use `additionally`, `crucial`,
  `delve`, `enduring`, `enhance`, `fostering`, `garner`, `interplay`,
  `intricate`, `landscape` (as prose — `\begin{landscape}` environment is fine),
  `pivotal`, `showcase`, `tapestry`, `testament`, `underscore`, `vibrant`,
  `leverage`, `utilize`, `utilise`, `facilitate`, `robust` (in prose — the
  literal directory name `robust/` in code listings is fine), `seamless`,
  `comprehensive`, `paradigm`, `holistic`, `cutting-edge`, `game-changing`,
  `serves as`, `stands as`, `boasts`, `it is important to note that`, or
  `in order to`.
- **Units & macros:** Non-breaking thin space before units (`28.3~kN`, `355~MPa`,
  `60.0~s`). Use `\NEMO{}` for the tool name and `\code{...}` for filenames,
  functions, parameters, and paths. Escape `% & $ # _ { } ~ ^` in text.
- **Citations:** Every `\cite{key}` must resolve in `references.bib` and refer
  to a real, verified source (DOI, standard number, or official document). Never
  fabricate references or page numbers.

---

## 5. Figures, UI Screenshots, and Layout Rules

- **All application UI screenshots (`images/app-*.png`) MUST be standalone
  single figures occupying the full text width (`\includegraphics[width=\textwidth]{...}`).**
  Never place UI screenshots side-by-side in `subfigure` environments or shrink
  them to `0.8\textwidth`/`0.85\textwidth` — desktop UI text becomes unreadable
  when narrowed.
- **Matplotlib plot legends:** Place legends cleanly outside curves (e.g.,
  centered above subplots with `loc="lower center", bbox_to_anchor=(0.5, 1.02),
  ncol=2, frameon=False`, or in guaranteed empty whitespace) and visually inspect
  the exported PNG before compiling.
- **Zero overflow:** Keep `pgfgantt` charts (`x unit`), wide tables, and equations
  within `\textwidth` so `main.log` reports **zero** `Overfull \hbox >= 10 pt`.
- **Numerical truth:** Every quantitative figure in Chapters 0, 3, 4, 6, 7, and 8
  (masses, stresses, FoS, displacements, mesh counts, convergence %, equilibrium
  residuals, solve times, benchmark errors, module line counts, test count) must
  match `data/facts.md`, `data/verification.json`, and live `pytest` output.
- **Line endings:** Several `structure/*.tex` files use Windows CRLF (`\r\n`).
  Preserve existing line endings when editing programmatically so git diffs stay
  minimal and clean.
