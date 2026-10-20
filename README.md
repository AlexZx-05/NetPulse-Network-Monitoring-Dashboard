# BRAHMO Clinical AI — Final Architecture and Doctor-Readiness Plan

**Name:** Deepak Sharma  
**Submission deadline (per latest email):** 20 October 2026  
**Assessment opened:** 18 October 2026, [enter the actual time and time zone]  
**Submitted:** [enter the actual date, time and time zone when you submit]

> This document describes the system I recommend building. It does not claim that the system is clinically approved or ready for doctors. The assessment pack reports that some early stages were built or tested, but does not include the evidence, source permissions, or clinical and legal approvals needed to confirm readiness. I treat those items as unverified.

## S1 · Final Architecture

### System design

```text
 TRUST BOUNDARY A — Clinic device / doctor
 ┌───────────────────────────────────────────────────────────────┐
 │ Doctor app: Scribe draft + consented patient-context version  │
 │ Review / clarify / edit / approve / reject; no auto-finalize   │
 └──────────────────────────────┬────────────────────────────────┘
                                │ TLS; authenticated actor, clinic,
                                │ purpose, contract version, request ID
 TRUST BOUNDARY B — BRAHMO service
 ┌──────────────────────────────▼────────────────────────────────┐
 │ API authorization + tenant scope + minimum-data policy         │
 │                  Orchestrator (no clinical decision authority) │
 │       ┌──────────────────────┴─────────────────────┐           │
 │       │                                            │           │
 │       ▼                                            ▼           │
 │ Drug identity graph / dated events       Evidence retrieval    │
 │ exact/reviewed mapping only              lexical + local vector│
 │ FDC ingredient expansion                 scope/applicability    │
 │       │                                  + citation validation │
 │       ▼                                            │           │
 │ Pure deterministic rules                           │           │
 │ no model invocation or network call                │           │
 │       └──────────────────────┬─────────────────────┘           │
 │                              ▼                                 │
 │ Typed findings + 8-state checks + claim/source provenance      │
 │                              │                                 │
 │ LLM boundary (optional, approved provider): evidence-only      │
 │ composition; no safety, identity, regulatory or dose decisions │
 └──────────────────────────────┬────────────────────────────────┘
                                │ result + versions + limitations
 TRUST BOUNDARY C — Approved doctor-facing result
 ┌──────────────────────────────▼────────────────────────────────┐
 │ Doctor inspects citations/checks; resolves ambiguity; approves │
 │ then saves/exports to the clinic record; audit/correction event│
 └───────────────────────────────────────────────────────────────┘

 TRUST BOUNDARY D — Content control plane (separate permissions)
 Source + license → immutable source copy/hash → extraction/QC
 → qualified review → tests → signed release/index manifest
 → serve / expire / withdraw / rollback
```

The system has separate areas for patient information, each clinic’s local rules, approved clinical sources, medicine and regulatory records, and any AI provider. A clinic’s own information must not change national medicine or regulatory records. One clinic must never see another clinic’s information. Documents and transcripts are untrusted data; they must never be treated as instructions to the AI.

### How a doctor uses it

1. The doctor signs in, selects the patient and consultation, and enters a question or starts from a Scribe prescription draft.
2. The app sends the doctor and clinic IDs, the reason for the request, and only the patient information needed for that request. It sends a structured prescription, not the whole transcript by default.
3. Each Scribe medicine entry includes the words captured, any possible brand or medicine code, strength and unit, form, route, frequency, duration, and where it came from. Missing details stay marked as missing. The system does not fill them in.
4. The patient-context record has a version and shows where each detail came from and when it was recorded. It may contain clinician-entered age, pregnancy or breastfeeding status, allergies, current medicines, and relevant health details. Missing or conflicting details stay visible; the system does not assume they are normal.
5. The medicine service uses an exact code or a reviewed alias to identify a product. If it cannot be sure, it asks the doctor to check the match. It does not use an uncertain match for a safety check. A verified combination product is split into its ingredients before checks run.
6. The question service searches only sources that have been approved for use and match the question’s topic, patient group, language and date. It shows citations or says it cannot confirm the answer.
7. The safety service runs fixed rules on verified medicine ingredients and available patient details. If important details or data are missing, it shows the applicable “unknown” status and explains why.
8. The doctor sees the result, its limits and its evidence, and can clarify, correct, edit, accept or reject it. Conflicting sources are shown separately; the system does not invent a compromise.
9. Nothing is prescribed, sent to a patient or finalized automatically. The doctor must confirm before anything is saved or exported. The system records which versions of the data and rules were used and what the doctor did.

### Contracts with Scribe and patient context

I do not assume access to either upstream codebase. These are proposed versioned JSON API contracts, not claims about existing interfaces. Reject unknown major versions, invalid units, duplicate IDs, untrusted tenant IDs, malformed timestamps and missing required provenance; return a typed integration error rather than silently dropping fields.

| Contract | Required fields and behavior |
|---|---|
| `scribe-prescription/v1` | `request_id`, `clinic_id`, `consultation_id`, `actor_id`, `purpose`, `captured_at`, `source_language`, `prescription[]`. Each line carries `line_id`, `verbatim_text`, optional `candidate_product_id`, `strength_value/unit`, `form`, `route`, `frequency_text`, `duration_text`, `quantity`, and `source_span` (transcript/document ID plus offsets or timestamp). Every normalized field carries `value`, `unit` where applicable, `confidence/source`, and `review_status`. Unknown values are null with an explicit reason; never convert a missing value to a clinical default. |
| `patient-context/v1` | `patient_ref` (pseudonymous), `clinic_id`, `context_version`, `observed_at`, `valid_until` if supplied, and a list of attributes. Each attribute carries its value, unit/code system, source, observation time, author, verification state and sensitivity label. The request identifies which attributes are needed and the permitted purpose. Conflicting observations remain separate and visible. |
| Response and correction | Return `request_id`, contract version, data-as-of time, one typed result per check/claim, source/rule/model/index versions and explicit limitations. Corrections append a new version with actor, reason and prior-value reference; they do not rewrite the original event or globally alter a canonical mapping. |

