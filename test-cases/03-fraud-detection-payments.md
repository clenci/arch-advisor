# Test case 3 — Real-time Fraud Detection for Payments

**Slug:** `fraud-detection-payments`  
**Flags triggered:** `hybrid-decision-candidate=true`, `hitl-candidate=true` (async review)  
**Architecture archetype:** hybrid rule+ML+LLM cascade, async HITL, saga rollback, event sourcing  
**Compliance:** PCI-DSS Level 1, full audit reconstruction  
**Team maturity:** experienced (ML/MLOps, no prior LLM experience)  

---

## Session start

When asked for a project name, enter:
```
fraud-detection-payments
```

---

## Group A — Domain and Purpose

**Q1. What problem does this system solve?**
We are a payment processor handling 50,000 transactions per day across e-commerce merchants. Our current rules-based fraud detection has a 3.2% false positive rate — legitimate transactions being blocked — which costs approximately $2M per year in lost merchant revenue and customer support. We also have a 0.8% miss rate — fraudulent transactions being approved — resulting in $4.5M per year in fraud losses and chargebacks. We need to reduce both rates simultaneously. The root cause is that the existing system can't interpret contextual signals: a $900 electronics purchase from a new device in a city the cardholder has never visited looks the same as fraud or a legitimate travel purchase, depending on context the rules can't read.

**Q2. Who are the end users?**
Two groups. Merchants submit payment authorizations via our API — these are external systems, no human involved at authorization time. Fraud analysts review flagged transactions and tune rules — these are internal users working in a case management system. The real-time authorization path is entirely system-to-system.

**Q3. What is the primary action?**
Transact — real-time fraud scoring that either approves, blocks, or escalates a payment authorization request. The decision is the output; the merchant's payment gateway executes it immediately.

> **Internal flags set by plugin (do not announce):**
> - `hybrid-decision-candidate = true` — primary action is classify+transact
> - `hitl-candidate = true` — fraud analysts review escalated cases and feed back into the model

---

## Group B — Scale and Performance

**Q4. What is the expected request volume?**
50,000 transactions per day (roughly 2,100/hour steady state). Peak: 400/minute during Black Friday and Cyber Monday. Daily peaks every lunch (12–2pm) and evening (7–9pm). Annual extreme peak during the November–December holiday period: 2–3× year-round baseline for 6 weeks.

**Q5. What is the acceptable response latency?**
Hard real-time. The payment authorization must complete within 200ms total. Our fraud scoring sub-system has an internal SLA of 80ms. If we exceed 80ms, the payment gateway times out and defaults the transaction to "approved" (fail-open). P99 must be under 80ms; P50 target is under 30ms.

**Q6. Is cost per request a hard constraint or a soft budget item?**
Hard constraint. We charge merchants $0.001 per transaction for fraud scoring (bundled in the processing fee). Our cost must stay below $0.0005 per transaction to maintain margin. LLM API calls at public pricing ($0.005–0.05 per call) are unaffordable for every transaction. The LLM path must only activate for the subset of transactions where it adds value.

**Group B mandatory follow-up — arrival pattern:**
> Plugin asks: "Is the request volume steady throughout the day, or does it spike in response to upstream events?"

Bursty with predictable patterns. Steady base with daily peaks at lunch and evening. Annual extreme peaks: Black Friday and Cyber Monday reach 10–15× normal volume, sustained for 4 days. The November–December holiday season is consistently 2–3× baseline for 6 weeks every year.

---

## Group C — Data and Integrations

**Q7. What data sources does the system need to access?**
Transaction data: tokenized card number, merchant ID, amount, location, device fingerprint, IP address, transaction time. Historical data: 90 days of prior transactions per card from our database. Merchant profile: average transaction size, historical fraud rate, industry category — our database. External real-time: card network velocity checks (Visa/MC APIs, sub-20ms). External cached: IP reputation feed (third party, updated hourly, cached locally to avoid latency).

**Q8. Are there existing systems that must be integrated?**
Card network APIs (Visa Direct, Mastercard Network Intelligence) — real-time calls, must stay under 20ms. These are on the critical path. The payment gateway receives our approve/block decision and executes it immediately — zero tolerance for malformed responses. Fraud case management system (NICE Actimize) for analyst review workflow: escalated cases are pushed to Actimize as cases, and analyst decisions return via webhook.

**Q9. What is the data sensitivity level?**
PCI-DSS Level 1. Every transaction involves card data — tokenized, but still regulated. PAN data cannot be stored post-authorization. All fraud model training and serving must occur within PCI-DSS-compliant infrastructure. Any LLM calls that involve card or transaction data must route through our Cardholder Data Environment (CDE).

