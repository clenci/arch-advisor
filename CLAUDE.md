# arch-advisor — development context

## What this repository is

Public repository for the `arch-advisor` Claude Code plugin. Marketplace: `arch-advisor`. The plugin is an interactive architecture advisor for multi-agent LLM systems, invoked via `/arch-advisor`.

## Structure

```
arch-advisor/
├── .claude-plugin/
│   └── marketplace.json          ← local marketplace registry
├── arch-advisor/                 ← main plugin (v5.0.0, current version)
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── commands/
│   │   └── arch-advisor.md       ← main command (all phases)
│   ├── skills/                   ← 15 skills (14 domain + pattern-deepening)
│   │   ├── pattern-deepening/    ← added in v4.2.0
│   │   ├── agent-internal-architecture/
│   │   ├── architecture-documentation/
│   │   ├── data-memory-storage/
│   │   ├── integration-protocols/
│   │   ├── legacy-integration/
│   │   ├── llm-frameworks/
│   │   ├── llm-selection-routing/
│   │   ├── multiagent-orchestration/
│   │   ├── observability-slo/
│   │   ├── omnichannel-architecture/
│   │   ├── rag-strategy/
│   │   ├── security-governance/
│   │   ├── testing-quality/
│   │   └── when-to-use-agents/
│   ├── hooks/
│   │   ├── hooks.json
│   │   └── session_start.py
│   └── CHANGELOG.md
├── COMPARACAO-VARIANTES.md       ← comparative evaluation rubric (18 dimensions, /90)
└── teste-case.md                 ← canonical test case (Technical-Document-Critic-Agent)
```

## How to install the plugin

```
/plugin marketplace add /path/to/arch-advisor
/plugin install arch-advisor@arch-advisor
```

## Local development (without installing)

```bash
./dev.sh           # invokes claude with --plugin-dir pointing to arch-advisor/
```

Edits to plugin files (`arch-advisor.md`, `SKILL.md`, `session_start.py`) are reflected immediately on the next invocation.

## Plugin flow (v5.0.0)

1. **Phase 1 — Discovery**: Asks for project name (slug), initializes `arch-advisor/<slug>/`; Groups A–E with adaptive follow-ups; incremental appends to `session.md` after each group; silent flags `hybrid-decision-candidate` and `hitl-candidate` computed in Group A
2. **Phase 1.5 — Tension Resolution**: one tension at a time, consequence framing, waits for response; appends to local `session.md`
3. **Phase 1.6 — Stress Test**: 3 questions (10x scale, budget −50%, future requirements); appends to local `session.md`
4. **Phase 1.7 — Summary Review**: creates `requirements.md`, `tradeoffs.md`, `README.md` (placeholder); structured summary + 2 meta-questions to the user; updates pointer
5. **Phase 2 — Requirements Analysis**: patterns, ambiguities, risks, constraints impact; updates `requirements.md` with resolved ambiguities
6. **Phase 3 — Architecture Proposal**: 3 options (MVA / Balanced / Next Scale Tier); updates `tradeoffs.md` with choice rationale; updates pointer
7. **Phase 3.5 — Pattern Deepening (visible)**: presents triggered patterns to the user; invokes `arch-advisor:pattern-deepening`; produces per-pattern blocks with concrete design decisions and critical constraint
8. **Phase 3.6 — Domain Deepening (silent)**: invokes up to 2 domain skills before artifact generation
9. **Phase 4 — Artifact Generation**: C4 diagram, ADR, Decision Matrix, NFR Checklist written to `arch-advisor/<slug>/`; explicitly invokes `architecture-documentation`, `observability-slo`, `testing-quality`, and `security-governance` (conditional); updates `README.md` with index + Key Decisions + Top Risks + When to Revisit
10. **Phase 5 — Refinement Loop**: Step 1 = artifact review; Step 2 = deepening menu mapped to skills; deepening docs in `arch-advisor/<slug>/`; `README.md` updated; pointer marked `complete`

## Current state and known gaps

