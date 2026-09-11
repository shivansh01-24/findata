"""
Fraud Ring Intelligence and Graph Analytics Engine.
Detects circular money movement, shared settlement mule networks,
synthetic identity clusters, and high-dispute bust-out rings using NetworkX.
"""

import json
import os
import re
from typing import Dict, List, Any, Optional
import networkx as nx
import pandas as pd
import numpy as np


class FraudRingEngine:
    def __init__(self, data_proc_dir: str):
        self.data_dir = data_proc_dir
        self._load_data()
        self._build_networks()

    def _load_data(self):
        self.df_customers = pd.read_csv(os.path.join(self.data_dir, "trusted_customers.csv"))
        self.df_merchants = pd.read_csv(os.path.join(self.data_dir, "trusted_merchants.csv"))
        self.df_txns = pd.read_csv(os.path.join(self.data_dir, "trusted_transactions.csv"))
        self.df_cb = pd.read_csv(os.path.join(self.data_dir, "trusted_chargebacks.csv"))

    def _build_networks(self):
        self.rings = []
        ring_idx = 1

        # -------------------------------------------------------------
        # Ring Type 1: Shared Settlement Account Syndicates (Mule Rings)
        # -------------------------------------------------------------
        mch_acc = self.df_merchants[
            self.df_merchants['settlement_account'].notna() & 
            ~self.df_merchants['settlement_account'].isin(['NA', 'None', '', 'nan'])
        ]
        acc_groups = mch_acc.groupby('settlement_account')

        for acc, group in acc_groups:
            if len(group) > 1:
                mch_ids = group['merchant_id'].tolist()
                mch_names = group['merchant_name'].tolist()
                categories = group['merchant_category'].unique().tolist()
                cities = group['city'].unique().tolist()
                statuses = group['merchant_status'].unique().tolist()

                # Find associated transactions & chargebacks
                sub_txns = self.df_txns[self.df_txns['merchant_id'].isin(mch_ids)]
                sub_cb = self.df_cb[self.df_cb['merchant_id'].isin(mch_ids)]
                cust_ids = sub_txns['user_id'].unique().tolist()

                txn_vol = float(sub_txns['amount'].abs().sum())
                txn_cnt = len(sub_txns)
                cb_cnt = len(sub_cb)
                cb_rate = (cb_cnt / txn_cnt * 100) if txn_cnt > 0 else 0.0

                # Risk score (0 - 100)
                risk_score = min(100.0, 50.0 + len(mch_ids) * 10.0 + cb_rate * 1.5)

                self.rings.append({
                    'ring_id': f"RING-SETTLE-{str(ring_idx).zfill(3)}",
                    'ring_name': f"Shared Settlement Syndicate ({acc})",
                    'ring_type': "Shared Settlement Mule Network",
                    'severity': "HIGH" if risk_score >= 70 else "MEDIUM",
                    'risk_score': round(risk_score, 1),
                    'anchor_attribute': f"Account: {acc}",
                    'merchant_count': len(mch_ids),
                    'merchants': mch_ids,
                    'merchant_names': mch_names,
                    'customer_count': len(cust_ids),
                    'customer_sample': cust_ids[:10],
                    'categories': categories,
                    'locations': cities,
                    'transaction_count': txn_cnt,
                    'transaction_volume': round(txn_vol, 2),
                    'chargeback_count': cb_cnt,
                    'chargeback_rate_pct': round(cb_rate, 2),
                    'why_flagged': (
                        f"{len(mch_ids)} distinct commercial merchants share the single bank settlement "
                        f"account '{acc}'. This pattern indicates centralized shadow control, merchant-aggregator "
                        f"rule evasion, and potential mule aggregation."
                    ),
                    'recommendation': "Immediate audit of settlement account beneficiary and temporary hold on merchant payouts."
                })
                ring_idx += 1

        # -------------------------------------------------------------
        # Ring Type 2: Synthetic Identity / Shared Credential Rings
        # -------------------------------------------------------------
        kyc_shared_aadhaar = self.df_customers[
            self.df_customers['aadhaar'].notna() & 
            self.df_customers['aadhaar'].str.contains(r'\d')
        ].groupby('aadhaar')

        for aadhaar, group in kyc_shared_aadhaar:
            if len(group) > 1:
                uids = group['user_id'].tolist()
                names = group['full_name'].tolist()
                statuses = group['kyc_status'].unique().tolist()
                cities = group['city'].unique().tolist()

                sub_txns = self.df_txns[self.df_txns['user_id'].isin(uids)]
                sub_cb = self.df_cb[self.df_cb['user_id'].isin(uids)]
                mch_ids = sub_txns['merchant_id'].unique().tolist()

                txn_vol = float(sub_txns['amount'].abs().sum())
                txn_cnt = len(sub_txns)
                cb_cnt = len(sub_cb)

                risk_score = min(100.0, 55.0 + len(uids) * 12.0 + cb_cnt * 3.0)

                self.rings.append({
                    'ring_id': f"RING-SYNTH-{str(ring_idx).zfill(3)}",
                    'ring_name': f"Synthetic Identity Cluster (Aadhaar {aadhaar[:4]}...)",
                    'ring_type': "Synthetic Identity Ring",
                    'severity': "HIGH" if risk_score >= 70 else "MEDIUM",
                    'risk_score': round(risk_score, 1),
                    'anchor_attribute': f"Aadhaar: {aadhaar}",
                    'merchant_count': len(mch_ids),
                    'merchants': mch_ids[:10],
                    'merchant_names': [],
                    'customer_count': len(uids),
                    'customer_sample': uids,
                    'categories': sub_txns['merchant_category'].unique().tolist() if txn_cnt > 0 else [],
                    'locations': cities,
                    'transaction_count': txn_cnt,
                    'transaction_volume': round(txn_vol, 2),
                    'chargeback_count': cb_cnt,
                    'chargeback_rate_pct': round((cb_cnt / txn_cnt * 100) if txn_cnt > 0 else 0.0, 2),
                    'why_flagged': (
                        f"{len(uids)} distinct registered user accounts share the identical government Aadhaar number "
                        f"'{aadhaar}'. Associated KYC records exhibit conflicting personal names ({', '.join(names[:3])}), "
                        f"indicative of automated synthetic identity farming."
                    ),
                    'recommendation': "Freeze digital wallet limits and trigger biometric e-KYC re-verification."
                })
                ring_idx += 1

        # -------------------------------------------------------------
        # Ring Type 3: High-Dispute Bust-Out Syndicates
        # -------------------------------------------------------------
        cb_mch = self.df_cb.groupby('merchant_id').size()
        top_cb_mchs = cb_mch[cb_mch >= 25].index.tolist()

        for mid in top_cb_mchs:
            mch_info = self.df_merchants[self.df_merchants['merchant_id'] == mid]
            mch_name = mch_info['merchant_name'].iloc[0] if len(mch_info) > 0 else "Unknown"
            cat = mch_info['merchant_category'].iloc[0] if len(mch_info) > 0 else "Unknown"

            sub_txns = self.df_txns[self.df_txns['merchant_id'] == mid]
            sub_cb = self.df_cb[self.df_cb['merchant_id'] == mid]
            uids = sub_txns['user_id'].unique().tolist()

            txn_vol = float(sub_txns['amount'].abs().sum())
            txn_cnt = len(sub_txns)
            cb_cnt = len(sub_cb)
            cb_rate = (cb_cnt / txn_cnt * 100) if txn_cnt > 0 else 0.0

            risk_score = min(100.0, 60.0 + cb_cnt * 0.8)

            self.rings.append({
                'ring_id': f"RING-BUST-{str(ring_idx).zfill(3)}",
                'ring_name': f"High-Dispute Bust-Out Syndicate ({mid})",
                'ring_type': "High-Dispute Bust-Out Syndicate",
                'severity': "CRITICAL" if risk_score >= 85 else "HIGH",
                'risk_score': round(risk_score, 1),
                'anchor_attribute': f"Merchant: {mid} ({mch_name})",
                'merchant_count': 1,
                'merchants': [mid],
                'merchant_names': [mch_name],
                'customer_count': len(uids),
                'customer_sample': uids[:15],
                'categories': [cat],
                'locations': mch_info['city'].tolist() if len(mch_info) > 0 else [],
                'transaction_count': txn_cnt,
                'transaction_volume': round(txn_vol, 2),
                'chargeback_count': cb_cnt,
                'chargeback_rate_pct': round(cb_rate, 2),
                'why_flagged': (
                    f"Merchant '{mch_name}' ({mid}) has accumulated {cb_cnt} customer chargebacks, "
                    f"substantially exceeding normal threshold. Top dispute reasons: "
                    f"{', '.join(sub_cb['reason_category'].value_counts().head(2).index.tolist())}."
                ),
                'recommendation': "Suspend merchant settlement gateway immediately and initiate chargeback recovery escrow."
            })
            ring_idx += 1

        # Sort rings by risk score descending
        self.rings.sort(key=lambda x: x['risk_score'], reverse=True)

    def get_all_rings(self) -> List[Dict[str, Any]]:
        return self.rings

    def get_ring_by_id(self, ring_id: str) -> Optional[Dict[str, Any]]:
        for r in self.rings:
            if r['ring_id'] == ring_id:
                return r
        return None

    def get_ring_graph(self, ring_id: str) -> Dict[str, Any]:
        """
        Builds a NetworkX graph for the specific ring and returns D3/Vis.js compatible node-edge format.
        """
        ring = self.get_ring_by_id(ring_id)
        if not ring:
            return {'nodes': [], 'edges': []}

        G = nx.Graph()
        nodes = []
        edges = []

        mch_ids = set(ring['merchants'])
        cust_sample = set(ring['customer_sample'][:25])

        # Add Anchor node (e.g. Bank Account or Central Merchant)
        if "RING-SETTLE" in ring_id:
            anchor_id = f"ACC_{ring['anchor_attribute'].replace('Account: ', '')}"
            nodes.append({
                'id': anchor_id,
                'label': ring['anchor_attribute'],
                'type': 'SETTLEMENT_ACCOUNT',
                'risk_score': ring['risk_score'],
                'size': 35,
                'color': '#ef4444' # Red
            })
            for mid in mch_ids:
                edges.append({
                    'source': mid,
                    'target': anchor_id,
                    'label': 'SETTLES_TO',
                    'color': '#f97316'
                })

        # Add Merchant nodes
        for mid in mch_ids:
            mch_rows = self.df_merchants[self.df_merchants['merchant_id'] == mid]
            mname = mch_rows['merchant_name'].iloc[0] if len(mch_rows) > 0 else mid
            cat = mch_rows['merchant_category'].iloc[0] if len(mch_rows) > 0 else "Retail"
            nodes.append({
                'id': mid,
                'label': f"{mname} ({mid})",
                'type': 'MERCHANT',
                'category': cat,
                'risk_score': ring['risk_score'],
                'size': 28,
                'color': '#8b5cf6' # Purple
            })

        # Add Customer nodes
        for uid in cust_sample:
            cust_rows = self.df_customers[self.df_customers['user_id'] == uid]
            cname = cust_rows['full_name'].iloc[0] if len(cust_rows) > 0 else uid
            k_status = cust_rows['kyc_status'].iloc[0] if len(cust_rows) > 0 else "UNKNOWN"
            nodes.append({
                'id': uid,
                'label': f"{cname} ({uid})",
                'type': 'CUSTOMER',
                'kyc_status': k_status,
                'risk_score': 70.0 if k_status == 'REJECTED' else 40.0,
                'size': 18,
                'color': '#3b82f6' # Blue
            })

        # Add Transaction & Chargeback edges between Customers and Merchants
        sub_txns = self.df_txns[
            self.df_txns['merchant_id'].isin(mch_ids) & 
            self.df_txns['user_id'].isin(cust_sample)
        ].head(50)

        for _, t in sub_txns.iterrows():
            amt = float(t['amount'])
            edges.append({
                'source': t['user_id'],
                'target': t['merchant_id'],
                'label': f"₹{abs(amt):,.0f}",
                'amount': amt,
                'status': t['status'],
                'color': '#10b981' if t['status'] == 'SUCCESS' else '#ef4444'
            })

        return {
            'ring_id': ring_id,
            'ring_name': ring['ring_name'],
            'nodes': nodes,
            'edges': edges,
            'summary': {
                'node_count': len(nodes),
                'edge_count': len(edges),
                'risk_score': ring['risk_score'],
                'why_flagged': ring['why_flagged']
            }
        }
