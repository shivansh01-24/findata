# FinData: UPI Fraud Intelligence Platform
### TransOrg AgentIQ Datathon — Track 1: FinTech & BFSI

[![Tests](https://img.shields.io/badge/tests-17%2F17%20passed-success)](https://github.com/shivansh01-24/findata)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-teal)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-blue)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6.2-purple)](https://vitejs.dev)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

An enterprise-grade UPI Fraud Intelligence & Merchant Risk Investigation Platform built for the **TransOrg AgentIQ Datathon**. It demonstrates the complete analytical progression:

```
Messy Data  ──►  Data Rescue  ──►  Trusted Analytics  ──►  Fraud Intelligence  ──►  Executive Dashboard  ──►  Agentic Graph AI
```

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Business Problem](#business-problem)
3. [Dataset Architecture](#dataset-architecture)
4. [Data Rescue & Preservation Philosophy](#data-rescue--preservation-philosophy)
5. [Entity Resolution Engine](#entity-resolution-engine)
6. [Cross-File Relationship & Foreign Key Validation](#cross-file-relationship--foreign-key-validation)
7. [Fraud Ring & Graph Intelligence](#fraud-ring--graph-intelligence)
8. [Merchant & Customer Risk Models](#merchant--customer-risk-models)
9. [Chargeback Intelligence & Benchmark Answers](#chargeback-intelligence--benchmark-answers)
10. [Executive Dashboard Architecture](#executive-dashboard-architecture)
11. [Agentic Graph AI Engine](#agentic-graph-ai-engine)
12. [OpenRouter Free-Model Fallback Architecture](#openrouter-free-model-fallback-architecture)
13. [Installation & Setup](#installation--setup)
14. [Running the Platform](#running-the-platform)
15. [Automated Test Suite](#automated-test-suite)
16. [Repository Structure](#repository-structure)
17. [Judging Rubric Compliance](#judging-rubric-compliance)

---

## 1. Project Overview

Digital payment rails (UPI) in India process billions of transactions monthly. Real-world financial telemetry is plagued by corrupt formatting, duplicate records, unverified settlement bank accounts, conflicting KYC identities, and organized money laundering syndicates.

This platform rescues dirty UPI transaction logs, customer KYC master data, merchant registries, and dispute logs without silently dropping records. It constructs an auditable **Trusted Analytical Layer**, extracts 295 graph fraud syndicates using **NetworkX**, delivers an **Executive Investigation Dashboard**, and embeds a domain-constrained **Agentic Graph AI** powered by OpenRouter free-tier LLMs with deterministic calculation grounding.

---

## 2. Business Problem

Financial institutions face three critical challenges:
1. **Mule Merchant Syndicates**: Unregistered entities funnelling transactions into shared shadow bank settlement accounts.
2. **Synthetic Identity Farming**: Disparate customer profiles registered with identical recycled Aadhaar numbers.
3. **High-Dispute Bust-Outs**: Storefronts experiencing explosive transaction volumes followed by extreme dispute and chargeback rates.

This platform bridges the gap between raw data engineering and executive decision-making.

---

## 3. Dataset Architecture

The platform operates on the official synthetic competition dataset:
- `track1_upi_transactions.csv` (20,400 raw rows)
- `track1_kyc_records.csv` (36,400 raw rows)
- `track1_merchants_master.csv` (6,210 raw rows)
- `track1_chargebacks.json` (2,884 raw records)
- `track1_dataset_notes.txt`

The raw files in `data/raw/` remain pristine and immutable.

---

## 4. Data Rescue & Preservation Philosophy

The platform rejects the destructive "bad row = delete row" approach. Every record undergoes:

```
RAW VALUE  ──►  CANONICAL VALUE  ──►  VALIDATION STATUS  ──►  DATA QUALITY FLAG
```

### Forensic Rescue Operations:
- **Identifier Standardization**: User IDs standardized from `usr12345`, `USR-12345`, `USR 12345`, `12345` to canonical `USRxxxxx`. Merchant IDs standardized to `MCHxxxx`. Transaction IDs to `TXNxxxxxxxx`.
- **Currency & Amount Parsing**: Strips mixed currency prefixes (`₹`, `INR`, `Rs.`), trailing multiplier abbreviations (`27.3k` -> `27300.0`), commas, and whitespace. Negative amounts are categorized as `REFUND_OR_REVERSAL_NEGATIVE`.
- **Multi-Format Timestamp Parser**: Resolves Unix epoch seconds (`1770063471`), ISO `YYYY-MM-DD`, European `DD/MM/YYYY`, US `MM-DD-YYYY`, and 12-hour AM/PM timestamps.
- **Transaction Status**: Standardized from 14 messy variants (`S`, `TXN_SUCCESS`, `COMPLETED`, `Fail`, `Declined`, `Initiated`) into `SUCCESS`, `FAILED`, `PENDING`.
- **UTR Normalization**: Removes embedded spaces (`UTR 2787678319` -> `UTR2787678319`); validates 10-digit format.
- **PAN & Aadhaar Validation**: PANs validated against `^[A-Z]{5}[0-9]{4}[A-Z]{1}$`. Aadhaars categorized into 12-digit, masked, or malformed.
- **Merchant MCC & Categories**: Resolves 82+ messy category strings into 10 canonical categories aligned with ISO MCC codes.

---

## 5. Entity Resolution Engine

Entity resolution on Customer KYC and Merchant Master separates duplicates into four distinct classes:
1. `SINGLETON`: Unique verified record.
2. `EXACT_DUPLICATE`: 100% identical duplicate rows safely consolidated.
3. `FORMATTING_DUPLICATE`: Discrepancies limited to whitespace, casing, or phone formatting.
4. `CONFLICTING_RECORD`: Divergent substantive attributes (e.g. differing PANs, Aadhaar numbers, or contradictory KYC statuses like `VERIFIED` vs `REJECTED`).

### Resolution Results:
- **Customer KYC**: 36,400 raw rows -> **28,920 Golden Customer Profiles**
  - 22,632 Singletons
  - 5,863 Conflicting Records resolved via confidence scoring
  - 251 Formatting Duplicates
  - 174 Exact Duplicates
- **Merchants Master**: 6,210 raw rows -> **4,343 Golden Merchant Records**
  - 2,931 Singletons
  - 1,310 Conflicting Merchant Records resolved
  - 97 Formatting Duplicates
  - 5 Exact Duplicates

---

## 6. Cross-File Relationship & Foreign Key Validation

- **Transaction to Customer FK**: 6,478 transactions link to customer KYC records (32.4%). Unlinked payer IDs are retained and flagged as `UNLINKED_CUSTOMER_ORPHAN`.
- **Transaction to Merchant FK**: 9,631 transactions link directly to Merchant master (48.2%).
- **Chargebacks to UPI Transactions**: **2,607 of 2,800 chargebacks link directly to UPI transactions (91.52%)**.
- **Missing Disputed Amounts**: 163 chargebacks with blank disputed amounts were successfully imputed from the matched UPI transaction amounts.
- **Orphan Chargebacks**: 193 unlinked disputes are retained and explicitly flagged with original identifiers.

---

## 7. Fraud Ring & Graph Intelligence

Using **NetworkX**, the intelligence engine maps the bipartite and projected graphs between Customers, Merchants, and Settlement Accounts, identifying **295 suspicious networks**:

1. **Shared Settlement Mule Syndicates (71 Networks)**:
   - Multiple commercial merchants funnel funds into identical bank settlement accounts (e.g. account `XXXX0207` shared by multiple merchants).
   - Indicates shadow aggregator bypass, shell companies, and centralized laundering.
2. **Synthetic Identity Clusters (185 Networks)**:
   - Clusters of user profiles sharing identical government Aadhaar credentials across conflicting legal names.
3. **High-Dispute Bust-Out Networks (39 Networks)**:
   - Merchants accumulating extreme chargeback velocity (e.g., `MCH8154`, `MCH4473`, `MCH9291`) with repeat disputing accounts.

Every ring provides an explainable dossier with **Why Flagged** rationale, transaction volume, chargeback rate, and actionable investigator recommendations.

---

## 8. Merchant & Customer Risk Models

### Multivariate Merchant Risk Index (0 - 100):
- Weighted combination of:
  - Baseline chargeback-to-transaction ratio (up to 35 pts)
  - Dispute severity (Critical / High priority cases) (up to 15 pts)
  - Shared settlement mule account flag (15 pts)
  - Ticket size abnormality (deviation > 2.5x of declared ticket size) (up to 15 pts)
  - Operational suspension status (`SUSPENDED` / `HOLD`) (up to 15 pts)
  - Conflicting entity records (5 pts)

### Customer Identity Risk Index (0 - 100):
- Evaluates repeat dispute abuse, shared Aadhaar cluster membership, conflicting KYC submissions, and regulatory rejection status.

---

## 9. Chargeback Intelligence & Benchmark Answers

### Official Datathon Benchmark Question:
> *"Which merchant category has the highest chargeback-to-transaction ratio this quarter?"*

**Answer computed from the trusted analytical layer (Q1 2026):**
1. **Apparel**: **30.34%** (44 chargebacks on 145 transactions)
2. **Miscellaneous Retail**: **18.87%** (308 chargebacks on 1,632 transactions)
3. **Department Store**: **17.92%** (31 chargebacks on 173 transactions)
4. **Transportation**: **13.59%** (403 chargebacks on 2,966 transactions)
5. **Restaurant**: **13.31%** (398 chargebacks on 2,990 transactions)
6. **Grocery**: **12.63%** (736 chargebacks on 5,826 transactions)
7. **Pharmacy**: **11.92%** (357 chargebacks on 2,996 transactions)
8. **Hotel & Lodging**: **11.38%** (336 chargebacks on 2,953 transactions)
9. **Telecom**: **8.70%** (10 chargebacks on 115 transactions)
10. **Books & Stationery**: **5.56%** (7 chargebacks on 126 transactions)

---

## 10. Executive Dashboard Architecture

The dashboard is built with React 19, TypeScript, Tailwind CSS, and Recharts:

- **View 1: Executive Overview**: High-level KPIs (₹224.95M Gross Volume, 85.27% Success Rate, ₹7.52M Disputed Volume, 14.0% Dispute Ratio), daily volume trends, category risk benchmarks, and severity breakdowns.
- **View 2: Fraud Ring Explorer**: Interactive Canvas-based Network Graph with physics layout, node dragging, click inspection, typology filters, and explainable dossiers.
- **View 3: Merchant Risk Center**: Ranked table with multi-factor risk scores, declared vs actual ticket sizes, category filters, and full 360-degree merchant dossiers.
- **View 4: Customer / Identity Risk Center**: Surveillance of conflicting KYC records, shared Aadhaar badges, repeat disputers, and customer dossiers.
- **View 5: Data Rescue & Audit Trail**: Transparent before/after metrics, duplicate resolution breakdown, and foreign key integrity.

---

## 11. Agentic Graph AI Engine

The Agent is a specialized **UPI Fraud Intelligence Assistant**:
1. **Hard Application-Level Domain Guard**: Strictly allows payment, fraud, KYC, and chargeback queries. Refuses off-topic questions (e.g., general knowledge, coding) with:
   > *"That is outside my field. I can only assist with UPI transactions, fraud, KYC/identity risk, merchant risk, chargebacks, and related analytics in this platform."*
2. **Prompt-Injection Defense**: Detects and blocks instruction overrides, persona hijacking, and secret extraction attempts before any LLM prompt is constructed.
3. **Deterministic Calculation Grounding**: Analytical numbers and rankings are calculated by the deterministic query engine. The LLM synthesizes the business narrative without hallucinating figures.
4. **Dynamic Chart Generation**: Returns bar charts, line charts, and KPI cards directly rendered in the chat drawer.

---

## 12. OpenRouter Free-Model Fallback Architecture

Per competition rules, OpenRouter is the only LLM provider used:
- Default sequence of free models:
  1. `meta-llama/llama-3.3-70b-instruct:free`
  2. `google/gemini-2.0-flash-exp:free`
  3. `qwen/qwen-2.5-72b-instruct:free`
  4. `mistralai/mistral-small-24b-instruct-2501:free`
  5. **Deterministic Fallback Engine** (if all LLMs fail or no API key is set)

### Resiliency Guarantee:
If OpenRouter is unavailable or rate-limited:
- **All Dashboard Views continue functioning at 100%**.
- The AI Agent gracefully falls back to verified deterministic responses.

---

## 13. Installation & Setup

### Prerequisites:
- Python 3.10+
- Node.js 18+ and npm

### 1. Clone the repository:
```bash
git clone https://github.com/shivansh01-24/findata.git
cd findata
```

### 2. Backend Setup:
```bash
python -m pip install -r requirements.txt
# Run the data rescue pipeline to build the trusted layer
python backend/pipeline/build_trusted_layer.py
```

### 3. Frontend Setup:
```bash
cd frontend
npm install
cd ..
```

---

## 14. Running the Platform

### Start Backend API Server:
```bash
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Frontend Dashboard:
```bash
cd frontend
npm run dev
```

Open your browser at `http://localhost:5173`.

---

## 15. Automated Test Suite

Run the test suite covering data standardizers, entity resolution, risk analytics, and agent guardrails:

```bash
python -m pytest tests/ -v
```

**Results: 17 passed in 6.56s (100% passing)**

---

## 16. Repository Structure

```
findata/
├── backend/
│   ├── api/
│   │   ├── agent/
│   │   │   ├── domain_guard.py          # Domain & injection defense
│   │   │   ├── deterministic_engine.py  # Grounded mathematical queries
│   │   │   └── openrouter_client.py     # Multi-model free fallback
│   │   └── main.py                      # FastAPI REST application
│   ├── intelligence/
│   │   ├── chargeback_analytics.py      # Category ratios & KPIs
│   │   ├── customer_risk.py             # Synthetic ID & KYC scoring
│   │   ├── fraud_rings.py               # NetworkX graph ring detection
│   │   └── merchant_risk.py             # Multivariate merchant risk
│   └── pipeline/
│       ├── build_trusted_layer.py       # Orchestration pipeline
│       ├── data_profiler.py             # Forensic profiler
│       ├── entity_resolution.py         # Golden record consolidation
│       └── standardizers.py             # Cleaning & rescue rules
├── data/
│   ├── raw/                             # Pristine source data (preserved)
│   └── processed/                       # Rescued trusted datasets
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AgentDrawer.tsx          # Natural language AI drawer
│   │   │   ├── CustomerRiskCenter.tsx   # View 4
│   │   │   ├── DataRescueAudit.tsx      # View 5
│   │   │   ├── ExecutiveOverview.tsx    # View 1
│   │   │   ├── FraudRingExplorer.tsx    # View 2
│   │   │   ├── KeyModal.tsx             # OpenRouter key settings
│   │   │   ├── MerchantRiskCenter.tsx   # View 3
│   │   │   ├── Navbar.tsx               # Navigation & status bar
│   │   │   └── NetworkGraph.tsx         # Interactive canvas graph
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
├── tests/
│   ├── test_agent.py                    # Domain, injection & fallback
│   ├── test_analytics.py                # KPIs, ratios & rankings
│   └── test_standardizers.py            # Normalization & parsing
├── DATA_DICTIONARY.md                   # Enterprise data dictionary
├── DATA_QUALITY_REPORT.md               # Forensic profiling report
└── README.md                            # Complete documentation
```

---

## 17. Judging Rubric Compliance

| Rubric Gate | Requirement | Implementation Status |
|---|---|---|
| **Gate 1** | Sanity & Raw Data Preservation | Source files preserved in `data/raw/` untouched; no synthetic replacements. |
| **Gate 2** | Data Engineering & Entity Resolution | Standardizers, 4-tier duplicate resolution, FK audit trail, before/after metrics. |
| **Gate 3** | Executive Dashboard & Business Value | 5 interactive views, interactive Canvas graph, category benchmark answers. |
| **Gate 4** | Engineering & Agentic Graph AI | Strict domain guard, injection defense, OpenRouter free fallback, deterministic grounding. |
