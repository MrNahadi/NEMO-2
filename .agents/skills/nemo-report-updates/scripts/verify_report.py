#!/usr/bin/env python3
"""Deterministic verification gate for NEMO's LaTeX project report.

Checks all machine-verifiable rules from WRITING-BRIEF.md, the standalone NEMO
framing contract, JKUAT UPRO layout standards, UI screenshot width rules,
cross-references/citations, data/facts.md synchronization, and main.log health.

Usage:
    python .agents/skills/nemo-report-updates/scripts/verify_report.py
    python .agents/skills/nemo-report-updates/scripts/verify_report.py --report-dir path/to/report
    python .agents/skills/nemo-report-updates/scripts/verify_report.py --skip-log
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Violation:
    file: str
    line: int
    rule: str
    message: str

    def format(self) -> str:
        loc = f"{self.file}:{self.line}" if self.line > 0 else self.file
        return f"{loc}: [{self.rule}] {self.message}"


LEGACY_NAME_RE = re.compile(r"\\NEMO\{\}[~\s]*[12]\b|\bNEMO[~\s]+[12]\b", re.IGNORECASE)
PHASE_SEQUEL_RE = re.compile(
    r"\b(?:first|second|previous)\s+phase\b|\bPhase\s+[12]\b",
    re.IGNORECASE,
)
OLD_OBJECTIVES_RE = re.compile(
    r"\bObjective\s+[456]\b|\bObjectives\s+1[–\-]6\b|\bRQ4\b"
    r"|\bsix\s+objectives\b|\bfour\s+research\s+questions\b",
    re.IGNORECASE,
)
EM_DASH_RE = re.compile(r"—|---")
EN_DASH_PROSE_RE = re.compile(r"\s--\s|\s–\s")

BANNED_WORDS = [
    "additionally",
    "crucial",
    "delve",
    "enduring",
    "enhance",
    "fostering",
    "garner",
    "interplay",
    "intricate",
    "landscape",
    "pivotal",
    "showcase",
    "tapestry",
    "testament",
    "underscore",
    "vibrant",
    "leverage",
    "utilize",
    "utilise",
    "facilitate",
    "robust",
    "seamless",
    "comprehensive",
    "paradigm",
    "holistic",
    "cutting-edge",
    "game-changing",
    "moreover",
    "furthermore",
]
BANNED_PHRASES = [
    r"\bserves\s+as\b",
    r"\bstands\s+as\b",
    r"\bboasts\b",
    r"\bit\s+is\s+important\s+to\s+note\s+that\b",
    r"\bin\s+order\s+to\b",
]
BANNED_WORDS_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(w) for w in BANNED_WORDS) + r")\b|"
    + "|".join(BANNED_PHRASES),
    re.IGNORECASE,
)

# Stale pre-V&V-patch numbers that must not reappear in prose/tables
STALE_NUMBERS_RE = re.compile(
    r"\b1\.1\.0\b|\b210\.4\b|\b184\.4\b|\b200\.2\b|\b36\.33\b|\b35\.15\b"
    r"|\b248\.4\b|\b253\.8\b|\b6\.42\b"
)

INCLUDEGRAPHICS_RE = re.compile(r"\\includegraphics(?:\[([^\]]*)\])?\{([^}]+)\}")
WIDTH_OPTION_RE = re.compile(r"(?:^|,)\s*width\s*=\s*([^,\s]+)")


def strip_comment(line: str) -> str:
    """Remove unescaped LaTeX % comments."""
    out = []
    escaped = False
    for ch in line:
        if ch == "%" and not escaped:
            break
        escaped = (ch == "\\") and not escaped
        out.append(ch)
    return "".join(out)


def check_tex_files(report_dir: Path, violations: list[Violation]) -> tuple[set[str], list[tuple[str, int, str]], list[tuple[str, int, str]]]:
    main_tex = report_dir / "main.tex"
    structure_dir = report_dir / "structure"
    tex_files = []
    if main_tex.exists():
        tex_files.append(main_tex)
    else:
        violations.append(Violation("main.tex", 0, "STRUCTURE_MISSING", "main.tex not found"))

    if structure_dir.exists():
        tex_files.extend(sorted(structure_dir.glob("*.tex")))
    else:
        violations.append(Violation("structure", 0, "STRUCTURE_MISSING", "structure/ directory not found"))

    labels: set[str] = set()
    label_locations: dict[str, tuple[str, int]] = {}
    refs: list[tuple[str, int, str]] = []
    cites: list[tuple[str, int, str]] = []

    for f in tex_files:
        rel = f.relative_to(report_dir).as_posix()
        text = f.read_text(encoding="utf-8")
        lines = text.splitlines()

        in_verbatim = False
        in_subfigure = False

        for lineno, raw_line in enumerate(lines, 1):
            code = strip_comment(raw_line)

            # Track verbatim / lstlisting blocks
            if re.search(r"\\begin\{(?:lstlisting|verbatim)\}", code):
                in_verbatim = True
            if re.search(r"\\begin\{subfigure\}", code):
                in_subfigure = True

            # Extract labels (even on lstlisting header lines)
            for m in re.finditer(r"\\label\{([^}]+)\}", code):
                lbl = m.group(1)
                if lbl in labels:
                    prev_file, prev_line = label_locations[lbl]
                    violations.append(
                        Violation(
                            rel,
                            lineno,
                            "LABEL_DUPLICATE",
                            f"Duplicate label '{lbl}' (previously defined at {prev_file}:{prev_line})",
                        )
                    )
                else:
                    labels.add(lbl)
                    label_locations[lbl] = (rel, lineno)
            for m in re.finditer(r"\blabel\s*=\s*\{?([A-Za-z0-9_:-]+)\}?", code):
                lbl = m.group(1)
                if lbl not in labels:
                    labels.add(lbl)
                    label_locations[lbl] = (rel, lineno)

            # Extract refs & cites
            for m in re.finditer(r"\\(?:ref|eqref|pageref|autoref)\{([^}]+)\}", code):
                refs.append((rel, lineno, m.group(1)))
            for m in re.finditer(r"\\cite[a-z]*\*?(?:\[[^\]]*\])*\{([^}]+)\}", code):
                for key in m.group(1).split(","):
                    k = key.strip()
                    if k:
                        cites.append((rel, lineno, k))

            # Image existence & full-width UI screenshot rule
            for m in INCLUDEGRAPHICS_RE.finditer(code):
                opts = m.group(1) or ""
                img_rel = m.group(2).strip()
                img_path = (report_dir / img_rel).resolve()
                if not img_path.exists():
                    violations.append(
                        Violation(rel, lineno, "IMAGE_MISSING", f"Referenced image not found: {img_rel}")
                    )

                img_name = Path(img_rel).name
                if img_name.startswith("app-"):
                    if in_subfigure:
                        violations.append(
                            Violation(
                                rel,
                                lineno,
                                "SCREENSHOT_SUBFIGURE",
                                f"UI screenshot '{img_rel}' must be a standalone single figure, not inside subfigure",
                            )
                        )
                    wm = WIDTH_OPTION_RE.search(opts)
                    width_val = wm.group(1) if wm else ""
                    if width_val != r"\textwidth":
                        violations.append(
                            Violation(
                                rel,
                                lineno,
                                "SCREENSHOT_FULL_WIDTH",
                                f"UI screenshot '{img_rel}' must use width=\\textwidth (found '{opts or 'none'}')",
                            )
                        )

            # Prose-level checks (skip inside verbatim/lstlisting bodies)
            if not in_verbatim:
                if LEGACY_NAME_RE.search(code):
                    violations.append(
                        Violation(rel, lineno, "FRAMING_LEGACY_NAME", f"Legacy phase/version name found: {code.strip()}")
                    )
                if PHASE_SEQUEL_RE.search(code):
                    violations.append(
                        Violation(rel, lineno, "FRAMING_PHASE_SEQUEL", f"Sequel phase wording found: {code.strip()}")
                    )
                if OLD_OBJECTIVES_RE.search(code):
                    violations.append(
                        Violation(rel, lineno, "OBJECTIVES_DRIFT", f"Outdated objective/RQ count found: {code.strip()}")
                    )
                if STALE_NUMBERS_RE.search(code):
                    violations.append(
                        Violation(rel, lineno, "STALE_NUMBER", f"Pre-patch version or FEA number found: {code.strip()}")
                    )
                if EM_DASH_RE.search(code):
                    violations.append(
                        Violation(rel, lineno, "STYLE_EM_DASH", f"Em-dash forbidden by WRITING-BRIEF.md: {code.strip()}")
                    )
                if EN_DASH_PROSE_RE.search(code) and "\\draw" not in code:
                    violations.append(
                        Violation(rel, lineno, "STYLE_EN_DASH", f"En-dash used as prose dash: {code.strip()}")
                    )

                # Strip LaTeX environment names like \begin{landscape} before checking banned prose words
                prose = re.sub(r"\\(?:begin|end)\{[^}]+\}", " ", code)
                prose = re.sub(r"\\(?:usepackage|label|ref|cite|code|texttt)\{[^}]+\}", " ", prose)
                bm = BANNED_WORDS_RE.search(prose)
                if bm:
                    violations.append(
                        Violation(
                            rel,
                            lineno,
                            "STYLE_BANNED_WORD",
                            f"Banned word/phrase '{bm.group(0)}' from WRITING-BRIEF.md: {code.strip()}",
                        )
                    )

            if re.search(r"\\end\{(?:lstlisting|verbatim)\}", code):
                in_verbatim = False
            if re.search(r"\\end\{subfigure\}", code):
                in_subfigure = False

    # Check required objectives structure in 01-introduction.tex
    intro = structure_dir / "01-introduction.tex"
    if intro.exists():
        intro_text = intro.read_text(encoding="utf-8")
        if r"\subsection{General objective}" not in intro_text:
            violations.append(
                Violation(
                    "structure/01-introduction.tex",
                    0,
                    "OBJECTIVES_STRUCTURE",
                    "Missing '\\subsection{General objective}'",
                )
            )
        if r"\subsection{Specific objectives}" not in intro_text:
            violations.append(
                Violation(
                    "structure/01-introduction.tex",
                    0,
                    "OBJECTIVES_STRUCTURE",
                    "Missing '\\subsection{Specific objectives}'",
                )
            )

    # Check JKUAT HDlogo reference in main.tex
    if main_tex.exists():
        main_text = main_tex.read_text(encoding="utf-8")
        if "HDlogo.png" not in main_text:
            violations.append(
                Violation("main.tex", 0, "JKUAT_LOGO", "Title page must reference ./media/HDlogo.png")
            )

    return labels, refs, cites


def check_refs_and_cites(
    report_dir: Path,
    labels: set[str],
    refs: list[tuple[str, int, str]],
    cites: list[tuple[str, int, str]],
    violations: list[Violation],
) -> None:
    for rel, lineno, r in refs:
        if r not in labels:
            violations.append(Violation(rel, lineno, "REF_MISSING", f"Undefined reference target '{r}'"))

    bib_file = report_dir / "references.bib"
    if not bib_file.exists():
        violations.append(Violation("references.bib", 0, "BIB_MISSING", "references.bib not found"))
        return

    bib_text = bib_file.read_text(encoding="utf-8")
    bib_keys = set(re.findall(r"@\w+\{([^,\s]+),", bib_text))
    for rel, lineno, key in cites:
        if key not in bib_keys:
            violations.append(Violation(rel, lineno, "CITE_MISSING", f"Citation key '{key}' missing from references.bib"))


def check_facts_sync(report_dir: Path, violations: list[Violation]) -> None:
    facts_file = report_dir / "data" / "facts.md"
    if not facts_file.exists() or facts_file.stat().st_size == 0:
        violations.append(Violation("data/facts.md", 0, "FACTS_MISSING", "data/facts.md is missing or empty"))

    verif_file = report_dir / "data" / "verification.json"
    if verif_file.exists():
        try:
            verif = json.loads(verif_file.read_text(encoding="utf-8"))
            if not verif.get("passed", False):
                violations.append(
                    Violation("data/verification.json", 0, "VERIFICATION_FAILED", "verification.json reports passed != true")
                )
            for b in verif.get("benchmarks", []):
                if not b.get("passed", False):
                    violations.append(
                        Violation(
                            "data/verification.json",
                            0,
                            "VERIFICATION_FAILED",
                            f"Benchmark '{b.get('id', 'unknown')}' reports passed != true",
                        )
                    )
        except json.JSONDecodeError as exc:
            violations.append(Violation("data/verification.json", 0, "VERIFICATION_INVALID", f"Invalid JSON: {exc}"))


def check_main_log(report_dir: Path, violations: list[Violation]) -> None:
    log_file = report_dir / "main.log"
    if not log_file.exists():
        violations.append(
            Violation("main.log", 0, "LOG_MISSING", "main.log not found; compile main.tex or pass --skip-log")
        )
        return

    lines = log_file.read_text(encoding="latin-1").splitlines()
    patterns = [
        ("LOG_ERROR", re.compile(r"^! ")),
        ("LOG_UNDEF_REF", re.compile(r"Reference `[^']+' on page .* undefined|There were undefined references")),
        ("LOG_UNDEF_CITE", re.compile(r"Citation `[^']+' on page .* undefined")),
        ("LOG_MULT_LABEL", re.compile(r"Label `[^']+' multiply defined|There were multiply-defined labels")),
        ("LOG_RERUN", re.compile(r"Rerun to get cross-references right")),
        ("LOG_LATEX_WARN", re.compile(r"^LaTeX Warning: ")),
        ("LOG_PKG_WARN", re.compile(r"^Package .* Warning: ")),
    ]
    overfull_re = re.compile(r"Overfull \\hbox \(([0-9.]+)pt too wide\)")

    for lineno, line in enumerate(lines, 1):
        for rule, rx in patterns:
            if rx.search(line):
                violations.append(Violation("main.log", lineno, rule, line.strip()))
        om = overfull_re.search(line)
        if om and float(om.group(1)) >= 10.0:
            violations.append(Violation("main.log", lineno, "LOG_OVERFULL_HBOX", line.strip()))


def main(argv: list[str] | None = None) -> int:
    default_report = Path(__file__).resolve().parents[4] / "reports" / "project-report"
    parser = argparse.ArgumentParser(description="Verify NEMO LaTeX project report rules and build log.")
    parser.add_argument("--report-dir", type=Path, default=default_report, help="Path to reports/project-report")
    parser.add_argument("--skip-log", action="store_true", help="Skip main.log compilation checks")
    args = parser.parse_args(argv)

    report_dir = args.report_dir.resolve()
    violations: list[Violation] = []

    labels, refs, cites = check_tex_files(report_dir, violations)
    check_refs_and_cites(report_dir, labels, refs, cites, violations)
    check_facts_sync(report_dir, violations)
    if not args.skip_log:
        check_main_log(report_dir, violations)

    if violations:
        print(f"FAIL: {len(violations)} violation(s) found in {report_dir}:")
        for v in violations:
            print("  " + v.format())
        return 1

    print(
        f"PASS: NEMO report verification clean ({report_dir}) "
        f"[labels={len(labels)}, refs={len(refs)}, cites={len(cites)}, log={'skipped' if args.skip_log else 'checked'}]"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
