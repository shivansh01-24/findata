"""
FIU-IND Suspicious Transaction Report (STR) & Regulatory Dossier Engine.
Generates statutory AML/CFT case files compliant with:
  - Prevention of Money Laundering Act (PMLA), 2002 - Section 12
  - Financial Intelligence Unit - India (FIU-IND) Guidelines for Reporting Entities
  - RBI Master Direction on Digital Payment Security & Fraud Risk Management
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

from backend.intelligence.fraud_rings import FraudRingEngine
from backend.intelligence.merchant_risk import MerchantRiskEngine
from backend.intelligence.customer_risk import CustomerRiskEngine


class FiuStrGenerator:
    def __init__(self, data_proc_dir: str):
        self.data_dir = data_proc_dir
        self.fraud_engine = FraudRingEngine(data_proc_dir)
        self.merchant_engine = MerchantRiskEngine(data_proc_dir)
        self.customer_engine = CustomerRiskEngine(data_proc_dir)

        self.df_txns = pd.read_csv(os.path.join(data_proc_dir, "trusted_transactions.csv"))
        self.df_cb = pd.read_csv(os.path.join(data_proc_dir, "trusted_chargebacks.csv"))
        self.df_merchants = pd.read_csv(os.path.join(data_proc_dir, "trusted_merchants.csv"))
        self.df_customers = pd.read_csv(os.path.join(data_proc_dir, "trusted_customers.csv"))

    def generate_ring_str(self, ring_id: str) -> Optional[Dict[str, Any]]:
        ring = self.fraud_engine.get_ring_by_id(ring_id)
        if not ring:
            return None

        now_utc = datetime.now(timezone.utc)
        report_ref = f"FIU-IND/STR/2026/UPI-{ring_id.upper()}"
        filing_date = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

        mch_ids = ring.get('merchants', [])
        cust_ids = ring.get('customer_sample', []) or ring.get('customers', [])

        sub_txns = self.df_txns[
            self.df_txns['merchant_id'].isin(mch_ids) | 
            self.df_txns['user_id'].isin(cust_ids)
        ].head(25)

        sub_cbs = self.df_cb[
            self.df_cb['merchant_id'].isin(mch_ids) | 
            self.df_cb['user_id'].isin(cust_ids)
        ].head(20)

        grounds_summary = self._build_ring_grounds(ring)
        regulatory_actions = self._build_statutory_actions(ring)

        md = self._render_ring_markdown(
            report_ref=report_ref,
            filing_date=filing_date,
            ring=ring,
            grounds=grounds_summary,
            txns=sub_txns,
            cbs=sub_cbs,
            actions=regulatory_actions
        )

        member_count = ring.get('merchant_count', 0) + ring.get('customer_count', 0)

        return {
            'report_metadata': {
                'report_reference': report_ref,
                'filing_date': filing_date,
                'reporting_entity': 'TransOrg Payment Aggregator & UPI Switch',
                'fiu_registration_no': 'FIU-IND-PSO-2026-UPI-91204',
                'statutory_framework': 'PMLA 2002 Section 12 / RBI Master Direction on Fraud Risk Management',
                'classification': 'CONFIDENTIAL // LAW ENFORCEMENT & FIU-IND REPORTING ONLY'
            },
            'target_syndicate': {
                'ring_id': ring['ring_id'],
                'ring_name': ring['ring_name'],
                'ring_type': ring['ring_type'],
                'risk_score': ring['risk_score'],
                'member_count': member_count,
                'merchants_involved': ring.get('merchants', []),
                'customers_involved': cust_ids,
                'total_volume_inr': ring.get('transaction_volume', 0.0),
                'transaction_count': ring.get('transaction_count', 0),
                'chargeback_count': ring.get('chargeback_count', 0),
                'dispute_rate_pct': ring.get('chargeback_rate_pct', 0.0)
            },
            'grounds_of_suspicion': grounds_summary,
            'network_topology': {
                'topology_type': ring['ring_type'],
                'anchor_attribute': ring.get('anchor_attribute', 'Distributed Settlement Routing'),
                'why_flagged': ring.get('why_flagged', '')
            },
            'forensic_transaction_sample': sub_txns[['txn_id', 'user_id', 'merchant_id', 'amount', 'status', 'utr', 'timestamp']].to_dict(orient='records'),
            'dispute_audit_sample': sub_cbs[['complaint_id', 'user_id', 'merchant_id', 'disputed_amount', 'reason_category', 'severity']].to_dict(orient='records'),
            'statutory_directives': regulatory_actions,
            'markdown_dossier': md
        }

    def generate_merchant_str(self, merchant_id: str) -> Optional[Dict[str, Any]]:
        mch = self.merchant_engine.get_merchant_dossier(merchant_id)
        if not mch:
            return None

        info = mch
        metrics = {
            'risk_score': mch.get('risk_score', 0.0),
            'risk_level': mch.get('risk_level', 'LOW'),
            'chargeback_rate': mch.get('cb_rate_pct', 0.0),
            'total_volume': mch.get('total_volume', 0.0),
            'chargeback_volume': mch.get('cb_volume', 0.0),
            'declared_ticket_size': mch.get('declared_avg_ticket_size', 0.0) or 0.0,
            'actual_avg_ticket_size': mch.get('avg_ticket', 0.0) or 0.0,
            'ticket_size_deviation_ratio': mch.get('ticket_deviation_ratio', 1.0) or 1.0
        }
        now_utc = datetime.now(timezone.utc)
        report_ref = f"FIU-IND/STR/2026/MCH-{merchant_id.upper()}"
        filing_date = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

        txns = self.df_txns[self.df_txns['merchant_id'] == merchant_id].head(25)
        cbs = self.df_cb[self.df_cb['merchant_id'] == merchant_id].head(20)

        grounds = [
            f"Merchant recorded a chargeback-to-transaction ratio of {metrics['chargeback_rate']}%, well above the 1.0% RBI regulatory threshold.",
            f"Actual average ticket size (Rs. {float(metrics['actual_avg_ticket_size']):,.2f}) deviated from declared baseline (Rs. {float(metrics['declared_ticket_size']):,.2f}) by a factor of {metrics['ticket_size_deviation_ratio']}x.",
            f"Settlement account '{info.get('settlement_account') or 'UNASSIGNED'}' identified under operational status '{info.get('merchant_status')}' in category '{info.get('merchant_category')}'."
        ]

        actions = [
            "1. Impose immediate freeze / lien on merchant settlement account.",
            "2. Suspend Virtual Payment Address (VPA) and revoke QR payment endpoints.",
            "3. Request statutory audited bank statements and verified tax invoices.",
            "4. File electronic STR with Financial Intelligence Unit - India (FIU-IND) portal."
        ]

        md = self._render_merchant_markdown(
            report_ref=report_ref,
            filing_date=filing_date,
            merchant=info,
            metrics=metrics,
            grounds=grounds,
            txns=txns,
            cbs=cbs,
            actions=actions
        )

        return {
            'report_metadata': {
                'report_reference': report_ref,
                'filing_date': filing_date,
                'reporting_entity': 'TransOrg Payment Aggregator & UPI Switch',
                'fiu_registration_no': 'FIU-IND-PSO-2026-UPI-91204',
                'statutory_framework': 'PMLA 2002 Section 12',
                'classification': 'CONFIDENTIAL // STR FILING'
            },
            'target_merchant': info,
            'operational_metrics': metrics,
            'grounds_of_suspicion': grounds,
            'forensic_transaction_sample': txns[['txn_id', 'user_id', 'amount', 'status', 'utr', 'timestamp']].to_dict(orient='records'),
            'dispute_sample': cbs[['complaint_id', 'user_id', 'disputed_amount', 'reason_category', 'severity']].to_dict(orient='records'),
            'statutory_directives': actions,
            'markdown_dossier': md
        }

    def _build_ring_grounds(self, ring: Dict[str, Any]) -> List[str]:
        grounds = []
        r_type = ring.get('ring_type', '')

        if 'Settlement' in r_type or 'Mule' in r_type:
            grounds.append(
                f"Multiple commercial storefronts ({ring.get('merchant_count', 0)} merchants) route funds into a single centralized settlement anchor ({ring.get('anchor_attribute')}), indicating classic mule aggregation."
            )
            grounds.append(
                f"Cumulative transaction volume of Rs. {ring.get('transaction_volume', 0.0):,.2f} with {ring.get('chargeback_count', 0)} dispute incidents ({ring.get('chargeback_rate_pct', 0.0)}% dispute velocity)."
            )
            grounds.append("Entities operate across disparate business categories, contradicting legitimate single-enterprise merchant architectures.")

        elif 'Synthetic' in r_type:
            grounds.append(
                f"Cluster of {ring.get('customer_count', 0)} KYC profiles exhibit shared credential linkages ({ring.get('anchor_attribute')}) and synthetic identity layering."
            )
            grounds.append(
                "High density of disputed UPI debits with customer dispute repeaters targeting multiple merchant terminals."
            )

        else:
            grounds.append(
                f"Merchant terminal exhibits sudden burst velocity with acute dispute density ({ring.get('chargeback_rate_pct', 0.0)}% chargeback ratio), characteristic of bust-out merchant abandonment."
            )
            grounds.append(
                f"Accumulated Rs. {ring.get('transaction_volume', 0.0):,.2f} in gross volume prior to chargeback settlement reconciliation."
            )

        return grounds

    def _build_statutory_actions(self, ring: Dict[str, Any]) -> List[str]:
        return [
            "1. Issue Section 12 PMLA freeze order against all linked settlement accounts and beneficiary bank nodes.",
            "2. Quarantine all Virtual Payment Addresses (VPAs) and device MAC/IMEI fingerprints across the national UPI switch.",
            "3. Transmit priority XML intelligence report to FIU-IND FINnet 2.0 Gateway.",
            "4. Coordinate with National Cyber Crime Reporting Portal (NCRP) and state Law Enforcement Cyber Cell for beneficiary recovery."
        ]

    def _render_ring_markdown(self, report_ref: str, filing_date: str, ring: Dict, grounds: List[str], txns: pd.DataFrame, cbs: pd.DataFrame, actions: List[str]) -> str:
        txns_md_table = "No transactions found"
        if len(txns) > 0:
            txns_md_table = "| Txn ID | User ID | Merchant ID | Amount (INR) | Status | UTR | Timestamp |\n|---|---|---|---|---|---|---|\n"
            for _, r in txns.head(8).iterrows():
                txns_md_table += f"| `{r.get('txn_id')}` | `{r.get('user_id')}` | `{r.get('merchant_id')}` | ₹{float(r.get('amount', 0)):,.2f} | **{r.get('status')}** | `{r.get('utr')}` | {r.get('timestamp')} |\n"

        cbs_md_table = "No chargebacks found"
        if len(cbs) > 0:
            cbs_md_table = "| Dispute ID | Counterparty | Disputed Amount | Reason Category | Severity |\n|---|---|---|---|---|\n"
            for _, r in cbs.head(8).iterrows():
                cbs_md_table += f"| `{r.get('complaint_id')}` | `{r.get('user_id')}` | ₹{float(r.get('disputed_amount', 0)):,.2f} | {r.get('reason_category')} | **{r.get('severity')}** |\n"

        grounds_str = "\n".join([f"- {g}" for g in grounds])
        actions_str = "\n".join([f"{a}" for a in actions])
        merchants_str = ", ".join([f"`{m}`" for m in ring.get('merchants', [])[:10]]) or "None"
        cust_list = ring.get('customer_sample', []) or ring.get('customers', [])
        customers_str = ", ".join([f"`{c}`" for c in cust_list[:10]]) or "None"
        member_cnt = ring.get('merchant_count', 0) + ring.get('customer_count', 0)

        return f"""# FINANCIAL INTELLIGENCE UNIT - INDIA (FIU-IND)
