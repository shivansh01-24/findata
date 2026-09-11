"""
Merchant Risk Intelligence Engine.
Evaluates merchant telemetry, chargebacks, ticket deviations, and syndicate associations.
Computes a Multivariate Merchant Risk Score (0 - 100) and investigation priority ranking.
"""

import os
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np


class MerchantRiskEngine:
    def __init__(self, data_proc_dir: str):
        self.data_dir = data_proc_dir
        self._load_data()
        self._compute_merchant_metrics()

    def _load_data(self):
        self.df_merchants = pd.read_csv(os.path.join(self.data_dir, "trusted_merchants.csv"))
        self.df_txns = pd.read_csv(os.path.join(self.data_dir, "trusted_transactions.csv"))
        self.df_cb = pd.read_csv(os.path.join(self.data_dir, "trusted_chargebacks.csv"))

    def _compute_merchant_metrics(self):
        # Transaction stats per merchant
        txn_stats = self.df_txns.groupby('merchant_id').agg(
            total_txns=('txn_id', 'count'),
            total_volume=('amount', lambda x: float(x.abs().sum())),
            avg_ticket=('amount', lambda x: float(x.abs().mean())),
            success_txns=('status', lambda x: int((x == 'SUCCESS').sum())),
            failed_txns=('status', lambda x: int((x == 'FAILED').sum()))
        ).reset_index()

        # Chargeback stats per merchant
        cb_stats = self.df_cb.groupby('merchant_id').agg(
            cb_count=('complaint_id', 'count'),
            cb_volume=('disputed_amount', lambda x: float(x.sum())),
            crit_cb_count=('severity', lambda x: int((x == 'Critical').sum())),
            high_cb_count=('severity', lambda x: int((x == 'High').sum())),
            top_reason=('reason_category', lambda x: x.mode()[0] if len(x) > 0 else 'None')
        ).reset_index()

        # Shared settlement accounts
        mch_acc = self.df_merchants[
            self.df_merchants['settlement_account'].notna() & 
            ~self.df_merchants['settlement_account'].isin(['NA', 'None', '', 'nan'])
        ]
        shared_accounts = set(mch_acc.groupby('settlement_account').filter(lambda g: len(g) > 1)['settlement_account'])

        # Merge with merchant master
        merged = self.df_merchants.merge(txn_stats, on='merchant_id', how='left')
        merged = merged.merge(cb_stats, on='merchant_id', how='left')

        # Fill NaNs
        merged['total_txns'] = merged['total_txns'].fillna(0).astype(int)
        merged['total_volume'] = merged['total_volume'].fillna(0.0).round(2)
        merged['avg_ticket'] = merged['avg_ticket'].fillna(0.0).round(2)
        merged['success_txns'] = merged['success_txns'].fillna(0).astype(int)
        merged['failed_txns'] = merged['failed_txns'].fillna(0).astype(int)
        merged['cb_count'] = merged['cb_count'].fillna(0).astype(int)
        merged['cb_volume'] = merged['cb_volume'].fillna(0.0).round(2)
        merged['crit_cb_count'] = merged['crit_cb_count'].fillna(0).astype(int)
        merged['high_cb_count'] = merged['high_cb_count'].fillna(0).astype(int)
        merged['top_reason'] = merged['top_reason'].fillna('None')

        # Chargeback rate %
        merged['cb_rate_pct'] = np.where(
            merged['total_txns'] > 0,
            (merged['cb_count'] / merged['total_txns'] * 100).round(2),
            0.0
        )

        # Shared settlement flag
        merged['shared_settlement_account'] = merged['settlement_account'].isin(shared_accounts)

        # Ticket deviation ratio
        merged['ticket_deviation_ratio'] = np.where(
            (merged['declared_avg_ticket_size'].notna()) & (merged['declared_avg_ticket_size'] > 0),
            (merged['avg_ticket'] / merged['declared_avg_ticket_size']).round(2),
            1.0
        )

        # Multivariate Risk Score (0 - 100)
        def calc_risk(row):
            score = 15.0 # baseline
            
            # 1. Chargeback rate & volume (up to 35 pts)
            rate = row['cb_rate_pct']
            cb_cnt = row['cb_count']
            if cb_cnt >= 20 or rate >= 25.0: score += 35.0
            elif cb_cnt >= 10 or rate >= 15.0: score += 25.0
            elif cb_cnt >= 5 or rate >= 10.0: score += 15.0
            elif cb_cnt > 0: score += 8.0

            # 2. High severity disputes (up to 15 pts)
            crit = row['crit_cb_count'] + row['high_cb_count']
            if crit >= 10: score += 15.0
            elif crit >= 5: score += 10.0
            elif crit > 0: score += 5.0

            # 3. Shared settlement mule account (15 pts)
            if row['shared_settlement_account']:
                score += 15.0

            # 4. Ticket deviation (up to 15 pts)
            dev = row['ticket_deviation_ratio']
            if dev >= 4.0 or dev <= 0.2: score += 15.0
            elif dev >= 2.5 or dev <= 0.4: score += 10.0

            # 5. Merchant status penalty (up to 15 pts)
            status = row['merchant_status']
            if status == 'SUSPENDED': score += 15.0
            elif status == 'INACTIVE': score += 5.0

            # 6. Entity conflicts
            if row['resolution_type'] == 'CONFLICTING_MERCHANT_RECORD':
                score += 5.0

            return min(100.0, round(score, 1))

        merged['risk_score'] = merged.apply(calc_risk, axis=1)

        def risk_level(score):
            if score >= 80: return 'CRITICAL'
            elif score >= 60: return 'HIGH'
            elif score >= 40: return 'MEDIUM'
            return 'LOW'

        merged['risk_level'] = merged['risk_score'].apply(risk_level)

        # Generate "Why Investigate" explanation
        def gen_why(row):
            reasons = []
            if row['cb_count'] >= 10:
                reasons.append(f"{row['cb_count']} total chargebacks ({row['cb_rate_pct']}% dispute rate)")
            if (row['crit_cb_count'] + row['high_cb_count']) >= 5:
                reasons.append(f"{row['crit_cb_count']} Critical and {row['high_cb_count']} High severity disputes")
            if row['shared_settlement_account']:
                reasons.append(f"Shares bank settlement account '{row['settlement_account']}' with other merchants")
            if row['ticket_deviation_ratio'] >= 3.0:
                reasons.append(f"Actual ticket size ₹{row['avg_ticket']:,.0f} is {row['ticket_deviation_ratio']}x higher than declared ₹{row['declared_avg_ticket_size']:,.0f}")
            if row['merchant_status'] == 'SUSPENDED':
                reasons.append("Account is currently SUSPENDED by operations")
            if not reasons:
                reasons.append("Normal operational profile within baseline thresholds")
            return " | ".join(reasons)

        merged['investigation_rationale'] = merged.apply(gen_why, axis=1)

        self.df_metrics = merged.sort_values(by='risk_score', ascending=False)

    def get_ranked_merchants(
        self, 
        category: Optional[str] = None, 
        risk_level: Optional[str] = None, 
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        df = self.df_metrics.copy()
        if category and category != 'ALL':
            df = df[df['merchant_category'].str.upper() == category.upper()]
        if risk_level and risk_level != 'ALL':
            df = df[df['risk_level'].str.upper() == risk_level.upper()]
        if status and status != 'ALL':
            df = df[df['merchant_status'].str.upper() == status.upper()]
            
        return df.head(limit).to_dict(orient='records')

    def get_merchant_dossier(self, merchant_id: str) -> Optional[Dict[str, Any]]:
        match = self.df_metrics[self.df_metrics['merchant_id'] == merchant_id]
        if len(match) == 0:
            return None
        mch = match.iloc[0].to_dict()

        # Add recent transactions
        recent_txns = self.df_txns[self.df_txns['merchant_id'] == merchant_id].head(20).to_dict(orient='records')
        # Add recent chargebacks
        recent_cbs = self.df_cb[self.df_cb['merchant_id'] == merchant_id].head(20).to_dict(orient='records')

        mch['recent_transactions'] = recent_txns
        mch['recent_chargebacks'] = recent_cbs
        return mch
