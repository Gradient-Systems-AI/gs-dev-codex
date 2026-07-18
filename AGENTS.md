# gs-dev-codex — repo guidance for Codex

This repo is the **Codex CLI port** of the `gs-dev` sprint-workflow plugin
(originally a Claude Code plugin, GitHub-integrated variant). It is a five-phase
development pipeline driven by skills and parallel subagents, and it uses the
**`gh` CLI** for GitHub Issues and Pull Requests. Run `gh auth login` before use.

It ships as a Codex plugin: skills live in `plugins/gs-dev/skills/`, and the 16
specialist subagents install into `~/.codex/agents/` (see README).

## The pipeline

Run these skills in order over a cycle:

1. **sprint-plan** — discovery, codebase scan, architecture discussion → Brief, Stories, ADRs, Sprint Plan (`.brief/`, `.stories/`, `.adr/`, `.sprint/`)
2. **sprint-tickets** — decompose the plan into right-sized **GitHub Issues** + a build-order issue with parallel wave analysis
3. **sprint-build** — implement Issues in parallel waves via `implementer` subagents, verify with `verify`, open draft PR(s)
4. **sprint-review** — fan out to the specialist reviewer agents, score findings 0–100, post only ≥75 as PR comments, flip the PR to ready
5. **sprint-refine** — fix findings, patch the system spec (`.spec/spec.md`) via `spec-keeper`, close the cycle

## How orchestration maps to Codex

- The skills are the orchestrators; they run on the **main thread** and delegate
  fan-out work to the custom agents under `~/.codex/agents/`. Keep `agents.max_depth = 1`.
- When a skill says "dispatch via the Agent tool" or "in one message with multiple
  Agent calls," that means: **delegate to Codex subagents in parallel**.
- Named specialists (`correctness-reviewer`, `clarity-reviewer`, `error-hunter`,
  `type-integrity-reviewer`, `test-integrity-reviewer`, `fragility-reviewer`,
  `exposure-reviewer`, `repo-scout`, `build-architect`, `spec-keeper`) carry their
  own model + reasoning + sandbox in `.codex/agents/*.toml`. Spawn them **by name**.
- Generic build work uses the `implementer` agent (one per Issue) and the `verify`
  agent (one per wave, runs the workspace verification command verbatim).
- Run `codex` from this repo root so repo-relative paths (`.agents/skills/...`) resolve.

## GitHub state

Tickets are GitHub Issues; builds go on a `feat/…` branch and open draft PR(s);
review posts PR comments and applies labels (`needs-review`, `needs-refine`).
The living system spec is `.spec/spec.md`; cycle artifacts are the dot-dirs
`.brief/`, `.stories/`, `.adr/`, `.sprint/`.
