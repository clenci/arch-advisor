# Test case script — /arch-advisor

Use these pre-written responses to run a reproducible session against the Technical Document Critic Agent use case.
When prompted for a project name at session start, enter: `document-critic-agent`

---

## Group A — Domain and Purpose

**Q1. What problem does this system solve?**
The system receives a technical document (Markdown) and produces a critical analysis report — classifying type and domain, evaluating depth, completeness, clarity, and actionability, and iteratively refining the report until acceptable quality is reached. It solves the problem of manual technical documentation review in software teams.

**Q2. Who are the end users?**
Primarily other systems (CI/CD pipelines, repository tooling) that invoke the agent programmatically via `agent.analyze()`. Developers consume the generated Markdown report — no interactive interface at runtime.

**Q3. What is the primary action the system takes?**
Orchestrate + generate: orchestrates a sequential 4-layer pipeline (Perception → Decision → Memory → Reflection) and produces a critical analysis report as its primary output.

---

## Group B — Scale and Performance

**Q4. What is the expected request volume?**
Low volume: tens of documents per day, no concurrency. Typical use case: analysis before merge (1–5 docs/hour per team). The module mentions scaling to 1,000 docs/day as a future improvement — not a current requirement.

**Q5. What is the acceptable response latency?**
Async — minutes. The pipeline executes 4–7 LLM calls in series (classify + generate + 1–3× [critique + revise]). Observed latency: 30s–3min per document. No real-time response requirement.

**Q6. Is cost per request a hard constraint or a soft budget item?**
Hard constraint: fixed budget of $0.30 per analysis. The agent stops the Reflection Loop when the budget is reached (`stoppedBy: "costBudget"`). Actual observed cost: $0.09–$0.15 per complete analysis with 3 iterations.

**Group B mandatory follow-up — arrival pattern:**
> The caller is a CI/CD pipeline (external automated system), so the plugin will ask whether volume is steady or bursty.

*Response:* Bursty — spikes tied to CI/CD events (commit, PR open, merge). During a sprint, a team might submit 10–20 documents in 30 minutes around a release, then nothing for hours.

---

## Group C — Data and Integrations

**Q7. What data sources does the system need to access?**
Local files: Markdown documents on disk (implemented). In-memory LTM: previous analyses indexed by domain to enrich the current report (implemented). Planned but not implemented: URLs, PDF, HTML — the module specified multiple formats and ChromaDB/SQLite; the implementation simplified to Markdown + in-memory LTM.

**Q8. Are there existing systems that must be integrated?**
None. The agent is autonomous. CI/CD integration happens in the external invocation layer, outside the agent's scope.

**Q9. What is the data sensitivity level?**
Internal: technical software documentation (architectures, patterns, design decisions). No PII, no data regulated by LGPD/GDPR/HIPAA.

---

## Group D — Constraints and Team

**Q10. Are there technology constraints?**
Language: TypeScript + Node.js. LLM: Anthropic Claude via corporate proxy (no direct access to the public API). Available models: Claude Sonnet 4.6 (default) and Haiku 4.5 (fast/cheap). No external vector store: the module planned ChromaDB/Pinecone, but the implementation uses word-overlap in-memory to keep zero external dependencies beyond the LLM. No database: the module planned SQLite; the implementation simplified to runtime memory.

**Q11. What is the team's familiarity with LLM/agent systems?**
Experienced: the system is being built as part of a Principal AI Architect study guide — the explicit goal was to master Reflection Loop, LTM, multi-layer pipeline, and design patterns (Strategy, Chain of Responsibility, State Machine).

**Q12. Are there compliance or audit requirements?**
None. Development/study environment. The module required structured logging and trace IDs for internal observability, not regulatory compliance.

---

## Group E — Failure, History, and Priorities

**Q13. Has this system (or something similar) been attempted before? If yes: what failed or was abandoned, and why?**
Yes — a simpler version was attempted without the Reflection Loop, using a single LLM call to generate the full report. It was abandoned because output quality was inconsistent: the report would miss critical gaps in documents that appeared well-structured on the surface. The multi-stage pipeline was introduced specifically to address this.

**Q14. If this system produces a wrong or low-quality output, what is the consequence?**
Developer wastes time reviewing a flawed report. In the worst case, a low-quality document passes review because the agent missed the gaps. No financial loss or regulatory exposure — this is an internal tooling system.

**Q15. If you had to cut one requirement to ship four weeks earlier, which would you cut?**
The LTM enrichment. The core value is in the Reflection Loop and the per-document quality assessment. The LTM adds marginal improvement (cross-document pattern recognition) but is not critical for the initial use case.

**Q16. Who, outside the development team, will decide whether this system is working well enough? What will they measure?**
The team lead reviewing pull requests. They will measure whether the agent catches the same issues a senior engineer would flag — specifically: undocumented assumptions, missing NFRs, and vague "why" sections in ADRs.