**Group C priority follow-up — HITL (hitl-candidate=true):**
> Plugin asks: "Does the fraud decision require synchronous human approval, or is human review asynchronous?"

Async review — not in the real-time path. The fraud score is applied immediately: approved, blocked, or "escalated" (approved but flagged). Fraud analysts review escalated cases within 4 hours and can retroactively block the card if fraud is confirmed. The analyst's decision feeds back as a labeled training example. There is no human in the authorization path.

---

## Group D — Constraints and Team

**Q10. Are there technology constraints?**
Java + Spring Boot for the payment processing core. Fraud scoring: Python microservice with existing ML models. Cloud: GCP (all payment infrastructure is there). LLM: we want to use an LLM for gray-zone pattern interpretation, but standard LLM APIs (OpenAI, Anthropic, etc.) are outside our PCI CDE boundary — sending card data to an external API would be a PCI violation. Options: Vertex AI deployed inside our GCP CDE project (same network boundary), or a self-hosted quantized model. No public cloud LLM endpoint lives inside a merchant's CDE.

**Q11. What is the team's familiarity with LLM/agent systems?**
Experienced in ML, new to LLMs. The fraud ML team has been building models for 6 years — XGBoost, gradient boosting, custom sequence models. They have strong MLOps pipelines, feature stores, and A/B testing infrastructure. They have never used LLMs, embeddings, or agent patterns, but they understand ML operations, model governance, and production reliability for high-stakes inference.

**Q12. Are there compliance or audit requirements?**
PCI-DSS Level 1, SAQ-D, annual QSA audit. Every fraud decision must be logged with: card token, merchant ID, fraud score, features used, model version, decision, analyst override if any, and outcome (confirmed fraud or false positive). Logs retained 12 months active, 7 years archived. Any new model component must go through the change management process: 30-day staging validation window before production deployment. Emergency exceptions require QSA pre-approval.

**Group D priority follow-up — Hybrid DE (hybrid-decision-candidate=true):**
> Plugin asks: "What fraction of transactions are 'obvious' cases versus cases that genuinely require LLM reasoning?"

About 85% of transactions are clearly legitimate (existing XGBoost score < 0.2) and 5% are clearly fraudulent (score > 0.9) — the rules and XGBoost handle these well. The remaining 10% are in the gray zone (score 0.2–0.9): these are the cases where the current model either blocks legitimate purchases or approves fraud. We want the LLM to analyze only these gray-zone cases using contextual signals (purchase narrative, merchant category context, geographic patterns) that XGBoost's feature vector doesn't capture.

---

## Group E — Failure, History, and Priorities

**Q13. Has this been attempted before?**
Three prior iterations. First: pure rules (5% false positive rate — too many blocks). Second: XGBoost on transaction features (current system — 3.2% false positive, 0.8% miss rate). Third: a neural network for sequence feature modeling — it improved repeat-fraud pattern detection but added 40ms latency; deployed only for offline batch scoring, not the real-time path. The LLM is the fourth iteration, specifically targeting the gray zone that all previous approaches failed on.

**Q14. If this system produces a wrong output, what is the consequence?**
Two failure modes with different costs. False positive (legitimate transaction blocked): customer cannot pay, merchant loses the sale, customer churns from the merchant. Estimated cost: ~$200 in merchant revenue loss + $15 in customer support. False negative (fraudulent transaction approved): average $180 chargeback + $25 fraud management overhead per event. Beyond individual costs: too many fraud disputes can trigger fines or network processing suspension from Visa/MC. The consequences are asymmetric — a false negative has regulatory exposure beyond the direct financial loss.

**Q15. If you had to cut one requirement to ship four weeks earlier, which would you cut?**
LLM-based novel pattern detection (detecting new attack patterns before training data exists). The core value is reducing gray-zone false positives using existing transaction features fed to a better model. The LLM novelty detection is valuable but non-critical for v1 — the accuracy improvement on known gray-zone patterns is the primary goal.

**Q16. Who outside the team decides if this is working? What will they measure?**
The Chief Risk Officer. She measures: false positive rate (target <1.5% from current 3.2%), fraud loss rate (target <0.5% of transaction volume from current 0.8%), and authorization rate (we have a contractual obligation with Visa to maintain ≥96.8% authorization rate — this cannot drop). Measured weekly via automated dashboards. The CRO also monitors PCI-DSS compliance posture — any QSA finding is escalated to the board.

**Q17. Are there multi-step operations requiring rollback?**
Yes. A payment authorization can involve multiple partial captures (e.g., hotel pre-authorization then final charge). If a fraud signal fires mid-transaction lifecycle, we must reverse prior authorizations: authorization → partial capture → fraud confirmed → reverse partial capture → block card. This is a saga: the reversal call goes to the Visa/MC reversal API and must complete within 72 hours. If the merchant has already fulfilled the order (digital goods, instant delivery), reversal recovers the funds but not the fulfilled goods — this is a known residual risk.

