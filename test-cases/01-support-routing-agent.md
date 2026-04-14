# Test case 1 — Customer Support Routing Agent

**Slug:** `support-routing-agent`  
**Flags triggered:** `hybrid-decision-candidate=true`, `hitl-candidate=true` (sync approval)  
**Architecture archetype:** multi-agent with rule engine cascade, HITL in real-time path  
**Compliance:** SOC 2, PII in AWS — cannot send raw data to external LLM  
**Team maturity:** familiar  

---

## Session start

When asked for a project name, enter:
```
support-routing-agent
```

---

## Group A — Domain and Purpose

**Q1. What problem does this system solve?**
Routes incoming customer support tickets to the right team (billing, technical, sales, cancellation) and generates a first-response draft. Our current keyword-based classifier misroutes 15% of tickets — the #1 driver of customer escalations. Misrouted tickets reach the right team 4–8 hours late; for cancellation-intent tickets that often means a churned customer.

**Q2. Who are the end users?**
Both. Customers submit tickets via web, email, and chat (humans). The routing decision writes back to Salesforce CRM (other system). Support agents review the generated draft before sending it to the customer.

**Q3. What is the primary action?**
Classify + generate. Classifies ticket intent and urgency, routes to the correct queue, generates a first-response draft for the support agent to review and send.

> **Internal flags set by plugin (do not announce):**
> - `hybrid-decision-candidate = true` — primary action is classify
> - `hitl-candidate = true` — draft goes to customer after human approval

---

## Group B — Scale and Performance

**Q4. What is the expected request volume?**
~2,000 tickets/day. Peak concurrency ~50 during business hours (9am–6pm). Post-incident spikes can reach 3–5× normal volume for 2–4 hours.

**Q5. What is the acceptable response latency?**
Near-real-time <30s. The routing decision must complete before the support agent opens the ticket. The draft response must appear on the same screen load.

**Q6. Is cost per request a hard constraint or a soft budget item?**
Soft budget. Target under $0.05 per ticket. Our current manual cost is ~$8 per ticket in labor — LLM cost is not a binding constraint. We'd like to track it but it won't stop a feature.

**Group B mandatory follow-up — arrival pattern:**
> Plugin asks: "Is the request volume steady throughout the day, or does it spike in response to upstream events?"

Bursty. Steady during business hours but spikes sharply after product incidents. Post-outage events can triple volume for 2–4 hours. Monday mornings after weekend releases are also consistently heavier.

---

## Group C — Data and Integrations

**Q7. What data sources does the system need to access?**
Salesforce CRM for customer history and previous tickets. Confluence knowledge base for support documentation and known issue articles. Real-time ticket stream from the web/email/chat ingestion layer.

**Q8. Are there existing systems that must be integrated?**
Salesforce CRM — stable REST API. The routing decision must write back to Salesforce to update ticket status and assignee queue. That's the integration that matters most operationally.

**Q9. What is the data sensitivity level?**
PII. Customer names, email addresses, account details, and support conversation history are in every ticket. Some tickets mention payment issues which may include partial billing data.

**Group C priority follow-up — HITL (hitl-candidate=true):**
> Plugin asks: "Does that output go directly to the downstream system, or does a human need to approve it first?"

The draft response is shown to the support agent on a review screen. The agent edits it or clicks send. Approval is synchronous — the agent is in the loop in real time before anything reaches the customer. The routing decision (which queue to assign) is fully automated; only the draft response goes through human review.

---

## Group D — Constraints and Team

**Q10. Are there technology constraints?**
Python + FastAPI backend. Cloud: AWS. LLM: we planned to use OpenAI GPT-4o, but our SOC 2 requirements say customer PII cannot leave the AWS environment. We may need to use AWS Bedrock instead. Available models on Bedrock: Claude Sonnet, Claude Haiku, Titan. No external vector databases — must use AWS-native (OpenSearch or Bedrock Knowledge Bases).

**Q11. What is the team's familiarity with LLM/agent systems?**
Familiar. We've built LLM features before — sentiment analysis and auto-tagging for tickets. This is our first agent with multi-step logic, tool use, and a write-back integration. Nobody on the team has built a hybrid rule+LLM pipeline before.