**Q17. Are there multi-step operations where a failure in a later step would require undoing earlier steps?**
No. Each analysis is an isolated read-only operation — no writes to external systems, no reservations, no transactions. If the pipeline fails mid-way, the partial report is simply discarded and the job is re-run. No rollback required.

**Q18. Is there a requirement to reconstruct exactly what happened at any past point in time?**
No strict audit requirement. The structured logs with trace IDs are for debugging purposes (why did the agent score this document 0.62?), not for regulatory reconstruction. Replay capability would be nice-to-have but is not a current requirement.

---

## Phase 1.5 — Tensions to expect and how to respond

### Expected tension: In-memory LTM does not persist between processes

> Accepted consciously. The module planned SQLite + ChromaDB; I simplified to focus on memory patterns, not infrastructure. For production, the `AnalysisLTM` interface supports swapping without changing the pipeline.

### Expected tension: 4–7 sequential LLM calls vs. latency target

> Accepted. The requirement is async. The Reflection Loop has a budget ceiling and a maximum iteration count as safety valves.

### Expected tension: Word-overlap may fail on multilingual terms

> Low real-world risk: the domain space is controlled by the classifier (values like 'software architecture', not free-form user queries).

### Expected tension: Perception limited to Markdown vs. multi-format requirement

> Deliberately reduced scope. The module planned TXT/PDF/HTML/URL; the implementation prioritized the Decision, Memory, and Reflection layers — which were the pedagogical focus.

---

## Phase 2 — Ambiguities to expect and how to respond

### A1 — LTM persistence model

*Is the agent invoked as a long-running process (server/daemon receiving multiple documents) or as an ephemeral process (a new process per analysis, standard in CI/CD jobs)?*

> The agent is long-running within a session: `DocumentAnalysisAgent` is instantiated once in `main()` and the `for (const doc of documents)` loop reuses the same instance — the LTM accumulates across analyses in the same run. Each new process starts with an empty LTM. So: ephemeral across processes, persistent within a process. In real CI/CD use (one process per commit), the LTM only adds value if multiple documents are analyzed in the same job — which is the case in `run.ts` (2 docs with overlapping domains). For cross-run persistence, the LTM would need to be serialized to disk.

### A2 — Reflection Loop stopping condition

*Does the loop stop only when the budget is reached or the counter hits 3, or is there a quality condition — can the critic signal "no further revisions needed" before hitting the limit?*

> Three stopping conditions are implemented, checked in order:
> 1. Quality threshold (`isAcceptable = overallScore >= 0.78`) — the loop exits early if the score is already sufficient (log: "Threshold reached")
> 2. Budget exhausted (`totalCost >= $0.30`) — interrupts before a revision iteration
> 3. Maximum iterations (`MAX_ITERATIONS = 3`) — absolute limit
>
> The critic does signal acceptable quality via `critique.isAcceptable`, and that is the primary exit condition — not just a counter or budget check.

### A3 — Perception stage extensibility contract

*Do future formats (URL, PDF, HTML) need a formal extension point (adapter interface) in the current design, or are they treated as completely out of scope and the pipeline can assume Markdown as the only input?*

> No formal adapter interface. The perception layer consists of two exported functions in `perception.ts`: `loadDocument(filePath): string` and `chunkDocument(content): Chunk[]`. There is no `SourceLoader` or `FormatAdapter` interface. Markdown is the only supported format — `loadDocument` uses `readFileSync` directly. Adding PDF/URL would require refactoring to a Strategy pattern, which does not exist today. The plugin will identify this as an extensibility gap.

### A4 — Cost tracking

*Is the per-LLM-call cost obtained via token count in the API response (post-call), via a pre-call estimate, or via fixed allocation per stage (e.g., classify=Haiku, generate=Sonnet)?*

> Post-call via the API's usage object. Every component that calls the LLM (classifier, report-generator, critic, reviser) calculates cost after receiving the response using `response.usage.input_tokens` and `response.usage.output_tokens` with hard-coded prices ($3.00/M input, $15.00/M output — Sonnet prices). The orchestrator accumulates `totalCost += componentCost`. No pre-call estimate, no fixed allocation — the calculation is always exact, based on real tokens consumed.

### A5 — Output schema

*Is the generated report schema fixed (predefined sections: Summary, Issues, Recommendations) or dynamic — determined by the type/domain of the document classified in the first stage?*

> Fixed schema with dynamic content. The sections are predefined in the ReportGenerator prompt: `### Summary`, `### Strengths`, `### Gaps and Issues`, `### Recommendations`, `### Quality Score`. The document type and domain (from the classifier) influence the content of those sections (via `focusAreas` and `ltmContext` injected into the prompt), but not the structure. The schema is free-form Markdown — there is no structured output parsing; `reportMarkdown` is a raw string.
