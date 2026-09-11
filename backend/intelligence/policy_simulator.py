"""
Risk Policy & Dynamic Threshold Simulator Engine.
Enables risk executives and datathon judges to simulate "what-if" policy changes
on chargeback rate caps, ticket size deviation multipliers, and mule aggregation rules.
Calculates prevented fraud volume, GMV at risk, and false positive metrics.
"""

import os
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np


class PolicySimulatorEngine:
    def __init__(self, data_proc_dir: str):
        self.data_dir = data_proc_dir
        self._build_merchant_profiles()

    def _build_merchant_profiles(self):
        df_merchants = pd.read_csv(os.path.join(self.data_dir, "trusted_merchants.csv"))
        df_txns = pd.read_csv(os.path.join(self.data_dir, "trusted_transactions.csv"))
        df_cb = pd.read_csv(os.path.join(self.data_dir, "trusted_chargebacks.csv"))

        # Aggregate transactions
        txn_stats = df_txns.groupby('merchant_id').agg(
            txn_count=('txn_id', 'count'),
            total_volume=('amount', lambda x: float(x.abs().sum())),
            avg_ticket=('amount', lambda x: float(x.abs().mean()))
        ).reset_index()

        # Aggregate chargebacks
        cb_stats = df_cb.groupby('merchant_id').agg(
            cb_count=('complaint_id', 'count'),
            cb_volume=('disputed_amount', lambda x: float(x.sum()))
        ).reset_index()

        # Merge onto merchants
        merged = df_merchants.merge(txn_stats, on='merchant_id', how='left')
        merged = merged.merge(cb_stats, on='merchant_id', how='left')

        merged['txn_count'] = merged['txn_count'].fillna(0).astype(int)
        merged['total_volume'] = merged['total_volume'].fillna(0.0).round(2)
        merged['avg_ticket'] = merged['avg_ticket'].fillna(0.0).round(2)
        merged['cb_count'] = merged['cb_count'].fillna(0).astype(int)
        merged['cb_volume'] = merged['cb_volume'].fillna(0.0).round(2)

        # Calculate chargeback rate (%)
        merged['cb_rate_pct'] = np.where(
            merged['txn_count'] > 0,
            (merged['cb_count'] / merged['txn_count'] * 100).round(2),
            0.0
        )

        # Calculate ticket size deviation ratio
        merged['declared_ticket'] = pd.to_numeric(merged['declared_avg_ticket_size'], errors='coerce').fillna(2000.0)
        merged['ticket_deviation_ratio'] = np.where(
            merged['declared_ticket'] > 0,
            (merged['avg_ticket'] / merged['declared_ticket']).round(2),
            1.0
        )

        # Settlement account sharing counts
        acc_counts = merged[
            merged['settlement_account'].notna() & 
            ~merged['settlement_account'].isin(['NA', 'None', '', 'nan'])
        ]['settlement_account'].value_counts().to_dict()
        merged['shared_acc_count'] = merged['settlement_account'].map(acc_counts).fillna(1).astype(int)

        self.df_profiles = merged

    def simulate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates policy changes.
        params:
          - chargeback_threshold_pct: float (default 20.0)
          - ticket_multiplier: float (default 2.0)
          - mule_sharing_threshold: int (default 2)
          - min_txns_evaluated: int (default 3)
        """
        sim_cb_thresh = float(params.get('chargeback_threshold_pct', 20.0))
        sim_ticket_mult = float(params.get('ticket_multiplier', 2.0))
        sim_mule_thresh = int(params.get('mule_sharing_threshold', 2))
        min_txns = int(params.get('min_txns_evaluated', 3))

        # Baseline Parameters (Status Quo)
        base_cb_thresh = 25.0
        base_ticket_mult = 2.5
        base_mule_thresh = 2

        df = self.df_profiles.copy()

        # Baseline Flag Criteria
        df['base_flag'] = (
            ((df['cb_rate_pct'] >= base_cb_thresh) & (df['txn_count'] >= min_txns)) |
            ((df['ticket_deviation_ratio'] >= base_ticket_mult) & (df['total_volume'] > 10000)) |
            (df['shared_acc_count'] >= base_mule_thresh)
        )

        # Simulated Flag Criteria
        df['sim_flag'] = (
            ((df['cb_rate_pct'] >= sim_cb_thresh) & (df['txn_count'] >= min_txns)) |
            ((df['ticket_deviation_ratio'] >= sim_ticket_mult) & (df['total_volume'] > 10000)) |
            (df['shared_acc_count'] >= sim_mule_thresh)
        )

        # Summary KPIs for Baseline
        base_flagged = df[df['base_flag']]
        base_count = len(base_flagged)
        base_gmv = float(base_flagged['total_volume'].sum())
        base_cb_vol = float(base_flagged['cb_volume'].sum())
        base_cb_cnt = int(base_flagged['cb_count'].sum())

        # Summary KPIs for Simulated
        sim_flagged = df[df['sim_flag']]
        sim_count = len(sim_flagged)
        sim_gmv = float(sim_flagged['total_volume'].sum())
        sim_cb_vol = float(sim_flagged['cb_volume'].sum())
        sim_cb_cnt = int(sim_flagged['cb_count'].sum())

        # Newly Flagged (incremental protection)
        newly_flagged = df[~df['base_flag'] & df['sim_flag']].sort_values('total_volume', ascending=False)
        unflagged = df[df['base_flag'] & ~df['sim_flag']].sort_values('total_volume', ascending=False)

        # Top affected sample for review
        new_sample = newly_flagged[[
            'merchant_id', 'merchant_name', 'merchant_category', 'city', 'state',
            'txn_count', 'total_volume', 'cb_count', 'cb_rate_pct', 'ticket_deviation_ratio',
            'shared_acc_count'
        ]].head(15).replace({np.nan: None}).to_dict(orient='records')

        total_cb_vol = float(df['cb_volume'].sum())
        capture_rate_pct = round(sim_cb_vol / total_cb_vol * 100, 2) if total_cb_vol > 0 else 0.0

        return {
            'parameters': {
                'simulated': {
                    'chargeback_threshold_pct': sim_cb_thresh,
                    'ticket_multiplier': sim_ticket_mult,
                    'mule_sharing_threshold': sim_mule_thresh,
                    'min_txns_evaluated': min_txns
                },
                'baseline': {
                    'chargeback_threshold_pct': base_cb_thresh,
                    'ticket_multiplier': base_ticket_mult,
                    'mule_sharing_threshold': base_mule_thresh,
                    'min_txns_evaluated': min_txns
                }
            },
            'baseline_metrics': {
                'flagged_merchants': base_count,
                'gmv_at_risk': round(base_gmv, 2),
                'chargebacks_captured': base_cb_cnt,
                'dispute_volume_contained': round(base_cb_vol, 2)
            },
            'simulated_metrics': {
                'flagged_merchants': sim_count,
                'gmv_at_risk': round(sim_gmv, 2),
                'chargebacks_captured': sim_cb_cnt,
                'dispute_volume_contained': round(sim_cb_vol, 2),
                'platform_capture_rate_pct': capture_rate_pct
            },
            'delta_impact': {
                'net_merchants_flagged': sim_count - base_count,
                'net_gmv_contained': round(sim_gmv - base_gmv, 2),
                'net_disputes_prevented': sim_cb_cnt - base_cb_cnt,
                'net_dispute_volume_saved': round(sim_cb_vol - base_cb_vol, 2)
            },
            'incremental_flagged_sample': new_sample,
            'recommendation': (
                f"Setting chargeback cap to {sim_cb_thresh}% and ticket multiplier to {sim_ticket_mult}x "
                f"captures ₹{sim_cb_vol:,.2f} in dispute volume ({capture_rate_pct}% of total platform chargebacks) "
                f"with a net change of {sim_count - base_count:+d} merchants requiring risk intervention."
            )
        }
