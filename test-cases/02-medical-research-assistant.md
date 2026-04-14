# Test case 2 — Medical Literature Research Assistant

**Slug:** `medical-research-assistant`  
**Flags triggered:** none (`hybrid-decision-candidate=false`, `hitl-candidate=false`)  
**Architecture archetype:** RAG pipeline, multi-corpus retrieval, structured synthesis generation  
**Compliance:** HIPAA (BAA required with LLM vendor), licensed content access control  
**Team maturity:** none (first LLM system)  

---

## Session start

When asked for a project name, enter:
```
medical-research-assistant
```

---

## Group A — Domain and Purpose

**Q1. What problem does this system solve?**
Clinical researchers at a hospital network need to search across thousands of internal clinical study reports, FDA submission documents, and licensed journal articles. The current process — a research librarian manually searching PubMed, SharePoint, and a vendor document portal — takes 3–5 business days per request. Researchers miss relevant studies because keyword search doesn't understand clinical synonyms (e.g., "myocardial infarction" vs. "heart attack" vs. "MI"). The system should retrieve relevant literature and generate a structured synthesis report summarizing the evidence.

**Q2. Who are the end users?**
Primarily internal researchers — clinical scientists and MDs doing research. Occasionally regulatory affairs teams preparing IND submissions. All users are internal hospital staff; no external customers. The system is accessed via a web portal.

**Q3. What is the primary action?**
Retrieve + generate. Retrieves relevant documents from a multi-corpus library and generates a structured synthesis report summarizing the evidence across sources.

> **Internal flags set by plugin (do not announce):**
> - `hybrid-decision-candidate = false` — primary action is retrieve+generate, not classify/route/transact
> - `hitl-candidate = false` — the report is delivered to a researcher for independent use; no output goes directly to a downstream system or patient

---

## Group B — Scale and Performance

**Q4. What is the expected request volume?**
Low: 20–50 synthesis requests per day across the hospital network. Peak is 5–10 concurrent requests during grant application season (twice a year). No real-time requirement.

**Q5. What is the acceptable response latency?**
Async — minutes. Researchers submit a request and expect a report within 5–15 minutes. This is a research workflow, not a clinical decision-support tool. No real-time SLA.

**Q6. Is cost per request a hard constraint or a soft budget item?**
Hard constraint. Research budget is fixed. Per-request cap is $2.00. A synthesis that costs $5.00 would require budget approval. We need to stay under $2.00 consistently.

**Group B mandatory follow-up — arrival pattern:**
> Plugin asks: "Is the request volume steady throughout the day, or does it spike in response to upstream events?"

Steady with seasonal spikes. Mostly flat across the year, but grant submission windows (NIH deadlines in February and June) double or triple volume for 2–3 weeks. During those windows, 80% of requests arrive in the last 3 business days before the deadline.

---

## Group C — Data and Integrations

**Q7. What data sources does the system need to access?**
Three corpora: (1) Internal clinical study reports on SharePoint — unstructured PDFs, some scanned; (2) Licensed journal articles from a third-party vendor portal (Elsevier, Wiley) — accessed via API with per-user access control; (3) Internal FDA submission documents in a document management system (Documentum). Each corpus has different access control rules.

**Q8. Are there existing systems that must be integrated?**
The vendor journal portal has an existing API we already use for manual searches — we keep that integration. Documentum has a REST API. SharePoint uses Microsoft Graph API. Authentication for all three systems runs through the hospital's Active Directory SSO.

**Q9. What is the data sensitivity level?**
HIPAA-regulated. The internal clinical study reports may contain de-identified patient data. Even de-identified data under HIPAA requires access controls — only researchers authorized for a specific study can access that study's documents. The licensed journal articles are not PHI but are subject to licensing restrictions — we cannot expose them to unauthorized users or cache them outside the licensed environment.

**Group C priority follow-up — regulated data (HIPAA conditional):**
> Plugin asks: "Is the regulated data processed by the LLM directly, or only metadata and references?"

Full document text is sent to the LLM for synthesis. The clinical study reports contain de-identified patient data. Under HIPAA, this means the LLM vendor must be a Business Associate (BA) — a BAA must be in place before processing any clinical documents. We currently use Azure OpenAI with an active BAA. If we switch LLM vendors, a new BAA is required before processing clinical content.

---

## Group D — Constraints and Team

**Q10. Are there technology constraints?**
Python stack. Cloud: Azure (hospital network is standardized on Microsoft). LLM: Azure OpenAI with BAA in place (GPT-4o). Vector store: the hospital IT team has approved Azure AI Search — we cannot deploy self-managed vector databases (security policy). Document processing: Azure Document Intelligence for PDF OCR. Everything must be in Azure commercial cloud with FedRAMP alignment; no on-premises components.