**Q12. Are there compliance or audit requirements?**
SOC 2 Type II. PII cannot leave AWS. Every LLM interaction must be logged: input hash, output hash, user ID, timestamp, routing decision, confidence score. We need to be able to show auditors that PII was handled within our AWS boundary at all times.

**Group D priority follow-up — Hybrid DE (hybrid-decision-candidate=true):**
> Plugin asks: "What fraction are 'obvious' cases versus cases that genuinely require LLM reasoning?"

About 60–70% of tickets are clear-cut: "my invoice is wrong" → billing, "the app won't load" → technical. We already have keyword rules that catch most of these in under 50ms. The remaining 30–40% are genuinely ambiguous — "I need help with my upgrade" could go to billing, sales, or technical depending on context. That's where the LLM earns its keep. We don't want to throw away the existing rules — they work fine for the majority.

---

## Group E — Failure, History, and Priorities

**Q13. Has this been attempted before?**
Yes. We built a keyword-matching classifier 18 months ago. It handles the obvious cases well but has a 15% misrouting rate on ambiguous tickets. We didn't abandon it — it's still running. We're augmenting it, not replacing it.

**Q14. What is the consequence of wrong output?**
Ticket goes to the wrong team. Customer waits an extra 4–8 hours for re-routing. NPS impact is measurable — we see a 12-point NPS drop on misrouted tickets vs. correctly routed ones. For cancellation-intent tickets, a routing delay is directly correlated with churn. Financial exposure per misrouted ticket: roughly $200 in estimated lifetime value risk for cancellation cases.

**Q15. If you had to cut one requirement to ship four weeks earlier, which would you cut?**
Draft response generation. The routing decision alone solves the core problem. The draft response is a nice-to-have that reduces agent handle time but isn't the reason we're building this.

**Q16. Who outside the team decides if this is working? What will they measure?**
The Support Operations lead owns this. She measures: first-contact resolution rate (FCR) — baseline 72%, target >85%. Re-routing rate — baseline 15%, target <5%. She reviews these weekly. If FCR doesn't improve within 60 days of launch, the project is considered failed.

**Q17. Are there multi-step operations requiring rollback?**
No. The CRM write (status + assignee) is a single idempotent operation. If it fails, the ticket stays in the unassigned queue and a support manager manually assigns it. No compensation logic needed.

**Q18. Is there a requirement to reconstruct past state exactly?**
No full event sourcing. We need audit logs — who routed what ticket, what the confidence score was, what draft was shown — but not the ability to replay the full decision state. Standard append-only log with a 90-day retention is sufficient.

---

## Phase 1.5 — Tensions to expect and how to respond

### Tension: PII in LLM context vs. SOC 2 data residency

> Conflict: Full ticket text (the input needed for accurate routing) contains PII. Sending it to OpenAI means PII leaves AWS, violating SOC 2. But AWS Bedrock has fewer model options and may reduce routing accuracy.

*If resolved toward compliance (stay in AWS):* Use AWS Bedrock. Model selection is restricted to Bedrock catalog (Claude, Titan). No fine-tuning on proprietary ticket data outside AWS. Routing accuracy depends on Bedrock model capability.

*If resolved toward capability (use OpenAI):* Must build a PII anonymization layer before sending to OpenAI. Adds latency (~50–100ms), adds engineering complexity, and creates a new failure mode (anonymizer misses a PII field).

**Response:** Resolved toward compliance. We use Bedrock. We'd rather constrain model choice than build a PII scrubber — a missed anonymization is worse than a slightly lower accuracy score. If Bedrock models underperform, we revisit.

---

### Tension: Rule engine first vs. LLM for all tickets

> Conflict: Always calling LLM adds 3–8s to every ticket and costs $0.03–0.05 per call. For the 60–70% of obvious cases, this is waste. But a pure rules approach has the known 15% failure rate. A hybrid (rules first, LLM for ambiguous cases) is the best quality/cost ratio but adds orchestration complexity.

*If resolved toward rules-first hybrid:* Need a confidence threshold from the rule engine. Cases below threshold go to LLM. Adds a decision layer, requires defining "ambiguous" precisely, and creates a category of tickets that can fail at two layers.

