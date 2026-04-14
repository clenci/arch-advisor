# arch-advisor

An interactive architecture advisor for multi-agent LLM systems, running as a Claude Code plugin. It conducts a structured discovery session — surfacing tensions, stress-testing requirements, and proposing grounded architectures — and produces four ready-to-use artifacts: a C4 container diagram, an Architecture Decision Record (ADR), a weighted decision matrix, and an NFR checklist.

## What it produces

- **C4 Container Diagram** — Mermaid diagram showing system components and relationships
- **ADR** — Architecture Decision Record for the primary structural decision, with justification and trade-offs
- **Decision Matrix** — Weighted scoring of three proposed options against criteria tied to your requirements
- **NFR Checklist** — Non-functional requirements with concrete targets (no TBDs), covering performance, cost, reliability, quality, observability, extensibility, and security
- **Deepening documents** (Phase 5) — Focused 1–2 page deep dives on agent coordination, RAG strategy, storage design, LLM selection, legacy integration, and more

## How it works

The advisor runs a 10-phase structured session: **Discovery** (5 groups of questions with adaptive follow-ups) → **Tension Resolution** (one tension at a time, consequence framing) → **Stress Test** (10× scale, −50% budget, future requirements) → **Summary Review** → **Requirements Analysis** → **Architecture Proposal** (3 options: MVA / Balanced / Next Scale Tier) → **Pattern Deepening** (12 architectural patterns, triggered selectively) → **Domain Deepening** (up to 2 domain skills applied silently before artifact generation) → **Artifact Generation** → **Refinement Loop** (review + deepening menu). All outputs are written incrementally to `arch-advisor/<session-slug>/` in your project directory. See [CHANGELOG.md](arch-advisor/CHANGELOG.md) for full version history.

## Installation

### Stable (from GitHub)

```
/plugin marketplace add https://github.com/cezarlenci/arch-advisor
/plugin install arch-advisor@arch-advisor
```

### Local development (edits reflected immediately)

```bash
# Using the wrapper script (recommended):
./dev.sh

# Or set a permanent shell alias:
alias arch='claude --plugin-dir /path/to/arch-advisor/arch-advisor'
```

The wrapper script (`dev.sh`) passes all arguments to `claude` with `--plugin-dir` pointing to the local source. Changes to any `SKILL.md`, `arch-advisor.md`, or `session_start.py` are live on the next invocation — no reinstall needed.

## Usage

```
/arch-advisor new              # start a new architecture session
/arch-advisor resume <slug>    # resume an existing session
```

Sessions are stored in `arch-advisor/<slug>/` relative to your current working directory.

## Testing

- **Test cases**: [`test-cases/`](test-cases/) — three scripted sessions with pre-written responses for reproducible testing:
  - `01-support-routing-agent` — hybrid+HITL flags, SOC 2/PII, no saga, no event sourcing
  - `02-medical-research-assistant` — no flags triggered, HIPAA/RAG multi-corpus, event sourcing required
  - `03-fraud-detection-payments` — hybrid+HITL flags, PCI-DSS, saga rollback, full event sourcing
- **Evaluation rubric**: [`COMPARACAO-VARIANTES.md`](COMPARACAO-VARIANTES.md) — 18-dimension rubric, /90 scale, for evaluating new plugin versions
- **Reference outputs**: [`casos-de-referencia/`](casos-de-referencia/) — two validated executions (87/90 and 89/90) for regression comparison

## Plugin structure

```
arch-advisor/
├── commands/
│   └── arch-advisor.md       ← main command (all 10 phases)
├── skills/                   ← 15 domain skills invoked selectively
│   ├── pattern-deepening/    ← 12 architectural patterns
│   ├── agent-internal-architecture/
│   ├── architecture-documentation/
│   ├── data-memory-storage/
│   ├── integration-protocols/
│   ├── legacy-integration/
│   ├── llm-frameworks/
│   ├── llm-selection-routing/
│   ├── multiagent-orchestration/
│   ├── observability-slo/
│   ├── omnichannel-architecture/
│   ├── rag-strategy/
│   ├── security-governance/
│   ├── testing-quality/
│   └── when-to-use-agents/
└── hooks/
    └── session_start.py      ← detects active sessions at conversation start
```

## Skills

| Skill | Trigger |
|---|---|
| `pattern-deepening` | Invoked in Phase 3.5 — implementation-level blocks for 12 architectural patterns |
| `agent-internal-architecture` | Reflection loops, multi-stage pipelines, STM/LTM, state machines, budget-controlled iteration |
| `architecture-documentation` | C4 diagram and ADR generation (Phase 4) |
| `data-memory-storage` | Vector databases, cross-session memory persistence, polyglot storage |
| `integration-protocols` | MCP servers, agent-to-agent communication, tool governance |
| `legacy-integration` | ERPs, CRMs, unstable legacy APIs |
| `llm-frameworks` | LangChain vs. LangGraph vs. CrewAI vs. custom |
| `llm-selection-routing` | Model selection, routing by cost/capability, multi-provider fallback |
| `multiagent-orchestration` | Multiple agents, inter-agent communication, parallel execution |
| `observability-slo` | Logging, tracing, SLOs, error budgets (Phase 4) |
| `omnichannel-architecture` | Multi-channel systems (chat, WhatsApp, email, web) |
| `rag-strategy` | Chunking, embedding models, retrieval methods, reranking |
| `security-governance` | LGPD/GDPR/HIPAA compliance, TRiSM controls, audit trails (Phase 4, conditional) |
| `testing-quality` | Eval frameworks, LLM-as-judge, quality gates (Phase 4) |
| `when-to-use-agents` | Agent vs. deterministic service decision framework |

## Current version

**v5.0.0** — Session Repository refactor. All outputs are self-contained per session in `arch-advisor/<slug>/`.

Validation scores: **87/90** (technical-document-critic-agent) · **89/90** (medical-diagnosis-voting-arbiter)

See [CHANGELOG.md](arch-advisor/CHANGELOG.md) for full history.

## License

MIT
