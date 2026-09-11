"""
Audit Rescue & Entity Diff Service.
Provides high-performance search and side-by-side reconciliation between
raw ingested source rows and canonical golden records.
Reveals every transformation, quality flag, and tie-breaker rationale.
"""

import os
import re
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

from backend.pipeline.standardizers import (
    normalize_user_id,
    normalize_merchant_id,
    normalize_pan,
    normalize_aadhaar,
    normalize_kyc_status,
    normalize_merchant_status
)


class AuditRescueService:
    def __init__(self, data_raw_dir: str, data_proc_dir: str):
        self.data_raw_dir = data_raw_dir
        self.data_proc_dir = data_proc_dir
        self._load_data()

    def _load_data(self):
        # 1. Load Processed Golden Datasets
        self.df_customers = pd.read_csv(os.path.join(self.data_proc_dir, "trusted_customers.csv"))
        self.df_merchants = pd.read_csv(os.path.join(self.data_proc_dir, "trusted_merchants.csv"))
        self.df_txns = pd.read_csv(os.path.join(self.data_proc_dir, "trusted_transactions.csv"))
        self.df_cb = pd.read_csv(os.path.join(self.data_proc_dir, "trusted_chargebacks.csv"))

        # 2. Load Raw Ingestion Datasets
        self.df_raw_kyc = pd.read_csv(
            os.path.join(self.data_raw_dir, "track1_kyc_records.csv"),
            dtype=str
        ).replace({np.nan: None})
        self.df_raw_kyc['original_row_idx'] = self.df_raw_kyc.index + 2  # 1-indexed plus header

        self.df_raw_mch = pd.read_csv(
            os.path.join(self.data_raw_dir, "track1_merchants_master.csv"),
            dtype=str
        ).replace({np.nan: None})
        self.df_raw_mch['original_row_idx'] = self.df_raw_mch.index + 2

        # 3. Build fast lookup index mapping canonical ID -> raw rows
        self._build_indices()

    def _build_indices(self):
        # Customers index: map canonical_id -> list of raw dicts
        self.customer_raw_map: Dict[str, List[Dict[str, Any]]] = {}
        for _, row in self.df_raw_kyc.iterrows():
            clean_id, flag = normalize_user_id(row.get('user_id'))
            if clean_id:
                row_dict = row.to_dict()
                row_dict['_id_flag'] = flag
                self.customer_raw_map.setdefault(clean_id, []).append(row_dict)

        # Merchants index: map canonical_id -> list of raw dicts
        self.merchant_raw_map: Dict[str, List[Dict[str, Any]]] = {}
        for _, row in self.df_raw_mch.iterrows():
            clean_id, flag = normalize_merchant_id(row.get('merchant_id'))
            if clean_id:
                row_dict = row.to_dict()
                row_dict['_id_flag'] = flag
                self.merchant_raw_map.setdefault(clean_id, []).append(row_dict)

        # Activity summary maps (Txn count, Chargeback count)
        self.cust_txn_counts = self.df_txns['user_id'].value_counts().to_dict()
        self.cust_cb_counts = self.df_cb['user_id'].value_counts().to_dict()
        self.mch_txn_counts = self.df_txns['merchant_id'].value_counts().to_dict()
        self.mch_cb_counts = self.df_cb['merchant_id'].value_counts().to_dict()

    def search_entities(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        q = query.strip().lower()
        if not q:
            return self.get_curated_cases()

        results = []

        # 1. Search Customers
        cust_matches = self.df_customers[
            self.df_customers['user_id'].str.lower().str.contains(q, na=False) |
            self.df_customers['full_name'].str.lower().str.contains(q, na=False) |
            self.df_customers['pan'].str.lower().str.contains(q, na=False)
        ]
        for _, c in cust_matches.head(limit).iterrows():
            uid = c['user_id']
            results.append({
                'entity_id': uid,
                'entity_type': 'CUSTOMER',
                'display_name': c['full_name'],
                'identifier': f"PAN: {c['pan'] or 'MISSING'}",
                'category_or_segment': c['risk_segment'],
                'status': c['kyc_status'],
                'resolution_type': c['resolution_type'],
                'raw_record_count': int(c['raw_record_count']),
                'confidence': float(c['resolution_confidence']),
                'txns_count': int(self.cust_txn_counts.get(uid, 0)),
                'cb_count': int(self.cust_cb_counts.get(uid, 0))
            })

        # 2. Search Merchants
        mch_matches = self.df_merchants[
            self.df_merchants['merchant_id'].str.lower().str.contains(q, na=False) |
            self.df_merchants['merchant_name'].str.lower().str.contains(q, na=False) |
            self.df_merchants['settlement_account'].str.lower().str.contains(q, na=False)
        ]
        for _, m in mch_matches.head(limit).iterrows():
            mid = m['merchant_id']
            results.append({
                'entity_id': mid,
                'entity_type': 'MERCHANT',
                'display_name': m['merchant_name'],
                'identifier': f"Settlement: {m['settlement_account'] or 'NONE'}",
                'category_or_segment': m['merchant_category'],
                'status': m['merchant_status'],
                'resolution_type': m['resolution_type'],
                'raw_record_count': int(m['raw_record_count']),
                'confidence': float(m['resolution_confidence']),
                'txns_count': int(self.mch_txn_counts.get(mid, 0)),
                'cb_count': int(self.mch_cb_counts.get(mid, 0))
            })

        return results[:limit]

    def get_entity_audit(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        norm_type = entity_type.strip().upper()
        clean_query = entity_id.strip()

        if norm_type == 'CUSTOMER':
            norm_id, _ = normalize_user_id(clean_query)
            if not norm_id:
                norm_id = clean_query.upper()

            c_match = self.df_customers[self.df_customers['user_id'] == norm_id]
            if len(c_match) == 0:
                return None
            golden = c_match.iloc[0].replace({np.nan: None}).to_dict()
            raw_rows = self.customer_raw_map.get(norm_id, [])

            attribute_diffs = self._diff_customer_attributes(golden, raw_rows)

            return {
                'entity_id': norm_id,
                'entity_type': 'CUSTOMER',
                'golden_record': golden,
                'raw_records': raw_rows,
                'attribute_diffs': attribute_diffs,
                'resolution_type': golden.get('resolution_type'),
                'resolution_confidence': float(golden.get('resolution_confidence', 1.0)),
                'conflict_details': golden.get('conflict_details'),
                'raw_record_count': len(raw_rows),
                'txns_count': int(self.cust_txn_counts.get(norm_id, 0)),
                'cb_count': int(self.cust_cb_counts.get(norm_id, 0))
            }

        elif norm_type == 'MERCHANT':
            norm_id, _ = normalize_merchant_id(clean_query)
            if not norm_id:
                norm_id = clean_query.upper()

            m_match = self.df_merchants[self.df_merchants['merchant_id'] == norm_id]
            if len(m_match) == 0:
                return None
            golden = m_match.iloc[0].replace({np.nan: None}).to_dict()
            raw_rows = self.merchant_raw_map.get(norm_id, [])

            attribute_diffs = self._diff_merchant_attributes(golden, raw_rows)

            return {
                'entity_id': norm_id,
                'entity_type': 'MERCHANT',
                'golden_record': golden,
                'raw_records': raw_rows,
                'attribute_diffs': attribute_diffs,
                'resolution_type': golden.get('resolution_type'),
                'resolution_confidence': float(golden.get('resolution_confidence', 1.0)),
                'conflict_details': golden.get('conflict_details'),
                'raw_record_count': len(raw_rows),
                'txns_count': int(self.mch_txn_counts.get(norm_id, 0)),
                'cb_count': int(self.mch_cb_counts.get(norm_id, 0))
            }

        return None

    def _diff_customer_attributes(self, golden: Dict, raw_rows: List[Dict]) -> List[Dict[str, Any]]:
        diffs = []
        fields = [
            ('User ID', 'user_id', 'user_id', 'Normalized prefix, uppercase conversion, stripped whitespace'),
            ('Full Name', 'full_name', 'full_name', 'Trimmed whitespace, normalized to Title Case, resolved conflicts by KYC recency'),
            ('PAN', 'pan', 'pan', 'Stripped hyphens/spaces, validated 10-char regex, checked fourth char status'),
            ('Aadhaar', 'aadhaar', 'aadhaar', 'Stripped spaces, masked to last 4 digits (XXXX-XXXX-NNNN), Verhoeff checksum validated'),
            ('KYC Status', 'kyc_status', 'kyc_status', 'Mapped legacy codes (V/P/R/KYC_DONE) to canonical VERIFIED, PENDING, REJECTED'),
            ('Monthly Income', 'monthly_income', 'monthly_income', 'Stripped currency symbols (Rs., INR), converted negative polarity, parsed floats'),
            ('Risk Segment', 'risk_segment', 'risk_segment', 'Harmonized tier categorization (LOW, MEDIUM, HIGH)'),
            ('Signup Date', 'signup_timestamp', 'signup_timestamp', 'Harmonized epoch/ISO timestamps into standard ISO-8601')
        ]

        for label, golden_col, raw_col, desc in fields:
            raw_vals = [r.get(raw_col) for r in raw_rows]
            unique_raw = set(str(v).strip() for v in raw_vals if v is not None)
            has_conflict = len(unique_raw) > 1

            diffs.append({
                'attribute': label,
                'canonical_value': golden.get(golden_col),
                'raw_values': raw_vals,
                'transformations_applied': desc,
                'conflict_detected': has_conflict,
                'distinct_raw_variants': len(unique_raw)
            })

        return diffs

    def _diff_merchant_attributes(self, golden: Dict, raw_rows: List[Dict]) -> List[Dict[str, Any]]:
        diffs = []
        fields = [
            ('Merchant ID', 'merchant_id', 'merchant_id', 'Normalized MCH prefix, stripped hyphens, uppercase conversion'),
            ('Merchant Name', 'merchant_name', 'merchant_name', 'Resolved conflicting trade names by operational priority and complete banking profile'),
            ('MCC / Category', 'merchant_category', 'merchant_category', 'Consolidated 82 granular/legacy MCCs into 10 canonical RBI categories'),
            ('Settlement Account', 'settlement_account', 'settlement_account', 'Extracted and validated bank account number, verified shared mule usage across multiple stores'),
            ('Merchant Status', 'merchant_status', 'merchant_status', 'Harmonized abbreviations (A/E/S) into ACTIVE, SUSPENDED, TERMINATED'),
            ('Declared Ticket Size', 'declared_avg_ticket_size', 'declared_avg_ticket_size', 'Parsed currency strings and floats, established transaction anomaly baseline')
        ]

        for label, golden_col, raw_col, desc in fields:
            raw_vals = [r.get(raw_col) for r in raw_rows]
            unique_raw = set(str(v).strip() for v in raw_vals if v is not None)
            has_conflict = len(unique_raw) > 1

            diffs.append({
                'attribute': label,
                'canonical_value': golden.get(golden_col),
                'raw_values': raw_vals,
                'transformations_applied': desc,
                'conflict_detected': has_conflict,
                'distinct_raw_variants': len(unique_raw)
            })

        return diffs

    def get_curated_cases(self) -> List[Dict[str, Any]]:
        return [
            {
                'entity_id': 'MCH7912',
                'entity_type': 'MERCHANT',
                'display_name': 'Sarma-Arya / dewan, tak and subramanian',
                'identifier': 'Settlement: ZNNS3870382152945',
                'category_or_segment': 'Grocery',
                'status': 'ACTIVE',
                'resolution_type': 'CONFLICTING_RECORD',
                'raw_record_count': 6,
                'confidence': 0.70,
                'txns_count': int(self.mch_txn_counts.get('MCH7912', 0)),
                'cb_count': int(self.mch_cb_counts.get('MCH7912', 0)),
                'curation_tag': '6-Row Merchant Conflict',
                'forensic_highlight': '6 raw records with clashing trade names, 2 different settlement bank accounts, and divergent operational statuses (Active vs Suspended).'
            },
            {
                'entity_id': 'USR10043',
                'entity_type': 'CUSTOMER',
                'display_name': 'Rehaan Buch / Inaya Lanka',
                'identifier': 'PAN: TWXGM2046F',
                'category_or_segment': 'HIGH',
                'status': 'VERIFIED',
                'resolution_type': 'CONFLICTING_RECORD',
                'raw_record_count': 2,
                'confidence': 0.65,
                'txns_count': int(self.cust_txn_counts.get('USR10043', 0)),
                'cb_count': int(self.cust_cb_counts.get('USR10043', 0)),
                'curation_tag': 'Conflicting KYC Names & PAN',
                'forensic_highlight': 'Identity collision: two distinct individuals (Rehaan Buch vs Inaya Lanka) mapped to same ID; one raw record had hyphenated PAN HGKBQ-4142-L and legacy status "P".'
            },
            {
                'entity_id': 'USR10052',
                'entity_type': 'CUSTOMER',
                'display_name': 'Rohan Kothari',
                'identifier': 'PAN: UBWTV8602C',
                'category_or_segment': 'MEDIUM',
                'status': 'VERIFIED',
                'resolution_type': 'CONFLICTING_RECORD',
                'raw_record_count': 3,
                'confidence': 0.75,
                'txns_count': int(self.cust_txn_counts.get('USR10052', 0)),
                'cb_count': int(self.cust_cb_counts.get('USR10052', 0)),
                'curation_tag': '3-Row Identity Collision',
                'forensic_highlight': '3 raw KYC rows: 2 rows for Rohan Kothari with lowercase PAN "ubwtv8602c", and 1 row for "   Ladli Doctor   " with un-trimmed whitespace and status PENDING.'
            },
            {
                'entity_id': 'USR10098',
                'entity_type': 'CUSTOMER',
                'display_name': 'Xiti Ben',
                'identifier': 'PAN: QUPZM7586 (Invalid 9-char)',
                'category_or_segment': 'LOW',
                'status': 'REJECTED',
                'resolution_type': 'FORMATTING_DUPLICATE',
                'raw_record_count': 2,
                'confidence': 0.95,
                'txns_count': int(self.cust_txn_counts.get('USR10098', 0)),
                'cb_count': int(self.cust_cb_counts.get('USR10098', 0)),
                'curation_tag': 'Missing Prefix & Malformed PAN',
                'forensic_highlight': 'Raw User ID arrived without "USR" prefix ("10098"). Rescued via regex prefix recovery. PAN flagged as MALFORMED (9 characters instead of 10).'
            },
            {
                'entity_id': 'USR45454',
                'entity_type': 'CUSTOMER',
                'display_name': 'Siddharth Chadha',
                'identifier': 'PAN: ZTYXQ9012K',
                'category_or_segment': 'LOW',
                'status': 'VERIFIED',
                'resolution_type': 'FORMATTING_DUPLICATE',
                'raw_record_count': 2,
                'confidence': 1.0,
                'txns_count': int(self.cust_txn_counts.get('USR45454', 0)),
                'cb_count': int(self.cust_cb_counts.get('USR45454', 0)),
                'curation_tag': 'Whitespace ID Un-mangling',
                'forensic_highlight': 'Raw ID contained internal whitespace ("USR 45454"). Cleaned and unified with canonical record.'
            },
            {
                'entity_id': 'MCH2637',
                'entity_type': 'MERCHANT',
                'display_name': 'Natarajan and Sons',
                'identifier': 'Settlement: UYRQ4820194829104',
                'category_or_segment': 'Apparel',
                'status': 'ACTIVE',
                'resolution_type': 'FORMATTING_DUPLICATE',
                'raw_record_count': 2,
                'confidence': 1.0,
                'txns_count': int(self.mch_txn_counts.get('MCH2637', 0)),
                'cb_count': int(self.mch_cb_counts.get('MCH2637', 0)),
                'curation_tag': 'Hyphenated Merchant ID',
                'forensic_highlight': 'Raw merchant ID had hyphen delimiter ("MCH-2637") and currency symbol prefix in ticket size ("Rs. 4,500"). Normalized cleanly into canonical schema.'
            }
        ]