## SUSPICIOUS TRANSACTION REPORT (STR) — DIGITAL PAYMENTS & UPI

**Reference No:** `{report_ref}`  
**Date of Filing:** `{filing_date}`  
**Reporting Entity:** TransOrg Payment Aggregator & UPI Switch  
**Regulatory Mandate:** Prevention of Money Laundering Act (PMLA) 2002, Section 12 | RBI/DPSS/2024-25/118  
**Classification:** STRICTLY CONFIDENTIAL // LAW ENFORCEMENT SENSITIVE  

---

### 1. TARGET SYNDICATE SUMMARY
- **Syndicate ID:** `{ring['ring_id']}` ({ring['ring_name']})
- **Typology Classification:** **{ring['ring_type']}**
- **Composite Risk Score:** **{ring['risk_score']} / 100.0 (CRITICAL)**
- **Entities Implicated:** {member_cnt} Nodes ({ring.get('merchant_count', 0)} Merchants, {ring.get('customer_count', 0)} Customers)
- **Cumulative UPI Volume:** ₹{ring.get('transaction_volume', 0.0):,.2f} across {ring.get('transaction_count', 0)} transactions
- **Disputed Volume / Velocity:** {ring.get('chargeback_count', 0)} Chargebacks (**{ring.get('chargeback_rate_pct', 0.0)}%** Dispute Ratio)