The receiving service derives clinic scope from the authenticated session and verifies it against the request; it never trusts a client-supplied `clinic_id` alone. Send structured fields and referenced transcript spans only when necessary, not a full transcript by default. A correction to patient context is separate from a proposed drug-master correction and is routed to the appropriate authorized reviewer.

### Two example paths

- **Clinical reference question:** A doctor asks what an approved national workflow says about a named topic. The system searches approved sources, checks that the source applies, and gives a short answer with a page or section citation. It labels local clinic guidance as local. If the source does not answer the question or relevant sources disagree, it says so and shows the evidence or abstains. It does not diagnose, calculate a patient-specific dose, triage, or create a treatment plan.
- **Medication review:** A prescription has a brand name that could refer to more than one product, or a combination medicine. The system shows the possible match and asks the doctor to resolve uncertainty. For a verified product it checks the ingredients against the other medicines and approved rules. If a frequency such as “SOS” prevents a complete exposure check, it says the check is partial. It does not guess a dose or suggest a replacement.

**Illustrative doctor-facing outputs (fictional identifiers/text only):**

```text
Reference | "What does the source say about fictional condition X?"
Answer    | "The fictional workflow says to consider action A, subject to exception B."
Evidence  | DEMO-1 v1.0, p. 4, 'Example', para. 2; linked table p. 3, row 3
Scope     | Fictional adult outpatient example; applicability reviewed for this query
Limits    | This is a source summary, not an individualized plan. Open the cited page.

Medicine review | Captured name: "DEMO-COMBINATION" (fictional)
Identity         | UNVERIFIED_INPUT — two candidate products; no ingredient check run
Doctor action    | Select the exact product or correct the captured name
Exposure check   | PARTIAL_COVERAGE — frequency "SOS" cannot be quantified by this system
Save/export      | Disabled until the doctor resolves the identity and reviews the draft
```

The examples demonstrate result shape only. They are not evidence, prescribing advice, or claims about any real medicine or guideline.

## S2 · Decision Register

| Area | Current position or gap → my choice | Why; strongest alternative I reject | Cost I accept | How I will validate it |
|---|---|---|---|---|
| D1. Sources | The pack names Indian sources but does not provide a full rights record. I will use approved ICMR and national-programme material for their stated topics, official regulatory notices for legal status, and clinic protocols only inside that clinic. | No single source is right for every question. I reject a universal rule that one source always overrides all others. | Some questions will have no approved answer until permissions and review are complete. | Keep a source and rights register; have clinicians check scope and counsel check reuse rights; test conflicts and withdrawals. |
| D2. Chunking | The pack does not specify how to split documents. I will split by headings and complete clinical points, preserving the surrounding heading, table labels, footnotes, units and exceptions. | Meaning often depends on nearby text. I reject fixed-size text splits as the only method because they can separate a number from its unit or exception. | More work to extract and review documents. | Compare citations and extracted tables with the original pages; test exceptions and cross-page references. |
| D3. Retrieval | The pack proposes hybrid search but leaves production details open. I will combine exact-word search with meaning-based search, then check source, topic, date and patient-group fit before answering. | Exact names and units need exact search; different wording needs meaning-based search. I reject vector-only search and AI deciding whether evidence is enough. | More processing time and more honest refusals when evidence is weak. | Test paraphrases, irrelevant questions, citations and applicability on held-out cases. |
| D4. Embeddings and index | The model and index are not chosen in the pack. I recommend a pinned local embedding model with exact-word search kept as a separate path. Each published index will have a version and hash. | Local processing avoids sending source text and questions to an embedding service by default. I reject a hosted embedding service as the starting choice because it adds a data processor and transfer risk. | Local compute, model maintenance and uncertain regional-language performance. | Check model permissions, version hashes, offline behavior and language-specific test results. |
| D5. Medicine data | The pack describes a medicine master and unverified combination candidates. I recommend a licensed, traceable medicine source plus reviewed local brand names. Uncertain matches stay unresolved. | A pharmacy list or similar spelling does not prove a medicine’s ingredients. I reject scraping commercial data or treating fuzzy matches as truth. | Licensing cost/dependency and slower addition of brands. | An independent reviewer checks a held-out product set. There must be zero silent wrong matches; report coverage and unresolved matches separately. |
| D6. Safety checks | The pack requires fixed rules and eight result states. I will keep checks deterministic, versioned and separate from any AI model. | This makes missing information visible. I reject AI-generated safety decisions and a simple safe/unsafe flag. | The system will sometimes report incomplete coverage and interrupt the doctor. | Test every result state and missing-data case; a qualified clinician approves each live safety rule. |
| D7. AI model/provider | The pack proposes a frontier model but leaves the provider and controls open. I will keep model use disabled until approved. If enabled, it may only write a concise response from checked evidence; it cannot supply facts, identify medicines or run safety checks. | This can make answers easier to read without making the model the source of truth. I reject unrestricted AI answers and custom medical training for now. | Without a model the answer feature may be narrower; with one there is provider and latency dependence. | Review provider terms and data handling; test each model and prompt version for unsupported claims and attacks before release. |
| D8. Data location | Hosting and residency are open. I recommend keeping patient and clinic data in an India-hosted service unless counsel approves another arrangement. | This reduces transfer uncertainty but does not itself prove legal compliance. I reject a global default location. | Fewer hosting choices and more constrained disaster recovery. | Document data flows, provider locations and contracts; obtain counsel approval and test backup recovery. |
| D9. Clinics and tenants | The pack mentions clinic overlays but not all isolation controls. I will check the clinic ID and user permission in the API, database, search, cache, exports and background jobs. | A screen-only filter is not enough. I reject separate systems for every clinic as the default because they are harder to operate. | More complex access controls and security testing. | Run cross-clinic access tests on every release and have an independent security reviewer check the design. |
| D10. Audit | The pack requires replay but does not define a complete audit record. I will keep an append-only record of the inputs, source/rule/model versions, results and doctor action, subject to approved privacy and retention limits. | This lets us investigate what the doctor saw. I reject editable “latest state” logs and keeping complete transcripts forever. | Storage and deletion rules make exact replay harder in some cases. | Test replay, access restrictions, retention and deletion; document when lawful deletion prevents full replay. |
| D11. Source precedence | The pack suggests a source ladder. I will decide precedence by the question’s legal or clinical topic, source authority, population and effective date. Show real disagreements side by side. | A legal notice, national programme and clinic protocol have different purposes. I reject one universal ranking. | More cases will need review or abstention. | Have qualified reviewers approve precedence examples and test superseded and conflicting documents. |
| D12. Offline use | Offline behavior is not specified. I will allow only a clearly marked, read-only reference bundle that is signed, approved and not expired. | Old medicine and regulatory data may be unsafe. I reject a silent fallback that looks current. | Some functions will stop during an outage. | Test loss of network, expiry, revocation and recovery; confirm the screen clearly shows what is unavailable. |