**Q18. Is there a requirement to reconstruct past state exactly?**
Yes. PCI-DSS requires full auditability of every fraud decision. We must be able to reconstruct exactly: what features were input, what score was produced, what decision was made, whether an analyst overrode it, and whether the transaction turned out to be actual fraud. This is full event sourcing — immutable append-only log of every fraud scoring event with all inputs and outputs, retained for 7 years. Model version must be captured per event so we can reproduce the exact model state at decision time.

---

## Phase 1.5 — Tensions to expect and how to respond

### Tension: LLM inside CDE vs. model capability

> Conflict: Real-time fraud scoring requires the LLM to run inside the PCI CDE. No public LLM API lives inside a payment processor's CDE — the options are a Vertex AI deployment or a self-hosted quantized model. Neither matches the capability of GPT-4o or Claude Sonnet.

*If resolved toward capability (external LLM):* Build a PII tokenization proxy — transaction data is tokenized/pseudonymized before leaving the CDE, sent to external LLM, response returned. Adds 50–100ms latency. Risk: tokenization failure that sends raw card data to an external endpoint is a PCI breach.

*If resolved toward compliance (LLM inside CDE):* Deploy a quantized model (Mistral 7B or Gemma 9B) on GPU instances within the GCP CDE project. Lower raw capability, but zero compliance risk. Training and serving pipeline complexity increases.

**Response:** LLM inside CDE. A tokenization failure sending card data to an external endpoint is a PCI breach — that's an unacceptable risk. Deploy Vertex AI with a quantized model inside the CDE boundary. Benchmark against gray-zone accuracy targets — if the smaller model doesn't reach the required improvement, we revisit with a hardware investment, not a compliance compromise.

---

### Tension: 80ms SLA vs. LLM inference latency

> Conflict: Even quantized LLMs on GPU achieve 50–200ms inference latency depending on prompt length and batch configuration. The entire fraud scoring budget is 80ms — a synchronous LLM call may consume it entirely, leaving no time for feature retrieval, rule evaluation, and network overhead.

*If resolved toward quality (LLM on critical path):* Invest in optimized GPU infrastructure (A100/H100 with dedicated serving). Must achieve P99 < 50ms LLM inference. High infrastructure cost; requires capacity planning for peak load.

*If resolved toward latency (LLM on async path):* Real-time decision uses only rules + XGBoost within the 80ms budget. LLM scores the gray-zone transactions asynchronously (200–500ms after authorization). If LLM confirms fraud, trigger immediate card block and the reversal saga. Risk: fraudulent transaction is already authorized before the LLM result arrives.

**Response:** Async path for v1. LLM result arrives after authorization for gray-zone cases. Monitor what fraction of LLM-confirmed fraud was already used before the block arrives (the "racing the model" window). If that fraction exceeds 30% of LLM-confirmed fraud cases in the first 60 days, invest in GPU infrastructure and move the LLM to the critical path in v2.

---

### Tension: PCI change management (30-day window) vs. fraud pattern evolution

> Conflict: PCI-DSS change management requires 30-day staging validation before any production model update. But fraud attack patterns can evolve in hours — a new card-testing attack pattern detected today needs a response in days, not weeks.

*If resolved toward full compliance (30-day window for everything):* New attack patterns are exploitable for up to 30 days. Compensate with emergency rule-based blocks (not model changes) that can be deployed faster. Model updates still take 30 days.

*If resolved toward speed (emergency patch process):* Define a documented "emergency model patch" process with QSA pre-approval for high-severity patterns. Allows 72-hour deployment window for attacks affecting >100 cards/hour. Requires additional documentation and QSA sign-off per activation.

**Response:** Emergency patch process. Work with the QSA to define a documented exception process for high-severity fraud pattern updates. Standard model changes still require the 30-day window. Emergency patches (velocity-based attacks affecting >100 cards/hour) get a 72-hour window with QSA pre-approval. This is already standard practice in the industry — our QSA has approved similar processes for other processors.

---

## Phase 1.6 — Stress test responses

**10× scale (500,000 transactions/day, 4,000/minute peak):**
The XGBoost inference layer scales horizontally — not the bottleneck. At 10× volume, the Visa Direct real-time API becomes the constraint: our current agreement allows 500 requests/second. At 4,000/minute (67/sec) we are well within limits today, but 10× puts us at ~670/sec — over the contracted limit. We'd need to renegotiate the Visa API agreement and add circuit breakers that skip the real-time Visa call and fall back to cached velocity data when the rate limit is approached. The async LLM path on Vertex AI scales fine.

