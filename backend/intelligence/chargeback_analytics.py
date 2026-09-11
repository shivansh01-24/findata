"""
Chargeback & Dispute Intelligence Engine.
Computes dispute ratios, category rankings, reason breakdowns, severity metrics,
and answers core datathon questions with verifiable accuracy.
"""

import os
from typing import Dict, List, Any
import pandas as pd
import numpy as np


class ChargebackAnalyticsEngine:
    def __init__(self, data_proc_dir: str):
        self.data_dir = data_proc_dir
        self._load_data()

    def _load_data(self):
        self.df_txns = pd.read_csv(os.path.join(self.data_dir, "trusted_transactions.csv"))
        self.df_cb = pd.read_csv(os.path.join(self.data_dir, "trusted_chargebacks.csv"))

    def get_category_chargeback_ratios(self) -> List[Dict[str, Any]]:
        """
        Calculates the chargeback-to-transaction ratio for every merchant category this quarter.
        Directly answers the benchmark question:
        'Which merchant category has the highest chargeback-to-transaction ratio this quarter?'
        """
        txn_counts = self.df_txns['merchant_category'].value_counts()
        txn_vols = self.df_txns.groupby('merchant_category')['amount'].apply(lambda x: float(x.abs().sum()))

        cb_counts = self.df_cb['merchant_category'].value_counts()
        cb_vols = self.df_cb.groupby('merchant_category')['disputed_amount'].sum()

        categories = sorted(list(set(txn_counts.index).union(set(cb_counts.index))))
        records = []

        for cat in categories:
            t_cnt = int(txn_counts.get(cat, 0))
            t_vol = float(txn_vols.get(cat, 0.0))
            c_cnt = int(cb_counts.get(cat, 0))
            c_vol = float(cb_vols.get(cat, 0.0))

            ratio_pct = round((c_cnt / t_cnt * 100), 2) if t_cnt > 0 else 0.0
            vol_ratio_pct = round((c_vol / t_vol * 100), 2) if t_vol > 0 else 0.0

            records.append({
                'category': cat,
                'transaction_count': t_cnt,
                'transaction_volume': round(t_vol, 2),
                'chargeback_count': c_cnt,
                'disputed_volume': round(c_vol, 2),
                'chargeback_to_transaction_ratio_pct': ratio_pct,
                'dispute_volume_ratio_pct': vol_ratio_pct
            })

        # Sort descending by ratio
        records.sort(key=lambda x: x['chargeback_to_transaction_ratio_pct'], reverse=True)
        return records

    def get_reason_distribution(self) -> List[Dict[str, Any]]:
        counts = self.df_cb['reason_category'].value_counts()
        vols = self.df_cb.groupby('reason_category')['disputed_amount'].sum()
        total_cbs = len(self.df_cb)

        records = []
        for reason, cnt in counts.items():
            records.append({
                'reason_category': reason,
                'count': int(cnt),
                'volume': round(float(vols.get(reason, 0.0)), 2),
                'percentage': round((cnt / total_cbs * 100), 2)
            })
        return records

    def get_severity_distribution(self) -> List[Dict[str, Any]]:
        counts = self.df_cb['severity'].value_counts()
        records = []
        for sev, cnt in counts.items():
            records.append({
                'severity': sev,
                'count': int(cnt),
                'percentage': round((cnt / len(self.df_cb) * 100), 2)
            })
        return records

    def get_channel_distribution(self) -> List[Dict[str, Any]]:
        counts = self.df_cb['channel'].value_counts()
        records = []
        for ch, cnt in counts.items():
            records.append({
                'channel': ch,
                'count': int(cnt),
                'percentage': round((cnt / len(self.df_cb) * 100), 2)
            })
        return records

    def get_resolution_distribution(self) -> List[Dict[str, Any]]:
        counts = self.df_cb['resolution_status'].value_counts()
        records = []
        for res, cnt in counts.items():
            records.append({
                'resolution_status': res,
                'count': int(cnt),
                'percentage': round((cnt / len(self.df_cb) * 100), 2)
            })
        return records

    def get_summary_kpis(self) -> Dict[str, Any]:
        total_txns = len(self.df_txns)
        total_vol = float(self.df_txns['amount'].abs().sum())
        successful_txns = int((self.df_txns['status'] == 'SUCCESS').sum())
        failed_txns = int((self.df_txns['status'] == 'FAILED').sum())
        pending_txns = int((self.df_txns['status'] == 'PENDING').sum())

        total_cbs = len(self.df_cb)
        total_cb_vol = float(self.df_cb['disputed_amount'].sum())
        overall_cb_ratio = round((total_cbs / total_txns * 100), 2) if total_txns > 0 else 0.0

        avg_delay = float(self.df_cb['reporting_delay_days'].dropna().mean())

        return {
            'total_transactions': total_txns,
            'total_volume': round(total_vol, 2),
            'avg_ticket_size': round(total_vol / total_txns, 2) if total_txns > 0 else 0.0,
            'successful_transactions': successful_txns,
            'success_rate_pct': round((successful_txns / total_txns * 100), 2) if total_txns > 0 else 0.0,
            'failed_transactions': failed_txns,
            'failure_rate_pct': round((failed_txns / total_txns * 100), 2) if total_txns > 0 else 0.0,
            'pending_transactions': pending_txns,
            'pending_rate_pct': round((pending_txns / total_txns * 100), 2) if total_txns > 0 else 0.0,
            'total_chargebacks': total_cbs,
            'total_disputed_volume': round(total_cb_vol, 2),
            'chargeback_ratio_pct': overall_cb_ratio,
            'avg_reporting_delay_days': round(avg_delay, 1)
        }