### 2. IMPLICATED NODES
- **Merchants:** {merchants_str}
- **Customers / Identities:** {customers_str}
- **Settlement Anchor:** `{ring.get('anchor_attribute', 'Distributed Routing')}`

---

### 3. STATUTORY GROUNDS OF SUSPICION (PMLA RULE 3)
{grounds_str}

---

### 4. FORENSIC TRANSACTION AUDIT TRAIL (SAMPLE)
{txns_md_table}

### 5. CHARGEBACK & DISPUTE CORROBORATION
{cbs_md_table}

---

### 6. MANDATORY STATUTORY DIRECTIVES & ENFORCEMENT
{actions_str}

---
*Generated electronically under automated forensic supervision by the TransOrg AgentIQ Track 1 Intelligence Engine.*
"""

    def _render_merchant_markdown(self, report_ref: str, filing_date: str, merchant: Dict, metrics: Dict, grounds: List[str], txns: pd.DataFrame, cbs: pd.DataFrame, actions: List[str]) -> str:
        txns_md_table = "No transactions found"
        if len(txns) > 0:
            txns_md_table = "| Txn ID | User ID | Amount (INR) | Status | UTR | Timestamp |\n|---|---|---|---|---|---|\n"
            for _, r in txns.head(8).iterrows():
                txns_md_table += f"| `{r.get('txn_id')}` | `{r.get('user_id')}` | ₹{float(r.get('amount', 0)):,.2f} | **{r.get('status')}** | `{r.get('utr')}` | {r.get('timestamp')} |\n"

        grounds_str = "\n".join([f"- {g}" for g in grounds])
        actions_str = "\n".join([f"{a}" for a in actions])

        return f"""# FINANCIAL INTELLIGENCE UNIT - INDIA (FIU-IND)