**Budget pressure (−50%):**
Drop the LLM component entirely. Fall back to XGBoost-only scoring with tuned threshold optimization. Accept that gray-zone accuracy doesn't improve in v1. Redirect the budget toward better feature engineering: additional velocity features, improved IP geolocation enrichment, and expanded device fingerprint signals — these have known ROI from prior model iterations.

**Future requirements:**
- Account takeover (ATO) detection: detecting when a fraudster has authenticated as a legitimate cardholder. Completely different signal patterns — behavioral biometrics, device fingerprinting, session sequence analysis. Different data model and different threat model. Plan separately; don't mix with payment fraud scoring.
- Cross-merchant fraud network detection: identifying coordinated attacks across multiple merchants by the same actor. Requires a graph database for card-merchant relationship analysis and graph ML. Major architecture addition, tentatively scoped for Q2 next year.

---

## Phase 1.7 — Meta-question responses

**Q1. Is there anything in the summary that feels wrong or incomplete?**
The async LLM path is described as improving fraud detection. But it creates a known attack vector: a fraudster who knows about the 200–500ms LLM scoring window can deliberately structure transactions to complete (and goods to be delivered) within that window before the block arrives. This is called "racing the model" and is a documented attack pattern against async fraud systems. The retroactive block and reversal saga is the mitigation — but the saga has a failure mode for digital goods: if the merchant has already fulfilled the order, reversal recovers funds but not the goods. This asymmetry between digital and physical merchants needs to be captured as an explicit risk in the architecture, not just in the tensions.

**Q2. What's the one thing not captured that will most affect the architecture?**
The feedback loop between analyst decisions and model retraining. Fraud analysts review escalated cases and make override decisions — confirmed fraud or false positive. Those analyst decisions are the gold-standard labeled training data for retraining the XGBoost model. If the pipeline from analyst decision → labeled training example → model retraining is broken or slow, the model never improves on the case types it gets wrong. This feedback loop is the highest-value engineering investment after the initial system — it's what converts the system from a point-in-time model into a continuously improving one. It's entirely absent from the requirements.

---

## Phase 2 — Ambiguities to expect and how to respond

### A1 — Gray zone threshold configuration

*Plugin asks: "Is the gray zone (0.2–0.9 on the XGBoost score) a global fixed threshold or does it vary per merchant?"*

> Per-merchant configurable. A luxury goods merchant with $800 average transaction size has a different risk tolerance than a $15 fast-food merchant. We need per-merchant risk thresholds stored in the merchant configuration: the gray zone lower bound (when to invoke the LLM) and the upper bound (auto-block regardless) both need merchant-level overrides. The global defaults (0.2 / 0.9) are the starting point; merchants can request threshold adjustments through a risk review process.

### A2 — Analyst workflow integration

*Plugin asks: "Do fraud analysts interact with escalated cases through a system your team builds, or an existing tool?"*

> Existing system — NICE Actimize. Escalated cases are pushed to Actimize as case records via their inbound case creation API. Analysts work entirely in Actimize. Their decisions (confirmed fraud / false positive) return to us via an Actimize outbound webhook. We do not build any analyst UI — we integrate with Actimize's inbound and outbound APIs. The webhook payload must include: case ID, card token, merchant ID, analyst decision, analyst ID, and timestamp for the model retraining pipeline.

### A3 — LLM output format

*Plugin asks: "What does the LLM produce — a fraud score, a classification, a natural language explanation, or some combination?"*

> Two outputs, not a score. (1) A 2–3 sentence plain-English explanation of why this transaction is suspicious, for the analyst's case review screen: "Unusual: card used in 3 countries within 90 minutes; merchant category (electronics) inconsistent with card's prior 90-day history (groceries, gas)." (2) A structured set of fraud signal tags from a predefined taxonomy: CARD_NOT_PRESENT, VELOCITY_ANOMALY, GEOGRAPHIC_ANOMALY, MERCHANT_CATEGORY_MISMATCH, etc. — for the case record in Actimize and as features in the model retraining pipeline. The LLM does not produce a numeric score — that remains XGBoost's responsibility.

### A4 — Reversal saga failure handling

*Plugin asks: "What is the timeout for the reversal saga, and what happens if the Visa reversal API call fails?"*

> 72-hour window per Visa/MC network rules. If the reversal API call fails (Visa API down, merchant reversal rejected), the system logs the failed attempt and triggers an alert to the chargeback team within 15 minutes. The chargeback team's SLA is 4 hours from fraud confirmation to manual escalation action. After 72 hours without a successful reversal, the system automatically escalates to the chargeback queue regardless of prior attempts — the chargeback team handles it as a standard dispute. All saga events (reversal attempts, failures, escalations) are written to the immutable event log for PCI audit.
