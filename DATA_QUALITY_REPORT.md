# Forensic Data Quality & Profiling Report

**TransOrg AgentIQ Datathon — Track 1: FinTech & BFSI UPI Fraud Intelligence Platform**  
*Generated at: 2026-09-11T15:58:09.508510*

---

## Executive Summary

A comprehensive forensic examination of all four source data files was executed. The dataset exhibits typical real-world enterprise payment telemetry anomalies:
1. **Formatting Corruption**: Casing, punctuation, mixed currencies (`₹`, `INR`, `Rs.`), negative amounts, and spaced/hyphenated identifiers.
2. **Duplicate & Conflicting Records**: Exact row duplicates across transactions (400), KYC (278), merchants (12), and disputes (84), alongside significant logical duplicates with conflicting attributes.
3. **Foreign Key Integrity**: 91.52% of chargeback records link directly to UPI transactions, leaving 219 orphan disputes requiring specialized handling.
4. **Synthetic Identity & Mule Rings**: 319 Aadhaar numbers are shared across multiple distinct user IDs, and 71 settlement bank accounts are shared across multiple merchant entities.

---

## 1. File Profiling Metrics

### 1.1 UPI Transactions (`track1_upi_transactions.csv`)
| Metric | Raw Value | Status / Impact |
|---|---|---|
| **Total Rows** | 20,400 | Core transaction log |
| **Exact Duplicate Rows** | 400 | Removed in rescue layer with audit |
| **Unique Txn IDs** | 20,000 | 100% unique after deduplication |
| **Missing UTRs** | 1,024 | Flagged as `MISSING_UTR` |
| **UTRs with Spaces** | 1,881 | Rescued via whitespace stripping |
| **Negative Amounts** | 429 | Preserved & classified as `REFUND_REVERSAL` |
| **Raw Status Formats** | 14 variants | Normalized to `SUCCESS`, `FAILED`, `PENDING` |

### 1.2 Customer KYC Records (`track1_kyc_records.csv`)
| Metric | Raw Value | Status / Impact |
|---|---|---|
| **Total Rows** | 36,400 | KYC master register |
| **Duplicate User IDs** | 4,235 | Evaluated for entity resolution |
| **Unique User IDs** | 32,165 | Canonical `USRxxxxx` format |
| **Missing PANs** | 1,896 | Flagged in identity risk index |
| **Missing Aadhaars** | 2,664 | Flagged in identity risk index |
| **Missing Monthly Income** | 2,933 | Imputed / preserved as null |
| **Raw KYC Status Variants** | 10 variants | Normalized to `VERIFIED`, `PENDING`, `REJECTED` |

### 1.3 Merchants Master (`track1_merchants_master.csv`)
| Metric | Raw Value | Status / Impact |
|---|---|---|
| **Total Rows** | 6,210 | Merchant registry |
| **Duplicate Merchant IDs** | 1,127 | Conflicting names & categories resolved |
| **Unique Merchant IDs** | 5,083 | Canonical `MCHxxxx` format |
| **Missing Settlement Accounts** | 2,451 | Flagged in merchant risk model |
| **Missing MCCs** | 514 | Imputed from category descriptions |
| **Raw Status Variants** | 10 variants | Normalized to `ACTIVE`, `INACTIVE`, `SUSPENDED` |

### 1.4 Chargebacks & Disputes (`track1_chargebacks.json`)
| Metric | Raw Value | Status / Impact |
|---|---|---|
| **Total Records** | 2,884 | Customer dispute log |
| **Exact Duplicates** | 84 | Consolidated |
| **Blank Disputed Amounts** | 183 | Imputed from matched UPI transaction amounts |
| **Dispute Reason Codes** | 34 distinct strings | Categorized into 4 core dispute categories |
| **Linkage to UPI Transactions** | 2,363 / 2,582 (91.52%) | 219 orphan disputes retained & flagged |

---

## 2. Data Rescue Principles & Transformations

```
RAW VALUE  ──►  CANONICAL VALUE  ──►  VALIDATION STATUS  ──►  DATA QUALITY FLAG
```

1. **Preservation over Deletion**: No data rows were silently deleted. Every record is retained and classified.
2. **Auditability**: Every transformed field tracks its origin, transformation rule, and resolution confidence score.
3. **Foreign Key Resilience**: Unlinked transactions and chargebacks are retained with explicit `ORPHAN` flags.