## SUSPICIOUS TRANSACTION REPORT (STR) — MERCHANT TERMINAL AUDIT

**Reference No:** `{report_ref}`  
**Date of Filing:** `{filing_date}`  
**Reporting Entity:** TransOrg Payment Aggregator & UPI Switch  
**Regulatory Mandate:** Section 12 PMLA, 2002  

---

### 1. MERCHANT IDENTITY & PROFILE
- **Merchant ID:** `{merchant['merchant_id']}`
- **Trade Name:** **{merchant['merchant_name']}**
- **Category (Canonical MCC):** {merchant['merchant_category']} (MCC: {merchant.get('mcc')})
- **Settlement Account:** `{merchant.get('settlement_account') or 'MISSING'}`
- **Location:** {merchant.get('city')}, {merchant.get('state')}
- **Operational Status:** {merchant.get('merchant_status')}

### 2. FORENSIC RISK & DISPUTE METRICS
- **Composite Risk Score:** **{metrics['risk_score']} / 100.0** ({metrics['risk_level']})
- **Chargeback Rate:** **{metrics['chargeback_rate']}%** (Platform Regulatory Limit: 1.0%)
- **Disputed Volume:** ₹{metrics['chargeback_volume']:,.2f} out of ₹{metrics['total_volume']:,.2f} GMV
- **Ticket Size Expansion:** Declared ₹{metrics['declared_ticket_size']:,.2f} vs Actual ₹{metrics['actual_avg_ticket_size']:,.2f} (**{metrics['ticket_size_deviation_ratio']}x**)

---

### 3. STATUTORY GROUNDS OF SUSPICION
{grounds_str}

### 4. TRANSACTION CHRONOLOGY (SAMPLE)
{txns_md_table}

---

### 5. STATUTORY REMEDIATION ACTIONS
{actions_str}

---
*Confidential Legal Dossier generated by TransOrg AgentIQ Track 1 Engine.*
"""