## S3 · Grounding & Sources Plan

### Sources and permissions

Being able to view a document online does not automatically give permission to store it, extract its text, index it, display excerpts or use it to train a model. I would block each source from production until its owner, version, terms and permitted uses are recorded and approved. I propose no model training on patient records or source documents.

| Source and role | Coverage, authority and version/date policy | Access and rights status; permitted use in this design |
|---|---|---|
| ICMR Standard Treatment Workflows, [ICMR STW portal](https://stw.icmr.org.in/) | Indian workflow guidance for the specific condition, setting and population named in each workflow. Record the document title, edition, publisher date as printed, retrieval date and supersession state. It is not a comprehensive formulary. | Portal access is not proof of commercial reuse rights. No source license is supplied in this assessment. Store/extract/index/display only after rights review; excerpts remain disabled until approved. No training use. |
| MoHFW and named national programme issuers, including [NTEP](https://tbcindia.mohfw.gov.in/), immunization, vector-borne disease and maternal-health programme documents | The currently designated guideline/circular for that programme’s exact topic and population. The issuing programme’s scope is authoritative for its programme, not a universal precedence over all clinical sources. Keep issue number, date, version and effective/superseded status. | Each document has separate rights and update status; no blanket license is assumed. Verify reuse terms for storage, extraction, indexing and excerpt display; no model training. |
| National Formulary of India 2021, Indian Pharmacopoeia Commission (IPC) | Generic medicine/formulary reference, not definitive Indian brand-to-product identity and not a substitute for current statutory notices. Preserve edition and monograph location. | Obtain the IPC publication and applicable reuse terms; no commercial indexing rights are established here. |
| CDSCO notices and Gazette of India publications, [CDSCO](https://cdsco.gov.in/) and [eGazette](https://egazette.gov.in/) | Primary regulatory event evidence: exact notification/order number, issuing authority, publication/effective dates, affected ingredient/product/form/strength, territory, exceptions, amendments, stays and reversals. A stock record is never evidence of lawful sale. | Use the actual instrument and current legal status. Government publication does not by itself grant every database or excerpt right. Legal counsel must approve storage, event extraction, indexing and display; no training use. |
| Drugs and Cosmetics Act, 1940 and Drugs Rules, 1945 (including product-relevant Schedules H, H1 and X), [India Code](https://www.indiacode.nic.in/) and CDSCO | Statutory/schedule context for a qualified reviewer. Use a dated consolidated text plus later Gazette instruments; do not infer a brand restriction from a schedule name alone. | Verify the currently operative consolidation and applicable licensing/redistribution terms. Rule interpretation and each product mapping require regulatory-pharmacist and legal review. |
| National List of Essential Medicines 2022, MoHFW | List membership for the listed medicine and stated formulation; not proof of brand equivalence, current controlled price, or local availability. Keep list edition and any later revision. | Check official reuse/database terms before reproducing or indexing; use no inferred brand matching. |
| NPPA, [price notifications and orders](https://nppaindia.nic.in/) | Statutory price ceiling/order only for the exact product description, strength and pack in the applicable order, with its effective date and amendments. | No price should be shown until the order has been matched and display/reuse approved. It does not provide current clinic stock. |
| PMBI, [Jan Aushadhi catalogue](https://janaushadhi.gov.in/) | PMBI-listed catalogue item and pack, not evidence of local stock, therapeutic interchangeability or suitability for an individual patient. | Treat as a separate catalogue feed; confirm current access, reuse and update terms before copying or indexing. |
| MIMS India (candidate commercial medicine-reference source; no contract or coverage confirmation supplied) | Candidate source for Indian brand/product monographs and, only if separately licensed and documented, interaction information. Vendor content is not legal/regulatory truth; reconcile exact product, ingredient, strength, form and date against primary or independently reviewed evidence. | Obtain written terms covering India coverage, product-level provenance, retention, extraction, search indexing, display, audit, updates and derived data. Until contracted and evaluated, this is a procurement candidate, not an enabled dependency. No training use. |
| Clinic/hospital formulary, protocol or antibiogram | Local, organization-scoped practice only. Require owner, approval, applicability, version/date, expiry, and source lineage. It cannot redefine national law or canonical product ingredients. | Written tenant authorization for ingestion and display; tenant isolation; no use in another tenant’s answers or global model/index. |
| WHO or other recognized international guidance | Background only when Indian sources do not resolve a question; label origin and date and require a clinician to judge applicability. It does not override applicable Indian rules. | Check the specific publication’s terms and local applicability. No general permission or training use is assumed. |

**Rights gate:** for every individual source, the register separately records permission for (1) access, (2) retaining a source copy, (3) text/OCR extraction, (4) search indexing and embeddings, (5) displaying quotations or derived excerpts, (6) retaining audit evidence, and (7) any training or fine-tuning. The default for training is **prohibited**. A missing or ambiguous right blocks that operation; a lawful citation link does not imply permission to retain or reproduce the source. No source license, MIMS contract, or legal approval is represented as already obtained.

### How information becomes usable

1. **Register it.** Record owner, location, file hash, version, dates, language, topic, scope and rights for storage, extraction, search, display and training. Unknown rights mean the document is held back.
2. **Keep the original.** Save an unchanged copy where permitted. Record the software used to extract text and connect extracted text to page numbers.
3. **Check extraction.** Compare text, tables, units, footnotes and symbols with the original. Missing pages, poor OCR or broken tables block publication.
4. **Review meaning.** A curator checks the extraction. A qualified clinician checks clinical meaning and scope. Safety rules and high-risk tables receive a second independent review.
5. **Split into useful pieces.** Split at headings and complete clinical points, not just after a fixed number of words. Keep headings, population, setting, units, exceptions, table headers, footnotes and cross-references with each piece.
6. **Test and publish.** Only approved, current pieces can be searched. Publish a new version as one change, with its source hashes, review approvals, search model, index version and test results. Keep the previous approved version available for rollback if still valid.
7. **Update or withdraw.** Check authorized sources for changes. Keep older versions for history, but do not use a superseded version for a current answer. Remove withdrawn or expired material from current search.

**Fictional example of a chunk and citation—not medical advice and not a clinical recommendation:**

```text
Source ID: DEMO-1; fictional version: 1.0; issued: 2026-01-01
Retrieved: 2026-10-20; page 4; heading: "Example"; paragraph 2
Scope metadata: fictional adult outpatient example; pregnancy status excluded
Claim text: "For fictional condition X, consider action A unless exception B."
Linked context: table title + row 3 on page 3; footnote defining exception B
Citation rendered: DEMO-1 v1.0, p. 4, "Example", para. 2; linked table p. 3, row 3
```

Search relevance is checked separately from source applicability and citation entailment. First, retrieval tests whether the passage is about the query; a separate deterministic/curator gate checks authority, jurisdiction, date, patient group, setting and formulation. Finally, a reviewer checks that the exact cited page/table supports the claim with units, qualifiers and exceptions. A relevant result can be inapplicable, and an in-scope citation can still fail to support the generated wording.

### Conflicts and missing permissions

For legal status, use the relevant official legal instrument and later events. For clinical questions, use a source that covers the topic and patient group. A clinic protocol applies only within that clinic. A newer document replaces an older one only when the issuing body or a verified record says it does. Show concurrent disagreements separately; do not let the AI decide which one is correct.

If a source’s permission is unclear, do not index or display it. This may mean the product cannot answer certain questions, identify some brands, show prices or run some safety checks. State that limitation instead of filling it with internet scraping or AI memory.

## S4 · Rules of Behavior for India

These are product rules, not a legal opinion. Counsel must check the current law, amendments, commencement dates and the proposed deployment before any live use. If that review is missing, do not enable the affected feature.

**Legal-source status for this plan:** the instruments below are the primary materials to review, not a claim that current commencement, amendments, classification or approvals have been independently certified. The assessment pack contains no counsel opinion. Before release, Indian privacy/medical-device/drug-regulatory counsel must confirm the Gazette text and effective dates **as of the release date**, the actual deployment states, and the exact product intended use. A link to a source portal is not evidence that the relevant notice has been checked.

| Situation | What the product must do | Basis and current uncertainty | How to enforce and who must approve |
|---|---|---|---|
| A clinical claim is shown | Cite an approved, versioned source or say it cannot be confirmed. Never invent a dose, safety claim or legal status. | This is a fixed assessment requirement. | Require a citation for each important claim; clinical reviewer approves the answer tests. |
| Patient information is processed | Use only the minimum attributes needed for the declared purpose; give the required notice; capture/record the lawful basis and any consent required; enforce access, retention, erasure, breach escalation and processor controls. Do not infer guardian authority for a child. | Primary instrument: Digital Personal Data Protection Act, 2023 (Act 22 of 2023), including §1(2) (commencement by notification), §§4–9 (processing, notice/consent and obligations), §§11–14 (data-principal rights), §§16–17 (transfers/exemptions); [India Code Act record](https://www.indiacode.nic.in/handle/123456789/20062), [MeitY data-protection framework](https://www.meity.gov.in/data-protection-framework), and [eGazette](https://egazette.gov.in/). The precise commencement notifications, Rules, transition/overlap with the IT Act/SPDI Rules and requirements applicable on the release date are **unverified here**. | No live patient data until privacy counsel produces a dated applicability matrix covering controller/data-fiduciary roles, notice, consent or other basis, children/guardian flow, processor terms, transfers, retention/erasure and breach duties. Enforce the approved purpose in API policy and data lifecycle. |
| Software may affect treatment decisions | Do not assume doctor supervision, intended-use wording or a disclaimer removes medical-device obligations. Do not launch a treatment recommendation feature until its classification and required pathway are decided. | Primary source: Medical Devices Rules, 2017, G.S.R. 78(E), 31 January 2017, effective 1 January 2018, including Rule 3(zb) definition and applicable classification/licensing provisions; amendments and current CDSCO guidance must be checked at [CDSCO Medical Devices](https://cdsco.gov.in/opencms/opencms/en/Medical-Device-Diagnostics/Medical-Device-Diagnostics/) and [eGazette](https://egazette.gov.in/). Whether this exact doctor-facing reference/checking product is a regulated medical device and its class/pathway are **not determined**. | Obtain a signed, feature-by-feature classification/intended-purpose memo from Indian regulatory counsel and, if needed, CDSCO clarification. Keep only features expressly cleared by that memo enabled; preserve evidence of any required registration/licence/quality system. |
| A remote consultation is involved | Do not let the software counsel a patient, issue a prescription or impersonate a registered medical practitioner. If integrated into telemedicine, keep the registered practitioner in control and apply the applicable consultation/prescription safeguards. | Primary guidance: MoHFW/NMC Telemedicine Practice Guidelines, 25 March 2020, together with the operative NMC Act/rules and later Gazette directions; [NMC](https://www.nmc.org.in/) and [MoHFW](https://mohfw.gov.in/). Applicability to a doctor-only reference tool versus a telemedicine platform, exact current guideline status and amendments require counsel verification. | Patient-facing advice and auto-prescribing remain excluded. Before a telemedicine integration, require a legal workflow map, RMP eligibility checks and approved UX/API boundaries. |
| A doctor uses the system | Present the product as an evidence and checking aid, not an order or substitute for professional judgment. Record clinician review and approval; do not claim that product terms transfer the clinician’s or manufacturer’s statutory responsibilities. | National Medical Commission Act, 2019 and the professional-conduct regulations/directions in force on the release date; [NMC rules and notifications](https://www.nmc.org.in/). The operative version and any abeyance/replacement notices must be verified from the official Gazette; this plan does not claim a current conduct-code determination. | Require verified practitioner identity/role where applicable, explicit approval before save/export, and audit. Counsel and clinical governance approve instructions, workflow and responsibility language. |
| Medicine restriction or schedule is shown | Use the dated primary instrument, exact scope and effective period. Model each notification, stay, reversal and supersession as an event; do not infer legality from a catalogue or stock listing. | Drugs and Cosmetics Act, 1940 and Drugs Rules, 1945 (including Schedules H, H1 and X), plus each CDSCO/Central or State licensing authority notification and operative court order; [India Code](https://www.indiacode.nic.in/), [CDSCO](https://cdsco.gov.in/) and [eGazette](https://egazette.gov.in/). A consolidated rulebook may lag a later notice; product-specific scope and current status are **unverified until checked**. | Ingestion requires source event, notification ID, publication/effective/expiry dates, jurisdiction, affected ingredient/product/form/strength and reviewer. A regulatory pharmacist verifies mapping; counsel resolves ambiguous scope. Otherwise return `SOURCE_CONFLICT` or `UNVERIFIED_INPUT`, not a legal conclusion. |
| Price or availability is shown | Show the exact product/pack, source and “as of” date. Keep statutory price, catalogue listing and local stock as separate facts; do not imply an equivalent medicine or recommend a substitute. | DPCO 2013 and current amendments/orders; NPPA price notifications; NLEM 2022 and later notices; PMBI catalogue. Primary source portals: [NPPA](https://nppaindia.nic.in/), [MoHFW](https://main.mohfw.gov.in/) and [PMBI](https://janaushadhi.gov.in/). Current order and exact product coverage must be checked; NLEM inclusion does not prove a brand price, and catalogue presence does not prove local stock. | Exact product/strength/pack match and current authorized feed are prerequisites. Data owner and counsel approve use and display; otherwise suppress the price/availability feature. |
| A source is copied, indexed or quoted | Use only the operations expressly permitted for the source; cite and link without retaining or reproducing unlicensed content where needed. Never train on sources or patient data without separate, explicit rights and approval. | Copyright Act, 1957 and source-specific government, publisher or vendor terms. Public accessibility is not a blanket commercial license. No rights opinion or source contract is supplied; specific exceptions and government-work terms require counsel review. | Rights register gates each data operation independently (S3). Block ingestion, embeddings and excerpts until legal/source-owner approval is recorded. |
| A check lacks information or a service | Show the correct unknown or unavailable state. Never display missing data as “safe.” | Fixed eight-state requirement. | Enforce typed results in the API and test all states in the user interface. QA and clinical reviewers approve. |
| A translation changes a clinical meaning | Show only a clinically checked translation. Keep the original text and unit available. | Product safety policy; patient-facing generated advice is excluded. | Mark each translation’s language and review status. A qualified bilingual clinician approves it. |
| A document or transcript contains instructions to the AI | Treat it as data only. It cannot change access, safety rules or system behavior. | Fixed assessment requirement and security policy. | Isolate retrieved text and test malicious instructions. Security reviewer approves. |

Do not enable live patient data, unlicensed source ingestion, unapproved AI-provider processing, patient-facing advice, automatic prescribing, patient-specific dose calculations, or unreviewed safety rules until the applicable legal, clinical and security approvals are documented.

## S5 · Correctness & Safety Design

### What is fixed and what AI may do

Medicine matching, ingredient breakdown, regulatory status and medication checks use fixed rules and versioned data. No AI model is called while a safety check is running. If an AI model is later approved, it may help write a short answer from evidence already selected by the system. It cannot make up facts, identify a medicine, calculate a patient-specific dose, diagnose, rank diagnoses, triage, create a treatment plan or advise a patient.

Every check returns exactly one of these states:

`HIT` · `CHECKED_NO_HIT` · `PARTIAL_COVERAGE` · `UNVERIFIED_INPUT` · `NOT_CHECKED` · `DATA_EXPIRED` · `SOURCE_CONFLICT` · `SERVICE_UNAVAILABLE`

Define a check as one named rule applied to one explicit subject/scope (for example, one ingredient or one regulatory event against one product). Return one and only one state for that check, plus `check_id`, subject IDs, evaluated-at time, rule/data versions, inputs used, missing fields, source evidence, explanation and clinician-facing next step. Do not collapse all findings into a single green/red prescription status: a confirmed `HIT` on one ingredient can coexist with `PARTIAL_COVERAGE` on another check. `CHECKED_NO_HIT` means only that the named check ran with adequate current information and found no issue; it does not mean the prescription is safe overall.

State semantics are explicit: a known applicable positive finding is `HIT`; a complete, current check with no finding is `CHECKED_NO_HIT`; an incomplete but partly executed check is `PARTIAL_COVERAGE`; an unresolved product/patient input is `UNVERIFIED_INPUT`; a rule intentionally not run is `NOT_CHECKED`; a required snapshot exceeds its approved freshness limit is `DATA_EXPIRED`; authoritative evidence cannot be reconciled is `SOURCE_CONFLICT`; and an essential dependency failed is `SERVICE_UNAVAILABLE`. No mapping, timeout, empty response or omitted field may be converted to `CHECKED_NO_HIT`.

### Medicine identity and patient details

Keep brand, product, ingredient, strength, unit, form, route, pack and country separate. A combination medicine has a separate record for each ingredient and strength. Similar spelling or transliteration may help find candidates, but cannot prove a match. If identity is uncertain, ask the doctor to review it; do not use it in safety checks.

Record where each patient detail came from and when it was observed. Show contradictions such as conflicting allergy records. Do not infer age, pregnancy, breastfeeding, kidney or liver status from a transcript. If frequency or duration is missing or unclear—for example, “SOS”—show cumulative exposure as partial rather than guessing.

A doctor’s correction records the old value, new value, person and reason. It becomes a proposed update to the relevant patient record or review queue; it does not automatically change the medicine master or make the correction true for everyone.

### Doctor screen and service failures

For each result show the medicine or claim involved, what was checked, the outcome, any missing coverage, the source and date, and the next action. The doctor can review a match, clarify details, open a citation, edit, reject or report a problem. Do not hide safety findings based only on dismissal data.

Check clinic and user permissions on every request, including search, cache, exports and background work. Shared computers need individual accounts, automatic screen lock and a clear sign-out. Clinic protocols stay private to that clinic.

If a source, medicine record or service is missing, old or unavailable, show the affected feature as unavailable or incomplete. Offline reference material may be used only if it is approved, signed and unexpired. Do not show an old result as current. The product starts with only the language and content coverage that has been tested; each additional language needs its own clinical review.

### Audit and incidents

Record the request, user and clinic, relevant patient-context version, medicine matches, results, source and rule versions, citations, outages, doctor edits and final action. Do not put raw patient details in general logs or analytics. Set retention and deletion rules with counsel. Keep only the content needed and legally allowed to investigate and reproduce past results.

If a serious wrong result, missed safety issue, clinic data leak, unsupported claim or stale legal status is suspected, stop the affected feature, preserve permitted evidence, inform the clinical, security and privacy owners, investigate, correct the data or rule, rerun tests and obtain approval before re-enabling it.

## S6 · What You Added

| Factor | What is missing or weak | Why it matters | Severity | What I recommend |
|---|---|---|---|---|
| Source permissions | Sources are named, but permissions for storage, search and display are not supplied. | Public access does not automatically allow commercial reuse. | Critical | Record rights for each source and block use until approved (S3, D1). |
| Medical-device classification | The pack asks about regulation but gives no classification decision. | Doctor review does not automatically exempt software from regulation. | Critical | Get a written, feature-specific legal review before release (S4). |
| Privacy-law status | Effective dates and deployment details need current confirmation. | Incorrect assumptions could lead to unlawful processing. | Critical | Counsel checks current Gazette notifications, responsibilities and data flows (S4). |
| Medicine-match errors | The pack describes matching, but provides no independent accuracy evidence. | A wrong ingredient can make later checks wrong. | Critical | Use reviewed mappings, hold uncertain matches and test against an independent held-out set (S1/S7). |
| Incomplete prescription details | The design does not fully describe what happens when frequency or duration is unclear. | A result could look complete when it is not. | High | Return partial coverage and show the missing details (S5). |
| Audit and deletion | Replay is required, but retention and deletion are not fully designed. | Keeping too much patient data creates privacy risk. | High | Minimize audit content and test access, retention and deletion (S2/S5). |
| Clinic data separation | Local clinic rules are mentioned; complete separation across services is not specified. | Data can leak through search, cache, exports or logs. | Critical | Enforce clinic permissions at every data path and test clinic-to-clinic access (S2/S5). |
| Independent evaluation | Held-out tests are mentioned, but no cases or results are supplied. | The system may appear better if test answers were seen during development. | High | Keep blinded cases with an independent custodian (S7). |
| Answer and abstention measures | Evaluation definitions and denominators are not provided. | A system that refuses every question could misleadingly look safe. | High | Measure useful supported answers, wrong confident claims and correct refusals separately (S7). |
| Reviewer backlog | A clinical reviewer is expected, but queue limits are not specified. | Unreviewed or out-of-date content could remain available. | High | Track and prioritize review queues; remove expired content and narrow coverage when review is delayed (S7/S8). |
| Alert fatigue | The plan proposes learning from doctor actions but does not show how false alarms will be confirmed. | A dismissed alert is not necessarily an incorrect alert. | High | Have clinicians review alert samples and missed issues; do not tune only from clicks (S7). |
| AI provider and attacks | The pack proposes an LLM but does not specify final terms and controls. | Data may leave the service and unsafe text may influence the model. | High | Keep model use off until approved; test provider terms, prompt attacks and citations (S2/S4/S5). |
| Language coverage | Many languages are in scope, but validation results are not supplied. | Translation or medicine-name errors can be dangerous. | High | Validate each language with bilingual clinical reviewers before enabling it (S5/S7). |
| Offline behavior | The pack identifies unreliable connectivity but does not set freshness limits. | Old data can look current. | High | Show outages clearly and disable checks when required data is stale (S2/S5). |
| Price and stock matching | Price, catalogue and stock sources have different meanings. | The product could claim an item is available or correctly priced when it is not. | High | Keep these sources separate and show exact match and date (S3/S4). |
| Updates and rollback | Versioning is required, but the full publication process is not supplied. | A source or rule update could silently change answers. | High | Publish tested, versioned releases and rehearse rollback (S1/S7). |
| Upstream contracts | Scribe and patient-context code is not included. | Missing fields might be mistaken for known facts. | High | Agree versioned contracts and test missing, stale and conflicting fields (S1/S5). |
| Incident response | An incident plan is expected, but no runbook evidence is supplied. | A serious defect may not be stopped quickly. | High | Name owners, define escalation, provide a feature shutoff and rehearse response (S5/S8). |

## S7 · Validation & QA Plan

### Test data and reviewers

Keep a versioned test set. For every case, record its source, patient group, specialty, language, expected result, expected citations, applicable rule and reviewer. Use synthetic cases or data that has been properly approved for testing. Do not put identifiable patient data in public test files.

Qualified clinicians approve clinical reference answers and safety cases. Counsel reviews legal-status cases. An independent person keeps the held-out answers; engineers who build the feature must not see or edit them. Keep separate sets for development, tuning and release testing. If a held-out set is exposed, replace it.

Test common and difficult cases: brand variations, combination medicines, duplicate ingredients, allergies, pregnancy, missing strengths, unclear frequency, conflicting or superseded sources, unsupported questions, other languages, malicious document text, outages and clinic separation. Report high-risk test results separately from estimates of normal use. Do not claim a test result that has not been measured.

### Tests and pass criteria

| Capability | Test data and method | Proposed pass criteria | Evidence | Who approves |
|---|---|---|---|---|
| Medicine identity | Independent labels for exact names, aliases, transliteration, similar brands and formulations. | Zero silent wrong matches. Uncertain matches must be flagged. Report accuracy and how much of the catalogue is covered separately. | Error list, coverage and audit trail. | Independent pharmacist and QA. |
| Safety checks | Clinician-approved cases, including missing details and high-risk cases. Test whole prescriptions and service failures. | No missed critical test case. Every check returns exactly one valid state. Missing or stale data never appears safe. | Test results and approved rule versions. | Clinical pharmacologist and QA. |
| Regulatory status | Official notices, amendments, stays, reversals and effective dates. | No wrong status in the held-out set. Unclear scope must be shown as unknown. | Notice source, event history and replay. | Regulatory reviewer and counsel. |
| Clinical answers and citations | Clinician-approved answers and questions that should not be answered. Test paraphrases and misleading search results. | Every important claim has a valid supporting citation. No unsupported important claim or out-of-date source is presented as current. Unsupported questions are refused. | Claim-by-claim review and source versions. | Independent clinician and QA. |
| Useful answers | Questions with an approved answer and a rubric for usefulness. | Proposed target: at least 95% of answerable test requests are rated both useful and supported in each enabled feature area. Report the sample size and uncertainty. | Reviewer scores and results by feature. | Clinician who did not build the feature. |
| Confidently wrong answers | Independent review of every important claim emitted confidently. | Zero critical wrong claims. Proposed overall target: at most 0.1%; any critical error blocks release regardless of averages. | Number of wrong claims, total confident claims and confidence interval. | Clinical safety lead and QA. |
| Correct refusals | Questions with no approved answer, ambiguous medicine identity or unavailable data. | Proposed target: at least 95% of cases that should be refused are refused correctly. Also report refusals on answerable questions. | Case outcomes and reason for each refusal. | Independent clinician and QA. |
| Citation and scope | Tests with tables, footnotes, exceptions and different patient groups. | Citation must support the exact claim, location and patient group. Search relevance alone does not pass this test. | Page/section checks and reviewer record. | Clinical curator and QA. |
| Privacy and clinic separation | Synthetic users, clinics and roles; test API, search, cache, logs, exports and background tasks. | No cross-clinic access. Unauthorized access is denied. Deletion follows the approved policy. | Automated security results and independent review. | Security reviewer. |
| Outages and replay | Simulate expired data, network loss, unavailable services and restore from backup. | Every failure is visible; no stale normal-looking answer; saved results can be reconstructed or redactions are explained. | Fault-test logs and replay report. | QA/SRE and clinical safety lead. |
| Speed and usability | Representative synthetic load and doctor task tests. | Proposed targets: safety checks p95 under 100 ms; reference answers p95 under 2 seconds when dependencies are working. Report actual p50/p95/p99 and failures. Doctors must find the source and be able to edit or reject the result. | Load report and usability findings. | QA/SRE and clinician. |

These are proposed release targets, not achieved results. A good average cannot excuse a critical safety error, wrong medicine match, missing citation, “unknown” shown as safe, clinic data leak or missing approval.

### Ongoing quality checks

Every change to a source, medicine mapping, rule, prompt, model, search method or language must run its relevant tests before release. A change to clinical meaning also needs clinical re-approval. Keep the old approved version available for rollback.

Use these denominators consistently; report counts, rates, enabled-scope strata and confidence intervals, not a pooled score alone:

- **Confidently wrong rate:** number of consequential claims that an independent reviewer marks materially wrong while the answer states them as established, divided by all consequential claims independently reviewed as stated facts. Report critical errors separately; a confidence score from a model is not the denominator.
- **Useful supported answer rate:** answerable requests for which the response is both clinically useful under the approved rubric and fully supported by its citations, divided by all independently labelled answerable requests. Proposed target: at least 95% in each enabled capability stratum, with sample size and interval shown.
- **Appropriate abstention rate:** unanswerable or out-of-scope requests correctly refused, divided by all independently labelled unanswerable/out-of-scope requests. Proposed target: at least 95%; separately report false abstentions on answerable requests.
- **Release blockers:** zero critical unsupported clinical claims, missed critical seeded safety traps, silent wrong identity mappings, unknown-as-safe renderings, cross-tenant disclosures, or unapproved live content. A weighted average cannot offset any blocker.

These proposed thresholds are gates to evaluate, not achieved performance claims. If the sample cannot support a meaningful confidence interval, the release decision must say so and narrow the claim rather than treating an unstable point estimate as proof.

- **Daily:** check outages, failed imports, serious alerts and urgent correction reports. Stop content that has not passed review.
- **Weekly:** review a risk-based sample of answers, refusals, alerts and corrections. Report rates by specialty, language and clinic. Clinical reviewers—not QA alone—decide whether clinical content is correct.
- **In production:** review every reported serious issue and safety event, plus a random sample of other results. Increase sampling after changes or a rise in errors. Missing doctor feedback is unknown, not proof that an answer was right.
- **After a change:** rerun the affected tests. Run the full relevant held-out set after changes to models, prompts, sources, medicine mappings, safety rules or languages. If tests fail, do not release the change.

Automated checks and risk-based sampling reduce manual work, but do not replace qualified review of clinical content or serious incidents.

## S8 · Doctor-Handover Checklist

Only release features, sources, patient groups, clinics and languages that have passed their checks. The word “validated” in a project stage does not by itself complete this list.

| Item | Required before release | Evidence and approver | Blocks handover? |
|---|---|---|---|
| Intended use | Plain statement of what the product does and does not do. | Product owner, clinical lead and regulatory counsel approve the scope. | Yes |
| Legal classification | Written decision on medical-device and other applicable requirements for the exact feature. | Dated legal review and any required approvals. | Yes |
| Privacy | Approved patient-data purpose, notices, access, retention, deletion, breach response and provider terms. | Privacy counsel and privacy lead verify documents and tests. | Yes |
| Source permissions | Every live source permits the intended storage, search, display and audit use. | Rights register and written permissions checked by legal/source owner. | Yes |
| Clinical content | Sources, medicine mappings and rules are current, in scope and reviewed. | Versioned release register approved by qualified reviewers. | Yes |
| Tested coverage | Doctors can see which specialties, populations, sources and languages are supported and which are not. | Results by feature and coverage statement approved by clinical lead and QA. | Yes |
| Scribe and patient data | Interfaces correctly show missing, stale and conflicting information. | Contract and end-to-end tests approved by integration owner and QA. | Yes |
| Doctor workflow | Doctor can see evidence, correct, edit, reject and approve; nothing finalizes automatically. | Usability results and approval-step tests reviewed by product and clinical leads. | Yes |
| Security | User roles, clinic separation, shared-device behavior and exports are tested. | Independent security review and access tests. | Yes |
| AI provider, if used | Provider terms, data location, retention and model version are approved; answer limits pass tests. | Legal, security and clinical approval. | Yes |
| Outage behavior | Stale or unavailable data is clearly shown and cannot look like a safe result. | Outage and expiry tests approved by QA/SRE and clinical lead. | Yes |
| Audit and deletion | Records can be accessed only by authorized people and follow approved retention/deletion rules. | Replay, access and deletion tests approved by privacy/security and QA. | Yes |
| Support and incidents | Named owners, clinic contact, feature shutoff and correction/rollback process are ready. | Runbook and incident exercise approved by operations and clinical safety. | Yes |
| Release approval | All critical tests pass; the release record lists what changed and which versions are active. | Test report and release record signed by someone other than the implementer. | Yes |
| Doctor instructions | Doctors know allowed use, limitations, all result states and how to report a problem. | Approved instructions and support contact. | Yes |
| Monitoring | Team tracks wrong answers, refusals, incomplete checks, ambiguous matches, outages, alerts and corrections. | Dashboard and review ownership confirmed by QA/SRE and clinical safety. | Yes |

The assessment pack does not include the evidence or approvals needed to mark these items complete. National availability must not be described as proof that every medicine, specialty, patient group or language has been validated.

## S9 · AI-Usage Note

1. I used an AI assistant to help organize the assessment requirements and make a first draft. I reviewed the recommendations and remain responsible for the final decisions and claims.  
2. I changed the earlier draft to use the new assessment pack only and removed details that came from the mistakenly shared technical-assessment material.  
3. The main remaining uncertainty is the current legal status and source reuse rights; qualified Indian legal and clinical reviewers must verify these before release.