**Q11. What is the team's familiarity with LLM/agent systems?**
None. This is the clinical informatics team's first LLM project. They have strong Python and data pipeline experience (ETL, SQL) but have never worked with embeddings, vector search, or LLM prompt engineering. No experience with RAG architectures or chunking strategies.

**Q12. Are there compliance or audit requirements?**
HIPAA BAA required with any LLM vendor that processes clinical documents. Every retrieval operation must be logged: user ID, query, document IDs retrieved, timestamp — for HIPAA audit trail. Documents must remain within the Azure commercial boundary. Audit log retention: 6 years minimum (HIPAA requirement).

---

## Group E — Failure, History, and Priorities

**Q13. Has this been attempted before?**
No. This is the first attempt to automate literature synthesis. The current process is entirely manual — handled by the research librarian.

**Q14. If this system produces a wrong or low-quality output, what is the consequence?**
Wrong synthesis could mislead a researcher and result in a flawed grant proposal or a missed citation in an IND submission. No direct patient harm (this is a research tool, not clinical decision support), but a researcher could waste months pursuing the wrong hypothesis. For regulatory submissions, a missed relevant citation could delay an IND application review.

**Q15. If you had to cut one requirement to ship four weeks earlier, which would you cut?**
Cross-corpus retrieval. Start with internal SharePoint documents only — that's the largest corpus and the one researchers struggle with most. Defer the vendor journal portal and Documentum integration to v2.

**Q16. Who outside the team decides if this is working? What will they measure?**
The Chief Research Officer. She will measure: time-to-synthesis (baseline 3–5 days → target same day), researcher satisfaction (survey score ≥ 4.0/5.0 after 90 days), and recall rate (relevant documents found by the system vs. found by the librarian in a manual parallel check — target ≥ 85%).

**Q17. Are there multi-step operations requiring rollback?**
No. Every synthesis is a read-only operation. No writes to any external system. If retrieval fails mid-pipeline, the request can simply be re-submitted. No saga or compensation logic required.

**Q18. Is there a requirement to reconstruct past state exactly?**
Yes. HIPAA requires that we can reconstruct exactly which documents were retrieved and what content was presented to the LLM for any synthesis request. If a researcher files a complaint or a breach investigation is opened, we must be able to show exactly what data was accessed, by whom, and what was sent to the LLM. This means event sourcing of the retrieval pipeline: document IDs, chunk IDs, and the exact prompt sent to the LLM must all be stored per request, with a 6-year retention period.

---

## Phase 1.5 — Tensions to expect and how to respond

### Tension: Semantic retrieval breadth vs. HIPAA access control

> Conflict: Semantic search on a shared vector index may retrieve documents the requesting researcher is not authorized to access. Embedding-based search doesn't enforce per-document access control — it returns the globally most-relevant documents.

*If resolved toward strict access control:* Apply ACL pre-filtering before the embedding search (filter by authorized study IDs first, then run semantic search within that subset). Reduces recall — a researcher will miss documents from studies they're not authorized on, even if clinically related. This is correct behavior.

*If resolved toward broad retrieval:* Run semantic search globally, then apply post-retrieval ACL filtering. Risk: document embeddings or metadata (study titles, participant counts) could leak information about documents the researcher is not entitled to see, even if the full document is filtered before the LLM.

**Response:** Strict access control. Apply ACL pre-filtering before the embedding search. Missing a document we're not authorized to see is correct behavior, not a failure. We'll accept the recall reduction in exchange for zero information leakage.

---

### Tension: Full document indexing vs. $2 per-request budget

> Conflict: Retrieving more chunks (higher recall) means sending more tokens to the LLM, which drives up cost. At GPT-4o pricing, $2.00 allows roughly 8,000 tokens of retrieved context — approximately 6–8 document chunks. Comprehensive synthesis requests on broad topics may need more.

*If resolved toward quality (more chunks):* Budget cap is exceeded on complex queries. Need to either raise the per-request cap or add query complexity classification to allocate more budget selectively.

*If resolved toward budget adherence:* Cap retrieved chunks at 8. Accept that synthesis reports for broad research questions may have lower recall.

**Response:** Accept the 8-chunk cap for v1. Add a "comprehensive mode" flag for regulatory submissions that allows up to $5/request — requires explicit opt-in by the researcher at submission time.

---

### Tension: Azure OpenAI model availability vs. capability

> Conflict: Azure OpenAI's available models lag behind the public OpenAI API by 1–2 model generations due to BAA certification lead time. We have GPT-4o under BAA, but newer reasoning models are not yet available in the Azure commercial boundary.

