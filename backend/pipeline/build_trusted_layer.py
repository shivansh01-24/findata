"""
Pipeline Orchestrator: Builds the Trusted Analytical Layer.
Executes raw profiling, data rescue, entity resolution, and relationship validation.
Saves trusted tables and audit trails to data/processed/.
"""

import json
import os
import sys
import pandas as pd
import numpy as np

# Ensure project root is in python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.pipeline.data_profiler import profile_raw_dataset, generate_markdown_report
from backend.pipeline.entity_resolution import (
    resolve_customer_entities,
    resolve_merchant_entities,
    validate_and_link_transactions,
    validate_and_link_chargebacks
)

DATA_RAW_DIR = os.path.join(ROOT_DIR, "data", "raw")
DATA_PROC_DIR = os.path.join(ROOT_DIR, "data", "processed")


def run_pipeline():
    print("=" * 70)
    print("STARTING DATA RESCUE & TRUSTED ANALYTICS PIPELINE")
    print("=" * 70)
    
    os.makedirs(DATA_PROC_DIR, exist_ok=True)
    
    # Step 1: Forensic Profiling of Raw Data
    print("\n[Step 1/5] Profiling Raw Data...")
    raw_profile = profile_raw_dataset(DATA_RAW_DIR)
    
    profile_json_path = os.path.join(DATA_PROC_DIR, "data_quality_report.json")
    with open(profile_json_path, 'w', encoding='utf-8') as f:
        json.dump(raw_profile, f, indent=2)
        
    report_md_path = os.path.join(ROOT_DIR, "DATA_QUALITY_REPORT.md")
    generate_markdown_report(raw_profile, report_md_path)
    print(f" -> Profiling report saved to {report_md_path}")
    
    # Step 2: Load Raw Files
    print("\n[Step 2/5] Loading Raw Data Files...")
    df_upi_raw = pd.read_csv(os.path.join(DATA_RAW_DIR, "track1_upi_transactions.csv"), dtype=str)
    df_kyc_raw = pd.read_csv(os.path.join(DATA_RAW_DIR, "track1_kyc_records.csv"), dtype=str)
    df_mch_raw = pd.read_csv(os.path.join(DATA_RAW_DIR, "track1_merchants_master.csv"), dtype=str)
    with open(os.path.join(DATA_RAW_DIR, "track1_chargebacks.json"), 'r', encoding='utf-8') as f:
        df_cb_raw = pd.DataFrame(json.load(f))
        
    print(f" -> Raw counts: UPI={len(df_upi_raw)}, KYC={len(df_kyc_raw)}, Merchants={len(df_mch_raw)}, CB={len(df_cb_raw)}")
    
    # Step 3: Entity Resolution on Customers & Merchants
    print("\n[Step 3/5] Resolving Customer & Merchant Entities...")
    df_customers, df_cust_audit = resolve_customer_entities(df_kyc_raw)
    print(f" -> Rescued {len(df_customers)} golden customer records from {len(df_kyc_raw)} raw rows")
    print(f"    (Resolution breakdown: {df_customers['resolution_type'].value_counts().to_dict()})")
    
    df_merchants, df_mch_audit = resolve_merchant_entities(df_mch_raw)
    print(f" -> Rescued {len(df_merchants)} golden merchant records from {len(df_mch_raw)} raw rows")
    print(f"    (Resolution breakdown: {df_merchants['resolution_type'].value_counts().to_dict()})")
    
    # Step 4: Validate and Link Transactions
    print("\n[Step 4/5] Validating & Linking Transactions...")
    df_txns, txn_audit = validate_and_link_transactions(df_upi_raw, df_merchants, df_customers)
    print(f" -> Retained {len(df_txns)} transactions from {len(df_upi_raw)} raw rows")
    print(f"    (Customer FK valid: {df_txns['customer_fk_valid'].sum()} | Merchant FK valid: {df_txns['merchant_fk_valid'].sum()})")
    
    # Step 5: Validate and Link Chargebacks
    print("\n[Step 5/5] Validating & Linking Chargebacks...")
    df_cb, cb_audit = validate_and_link_chargebacks(df_cb_raw, df_txns, df_merchants, df_customers)
    print(f" -> Retained {len(df_cb)} chargebacks from {len(df_cb_raw)} raw rows")
    print(f"    (Linked to UPI: {df_cb['txn_link_valid'].sum()} | Imputed amounts: {df_cb['amount_imputed'].sum()})")
    
    # Save Trusted Datasets
    print("\nSaving Trusted Datasets to data/processed/...")
    
    df_customers.to_csv(os.path.join(DATA_PROC_DIR, "trusted_customers.csv"), index=False)
    df_customers.to_json(os.path.join(DATA_PROC_DIR, "trusted_customers.json"), orient='records', indent=2)
    
    df_merchants.to_csv(os.path.join(DATA_PROC_DIR, "trusted_merchants.csv"), index=False)
    df_merchants.to_json(os.path.join(DATA_PROC_DIR, "trusted_merchants.json"), orient='records', indent=2)
    
    df_txns.to_csv(os.path.join(DATA_PROC_DIR, "trusted_transactions.csv"), index=False)
    # Save a subset or partitioned json for fast API loading
    df_txns.to_json(os.path.join(DATA_PROC_DIR, "trusted_transactions.json"), orient='records')
    
    df_cb.to_csv(os.path.join(DATA_PROC_DIR, "trusted_chargebacks.csv"), index=False)
    df_cb.to_json(os.path.join(DATA_PROC_DIR, "trusted_chargebacks.json"), orient='records', indent=2)
    
    # Save pipeline metrics and audit summaries
    metrics = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'counts': {
            'raw_upi': len(df_upi_raw),
            'trusted_upi': len(df_txns),
            'raw_kyc': len(df_kyc_raw),
            'trusted_customers': len(df_customers),
            'raw_merchants': len(df_mch_raw),
            'trusted_merchants': len(df_merchants),
            'raw_chargebacks': len(df_cb_raw),
            'trusted_chargebacks': len(df_cb)
        },
        'customer_resolution': df_customers['resolution_type'].value_counts().to_dict(),
        'merchant_resolution': df_merchants['resolution_type'].value_counts().to_dict(),
        'transaction_status': df_txns['status'].value_counts().to_dict(),
        'chargeback_linkage': {
            'linked_to_upi': int(df_cb['txn_link_valid'].sum()),
            'orphan_chargebacks': int((~df_cb['txn_link_valid']).sum()),
            'amounts_imputed': int(df_cb['amount_imputed'].sum())
        }
    }
    
    with open(os.path.join(DATA_PROC_DIR, "pipeline_metrics.json"), 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
        
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"All trusted artifacts written to: {DATA_PROC_DIR}")
    print("=" * 70)
    return metrics


if __name__ == "__main__":
    run_pipeline()
