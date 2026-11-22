---
name: nemo-report-updates
description: >-
  Update, synchronize, verify, and compile NEMO's LaTeX final-year BSc Marine
  Engineering project report in reports/project-report/. Use this skill whenever
  the user asks to edit report chapters, update report numbers after engine or
  FEA changes, regenerate report figures or UI screenshots, fix citations,
  labels, tables, or LaTeX layout warnings, or recompile main.pdf. Do not use
  for interactive multi-session learning (use teach) or for standalone code
  changes in engine/ or app/ that do not ask to update the report.
---

# NEMO Project Report Updates

This skill governs every edit to NEMO's JKUAT final-year BSc Marine Engineering
report in `reports/project-report/`. It keeps prose, figures, UI screenshots,
citations, and `main.pdf` synchronized with executed engine outputs and enforces
institutional, framing, style, and layout rules through a deterministic checker.

## Core Invariants (Non-Negotiable)

Read [references/rules-and-style.md](./references/rules-and-style.md) for the
complete rule set. Never violate these core constraints:

1. **Ground every number in raw executed outputs.** Read
   `reports/project-report/data/facts.md` and `data/verification.json` before
   editing. Never invent figures, test counts, solve times, or citations.
2. **Standalone `\NEMO{}` project framing.** Never refer to the project as
   `NEMO 2`, `\NEMO{}~2`, `first phase`, `second phase`, or `Phase 1/2`. Cite
   prior prototype trials concisely only as early exploratory testing context.
3. **Subtle marine-engineering defense register.** Write for a panel of BSc
   Marine Engineering lecturers (shipboard load paths, ASME BTH-1, AISC 360-16,
   IACS UR S10, ship-motion accelerations, machinery-space pipe resonance, foil
   hydrodynamics and cavitation, shipyard plate stock) without overstatement.
4. **Golden Thread alignment.** Preserve Section 1.4 (`1.4.1 General objective`
   and `1.4.2 Specific objectives` with 3 achieved objectives) and 3 aligned
   Research Questions across Chapters 1, 2, 3, 4, 5, and 7. Keep unproven items
   (physical proof testing, formal usability studies) in Scope/Limitations and
   Future Work.
5. **`WRITING-BRIEF.md` prose discipline.** Plain formal academic English,
   active voice, sentence-case headings, thin spaces before units (`28.3~kN`),
   **zero** em-dashes (`---`, `—`), **zero** en-dashes used as prose dashes, and
   **zero** banned AI buzzwords.
6. **Readable figures & full-width UI screenshots.** Every application UI
   screenshot (`images/app-*.png`) MUST be a standalone single figure at full
   `\textwidth` (`width=\textwidth`) — never inside a `subfigure` or shrunk
   below `\textwidth`. Keep Matplotlib plot legends clear of data curves.
7. **JKUAT UPRO layout & CRLF hygiene.** Preserve the preamble, `./media/HDlogo.png`,
   Roman front matter, Arabic chapters, IEEEtran citations, `booktabs`+`tabularx`
   tables, `[H]` floats, and existing CRLF line endings when patching `.tex` files.

## Step-by-Step Update Workflow

### Step 1: Audit raw sources first

1. Inspect `reports/project-report/WRITING-BRIEF.md`, `data/facts.md`,
   `data/verification.json`, and the specific `.tex` files being modified (never
   rely on `main.pdf` text alone).
2. If the user's change affects engine outputs, solver results, test counts,
   plots, or UI screens, identify which upstream artifacts in
   `reports/project-report/data/` and `reports/project-report/images/` must be
   regenerated first.

### Step 2: Regenerate upstream data, plots, PDF samples, and UI screenshots (when needed)

Follow the exact commands in [references/pipeline-and-build.md](./references/pipeline-and-build.md):

- Engine/FEA/case/verification changes: run `make_report_data.py`, `dump_facts.py`,
  `make_figures.py`, and `render_pdf_pages.py`.
- Advanced settings changes: run `make_advanced_data.py`.
- Frontend/UI changes: run `stage_projects.py` and `screenshots.py` against a
  freshly built `app/dist`.
- Inspect every regenerated plot and screenshot visually to confirm zero clipped
  text, zero overlapping legends, and accurate numbers.

### Step 3: Edit `.tex` and `references.bib`

1. Keep edits surgical and preserve existing file line endings (CRLF in edited
   `.tex` files).
2. Use `\NEMO{}` for the project name and `\code{...}` for paths, filenames, and
   identifiers.
3. Verify every added BibTeX entry against an official source or DOI before
   adding it to `reports/project-report/references.bib`. Never fabricate a source.
4. When adding or splitting figures/tables/sections, update every `\ref{...}` in
   prose so no dangling or mismatched numbers remain.

### Step 4: Compile `main.pdf` cleanly with MiKTeX

Run the full MiKTeX compile sequence documented in
[references/pipeline-and-build.md](./references/pipeline-and-build.md) (`pdflatex`
-> `bibtex` -> `pdflatex` -> `pdflatex` when citations changed, or two `pdflatex`
passes otherwise). Every pass must exit with code `0`.

### Step 5: Run the deterministic verification gate & visual spot-check

Run the bundled validator script from the repository root:

```powershell
engine\.venv\Scripts\python.exe .agents\skills\nemo-report-updates\scripts\verify_report.py
```

The update is **not complete** until:

1. `verify_report.py` exits with code **`0`** (zero framing regressions, zero
   style violations, all `app-*.png` screenshots single & full-width, zero
   broken images/labels/refs/citations, clean `main.log` with zero errors, zero
   warnings, and zero `Overfull \hbox >= 10 pt`).
2. You visually render and inspect the affected pages of `main.pdf` (using
   `pypdfium2` or `pdftoppm`) to confirm typography, tables, figures, and margins
   look publication-ready.
3. `git status` shows no stray scratch files in the repository.