### Resolved gaps

**1. Group B follow-up** — RESOLVED (v4.0.0)
- The condition `"if any answer is underspecified"` was replaced with an explicit positive check: if the caller is an external system or automated process AND the arrival pattern (steady vs. bursty) was not explicitly stated → follow-up is mandatory.

**2. Structural amplitude of options** — RESOLVED (v4.0.0)
- Option C must introduce at least one infrastructure component not present in Option B (durable queue, external store, separate worker process). Prevents two tiers of similar complexity.

**3. `agent-internal-architecture` trigger** — RESOLVED (v4.1.0)
- Trigger criterion made explicit: fires when the architecture includes a Reflection Loop, multi-stage pipeline, STM/LTM, explicit state machine, or budget-controlled iteration.

**4. HITL and Hybrid DE flags untested** — RESOLVED (v4.2.0, validated in v7)
- Both flags (`hitl-candidate` and `hybrid-decision-candidate`) validated in the medical-diagnosis-voting-arbiter case (89/90).
- Group C HITL follow-up: distinguishes synchronous vs. asynchronous approval; async activates HITL+Checkpointing in Pattern Deepening.
- Group D Hybrid DE follow-up: collects fraction of deterministic cases to decide if Rule Engine + LLM cascade is justified.

**5. `arch-advisor:pattern-deepening` skill** — RESOLVED (v4.2.0)
- 12 blocks implemented; 4/12 fired in the tech-doc-critic case (no false positives); 7/12 in medical-diagnosis.

### Remaining gap (single)

**5c — `agent-internal-architecture` not offered in deepening menu for cascade state machines** — HIGH PRIORITY (1 point to 90/90)

Current score: 4/5. The deepening menu inclusion criterion (Phase 5 Step 2) covers "Reflection Loop, multi-stage pipeline, STM/LTM, explicit state machine, budget-controlled iteration" — but does not explicitly cover cascades with multiple deterministic stages (e.g., VotingCoordinator with majority → weighted → threshold → arbiter). The medical-diagnosis case has exactly this structure and the criterion did not capture it.

**Pending fix in `arch-advisor.md`:** expand the inclusion criterion to:
> "Include if the chosen architecture has a VotingCoordinator, cascade strategy, or any internal component with a multi-stage deterministic pipeline — not only single agents with reflection loops."

### What has been validated and works

- Tension Resolution with consequence framing generates new architectural components (BudgetMonitor, CheckpointStore emerged from tensions, not requirements)
- Stress Test calibrates thresholds with user data (vs. generic estimates)
- Explicit skill invocations in Phase 4 produce measurable and traceable differences in artifacts
- Deepening menu (Phase 5 Step 2) generates implementation detail that the main flow does not reach
- Phase 3.5 Pattern Deepening: 4/12 correct blocks in tech-doc-critic; 7/12 in medical-diagnosis; 0 false positives in both
- Flags `hybrid-decision-candidate` and `hitl-candidate`: validated in medical-diagnosis; all 4 flags fired correctly

## Scores by version

| Version | Score | Validated case |
|---|---|---|
| v1.0.0 | 40/90 | Technical-Document-Critic-Agent |
| v2.0.0 | 46/90 | Technical-Document-Critic-Agent |
| v3.0.0 | 54/90 | Technical-Document-Critic-Agent |
| v4.0.0 | 82/90 | Technical-Document-Critic-Agent |
| v4.1.0 | 87/90 | Technical-Document-Critic-Agent |
| v4.2.0 (v6) | 87/90 | Technical-Document-Critic-Agent (regression) |
| v4.2.0 (v7) | 89/90 | Medical-Diagnosis-Voting-Arbiter |
| v4.3.0 | — | (gap 5c fixed; not re-validated) |
| v5.0.0 | — | (Session Repository refactor; not re-validated) |

## References

- `arch-advisor/CHANGELOG.md` — version history v1→v5.0.0
- `teste-case.md` — canonical test case for running sessions against the plugin