*If resolved toward compliance (stay on Azure):* Accept current model capability. Track Azure's model release schedule and upgrade when next-gen models become available.

*If resolved toward capability (use public API):* Must build a PII anonymization layer before sending clinical documents. Adds engineering complexity and creates a new failure mode: a missed anonymization is a HIPAA breach.

**Response:** Stay on Azure. We cannot afford the risk of a missed anonymization sending de-identified patient data to a non-BAA endpoint. If Azure model capability proves insufficient for synthesis quality, we revisit with Legal before any migration.

---

## Phase 1.6 — Stress test responses

**10× scale (200–500 requests/day):**
Azure AI Search scales horizontally — not the bottleneck. The bottleneck would be Azure OpenAI rate limits (tokens per minute per deployment). We'd need to provision multiple GPT-4o deployments or switch to PTU (provisioned throughput units) for burst capacity. The Document Intelligence OCR pipeline would also become a bottleneck for new document ingestion during corpus updates.

**Budget pressure (−50%):**
Drop the synthesis generation step. Return ranked document abstracts instead of a full LLM-generated synthesis. Retrieve + rank + per-document abstract summary (much cheaper) vs. comprehensive cross-document narrative synthesis. Researchers get a reading list with per-document summaries rather than a synthesized report.

**Future requirements:**
- Clinical trial matching: researchers want to check whether a patient profile matches criteria for ongoing trials — different privacy model, structured data matching rather than document retrieval, may require re-architecture of the retrieval layer.
- Real-time PubMed feed: automatic ingestion of new publications matching researcher interest profiles. Changes the system from request-driven to a continuous pipeline — adds significant infrastructure complexity. Planned for Q4 of next year.

---

## Phase 1.7 — Meta-question responses

**Q1. Is there anything in the summary that feels wrong or incomplete?**
The HIPAA constraint is described as requiring a BAA with the LLM vendor. That's correct but incomplete — HIPAA also governs the vector store. Azure AI Search indexes will contain clinical document embeddings and metadata. If that metadata includes study titles or participant counts, it's potentially PHI-adjacent. The BAA must cover Azure AI Search as well, not just Azure OpenAI. Our Microsoft Enterprise Agreement covers both, but Legal must explicitly confirm before go-live.

**Q2. What's the one thing not captured that will most affect the architecture?**
The per-user access control model across three different document systems. Each corpus has a different entitlement model: SharePoint uses AD groups, Documentum has its own role system, and the vendor portal has per-organization licenses. Unifying access control pre-retrieval across three different ACL systems is the hardest engineering problem in this project — and it's not in the requirements anywhere. Getting it wrong means either over-restricting (researchers miss documents they're entitled to) or under-restricting (HIPAA violation).

---

## Phase 2 — Ambiguities to expect and how to respond

### A1 — Multi-corpus retrieval strategy

*Plugin asks: "Should the system retrieve from all three corpora simultaneously and merge results, or query them sequentially with routing logic?"*

> Simultaneous retrieval with merge, ranked by relevance. We don't want researchers to miss a relevant internal study because an external journal article scored higher. Merge the ranked results, display provenance (which corpus each result came from), and apply a recency boost for internal studies — they're often more relevant to our specific patient population.

### A2 — Chunk boundaries for clinical PDFs

*Plugin asks: "Are the clinical study reports structured documents (consistent section headers like Methods, Results, Discussion) or free-form?"*

> Mixed. Older reports (pre-2015) are scanned PDFs — no OCR metadata, section headers not machine-readable. Post-2015 reports are digitally created with consistent ICH E3 structure (Introduction, Methods, Results, Conclusions). The chunking strategy must handle both: structured section-aware chunking for newer documents and fixed-size chunking for legacy scanned documents.

### A3 — Synthesis output format

*Plugin asks: "Does the synthesis report need a fixed schema (e.g., PICO format: Population, Intervention, Comparison, Outcome) or is free-form narrative acceptable?"*

> PICO format required for grant applications. Free-form acceptable for exploratory research. The request submission form should include a "purpose" field (grant / exploratory / regulatory) that determines the output template. Regulatory submissions need an additional evidence quality assessment per document (RCT vs. observational vs. case study).

### A4 — What to do when retrieved documents are insufficient

*Plugin asks: "If the system retrieves fewer than a minimum threshold of relevant documents, does it return a low-confidence synthesis or escalate?"*

> Escalate to the research librarian. If retrieval returns fewer than 3 documents above the relevance threshold, the system sends an alert to the research librarian with the original query and partial results. The librarian supplements the search and can add documents to the corpus manually. The system does not generate a synthesis from insufficient evidence — an under-evidenced synthesis report could mislead the researcher.
