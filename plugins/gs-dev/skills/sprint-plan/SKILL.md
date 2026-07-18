---
name: sprint-plan
description: "Create a Sprint Plan (the cycle-versioned objective), capture ADRs, write or update the living Brief and Stories, and patch the system Spec through guided discovery, codebase exploration, and architecture discussion. Use when user has an idea for what to build, says 'I want to build', 'let's plan', 'I have a project idea', or wants to start a new development cycle."
argument-hint: "Brief description of the feature (optional)"
---

> **Codex adaptation note.** This skill was ported from a Claude Code plugin. Translate its Claude-isms as you execute:
> - **"the Agent tool" / "dispatch a subagent" / "in one message with multiple Agent calls"** -> delegate to Codex **subagents**. To fan out in parallel, ask for the work to be delegated to N subagents at once; Codex collects their results back into this thread. The named specialists (`correctness-reviewer`, `clarity-reviewer`, etc.) are installed as custom agents under `~/.codex/agents/` (synced by this plugin) -- spawn them by name.
> - **Model tiers** -- when the skill names a Claude model for a subagent, it maps to a real Codex model chosen **per tier at install** from the models this machine actually has: `opus`/`inherit` -> **L** (frontier, e.g. `gpt-5.6-sol`, high reasoning); `sonnet` -> **M** (balanced, e.g. `gpt-5.6-terra`, medium); `haiku` -> **S** (fast, e.g. `gpt-5.6-luna`, low). Each named specialist already carries its resolved model + effort in `~/.codex/agents/*.toml` (synced by this plugin, with automatic fallback to gpt-5.5/5.4 when the 5.6 family is absent), so you spawn it by name and never set the model yourself.
> - **Build subagents** route by ticket complexity to distinct agents/models: **S** -> `implementer-s` (fast), **M** -> `implementer-m` (balanced), **L** -> `implementer-l` (frontier, high reasoning); workspace verification -> `verify` (fast).
> - This variant uses the **`gh` CLI** for Issues/PRs -- make sure `gh auth status` is green before running the tickets/build/review phases.
> - Parallel fan-out is capped by `agents.max_threads` in `~/.codex/config.toml` -- set it to 8+ so the full review panel runs at once (see the plugin's `config.example.toml`). Bundled files referenced below (`formats/`, `prompts/`) are relative to this skill's own directory.


# /sprint-plan — Sprint Plan + ADR Creation

You are an experienced planning partner taking the user from a raw idea to a complete cycle plan. That plan isn't one file — it's five artifacts, each changing at its own pace:

1. **Brief** (`.brief/brief.md`) — the living product charter (vision, problem, target users, principles, north-star + quality goals as guardrails, non-goals, definition-of-done home). Written once on greenfield; lightly touched thereafter.
2. **Stories** (`.stories/STORIES.md`) — the living set of current-relevant wants with stable monotonic IDs (US-001…). Edited as wants are added, refined, or die.
3. **ADRs** (`.adr/ADR.md`) — the append-only log of architectural decisions (MADR-lite + mandatory Y-statement). History is load-bearing; never edit, never delete.
4. **Spec** (`.spec/spec.md`) — the cycle-living system description. Read here; patched by `/sprint-refine`, not by this skill.
5. **Sprint Plan** (`.sprint/sprint-v{N}.md`) — the cycle-versioned, immutable objective for THIS cycle. This skill's primary write target.

On a brand-new product idea (no Brief yet), an optional sixth file can precede these — `.brief/market-research.md`: a one-time, non-canonical competitor/market scan (Phase 0.5) that informs the Brief but sits outside the versioned model and isn't read automatically by anything downstream.

Five phases carry the work: project setup, discovery, codebase exploration, architecture discussion (with decision tracking), and writing (Sprint Plan + ADRs + Stories, plus the Brief on greenfield).

The Sprint Plan feeds `/sprint-tickets`. The ADRs constrain every phase that follows. Every artifact points at the others instead of restating them — the Sprint Plan cites US-### and the Brief's DoD rather than re-listing story sentences or quality goals.

**Initial request:** $ARGUMENTS

---

## Phase 0: Project Setup

Before anything else, read what already exists and make sure the project is ready.

### 0.1 Read existing artifacts

Scan for the five-artifact model. Each read below is **skip-if-absent** — a missing file just means greenfield or pre-migration, not an error.

**Read `.brief/brief.md` (if it exists):**
- The living product charter: vision, durable problem, target users, principles (the product's governing tenets), north-star metric + quality goals as guardrails, non-goals, and the canonical definition-of-done.
- Stay aligned with it — this cycle's Sprint Plan has to serve the Brief's north-star and respect its non-goals.
- If it's missing, this is likely a greenfield first cycle — the Brief gets authored in Phase 4.

**Read `.stories/STORIES.md` (if it exists):**
- The living set of current-relevant wants, each with a stable monotonic ID (US-001…). It's both the alignment source and the sprint-fuel source (the *story backlog* — distinct from the *review backlog* at `.sprint/backlog.md`).
- Note which US-### the user's intent maps onto. New wants get the next free ID; conflicts get resolved (loser edited or removed, the WHY routed to an ADR) in Phase 4.

**Read `.spec/spec.md` (if it exists):**
- The current system description from the last cycle.
- Use it to understand what already EXISTS without re-exploring the whole codebase.
- Surface the key points: "Based on the spec, the system currently has [summary]. What are we adding?"

**Read `.adr/ADR.md` (if it exists):**
- Prior decisions that CONSTRAIN this cycle.
- Note any "Revisit when" conditions that may now be met — these carry deferred debt too.
- Surface relevant constraints: "Previous decisions to keep in mind: [key ADRs]"

**Read the `.sprint/` directory:**
- Which Sprint Plans exist, what status, what they cover. (Versions map 1:1 to sprints — every `sprint-v*.md` is a real plan, never a dumping ground.)

### 0.2 Project scan and context-aware opening

Before asking the first question, scan the project.

**Read:** `package.json`, `README.md`, `CLAUDE.md`, the top-level folder structure.

If `.spec/spec.md` exists, you already know the system — lean on it instead of re-reading everything. Adapt the opening line accordingly:

| State | Opening |
|-------|---------|
| Spec exists | "I've read your spec — [system summary]. What are we building next?" |
| Draft Sprint Plan exists | "You've got a draft going (v{N}) — covers [summary]. Let's finish it." |
| Only built/archived Sprint Plans, no draft | "Last cycle was [summary]. Ready for the next one?" |
| Code exists but no docs | "I can see [project description]. What's the plan?" |
| Empty project | "What are you building?" |

### 0.3 Sprint Plan lifecycle

Enforce the Sprint Plan lifecycle: `draft → built → archived` (+ `abandoned`). `draft` covers everything up to working code — planning **and** the build against it; `/sprint-build` is what flips it to `built` once the code lands (not `/sprint-tickets`, and not this skill). There's no `released` status on a project Sprint Plan. Tech debt and below-threshold review findings never enter the version sequence — `/sprint-review` routes them to the review backlog (`.sprint/backlog.md`), which nothing reads automatically.

**Active-draft limit:** at most ONE `status: draft` in `.sprint/` at a time. If a draft already exists, push to finish it. If the user wants to abandon it instead, mark it `abandoned` and start a fresh one.

**Cascade on a new draft:** creating a new draft flips every previous `built` Sprint Plan to `archived`. Work out the version number from what's already on disk.

**This skill only ever creates Sprint Plans in `status: draft`.** It never writes built or archived directly.

### 0.4 Basic scaffolding

1. Check for `.sprint/` — create if missing.
2. Check for `.adr/` — create if missing (with a brief note: "ADRs capture WHY you chose what you chose — future you will thank present you.").
3. Check for `.stories/` — create if missing (holds the living `STORIES.md`).
4. **Greenfield only:** if `.brief/brief.md` doesn't exist yet, create the `.brief/` folder — `brief.md` gets authored in Phase 4 (first cycle only).
5. Check for `.git/` — init if missing.

---

## Phase 0.5: Greenfield Market Research (optional, greenfield only)

**Trigger:** only when `.brief/brief.md` doesn't exist — a first cycle, a brand-new product idea. Skip entirely once a project already has a Brief; this only ever runs once.

Before Discovery, offer a quick market/competitor scan so the Brief's Vision, Problem, and Value proposition rest on more than the user's own framing:

> "Before we dive into discovery — want me to do a quick scan of the market first? I'll look at a handful of competitors/alternatives and where the gaps are. Takes a couple minutes and feeds directly into the Brief. Or we can skip straight to discovery if you already know the landscape."

**If the user accepts:**
1. If the idea is still vague, ask one clarifying question first — "What's the product in a sentence, and who's it for?" — enough to search on, not a full Discovery pass.
2. Run 2-4 targeted WebSearch queries for direct competitors/alternatives, how they position themselves, and any obvious gap or underserved angle.
3. Present a short summary — 5-8 bullets max, a scan, not a report:
   > "Quick market scan:
   > - **Alternatives:** [name] — [one line on positioning], [name] — [one line]...
   > - **Gap/opening:** [what's underserved or poorly done by existing options]
   > - **Watch out for:** [anything that suggests the space is crowded/hard, if true]"
4. Ask: "Does this match what you were expecting, or does it change how you're thinking about this?"
5. Write the findings to `.brief/market-research.md` — dated, reference-only. It isn't one of the five versioned artifacts and nothing downstream reads it automatically; it just keeps the research from being lost, so Phase 4.0 can draw on it when drafting the Brief. Keep it as short as the summary above — not a full standalone report.

**If the user declines** → go straight to Phase 1. Don't bring it up again this session.

---

## Phase 1: Discovery

**Goal:** understand the problem the user wants solved. Read their depth and adapt to it.

### Gauge depth from signals

- Vague input ("I want to build something for my team") → start with problem framing, keep the language simple.
- Specific input ("Add a webhook endpoint with retry logic") → skip the basics, ask about edge cases.
- Empty → fall back to the opening from Phase 0.2.

### Discovery questions (one at a time, adapt based on answers)

- What problem does this solve? Who experiences it?
- What does success look like? How will you know it worked?
- What constraints exist — time, tech, team, budget?
- What's the simplest version that would actually be useful?

### When a spec already exists

If `.spec/spec.md` exists, you already know the system — skip questions about "what tech stack" or "what does the project do." Jump straight to what's NEW this cycle.

### Gate

Once you can summarize the feature in 3-5 sentences and the user confirms it captures their intent, move to Phase 2.

---

## Phase 2: Codebase Exploration

**Goal:** get fresh codebase context for whatever this feature will touch.

Launch 2-3 `repo-scout` agents (sonnet, parallel) using `prompts/repo-scout-prompt.md`. Give each a different mode — architecture mapping, pattern matching, integration analysis.

If `.spec/spec.md` exists, scope exploration to the areas the new feature actually TOUCHES — don't re-map what the spec already covers. The spec is the system map.

Only read files where you need more than the explorers already surfaced — they quote the relevant code, so don't re-read wholesale. Check findings against the spec:
- **Consistent** → proceed silently.
- **Drift detected** → note it; it may need a spec update in `/sprint-refine`.

---

## Phase 3: Architecture Discussion

Architectural decisions surface here. Track them as they emerge.

### The discussion

Work through the technical approach with the user. Cover:
- How does this feature fit the existing architecture?
- What new components/services/tables does it need?
- What patterns does it follow, or break from?
- What alternatives exist?

### Decision tracking

As the discussion moves, quietly note any decision that crosses the ADR threshold:
- Crosses a module or service boundary.
- Introduces a new dependency.
- Constrains future options.
- Would still be argued about in six months.

For each qualifying decision, track:
- What was decided.
- What alternatives came up, and why they were rejected.
- What consequences it creates.

Don't break the flow to formally write ADRs yet — let the conversation stay natural. Capture happens in Phase 4.

---

## Phase 4: Write Sprint Plan + Capture ADRs + Update Stories (+ greenfield Brief)

### 4.0 Greenfield Brief authoring (first cycle only)

If `.brief/brief.md` doesn't exist, author it now, and only now. There's no separate founding-doc step — the Brief itself is the founding document.

1. If `.brief/market-research.md` exists (from Phase 0.5), read it — let the competitive gap/opening sharpen the Vision and Value proposition, and let any "watch out for" findings inform the Non-goals or Principles where relevant. Distill it; don't quote it at length.
2. Use `formats/brief-format.md`. Write to `.brief/brief.md`.
3. Capture: vision (one sentence), durable problem, target users (one line), value prop, the principles/tenets, the north-star metric DEFINITION + guardrails (no period targets), 3-5 quality goals as guardrails, durable non-goals, the canonical definition-of-done home, and a `last_reviewed` date. Frontmatter is `last_reviewed` ONLY — no version/status/author.
4. Keep it a charter, not a discovery dump. On later cycles, touch the Brief only when strategy shifts — and pair every strategic shift with a product ADR.

### 4.1 Write the Sprint Plan

Use `formats/sprint-format.md`. Write to `.sprint/sprint-v{N}.md`.

The Sprint Plan is the cycle-versioned, immutable objective for THIS cycle. Its **User-stories slice REFERENCES the US-### IDs** from `.stories/STORIES.md` plus any cycle-specific detail — it never restates the story sentence itself. Its Definition-of-Done points back at the Brief; its success metric names the Brief's north-star. A greenfield first cycle writes `sprint-v1.md`.

### 4.2 Create / edit Stories + conflict detection

Reconcile `.stories/STORIES.md` with this cycle's intent, following `formats/stories-format.md`. Stories are LIVING, not append-only — edit them, and remove entries whose want has died.

1. **New wants** → add entries with the next free monotonic ID (US-001, US-002, …). IDs are NEVER reused; removing one retires the number and leaves the gap (git keeps the history). Format: "As a X, I want Y, so that Z" — the so-that is mandatory — plus epic. No status, no acceptance criteria; built-vs-unbuilt gets derived later by `/sprint-refine`'s coverage view. Run an optional INVEST check on new entries.
2. **Conflict detection** → if a new want contradicts an existing story, resolve it: edit or remove the loser. The WHY behind picking the winner is an architectural/product decision — **route it to an ADR**, it doesn't belong in STORIES.md. Removing a story retires its ID.
3. If `.stories/STORIES.md` doesn't exist yet, create it with a short header explaining it's the living set of current-relevant wants with stable monotonic IDs.

### 4.3 Capture ADRs (with a one-time alignment check at the gate)

Once the Sprint Plan and Stories are drafted, look back over the architecture discussion. For each decision that crosses the threshold:

1. Draft an ADR entry using the format in `formats/adr-format.md`.
2. Include the mandatory Y-statement, context, alternatives, consequences, coarse subsystem scope, and revisit trigger. Also draft a product ADR for any story-conflict WHY (4.2) and for any strategic shift that touched the Brief (4.0).

**Alignment check (one-time, at this gate only):** before presenting the ADRs, sanity-check the cycle's plan against the Brief's product principles and non-goals — e.g. a "privacy over personalisation" principle, or a durable non-goal the plan would cross. This is **flag-not-block** — if something seems to cut against a principle, surface it for the user to resolve right here. It's not a separate enforced gate elsewhere in the flow; raise it once, at this approval step, and move on.

**Resolution gate (`[OPEN QUESTION]`):** while planning, if you hit something you can't resolve from the user, the artifacts, or the codebase — an ambiguous requirement, an unstated decision, a missing constraint — drop an `[OPEN QUESTION: <the specific question>]` marker inline where it belongs (the draft Sprint Plan or a Story). Before the plan is approved and leaves `draft`, **every marker has to be resolved**: surface them as "I don't have enough to build this — clarify: …" and only proceed once none remain. A frozen plan with an open `[OPEN QUESTION]` isn't ready. This is quality control at the point of creation — never punting an unknown to a later phase.

**Approval gate — present to the user:**

> "I identified [N] architectural decisions worth recording as ADRs:
>
> 1. **ADR-{NNN}: {title}** — {Y-statement summary}
> 2. **ADR-{NNN}: {title}** — {Y-statement summary}
>
> [If any principle flag:] One thing to flag against your Brief principles: [concern]. Happy to proceed, or adjust?
>
> Want to review these before I write them? (approve / edit / remove any)"

**Gate:** the user must explicitly approve. They may:
- Approve all → write them.
- Edit → adjust wording, add or remove alternatives.
- Remove → "That's too small for an ADR" — respect it.
- Add → "You missed one: we also decided X" — draft it.
- Resolve the principle flag — proceed as-is, or adjust the plan.

### 4.4 Commit artifacts

**Commit before signalling completion — this is not optional.** The session may end right after this step.

```bash
git add .sprint/sprint-v{N}.md .adr/ADR.md .stories/STORIES.md
# greenfield first cycle also:
git add .brief/brief.md
git commit -m "docs: Sprint Plan v{N} + ADRs + Stories for {feature name}"
```

If `.adr/ADR.md` didn't exist before, it gets created with this header:

```markdown
# Architecture Decision Records

All architectural decisions for this project. One decision per section, numbered sequentially. Decisions are append-only — to reverse a decision, add a new one that supersedes it.

---

{ADR entries here}
```

---

## Phase 5: Handoff

The Sprint Plan, ADRs, and Stories (plus the Brief on greenfield) are now committed. Since the Phase 2 codebase exploration is still in context, the fastest path is to **run `/sprint-tickets` in the same session** — it detects the retained map and skips its own cold re-exploration. Offer it:

> "Sprint Plan, ADRs, and Stories are committed, and I've still got the codebase map loaded from planning. Run `/sprint-tickets` now in this session and it'll reuse that exploration instead of starting cold. Ready?"

Then give a brief summary of what was captured:
- Sprint Plan: what's being built this cycle (the single pass/fail objective).
- Stories: new/edited US-### (just IDs + one-liners).
- ADRs: key decisions (just titles).
- Brief (greenfield only): authored as the founding charter.
- Next step: `/sprint-tickets` — same session reuses this exploration (no cold re-explore); a fresh session re-derives context from the spec or a cold sweep.

---

## Key Principles

- **Five artifacts, five paces**: Brief (living charter), Stories (living wants), ADRs (append-only history), Spec (cycle-living, patched by `/sprint-refine`), Sprint Plan (cycle-versioned, immutable). Each REFERENCES the others — never reproduces them.
- **Spec-aware**: if a spec exists, you already know the system. Don't re-ask what you can read.
- **Stories are living, IDs are forever**: edit or remove wants freely, but never reuse a US-### — a removed ID is retired, the gap stays, git holds the history.
- **Conflicts route to ADRs**: when a new want beats an old one, edit or remove the loser and record the WHY as an ADR — not in STORIES.md.
- **ADRs emerge from conversation**: don't force them. Track decisions naturally, formalize afterward.
- **Approval gate for ADRs**: the user sees and approves before anything gets written. It's their project, their decisions. The one-time alignment check rides this same gate — flag-not-block — rather than getting its own separate checkpoint.
- **Commit before done**: artifacts only count once they're on disk. The session may end immediately after.
- **Batch Bash & trust the explorers**: combine independent `git` reads into one invocation, and lean on the explorer agents' quoted findings instead of re-reading files wholesale. macOS/BSD-portable shell only.
- **Threshold matters**: not every choice earns an ADR. When in doubt, leave it in the Sprint Plan.
- **Append-only ADRs**: never edit existing entries. New entries go at the bottom.
- **Review backlog, not Issues**: below-threshold review findings go to the review backlog (`.sprint/backlog.md`), never filed as GitHub Issues — those are for committed work only.
