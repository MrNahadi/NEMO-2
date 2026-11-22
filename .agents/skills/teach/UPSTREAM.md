# Upstream Provenance & Repo Hygiene (`teach`)

- **Upstream repository:** https://github.com/mattpocock/skills
- **Upstream path:** `skills/productivity/teach`
- **Pinned commit SHA:** `abeeaf95660ba9e8b7c753eb38f441ca707a8823`
- **Commit date:** `2026-11-19 13:34:58 +0000` (`Merge pull request #1455 from mattpocock/ci-frontmatter-check`)
- **License:** MIT License (Copyright (c) 2026 Matt Pocock — see [`LICENSE`](./LICENSE))

## Bundled upstream files (vendored verbatim)

- `SKILL.md`
- `GLOSSARY-FORMAT.md`
- `LEARNING-RECORD-FORMAT.md`
- `MISSION-FORMAT.md`
- `RESOURCES-FORMAT.md`
- `agents/openai.yaml`
- `LICENSE`

## Repository hygiene when running `teach` in NEMO

The `teach` skill treats the current working directory as a stateful learning workspace and creates `MISSION.md`, `RESOURCES.md`, `NOTES.md`, `./lessons/`, `./reference/`, `./learning-records/`, and `./assets/`.

To keep the NEMO engineering repository root clean:

- Run `/teach` inside a dedicated subdirectory under `learning/` (for example `learning/<topic>/`), **not** at the repository root.
- `learning/` is ignored in the root `.gitignore` so personal multi-session HTML lessons and notes never dirty `git status`.
