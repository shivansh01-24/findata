"""
Entity Resolution Engine.
Resolves duplicate and conflicting entities across Customers, Merchants, Transactions, and Chargebacks.
Preserves audit trails and produces golden records with confidence scoring.
"""

import re
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np

from backend.pipeline.standardizers import (
    normalize_user_id,
    normalize_merchant_id,
    normalize_txn_id,
    parse_amount,
    parse_timestamp,
    normalize_pan,
    normalize_aadhaar,
    normalize_kyc_status,
    normalize_risk_segment,
    normalize_mcc,
    normalize_merchant_category,
    normalize_merchant_status,
    normalize_txn_status,
    normalize_utr,
    normalize_dispute_reason,
    normalize_dispute_severity,
    normalize_resolution_status
)


def resolve_customer_entities(df_kyc: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs entity resolution on raw KYC records.
    Distinguishes:
      - SINGLETON
      - EXACT_DUPLICATE
      - FORMATTING_DUPLICATE
      - CONFLICTING_RECORD
    Returns:
      - golden_customers: DataFrame of resolved customer profiles
      - customer_audit_trail: DataFrame detailing resolution history & conflicts
    """
    df = df_kyc.copy()
    
    # 1. Normalize identifiers and core attributes for each row
    user_results = df['user_id'].apply(normalize_user_id)
    df['canonical_user_id'] = [r[0] for r in user_results]
    df['user_id_flag'] = [r[1] for r in user_results]
    
    pan_results = df['pan'].apply(normalize_pan)
    df['canonical_pan'] = [r[0] for r in pan_results]
    df['pan_flag'] = [r[1] for r in pan_results]
    
    aadhaar_results = df['aadhaar'].apply(normalize_aadhaar)
    df['canonical_aadhaar'] = [r[0] for r in aadhaar_results]
    df['aadhaar_flag'] = [r[1] for r in aadhaar_results]
    
    kyc_results = df['kyc_status'].apply(normalize_kyc_status)
    df['canonical_kyc_status'] = [r[0] for r in kyc_results]
    
    risk_results = df['risk_segment'].apply(normalize_risk_segment)
    df['canonical_risk_segment'] = [r[0] for r in risk_results]
    
    income_results = df['monthly_income'].apply(parse_amount)
    df['canonical_monthly_income'] = [abs(r[0]) if r[0] is not None else np.nan for r in income_results]
    
    signup_results = df['signup_timestamp'].apply(parse_timestamp)
    df['canonical_signup_ts'] = [r[0] for r in signup_results]
    
    golden_records = []
    audit_records = []
    
    grouped = df.groupby('canonical_user_id', dropna=False)
    
    for uid, group in grouped:
        if pd.isna(uid) or uid is None:
            # Handle records without valid user id
            for idx, row in group.iterrows():
                audit_records.append({
                    'raw_user_id': row['user_id'],
                    'canonical_user_id': None,
                    'resolution_type': 'UNRESOLVED_MISSING_ID',
                    'conflict_details': 'Record has no extractable user ID',
                    'confidence': 0.0
                })
            continue
            
        group_len = len(group)
        
        if group_len == 1:
            row = group.iloc[0]
            res_type = 'SINGLETON'
            confidence = 1.0
            conflict_details = 'No duplicate records found'
            best_row = row
        else:
            # Check for exact duplicate rows
            unique_rows = group.drop_duplicates(subset=[c for c in group.columns if not c.startswith('canonical_')])
            if len(unique_rows) == 1:
                res_type = 'EXACT_DUPLICATE'
                confidence = 1.0
                conflict_details = f'{group_len} identical duplicate rows consolidated'
                best_row = group.iloc[0]
            else:
                # Check substantive conflicts (divergent PAN, Aadhaar, KYC status)
                unique_pans = group['canonical_pan'].dropna().unique()
                unique_aadhaar = group['canonical_aadhaar'].dropna().unique()
                unique_statuses = group['canonical_kyc_status'].unique()
                unique_names = group['full_name'].str.strip().str.title().unique()
                
                conflicts = []
                if len(unique_pans) > 1:
                    conflicts.append(f"Conflicting PANs: {list(unique_pans)}")
                if len(unique_aadhaar) > 1:
                    conflicts.append(f"Conflicting Aadhaars: {list(unique_aadhaar)}")
                if len(unique_statuses) > 1:
                    conflicts.append(f"Conflicting KYC Statuses: {list(unique_statuses)}")
                if len(unique_names) > 1:
                    conflicts.append(f"Conflicting Names: {list(unique_names)}")
                    
                if conflicts:
                    res_type = 'CONFLICTING_RECORD'
                    confidence = 0.50
                    conflict_details = "; ".join(conflicts)
                else:
                    res_type = 'FORMATTING_DUPLICATE'
                    confidence = 0.85
                    conflict_details = f'{group_len} records with formatting/casing variations consolidated'
                    
                # Pick best golden record using priority hierarchy:
                # 1. VERIFIED > PENDING > REJECTED
                # 2. Has valid PAN & Aadhaar
                # 3. Valid monthly income
                def record_score(r):
                    score = 0
                    if r['canonical_kyc_status'] == 'VERIFIED': score += 10
                    elif r['canonical_kyc_status'] == 'PENDING': score += 5
                    if r['pan_flag'] == 'VALID_PAN': score += 4
                    if r['aadhaar_flag'] in ('VALID_12_DIGIT_AADHAAR', 'MASKED_AADHAAR'): score += 3
                    if pd.notna(r['canonical_monthly_income']) and r['canonical_monthly_income'] > 0: score += 2
                    if pd.notna(r['canonical_signup_ts']): score += 1
                    return score
                    
                scores = [record_score(r) for _, r in group.iterrows()]
                best_idx = np.argmax(scores)
                best_row = group.iloc[best_idx]
                
        # Create golden record
        golden_records.append({
            'user_id': uid,
            'full_name': str(best_row['full_name']).strip().title(),
            'pan': best_row['canonical_pan'],
            'pan_flag': best_row['pan_flag'],
            'aadhaar': best_row['canonical_aadhaar'],
            'aadhaar_flag': best_row['aadhaar_flag'],
            'city': str(best_row['city']).strip().title(),
            'state': str(best_row['state']).strip().title(),
            'occupation': str(best_row['occupation']).strip().title(),
            'monthly_income': best_row['canonical_monthly_income'],
            'signup_timestamp': best_row['canonical_signup_ts'],
            'kyc_status': best_row['canonical_kyc_status'],
            'risk_segment': best_row['canonical_risk_segment'],
            'resolution_type': res_type,
            'resolution_confidence': confidence,
            'raw_record_count': group_len,
            'conflict_details': conflict_details
        })
        
        audit_records.append({
            'canonical_user_id': uid,
            'raw_records_merged': group_len,
            'resolution_type': res_type,
            'confidence': confidence,
            'conflict_details': conflict_details
        })
        
    df_golden = pd.DataFrame(golden_records)
    df_audit = pd.DataFrame(audit_records)
    return df_golden, df_audit


def resolve_merchant_entities(df_merchants: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs entity resolution on raw Merchants Master records.
    Distinguishes:
      - SINGLETON
      - EXACT_DUPLICATE
      - FORMATTING_DUPLICATE
      - CONFLICTING_MERCHANT_RECORD
    """
    df = df_merchants.copy()
    
    mch_results = df['merchant_id'].apply(normalize_merchant_id)
    df['canonical_merchant_id'] = [r[0] for r in mch_results]
    
    mcc_results = df['mcc'].apply(normalize_mcc)
    df['canonical_mcc'] = [r[0] for r in mcc_results]
    
    status_results = df['merchant_status'].apply(normalize_merchant_status)
    df['canonical_status'] = [r[0] for r in status_results]
    
    ticket_results = df['declared_avg_ticket_size'].apply(parse_amount)
    df['canonical_ticket_size'] = [abs(r[0]) if r[0] is not None else np.nan for r in ticket_results]
    
    date_results = df['onboarding_date'].apply(parse_timestamp)
    df['canonical_onboarding'] = [r[0] for r in date_results]
    
    golden_records = []
    audit_records = []
    
    grouped = df.groupby('canonical_merchant_id', dropna=False)
    
    for mid, group in grouped:
        if pd.isna(mid) or mid is None:
            continue
            
        group_len = len(group)
        if group_len == 1:
            row = group.iloc[0]
            res_type = 'SINGLETON'
            confidence = 1.0
            conflict_details = 'No duplicates'
            best_row = row
        else:
            unique_rows = group.drop_duplicates(subset=[c for c in group.columns if not c.startswith('canonical_')])
            if len(unique_rows) == 1:
                res_type = 'EXACT_DUPLICATE'
                confidence = 1.0
                conflict_details = f'{group_len} identical rows consolidated'
                best_row = group.iloc[0]
            else:
                unique_names = group['merchant_name'].str.strip().str.title().unique()
                unique_cats = group['merchant_category'].str.strip().str.title().unique()
                unique_cities = group['city'].str.strip().str.title().unique()
                
                conflicts = []
                if len(unique_names) > 1:
                    conflicts.append(f"Conflicting Names: {list(unique_names)}")
                if len(unique_cats) > 1:
                    conflicts.append(f"Conflicting Categories: {list(unique_cats)}")
                if len(unique_cities) > 1:
                    conflicts.append(f"Conflicting Cities: {list(unique_cities)}")
                    
                if conflicts:
                    res_type = 'CONFLICTING_MERCHANT_RECORD'
                    confidence = 0.55
                    conflict_details = "; ".join(conflicts)
                else:
                    res_type = 'FORMATTING_DUPLICATE'
                    confidence = 0.85
                    conflict_details = f'{group_len} records with formatting variations consolidated'
                    
                # Pick best record:
                # 1. Has valid settlement account
                # 2. ACTIVE status
                # 3. Has declared ticket size
                def mch_score(r):
                    score = 0
                    settle = str(r['settlement_account']).strip()
                    if settle and settle not in ('NA', 'None', 'nan'): score += 5
                    if r['canonical_status'] == 'ACTIVE': score += 4
                    if pd.notna(r['canonical_ticket_size']): score += 2
                    if pd.notna(r['canonical_mcc']): score += 2
                    return score
                    
                scores = [mch_score(r) for _, r in group.iterrows()]
                best_idx = np.argmax(scores)
                best_row = group.iloc[best_idx]
                
        # Canonical category
        category, cat_flag = normalize_merchant_category(
            best_row['merchant_category'], 
            mcc=best_row['canonical_mcc']
        )
        
        # Settlement account
        settle_acc = str(best_row['settlement_account']).strip()
        if not settle_acc or settle_acc in ('NA', 'None', 'nan'):
            settle_acc = None
            
        golden_records.append({
            'merchant_id': mid,
            'merchant_name': str(best_row['merchant_name']).strip().title(),
            'mcc': best_row['canonical_mcc'],
            'merchant_category': category,
            'business_type': str(best_row['business_type']).strip().title(),
            'city': str(best_row['city']).strip().title(),
            'state': str(best_row['state']).strip().title(),
            'onboarding_date': best_row['canonical_onboarding'],
            'settlement_account': settle_acc,
            'merchant_status': best_row['canonical_status'],
            'declared_avg_ticket_size': best_row['canonical_ticket_size'],
            'resolution_type': res_type,
            'resolution_confidence': confidence,
            'raw_record_count': group_len,
            'conflict_details': conflict_details
        })
        
        audit_records.append({
            'canonical_merchant_id': mid,
            'raw_records_merged': group_len,
            'resolution_type': res_type,
            'confidence': confidence,
            'conflict_details': conflict_details
        })
        
    df_golden = pd.DataFrame(golden_records)
    df_audit = pd.DataFrame(audit_records)
    return df_golden, df_audit


def validate_and_link_transactions(
    df_upi: pd.DataFrame, 
    df_merchants: pd.DataFrame, 
    df_customers: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Standardizes UPI transactions, validates foreign keys against golden masters,
    and classifies amounts, timestamps, and statuses.
    """
    df = df_upi.copy()
    
    # 1. Deduplicate exact duplicate raw rows while logging audit
    exact_dup_mask = df.duplicated()
    exact_dup_count = exact_dup_mask.sum()
    df = df.drop_duplicates().copy()
    
    # Standardize IDs
    txn_res = df['txn_id'].apply(normalize_txn_id)
    df['canonical_txn_id'] = [r[0] for r in txn_res]
    
    usr_res = df['user_id'].apply(normalize_user_id)
    df['canonical_user_id'] = [r[0] for r in usr_res]
    
    mch_res = df['merchant_id'].apply(normalize_merchant_id)
    df['canonical_merchant_id'] = [r[0] for r in mch_res]
    
    # Standardize amounts
    amt_res = df['amount'].apply(parse_amount)
    df['canonical_amount'] = [r[0] for r in amt_res]
    df['amount_flag'] = [r[1] for r in amt_res]
    
    # Standardize timestamps
    ts_res = df['timestamp'].apply(parse_timestamp)
    df['canonical_timestamp'] = [r[0] for r in ts_res]
    df['timestamp_flag'] = [r[1] for r in ts_res]
    
    # Standardize status
    status_res = df['status'].apply(normalize_txn_status)
    df['canonical_status'] = [r[0] for r in status_res]
    
    # Standardize UTR
    utr_res = df['utr'].apply(normalize_utr)
    df['canonical_utr'] = [r[0] for r in utr_res]
    df['utr_flag'] = [r[1] for r in utr_res]
    
    # Standardize MCC
    mcc_res = df['mcc'].apply(normalize_mcc)
    df['canonical_mcc'] = [r[0] for r in mcc_res]
    
    # 2. Cross-table Foreign Key Validation
    known_users = set(df_customers['user_id'])
    known_merchants = set(df_merchants['merchant_id'])
    mch_mcc_lookup = dict(zip(df_merchants['merchant_id'], df_merchants['mcc']))
    mch_cat_lookup = dict(zip(df_merchants['merchant_id'], df_merchants['merchant_category']))
    
    df['customer_fk_valid'] = df['canonical_user_id'].isin(known_users)
    df['merchant_fk_valid'] = df['canonical_merchant_id'].isin(known_merchants)
    
    # Category resolution:
    # 1. Use txn MCC if valid
    # 2. Impute from merchant master
    # 3. Fallback
    def resolve_txn_cat(row):
        mcc = row['canonical_mcc']
        if pd.isna(mcc) or not mcc:
            mcc = mch_mcc_lookup.get(row['canonical_merchant_id'])
            
        mch_cat = mch_cat_lookup.get(row['canonical_merchant_id'])
        cat, _ = normalize_merchant_category(mch_cat, mcc=mcc)
        return cat, mcc
        
    cat_results = [resolve_txn_cat(row) for _, row in df.iterrows()]
    df['merchant_category'] = [r[0] for r in cat_results]
    df['effective_mcc'] = [r[1] for r in cat_results]
    
    # Extract date parts
    df['txn_date'] = pd.to_datetime(df['canonical_timestamp']).dt.date
    df['hour_of_day'] = pd.to_datetime(df['canonical_timestamp']).dt.hour
    
    trusted_txns = df[[
        'canonical_txn_id', 'canonical_timestamp', 'txn_date', 'hour_of_day',
        'canonical_user_id', 'canonical_merchant_id', 'merchant_category', 'effective_mcc',
        'canonical_amount', 'amount_flag', 'canonical_status', 'canonical_utr', 'utr_flag',
        'customer_fk_valid', 'merchant_fk_valid'
    ]].rename(columns={
        'canonical_txn_id': 'txn_id',
        'canonical_timestamp': 'timestamp',
        'canonical_user_id': 'user_id',
        'canonical_merchant_id': 'merchant_id',
        'canonical_amount': 'amount',
        'canonical_status': 'status',
        'canonical_utr': 'utr'
    })
    
    audit_summary = pd.DataFrame([{
        'raw_rows': len(df_upi),
        'exact_duplicates_removed': exact_dup_count,
        'retained_transactions': len(trusted_txns),
        'valid_customer_fk_count': trusted_txns['customer_fk_valid'].sum(),
        'orphan_customer_count': (~trusted_txns['customer_fk_valid']).sum(),
        'valid_merchant_fk_count': trusted_txns['merchant_fk_valid'].sum(),
        'orphan_merchant_count': (~trusted_txns['merchant_fk_valid']).sum(),
        'negative_amounts_count': (trusted_txns['amount'] < 0).sum()
    }])
    
    return trusted_txns, audit_summary


def validate_and_link_chargebacks(
    df_chargebacks: pd.DataFrame,
    df_transactions: pd.DataFrame,
    df_merchants: pd.DataFrame,
    df_customers: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Standardizes chargeback/dispute records, validates link to UPI transactions,
    imputes missing disputed amounts from transactions, and tracks orphans.
    """
    df = df_chargebacks.copy()
    
    # 1. Exact duplicates removal
    exact_dup_count = df.duplicated().sum()
    df = df.drop_duplicates().copy()
    
    # Standardize IDs
    df['canonical_txn_id'] = df['txn_id'].apply(lambda x: normalize_txn_id(x)[0])
    df['canonical_user_id'] = df['user_id'].apply(lambda x: normalize_user_id(x)[0])
    df['canonical_merchant_id'] = df['merchant_id'].apply(lambda x: normalize_merchant_id(x)[0])
    
    # Standardize amounts
    amt_res = df['disputed_amount'].apply(parse_amount)
    df['canonical_disputed_amount'] = [r[0] for r in amt_res]
    df['amount_imputed'] = False
    
    # Standardize timestamps
    txn_ts = df['transaction_timestamp'].apply(parse_timestamp)
    df['canonical_txn_timestamp'] = [r[0] for r in txn_ts]
    
    rep_ts = df['reported_timestamp'].apply(parse_timestamp)
    df['canonical_reported_timestamp'] = [r[0] for r in rep_ts]
    
    resp_ts = df['bank_response_timestamp'].apply(parse_timestamp)
    df['canonical_bank_response_timestamp'] = [r[0] for r in resp_ts]
    
    # Standardize categorical fields
    df['canonical_reason'] = df['reason_code'].apply(lambda x: normalize_dispute_reason(x)[0])
    df['canonical_severity'] = df['severity'].apply(lambda x: normalize_dispute_severity(x)[0])
    df['canonical_resolution'] = df['resolution_status'].apply(lambda x: normalize_resolution_status(x)[0])
    df['channel'] = df['channel'].str.strip().str.title()
    
    # Link to UPI transactions
    txn_dict = df_transactions.set_index('txn_id').to_dict('index')
    
    linked_flags = []
    category_list = []
    
    for idx, row in df.iterrows():
        t_id = row['canonical_txn_id']
        matched_txn = txn_dict.get(t_id)
        
        if matched_txn:
            linked_flags.append(True)
            category_list.append(matched_txn['merchant_category'])
            # If disputed amount is missing, impute from transaction amount
            if pd.isna(row['canonical_disputed_amount']):
                df.at[idx, 'canonical_disputed_amount'] = abs(matched_txn['amount'])
                df.at[idx, 'amount_imputed'] = True
        else:
            linked_flags.append(False)
            category_list.append(None)
            
    df['txn_link_valid'] = linked_flags
    df['merchant_category'] = category_list
    
    # If merchant_category is still None, try to get from merchant master
    mch_cat_lookup = dict(zip(df_merchants['merchant_id'], df_merchants['merchant_category']))
    for idx, row in df.iterrows():
        if pd.isna(df.at[idx, 'merchant_category']):
            df.at[idx, 'merchant_category'] = mch_cat_lookup.get(row['canonical_merchant_id'], 'Miscellaneous Retail')
            
    # Calculate reporting delay in days
    rep_dt = pd.to_datetime(df['canonical_reported_timestamp'])
    txn_dt = pd.to_datetime(df['canonical_txn_timestamp'])
    df['reporting_delay_days'] = (rep_dt - txn_dt).dt.total_seconds() / (24 * 3600)
    
    trusted_cb = df[[
        'complaint_id', 'canonical_txn_id', 'canonical_user_id', 'canonical_merchant_id',
        'merchant_category', 'canonical_txn_timestamp', 'canonical_reported_timestamp',
        'canonical_bank_response_timestamp', 'reporting_delay_days',
        'canonical_disputed_amount', 'amount_imputed', 'canonical_reason', 'complaint_text',
        'canonical_severity', 'canonical_resolution', 'channel', 'txn_link_valid'
    ]].rename(columns={
        'canonical_txn_id': 'txn_id',
        'canonical_user_id': 'user_id',
        'canonical_merchant_id': 'merchant_id',
        'canonical_disputed_amount': 'disputed_amount',
        'canonical_txn_timestamp': 'transaction_timestamp',
        'canonical_reported_timestamp': 'reported_timestamp',
        'canonical_bank_response_timestamp': 'bank_response_timestamp',
        'canonical_reason': 'reason_category',
        'canonical_severity': 'severity',
        'canonical_resolution': 'resolution_status'
    })
    
    audit_summary = pd.DataFrame([{
        'raw_chargebacks': len(df_chargebacks),
        'exact_duplicates_removed': exact_dup_count,
        'retained_chargebacks': len(trusted_cb),
        'linked_to_txn_count': trusted_cb['txn_link_valid'].sum(),
        'orphan_chargebacks_count': (~trusted_cb['txn_link_valid']).sum(),
        'amounts_imputed_count': trusted_cb['amount_imputed'].sum()
    }])
    
    return trusted_cb, audit_summary