*If resolved toward LLM-for-all:* Simpler pipeline. Every ticket goes through the same path. Higher cost per ticket (~$0.04 vs. ~$0.015 for hybrid). Higher latency for simple tickets.

**Response:** Hybrid. The existing keyword rules are already built and working. We route obvious cases through rules (<50ms), send the ambiguous 30–40% to the LLM. The threshold is the confidence score from the existing classifier — if score < 0.85, the ticket goes to LLM.

---

### Tension: Synchronous draft generation vs. agent-perceived latency

> Conflict: Generating the draft response in the same synchronous path as routing adds 5–10s. The 30s SLA technically allows this, but in practice support agents find anything over 5s frustrating and will start ignoring the draft.

*If resolved toward sync:* Simpler architecture. One request, one response. Draft arrives with routing. Latency may exceed agent tolerance.

*If resolved toward async draft:* Routing completes in <2s. Draft appears 5–10s later as a push notification. More complex — requires WebSocket or polling. Avoids agent frustration.

**Response:** Accept synchronous for v1 — our SLA is 30s and we want to ship the simple version first. We'll monitor agent behavior in production. If agents stop using the draft within the first 30 days, we make it async in v1.1.

---

## Phase 1.6 — Stress test responses

**10× scale (20,000 tickets/day, 500 peak concurrent):**
The Salesforce write-back API becomes the bottleneck first — our Salesforce plan has a 100 API calls/minute rate limit. At 500 concurrent tickets, we'd saturate that in seconds. We'd need to queue CRM writes and accept that ticket assignment in Salesforce happens up to 30 seconds after the routing decision. The LLM tier scales horizontally on Bedrock — that's not the constraint.

**Budget pressure (−50%):**
Sacrifice draft response quality. Switch draft generation to Claude Haiku (cheapest, fastest). Keep Claude Sonnet for the routing/classification step where accuracy matters. This cuts per-ticket LLM cost roughly in half.

**Future requirements:**
- Multi-language support: confirmed for Q3 (within 12 months). The routing model must handle Spanish, Portuguese, and French tickets by then. Extension point needed now: language detection before routing, model selection per language.
- Proactive outreach (agent-initiated): possible but not committed. If it ships, it changes the system from reactive (incoming tickets) to proactive — a different use case, defer completely.

---

## Phase 1.7 — Meta-question responses

**Q1. Is there anything in the summary that feels wrong or incomplete?**
The 30s latency requirement is described as if it's a soft SLA. It's actually a hard one from the product team — anything slower breaks the support agent's workflow because the ticket routing and draft must appear before they click to open the ticket. I'd sharpen it to: <5s for routing decision, <15s for full response including draft.

**Q2. What's the one thing not captured that will most affect the architecture?**
The Salesforce rate limit. We have 100 API calls per minute on our current plan — that's the real binding constraint at scale, not the LLM. If we hit 500 concurrent tickets during a post-incident spike, the CRM write-back queue will back up. That's the failure mode most likely to cause an outage, and it's not in the requirements anywhere.

---

## Phase 2 — Ambiguities to expect and how to respond

### A1 — Does routing need to be explainable to the agent?

*Plugin asks: Does the routing decision need to show the support agent why it was routed (e.g., "billing: invoice keyword + enterprise account type"), or is a confidence score sufficient?*

> Explainability is required. Support agents need to know why a ticket was routed to them — it helps them prepare before reading the ticket. A bare confidence score isn't actionable. We need at minimum: top 2 routing signals displayed ("account type: enterprise" + "keyword match: invoice dispute").

### A2 — Fallback when LLM is unavailable

*Plugin asks: What happens when the LLM call fails or times out?*

> Fall back to keyword rules for all tickets — same as the current system. If rules produce a low-confidence result, route to a generic "needs-review" queue. We'd rather have a slightly higher misrouting rate than block ticket processing. Timeout threshold: 8s before fallback triggers.

### A3 — Draft response timing relative to routing

*Plugin asks: Is the draft generated before or after routing? Does it use context about the destination team?*

> After routing, using team context. The draft should be tailored: a billing draft uses different tone and references different resources than a technical draft. The team assignment is an input to the draft generation prompt. This means draft generation is sequentially dependent on routing — they can't run in parallel.
