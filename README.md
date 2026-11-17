# NEMO 2

NEMO designs marine steelwork: lifting padeyes, pipe support brackets and the
structure inside stabilizer fins. You describe the job, and NEMO:

- picks the sizes from the plate stock your workshop has;
- checks the design against the rules that fit the part: ASME BTH-1 for padeyes,
  AISC 360 for pipe supports (with a pipe-span vibration check), IACS UR S10 for
  stabilizer fins (with its own foil load model and a cavitation check);
- runs a built-in stress simulation;
- shows its working: every formula with its numbers, a live view of the search
  and the stress solve, and a Verification page that reruns its benchmarks;
- gives you a PDF calculation report with a fabrication drawing, a 3D model (STEP)
  and a cutting file (DXF);
- if you use Autodesk Fusion, opens padeyes there as editable models, checks your
  edits, and records a Fusion stress cross-check in the report.

NEMO is a design aid. A competent engineer must review every design before it is
made or used.

## Start here

1. Double-click **Install NEMO.bat** (first time only, needs internet).
2. Double-click the **NEMO** shortcut on your desktop.

Full instructions: [Getting started](docs/getting-started.md).

## Guides

| Guide | For |
| --- | --- |
| [Getting started](docs/getting-started.md) | Installing and your first design |
| [User guide](docs/user-guide.md) | Every screen explained, with worked examples |
| [Pipe support brackets](docs/pipe-support-brackets.md) | The bracket's questions, checks and the pipe vibration check |
| [Stabilizer fins](docs/stabilizer-fins.md) | The fin's questions, loads, checks and cavitation |
| [Understanding your results](docs/understanding-results.md) | What the checks and the stress result mean |
| [Glossary](docs/glossary.md) | Engineering words in plain language |
| [Troubleshooting](docs/troubleshooting.md) | When something does not work |
| [Limits and safety](docs/limits-and-safety.md) | What NEMO does not check |
| [Using NEMO with Fusion](docs/using-nemo-with-fusion.md) | Connecting Fusion, opening designs, checking edits and cross-checking stress |
| [Engineering manual](docs/engineering-manual.md) | Every equation, source and verification result |
| [Developer guide](docs/developer-guide.md) | For programmers only |

## Folders

| Folder | Contents |
| --- | --- |
| `engine/` | Calculation engine (Python) |
| `app/` | The screens you use (runs in your browser) |
| `design-system/` | Graphite design system the screens follow |
| `docs/` | Guides |
| `tools/` | Installer |
| `PLAN.md` | The agreed plan and progress |
