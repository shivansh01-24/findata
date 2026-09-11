"""
Customer & Synthetic Identity Risk Engine.
Scores customer identity risk, tracks conflicting KYC records, shared Aadhaar credentials,
and repeated dispute abuse patterns.
"""

import os
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np


class CustomerRiskEngine:
    def __init__(self, data_proc_dir: str):
        self.data_dir = data_proc_dir
        self._load_data()
        self._compute_customer_metrics()

    def _load_data(self):
        self.df_customers = pd.read_csv(os.path.join(self.data_dir, "trusted_customers.csv"))
        self.df_txns = pd.read_csv(os.path.join(self.data_dir, "trusted_transactions.csv"))
        self.df_cb = pd.read_csv(os.path.join(self.data_dir, "trusted_chargebacks.csv"))

    def _compute_customer_metrics(self):
        # Transaction stats per customer
        txn_stats = self.df_txns.groupby('user_id').agg(
            total_txns=('txn_id', 'count'),
            total_volume=('amount', lambda x: float(x.abs().sum())),
            success_txns=('status', lambda x: int((x == 'SUCCESS').sum())),
            failed_txns=('status', lambda x: int((x == 'FAILED').sum()))
        ).reset_index()

        # Chargeback stats per customer
        cb_stats = self.df_cb.groupby('user_id').agg(
            cb_count=('complaint_id', 'count'),
            cb_volume=('disputed_amount', lambda x: float(x.sum())),
            crit_cb_count=('severity', lambda x: int((x == 'Critical').sum())),
            high_cb_count=('severity', lambda x: int((x == 'High').sum())),
            top_reason=('reason_category', lambda x: x.mode()[0] if len(x) > 0 else 'None')
        ).reset_index()

        # Shared Aadhaar cluster identification
        valid_aadhaar = self.df_customers[
            self.df_customers['aadhaar'].notna() & 
            self.df_customers['aadhaar'].str.contains(r'\d')
        ]
        shared_aadhaars = set(valid_aadhaar.groupby('aadhaar').filter(lambda g: len(g) > 1)['aadhaar'])

        # Merge with customer master
        merged = self.df_customers.merge(txn_stats, on='user_id', how='left')
        merged = merged.merge(cb_stats, on='user_id', how='left')

        # Fill NaNs
        merged['total_txns'] = merged['total_txns'].fillna(0).astype(int)
        merged['total_volume'] = merged['total_volume'].fillna(0.0).round(2)
        merged['success_txns'] = merged['success_txns'].fillna(0).astype(int)
        merged['failed_txns'] = merged['failed_txns'].fillna(0).astype(int)
        merged['cb_count'] = merged['cb_count'].fillna(0).astype(int)
        merged['cb_volume'] = merged['cb_volume'].fillna(0.0).round(2)
        merged['crit_cb_count'] = merged['crit_cb_count'].fillna(0).astype(int)
        merged['high_cb_count'] = merged['high_cb_count'].fillna(0).astype(int)
        merged['top_reason'] = merged['top_reason'].fillna('None')

        # Synthetic identity flag
        merged['shared_aadhaar_cluster'] = merged['aadhaar'].isin(shared_aadhaars)

        # Multi-factor Identity Risk Score (0 - 100)
        def calc_cust_risk(row):
            score = 10.0 # baseline

            # 1. Dispute repeater (up to 40 pts)
            cb_cnt = row['cb_count']
            if cb_cnt >= 8: score += 40.0
            elif cb_cnt >= 4: score += 25.0
            elif cb_cnt >= 1: score += 12.0

            # 2. Shared Aadhaar / Synthetic identity (25 pts)
            if row['shared_aadhaar_cluster']:
                score += 25.0

            # 3. Conflicting KYC entity record (15 pts)
            if row['resolution_type'] == 'CONFLICTING_RECORD':
                score += 15.0

            # 4. KYC status penalty
            if row['kyc_status'] == 'REJECTED': score += 15.0
            elif row['kyc_status'] == 'PENDING': score += 5.0

            # 5. Identifier flaws
            if row['pan_flag'] == 'MALFORMED_PAN_FORMAT': score += 8.0
            elif row['pan_flag'] == 'MISSING_PAN': score += 4.0

            if row['aadhaar_flag'] == 'MALFORMED_AADHAAR': score += 8.0

            # 6. Risk segment prior
            if row['risk_segment'] == 'HIGH': score += 10.0

            return min(100.0, round(score, 1))

        merged['risk_score'] = merged.apply(calc_cust_risk, axis=1)

        def cust_risk_level(score):
            if score >= 80: return 'CRITICAL'
            elif score >= 60: return 'HIGH'
            elif score >= 40: return 'MEDIUM'
            return 'LOW'

        merged['risk_level'] = merged['risk_score'].apply(cust_risk_level)

        def gen_cust_why(row):
            reasons = []
            if row['cb_count'] >= 3:
                reasons.append(f"Repeat disputer: {row['cb_count']} chargebacks filed totaling ₹{row['cb_volume']:,.0f}")
            if row['shared_aadhaar_cluster']:
                reasons.append(f"Shares Aadhaar '{row['aadhaar']}' with multiple registered accounts (Synthetic ID signal)")
            if row['resolution_type'] == 'CONFLICTING_RECORD':
                reasons.append(f"Conflicting KYC records detected: {row['conflict_details']}")
            if row['kyc_status'] == 'REJECTED':
                reasons.append("KYC status is REJECTED")
            if row['pan_flag'] == 'MALFORMED_PAN_FORMAT':
                reasons.append(f"Malformed PAN format: '{row['pan']}'")
            if not reasons:
                reasons.append("Clean identity verification profile")
            return " | ".join(reasons)

        merged['investigation_rationale'] = merged.apply(gen_cust_why, axis=1)

        self.df_metrics = merged.sort_values(by='risk_score', ascending=False)

    def get_ranked_customers(
        self,
        kyc_status: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        df = self.df_metrics.copy()
        if kyc_status and kyc_status != 'ALL':
            df = df[df['kyc_status'].str.upper() == kyc_status.upper()]
        if risk_level and risk_level != 'ALL':
            df = df[df['risk_level'].str.upper() == risk_level.upper()]
        df = df.replace({np.nan: None})
        return df.head(limit).to_dict(orient='records')

    def get_customer_dossier(self, user_id: str) -> Optional[Dict[str, Any]]:
        match = self.df_metrics[self.df_metrics['user_id'] == user_id]
        if len(match) == 0:
            return None
        cust = match.replace({np.nan: None}).iloc[0].to_dict()

        # Add recent transactions & chargebacks
        recent_txns = self.df_txns[self.df_txns['user_id'] == user_id].replace({np.nan: None}).head(20).to_dict(orient='records')
        recent_cbs = self.df_cb[self.df_cb['user_id'] == user_id].replace({np.nan: None}).head(20).to_dict(orient='records')

        cust['recent_transactions'] = recent_txns
        cust['recent_chargebacks'] = recent_cbs
        return cust
