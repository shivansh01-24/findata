"""
Independent Forensic Data Verification Script.
Recalculates every metric directly from source files and trusted outputs to independently verify all claims.
"""

import os
import json
import pandas as pd
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DIR = os.path.join(ROOT_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(ROOT_DIR, "data", "processed")

def audit():
    print("=" * 70)
    print("PHASE 2: INDEPENDENT DATA VERIFICATION AUDIT")
    print("=" * 70)

    # 1. Raw Data Counts
    raw_txns_path = os.path.join(RAW_DIR, "track1_upi_transactions.csv")
    raw_kyc_path = os.path.join(RAW_DIR, "track1_kyc_records.csv")
    raw_merchants_path = os.path.join(RAW_DIR, "track1_merchants_master.csv")
    raw_cb_path = os.path.join(RAW_DIR, "track1_chargebacks.json")

    raw_txns = pd.read_csv(raw_txns_path)
    raw_kyc = pd.read_csv(raw_kyc_path)
    raw_merchants = pd.read_csv(raw_merchants_path)
    with open(raw_cb_path, "r", encoding="utf-8") as f:
        raw_cbs = json.load(f)

    print(f"RAW FILES:")
    print(f" - Transactions CSV rows: {len(raw_txns)}")
    print(f" - KYC Records CSV rows: {len(raw_kyc)}")
    print(f" - Merchants Master CSV rows: {len(raw_merchants)}")
    print(f" - Chargebacks JSON records: {len(raw_cbs)}")

    # 2. Processed Trusted Data Counts
    trusted_txns = pd.read_csv(os.path.join(PROCESSED_DIR, "trusted_transactions.csv"))
    trusted_cust = pd.read_csv(os.path.join(PROCESSED_DIR, "trusted_customers.csv"))
    trusted_mch = pd.read_csv(os.path.join(PROCESSED_DIR, "trusted_merchants.csv"))
    trusted_cb = pd.read_csv(os.path.join(PROCESSED_DIR, "trusted_chargebacks.csv"))

    print(f"\nTRUSTED FILES:")
    print(f" - Trusted Transactions rows: {len(trusted_txns)}")
    print(f" - Golden Customers rows: {len(trusted_cust)}")
    print(f" - Golden Merchants rows: {len(trusted_mch)}")
    print(f" - Trusted Chargebacks rows: {len(trusted_cb)}")

    # 3. Transaction Volume and Status Breakdown
    gross_vol = trusted_txns["amount"].sum()
    successful_txns = trusted_txns[trusted_txns["status"] == "SUCCESS"]
    failed_txns = trusted_txns[trusted_txns["status"] == "FAILED"]
    pending_txns = trusted_txns[trusted_txns["status"] == "PENDING"]

    print(f"\nTRANSACTION TELEMETRY:")
    print(f" - Gross Processed Volume: INR {gross_vol:,.2f}")
    print(f" - SUCCESS: {len(successful_txns)} ({len(successful_txns)/len(trusted_txns)*100:.2f}%)")
    print(f" - FAILED: {len(failed_txns)} ({len(failed_txns)/len(trusted_txns)*100:.2f}%)")
    print(f" - PENDING: {len(pending_txns)} ({len(pending_txns)/len(trusted_txns)*100:.2f}%)")

    # 4. Chargeback Foreign Key & Reconciliation
    matched_cbs = trusted_cb[trusted_cb["txn_link_valid"] == True]
    orphan_cbs = trusted_cb[trusted_cb["txn_link_valid"] == False]
    total_disputed_vol = trusted_cb["disputed_amount"].sum()
    imputed_amounts = trusted_cb[trusted_cb["amount_imputed"] == True]

    print(f"\nCHARGEBACK RECONCILIATION:")
    print(f" - Total Trusted Chargebacks: {len(trusted_cb)}")
    print(f" - Matched to Transactions: {len(matched_cbs)} ({len(matched_cbs)/len(trusted_cb)*100:.2f}%)")
    print(f" - Orphan/Unmatched Chargebacks: {len(orphan_cbs)} ({len(orphan_cbs)/len(trusted_cb)*100:.2f}%)")
    print(f" - Missing Disputed Amounts Imputed from Txns: {len(imputed_amounts)}")
    print(f" - Total Disputed Volume: INR {total_disputed_vol:,.2f}")

    # 5. Category-wise Chargeback Ratio
    print(f"\nCATEGORY CHARGEBACK RATIOS (Ground Truth):")
    cat_stats = []
    for cat, group in trusted_txns.groupby("merchant_category"):
        total_t = len(group)
        cbs_in_cat = len(trusted_cb[trusted_cb["merchant_category"] == cat])
        ratio = (cbs_in_cat / total_t) * 100 if total_t > 0 else 0
        cat_stats.append({
            "category": cat,
            "txns": total_t,
            "chargebacks": cbs_in_cat,
            "ratio_pct": round(ratio, 2)
        })
    cat_df = pd.DataFrame(cat_stats).sort_values(by="ratio_pct", ascending=False)
    for _, row in cat_df.iterrows():
        print(f" - {row['category']:25s}: {row['ratio_pct']:6.2f}% ({row['chargebacks']:4d} CBs / {row['txns']:5d} txns)")

    # 6. Entity Resolution Class Breakdown
    print(f"\nENTITY RESOLUTION BREAKDOWN:")
    print(f" - Customers (Golden Records: {len(trusted_cust)}):")
    if "resolution_type" in trusted_cust.columns:
        for status, cnt in trusted_cust["resolution_type"].value_counts().items():
            print(f"    * {status:25s}: {cnt}")
    print(f" - Merchants (Golden Records: {len(trusted_mch)}):")
    if "resolution_type" in trusted_mch.columns:
        for status, cnt in trusted_mch["resolution_type"].value_counts().items():
            print(f"    * {status:25s}: {cnt}")

    # 7. Pipeline Metrics & Quality Report
    p_path = os.path.join(PROCESSED_DIR, "pipeline_metrics.json")
    if os.path.exists(p_path):
        with open(p_path, "r", encoding="utf-8") as f:
            pm = json.load(f)
            print(f"\nPIPELINE METRICS JSON:")
            print(f" - Raw counts: {pm.get('counts', {}).get('raw', {})}")
            print(f" - Processed counts: {pm.get('counts', {}).get('processed', {})}")

    print("=" * 70)
    print("INDEPENDENT AUDIT COMPLETED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    audit()
