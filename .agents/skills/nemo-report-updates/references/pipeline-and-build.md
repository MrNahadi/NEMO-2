# NEMO Report Data Regeneration & MiKTeX Build Pipeline

All commands below assume repository root `C:\Users\muigu\Desktop\SIDE\NEMO2`
unless stated otherwise.

---

## 1. Upstream Data, Figures & PDF Samples

Run only the stages affected by your code/UI changes:

### A. Case studies, verification suite, and `data/facts.md`

```powershell
# Run from engine/ using the engine virtual environment
Set-Location C:\Users\muigu\Desktop\SIDE\NEMO2\engine

# Full regeneration (cases + verification + sweeps):
.venv\Scripts\python.exe ..\reports\project-report\tools\make_report_data.py

# Or selective regeneration (faster when only cases + verification changed):
.venv\Scripts\python.exe ..\reports\project-report\tools\make_report_data.py cases verification

# Advanced settings data (if oblique sling / bracket flexibility / fin astern changed):
.venv\Scripts\python.exe ..\reports\project-report\tools\make_advanced_data.py

# Rebuild human-readable numerical source of truth (data/facts.md):
.venv\Scripts\python.exe ..\reports\project-report\tools\dump_facts.py
```

### B. Matplotlib plots & 3D stress renders (`images/*.png`)

```powershell
Set-Location C:\Users\muigu\Desktop\SIDE\NEMO2\engine
.venv\Scripts\python.exe ..\reports\project-report\tools\make_figures.py
```

To regenerate a single figure (e.g., `panel-validation.png`) during layout tuning,
import `make_figures` from `reports/project-report/tools/`, call `_fonts()`, and
invoke the specific function (e.g., `panel_validation()`).

### C. Rendered sample pages from generated PDF calculation reports

`render_pdf_pages.py` requires `pypdfium2` and `Pillow` (not installed inside
`engine/.venv`; use a Python venv outside the repository if needed):

```powershell
<python-with-pypdfium2> C:\Users\muigu\Desktop\SIDE\NEMO2\reports\project-report\tools\render_pdf_pages.py
```

### D. Live Desktop UI Screenshots (`images/app-*.png`)

`screenshots.py` requires `playwright` (Chromium) and a freshly built `app/dist`.
Stage the three case-study projects into a temporary directory outside the repo
so the repo stays clean:

```powershell
# 1. Stage projects into a scratch folder
engine\.venv\Scripts\python.exe reports\project-report\tools\stage_projects.py <scratch>\staged_projects

# 2. Capture all 10 UI screenshots (uses local server on port 8768, shuts it down cleanly)
<python-with-playwright> reports\project-report\tools\screenshots.py <scratch>\staged_projects
```

Confirm all 10 files (`app-home`, `app-new-design`, `app-padeye-describe`,
`app-bracket-motion`, `app-padeye-results`, `app-padeye-check-working`,
`app-fin-results-stress`, `app-bracket-record`, `app-verification`, `app-running`)
updated cleanly and that no server remains listening on port `8768`.

---

## 2. Automated Test Count & Module Metrics

Before updating test counts or Appendix A LOC tables, verify live numbers:

```powershell
Set-Location C:\Users\muigu\Desktop\SIDE\NEMO2\engine
.venv\Scripts\python.exe -m pytest -q
```

---

## 3. Compiling `main.tex` -> `main.pdf` (MiKTeX on Windows)

```powershell
Set-Location C:\Users\muigu\Desktop\SIDE\NEMO2\reports\project-report
$texbin = "C:\Users\muigu\AppData\Local\Programs\MiKTeX\miktex\bin\x64"

# Full build (use whenever references.bib or citations changed):
& "$texbin\pdflatex.exe" -interaction=nonstopmode main.tex
& "$texbin\bibtex.exe" main
& "$texbin\pdflatex.exe" -interaction=nonstopmode main.tex
& "$texbin\pdflatex.exe" -interaction=nonstopmode main.tex
```

If only `.tex` prose or images changed (no BibTeX changes), two `pdflatex`
passes suffice to settle cross-references, ToC, LoF, and LoT.

---

## 4. Verification Gate & Visual Inspection

1. Run the deterministic checker:

```powershell
Set-Location C:\Users\muigu\Desktop\SIDE\NEMO2
engine\.venv\Scripts\python.exe .agents\skills\nemo-report-updates\scripts\verify_report.py
```

2. Visually inspect modified pages of `reports/project-report/main.pdf` by
   rendering them to a temporary folder outside the repository (via `pypdfium2`
   or MiKTeX's `pdftoppm.exe`) and checking margins, captions, legends, tables,
   and screenshot legibility.
