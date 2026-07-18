# gs-dev (Codex CLI plugin)

A **Codex CLI port** of the `gs-dev` sprint-workflow — plan a cycle, break it into
GitHub Issues, build in parallel waves, review with a panel of specialist subagents
that post PR comments, and close the cycle out. Uses the `gh` CLI.

This repo is a **Codex plugin marketplace**: its root holds the marketplace catalog
and the `gs-dev` plugin. Ported from the original [Claude Code gs-dev plugin](https://github.com/Gradient-Systems-AI/gs-dev).

## Layout

```
gs-dev-codex/                         # <- this repo IS the marketplace root
├── .agents/plugins/marketplace.json  # catalog → plugins/gs-dev
├── plugins/gs-dev/
│   ├── .codex-plugin/plugin.json     # plugin manifest (skills + hooks)
│   ├── skills/                       # 5 skills → the /sprint-* workflow
│   ├── agents/                       # 16 subagents: reviewers + spec-reviewer + scorer + verify + implementer-s/m/l
│   └── hooks/                        # SessionStart hook that syncs the agents
├── AGENTS.md
├── config.example.toml
└── README.md
```

## Install (tested on codex-cli 0.144.5)

```bash
# 1. Register this repo as a marketplace (local path, or owner/repo / git URL once pushed)
codex plugin marketplace add Gradient-Systems-AI/gs-dev-codex

# 2. Install the plugin (brings the 5 skills)
codex plugin add gs-dev@gradientsystems

# 3. Install the 16 subagents into ~/.codex/agents/
#    Option A — run the bundled installer from the plugin cache (one command):
bash ~/.codex/plugins/cache/gradientsystems/gs-dev/*/hooks/install-agents.sh
#    Option B — let the bundled SessionStart hook do it automatically on next
#    interactive `codex` launch (Codex will ask once to trust the hook; approve it).

# 4. gh auth login   # this variant creates Issues and PRs
```

Then set `agents.max_threads = 8` in `~/.codex/config.toml` (see `config.example.toml`)
so the 7-agent review panel runs in parallel instead of serializing.

Verify: `codex plugin list -m gradientsystems` shows `installed, enabled`, and
`ls ~/.codex/agents` lists the 16 `*.toml` agents.

### Why the agents install separately

Codex plugin manifests bundle **skills, MCP, apps, and hooks — but not custom
subagents** (verified against the plugin schema). The gs-dev skills spawn named
specialists (`correctness-reviewer`, `implementer`, `verify`, …) that must live in
`~/.codex/agents/`. Step 3 puts them there — either by one command, or via the
bundled hook once you trust it. The hook is idempotent and never clobbers your edits.

## What was ported, and how

| Claude Code primitive | → Codex equivalent |
|---|---|
| `skills/*/SKILL.md` | Codex **skills** (same format), bundled in the plugin |
| `agents/*.md` (`model`, `tools`) | `~/.codex/agents/*.toml` (`name`, `description`, `developer_instructions`, `model_reasoning_effort`, `sandbox_mode`) |
| `Agent` tool parallel dispatch | Codex **subagents** (`agents.max_threads` caps fan-out) |
| per-agent `model: sonnet/opus/inherit` | per-agent **tier (L/M/S)** → a real model resolved at install + `model_reasoning_effort` |
| `tools: Read, Glob, Grep` (read-only) | `sandbox_mode = "read-only"` (reviewers) / `"workspace-write"` (spec-keeper, implementer, verify) |
| `${CLAUDE_PLUGIN_ROOT}/skills/...` | skill-relative paths (`formats/…`, `../other-skill/formats/…`) |
| `.claude-plugin/plugin.json` + `marketplace.json` | `.codex-plugin/plugin.json` + `.agents/plugins/marketplace.json` |
| `gh` / `git` bash | unchanged |

### Model selection — a real model per complexity tier, resolved at install

Each agent is tagged with a tier (`L`/`M`/`S`). At install, `hooks/resolve-models.py`
reads `~/.codex/models_cache.json` (the models your Codex actually has) and picks the
best available model per tier, then sets it plus a reasoning effort in each agent file.

| Tier | Preferred model | Fallbacks | Effort | Agents |
|---|---|---|---|---|
| **L** — complex / high-stakes | `gpt-5.6-sol` (frontier) | `gpt-5.5` → `gpt-5.4` | high | correctness, clarity, type-integrity, build-architect, `implementer-l` |
| **M** — balanced / everyday | `gpt-5.6-terra` | `gpt-5.4` → `gpt-5.5` | medium | error-hunter, exposure, test-integrity, fragility, repo-scout, spec-keeper, spec-reviewer, scorer, `implementer-m` |
| **S** — simple / fast | `gpt-5.6-luna` | `gpt-5.4-mini` → `gpt-5.4` | low | verify, `implementer-s` |

Why this is robust:
- **Different models per complexity**, not one model with the thinking turned up/down.
- **Self-adapting** — resolves against each machine's model list; never writes an invalid id.
- **Graceful fallback** — if nothing matches, the agent omits `model` and inherits the session model.
- **Idempotent** and **respects your overrides** — pin a model by editing the agent's
  `model = ` line in `~/.codex/agents/` and deleting its `# gs-dev:auto` marker; the installer leaves it alone.
- The `S/M/L` ticket labels drive `sprint-build` to the matching `implementer-s/m/l` agent.

## Verified vs. still to validate

**Verified live** on codex-cli 0.144.5: marketplace registers, `codex plugin add`
installs the plugin to the cache with skills + agents + hooks, the plugin shows
`installed, enabled`, and the installer resolves per-tier models and places all 16 agents in
`~/.codex/agents/`.

**Worth confirming in real use:**
- The `SessionStart` hook auto-firing requires a one-time **hook-trust** approval in
  interactive Codex; under `codex exec` untrusted hooks are skipped. Step 3 Option A
  sidesteps this.
- Codex's subagent delegation is more model-driven than Claude's explicit `Agent`
  calls — smoke-test the two fan-out moments (a `sprint-build` wave; the
  `sprint-review` 7-agent panel) and confirm it parallelizes rather than working inline.
- `fragility-reviewer`'s `gh` PR-comment lookup needs network; the git-churn analysis
  runs regardless.

## Provenance

Ported from the Claude Code gs-dev plugin, itself adapted from LikeAHuman.ai under MIT.
