# FinData: UPI Fraud Intelligence Platform
## TransOrg AgentIQ Datathon — Track 1: FinTech & BFSI

---

## Slide 1: Title & Executive Overview
* **Product Name:** FinData — Enterprise UPI Fraud Intelligence Platform
* **Core Value Proposition:** Transforming dirty, fragmented payment logs into verifiable, graph-powered fraud intelligence and grounded agentic AI.
* **Key Progression:** `Messy Data → Forensic Data Rescue → Trusted Analytics → Fraud Intelligence → Executive Dashboard → Agentic Graph AI`

---

## Slide 2: The Challenge: Real-World UPI Data Chaos
* **Four Heterogeneous Source Files:**
  * 20,400 UPI Transactions
  * 36,400 Customer KYC Records
  * 6,210 Merchant Master Profiles
  * 2,884 Chargebacks & Disputes
* **Severe Telemetry Quality Issues:**
  * 400 transaction exact duplicates, 4,235 KYC duplicates, 1,127 merchant duplicates.
  * Spaced/hyphenated IDs (`USR 45454`, `MCH-2637`), corrupted currency symbols (`Rs.`, `₹`, `INR`), negative refund amounts.
  * 319 shared Aadhaar clusters (synthetic identity markers) and 71 shared settlement bank accounts (mule syndicates).
  * 219 orphan disputes requiring forensic linkage.

---

## Slide 3: Forensic Data Rescue Architecture
* **Philosophical Principle:** Preservation over Deletion (Zero silent record drops).
* **Deterministic Transformation Pipeline:**
  * **Customers:** 36,400 raw rows $\rightarrow$ **28,920 Golden Customer Records**
  * **Merchants:** 6,210 raw rows $\rightarrow$ **4,343 Golden Merchant Masters**
  * **Transactions:** 20,400 raw rows $\rightarrow$ **20,000 Trusted Transactions** (₹249.77M Volume)
  * **Chargebacks:** 2,884 raw rows $\rightarrow$ **2,800 Validated Disputes** (₹8.86M Volume)
* **Forensic Entity Resolution Diff Engine:**
  * Side-by-side reconciliation matrix with cell-level conflict highlighting and confidence scoring.
  * Immutable transformation audit trails across all entities.

---

## Slide 4: Authoritative Analytical Ground Truth
* **Core Competition Benchmark Finding:**
  > *"Which merchant category has the highest chargeback-to-transaction ratio this quarter?"*
* **Complete Q1 2026 Category Distribution:**
  1. **Apparel:** **30.34%** (44 chargebacks / 145 transactions) — **#1 Highest Dispute Density**
  2. **Miscellaneous Retail:** **18.87%** (308 chargebacks / 1,632 transactions) — **Highest Total Chargeback Count**
  3. **Department Store:** **17.92%** (31 chargebacks / 173 transactions)
  4. **Transportation:** **14.89%** (443 chargebacks / 2,975 transactions)
  5. **Telecom:** **14.29%** (18 chargebacks / 126 transactions)
  6. **Restaurant:** **13.97%** (419 chargebacks / 3,000 transactions)
  7. **Grocery:** **13.13%** (767 chargebacks / 5,840 transactions)
  8. **Pharmacy:** **12.82%** (385 chargebacks / 3,004 transactions)
  9. **Hotel & Lodging:** **12.45%** (369 chargebacks / 2,964 transactions)
  10. **Books & Stationery:** **11.35%** (16 chargebacks / 141 transactions)
* **Platform Average:** **14.00%** (2,800 disputes / 20,000 transactions)

---

## Slide 5: Graph AI & Multi-Hop Fraud Rings
* **295 Suspicious Networks Uncovered:**
  * **Shared Settlement Mules (71 Rings):** Multiple independent merchant storefronts funneling revenue into single destination accounts.
  * **Bust-Out Merchant Schemes (184 Rings):** Rapid escalation in transaction velocity and ticket size followed by massive dispute surges.
  * **Synthetic Identity Clusters (40 Rings):** Reused national identity documents (Aadhaar/PAN) creating linked puppet customer profiles.
* **Interactive Canvas Graph Visualizer:** Physics layout, dynamic node dragging, multi-hop path tracing, and node detail inspection.

---

## Slide 6: Merchant & Customer Risk Surveillance
* **Merchant Risk Index (0–100 Composite):**
  * Dynamic formula combining dispute excess, gross loss volume, ticket size anomaly multiplier, and mule account sharing.
  * Top Flagged Merchant: `MCH9291` (Score 95.0, 78 chargebacks, 29.5% dispute rate).
* **Customer KYC & Identity Risk Index:**
  * Surveillance of repeat dispute abusers (`USR97772` with 16 disputes) and shared credential syndicates.

---

## Slide 7: Interactive Risk Policy Simulation ("What-If" Analysis)
* **Real-Time Portfolio Modeling:**
  * Interactive sliders for Dispute Cap (5%–50%), Ticket Size Multiplier (1.0x–4.0x), and Mule Sharing Threshold (1–5).
  * Instant recalculation of newly flagged merchants, contained dispute volume, and platform capture rate.
  * Direct 1-click generation of regulatory investigation dossiers for triggered entities.

---

## Slide 8: Regulatory Compliance & FIU-IND STR Dossiers
* **Automated Investigation & STR Pre-Filing Packages:**
  * Aligned with Prevention of Money Laundering Act (PMLA) Section 12 and FIU-IND FINnet guidelines.
  * Comprehensive dossiers for all 295 fraud rings and high-risk merchants.
  * Includes Statutory Reference IDs, Grounds of Suspicion, Itemized Transaction Logs with UTRs, and Enforcement Directives.
  * Dual export in Formatted Legal Markdown and Structured JSON.

---

## Slide 9: Domain-Guarded Agentic AI & Resilient Failover
* **Multi-Tier Agentic Architecture:**
  1. **Domain Guard:** Application-level regex and security filters enforcing strict payments/fraud domain boundaries and blocking prompt injections.
  2. **Deterministic Query Engine:** Extracts exact ground-truth facts from verified Pandas dataframes with zero calculation hallucination.
  3. **OpenRouter Free Tier:** Prioritized fallback across verified free models (`inclusionai/ling-3.0-flash-fin:free`, `nvidia/nemotron-3.5-lightning:free`, etc.).
  4. **Local Deterministic Fallback:** 0ms downtime failover upon upstream outages.
  5. **Credential Masking:** 100% server-side key protection; zero client leaks.

---

## Slide 10: Engineering Rigor & Verification
* **42 / 42 Pytest Tests Passing (100% Success):**
  * Unit tests, standardizers, entity resolution, risk engines, agent NLP, and Playwright browser E2E tests.
* **13 / 13 Smoke Tests Passing:** Full end-to-end API and UI validation.
* **Automated Playwright Visual Suite:** Headless browser automation capturing 8 high-resolution 1920x1080 visual proofs.
* **Production Build:** Clean React 19 + TypeScript + Tailwind SPA served natively by FastAPI backend.

---

## Slide 11: Summary & Strategic Impact
* **From Unreliable Logs to Auditable Intelligence:**
  * Verifiable source of truth across all 20,000 transactions and 2,800 chargebacks.
  * Actionable tools for risk officers, compliance investigators, and executive leadership.
  * Production-ready, fully open-source, and defensible under rigorous technical scrutiny.
