"""
Data Standardization and Rescue Module.
Translates messy, corrupt raw inputs into canonical values with validation status and audit flags.
Preserves original values while providing trustworthy normalized data.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
import pandas as pd
import numpy as np


# -----------------------------------------------------------------------------
# IDENTIFIER STANDARDIZERS
# -----------------------------------------------------------------------------

def normalize_user_id(val: Any) -> Tuple[Optional[str], str]:
    """
    Standardizes user IDs to USRxxxxx (e.g. USR12345).
    Handles: USR12345, usr12345, USR-12345, USR 12345, usr_12345, 12345.
    Returns: (canonical_id, quality_flag)
    """
    if pd.isna(val) or val is None:
        return None, "MISSING_USER_ID"
    
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", ""):
        return None, "EMPTY_USER_ID"
    
    digits = re.findall(r'\d+', s)
    if not digits:
        return None, "INVALID_USER_ID_NO_DIGITS"
    
    # Standardize to USR + 5 digits
    canonical = f"USR{digits[0].zfill(5)}"
    
    if s == canonical:
        flag = "VALID_EXACT"
    else:
        flag = "STANDARDIZED_FROM_DIRTY"
    return canonical, flag


def normalize_merchant_id(val: Any) -> Tuple[Optional[str], str]:
    """
    Standardizes merchant IDs to MCHxxxx (e.g. MCH1234).
    Handles: MCH1234, mch1234, MCH-1234, MCH 1234, 1234.
    Returns: (canonical_id, quality_flag)
    """
    if pd.isna(val) or val is None:
        return None, "MISSING_MERCHANT_ID"
    
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", ""):
        return None, "EMPTY_MERCHANT_ID"
    
    digits = re.findall(r'\d+', s)
    if not digits:
        return None, "INVALID_MERCHANT_ID_NO_DIGITS"
    
    canonical = f"MCH{digits[0].zfill(4)}"
    if s == canonical:
        flag = "VALID_EXACT"
    else:
        flag = "STANDARDIZED_FROM_DIRTY"
    return canonical, flag


def normalize_txn_id(val: Any) -> Tuple[Optional[str], str]:
    """
    Standardizes transaction IDs to TXNxxxxxxxx.
    Returns: (canonical_id, quality_flag)
    """
    if pd.isna(val) or val is None:
        return None, "MISSING_TXN_ID"
    
    s = str(val).strip().upper()
    if not s:
        return None, "EMPTY_TXN_ID"
    
    digits = re.findall(r'\d+', s)
    if digits:
        canonical = f"TXN{digits[0].zfill(8)}"
    else:
        canonical = s
        
    return canonical, "VALID_EXACT" if s == canonical else "STANDARDIZED_FROM_DIRTY"


# -----------------------------------------------------------------------------
# AMOUNT AND CURRENCY PARSING
# -----------------------------------------------------------------------------

def parse_amount(val: Any) -> Tuple[Optional[float], str]:
    """
    Parses currency strings like 'Rs. 6362.9', '₹16,466.93', 'INR 13,312', '-23820.57', '27.3k'.
    Distinguishes negative amounts (refunds / reversals) from normal positive debits.
    Returns: (canonical_float, quality_flag)
    """
    if pd.isna(val) or val is None:
        return None, "MISSING_AMOUNT"
    
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", ""):
        return None, "EMPTY_AMOUNT"
    
    # Check for multiplier suffix like 'k' or 'K' (thousands)
    multiplier = 1.0
    if s.lower().endswith('k'):
        multiplier = 1000.0
        s = s[:-1].strip()
    
    # Check negative
    is_neg = '-' in s
    
    # Remove known currency words/symbols first so abbreviation dots (like in 'Rs.') don't collide with decimal dot
    s = re.sub(r'(?i)(rs\.?|inr|₹)', '', s)
    
    # Remove other non-digit non-dot characters
    cleaned = re.sub(r'[^\d.]', '', s)
    if not cleaned:
        return None, "MALFORMED_AMOUNT"
    
    # If multiple dots remain, keep only the last one as decimal point
    if cleaned.count('.') > 1:
        parts = cleaned.split('.')
        cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
    
    try:
        amt = float(cleaned) * multiplier
        if is_neg:
            amt = -amt
            return amt, "REFUND_OR_REVERSAL_NEGATIVE"
        if amt == 0.0:
            return 0.0, "ZERO_AMOUNT"
        return amt, "VALID_AMOUNT"
    except Exception:
        return None, "PARSE_ERROR"


# -----------------------------------------------------------------------------
# TIMESTAMP PARSING
# -----------------------------------------------------------------------------

TIMESTAMP_FORMATS = [
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %I:%M:%S %p',
    '%Y-%m-%d',
    '%d/%m/%Y %H:%M:%S',
    '%d/%m/%Y %I:%M:%S %p',
    '%d/%m/%Y',
    '%m-%d-%Y %I:%M:%S %p',
    '%m-%d-%Y %H:%M:%S',
    '%m-%d-%Y',
    '%d-%m-%Y %H:%M:%S',
    '%d-%m-%Y',
    '%Y/%m/%d %H:%M:%S',
    '%Y/%m/%d',
    '%d-%b-%Y %H:%M:%S',
    '%d-%b-%Y',
    '%b-%d-%Y %H:%M:%S',
    '%b-%d-%Y',
]

def parse_timestamp(val: Any) -> Tuple[Optional[str], str]:
    """
    Parses mixed timestamps: Unix epoch, ISO, US format, European format, 12-hour AM/PM.
    Returns: (ISO_string 'YYYY-MM-DD HH:MM:SS', quality_flag)
    """
    if pd.isna(val) or val is None:
        return None, "MISSING_TIMESTAMP"
    
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", ""):
        return None, "EMPTY_TIMESTAMP"
    
    # Unix epoch seconds (e.g. 1770063471)
    if re.match(r'^\d{9,11}$', s):
        try:
            dt = datetime.fromtimestamp(int(s), timezone.utc)
            return dt.strftime('%Y-%m-%d %H:%M:%S'), "UNIX_EPOCH_CONVERTED"
        except Exception:
            pass
            
    # Try formats
    for fmt in TIMESTAMP_FORMATS:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S'), "STANDARDIZED_TIMESTAMP"
        except ValueError:
            continue
            
    # Fallback to dateutil parser via pandas
    try:
        dt = pd.to_datetime(s, dayfirst=True)
        if pd.notna(dt):
            return dt.strftime('%Y-%m-%d %H:%M:%S'), "HEURISTIC_PARSED_TIMESTAMP"
    except Exception:
        pass
        
    return None, "UNPARSABLE_TIMESTAMP"


# -----------------------------------------------------------------------------
# TRANSACTION STATUS NORMALIZATION
# -----------------------------------------------------------------------------

def normalize_txn_status(val: Any) -> Tuple[str, str]:
    """
    Normalizes transaction status to SUCCESS, FAILED, or PENDING.
    """
    if pd.isna(val) or val is None:
        return "PENDING", "MISSING_STATUS_DEFAULTED_PENDING"
    
    s = str(val).strip().upper()
    
    if s in ('SUCCESS', 'S', 'TXN_SUCCESS', 'COMPLETED'):
        return "SUCCESS", "STATUS_SUCCESS"
    elif s in ('FAILED', 'TXN_FAILED', 'FAIL', 'DECLINED', 'F'):
        return "FAILED", "STATUS_FAILED"
    elif s in ('PENDING', 'PROCESSING', 'INITIATED'):
        return "PENDING", "STATUS_PENDING"
    else:
        return "UNKNOWN", "UNRECOGNIZED_STATUS"


# -----------------------------------------------------------------------------
# UTR NORMALIZATION
# -----------------------------------------------------------------------------

def normalize_utr(val: Any) -> Tuple[Optional[str], str]:
    """
    Standardizes UTR values. Strips spaces and validates length/format.
    Example: 'UTR 2787678319' -> 'UTR2787678319'
    """
    if pd.isna(val) or val is None:
        return None, "MISSING_UTR"
    
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", ""):
        return None, "EMPTY_UTR"
    
    cleaned = re.sub(r'[\s\-]', '', s).upper()
    
    # Check pattern: UTR followed by 10 digits
    if re.match(r'^UTR\d{10}$', cleaned):
        if cleaned == s:
            return cleaned, "VALID_UTR"
        else:
            return cleaned, "RESCUED_UTR_SPACES_REMOVED"
    elif re.match(r'^\d{10,12}$', cleaned):
        return f"UTR{cleaned[:10]}", "RESCUED_UTR_PREFIX_ADDED"
    else:
        return cleaned, "NON_STANDARD_UTR_FORMAT"


# -----------------------------------------------------------------------------
# KYC IDENTIFIERS & ATTRIBUTES
# -----------------------------------------------------------------------------

PAN_REGEX = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')

def normalize_pan(val: Any) -> Tuple[Optional[str], str]:
    """
    Normalizes Indian PAN: 5 letters, 4 digits, 1 letter (e.g. SEJAA8194O).
    Handles spaces, lowercase, hyphens.
    """
    if pd.isna(val) or val is None:
        return None, "MISSING_PAN"
    
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", ""):
        return None, "EMPTY_PAN"
    
    cleaned = re.sub(r'[\s\-]', '', s).upper()
    if PAN_REGEX.match(cleaned):
        return cleaned, "VALID_PAN"
    else:
        return cleaned, "MALFORMED_PAN_FORMAT"


def normalize_aadhaar(val: Any) -> Tuple[Optional[str], str]:
    """
    Normalizes Indian Aadhaar: 12 digits or masked XXXX-XXXX-1234.
    """
    if pd.isna(val) or val is None:
        return None, "MISSING_AADHAAR"
    
    s = str(val).strip().upper()
    if not s or s.lower() in ("nan", "none", "null", ""):
        return None, "EMPTY_AADHAAR"
    
    cleaned = re.sub(r'[\s\-]', '', s)
    
    if re.match(r'^\d{12}$', cleaned):
        return cleaned, "VALID_12_DIGIT_AADHAAR"
    elif 'X' in cleaned:
        return cleaned, "MASKED_AADHAAR"
    elif re.match(r'^\d{13,}$', cleaned):
        return cleaned, "EXCESS_DIGITS_AADHAAR"
    else:
        return cleaned, "MALFORMED_AADHAAR"


def normalize_kyc_status(val: Any) -> Tuple[str, str]:
    """
    Standardizes KYC status to VERIFIED, PENDING, or REJECTED.
    """
    if pd.isna(val) or val is None:
        return "PENDING", "MISSING_KYC_STATUS_DEFAULTED"
    
    s = str(val).strip().upper()
    
    if s in ('VERIFIED', 'APPROVED', 'KYC_DONE', 'V', 'DONE'):
        return "VERIFIED", "KYC_VERIFIED"
    elif s in ('PENDING', 'P', 'IN_PROGRESS', 'UNDER REVIEW'):
        return "PENDING", "KYC_PENDING"
    elif s in ('REJECTED', 'REJECT', 'R'):
        return "REJECTED", "KYC_REJECTED"
    else:
        return "UNKNOWN", "KYC_STATUS_UNKNOWN"


def normalize_risk_segment(val: Any) -> Tuple[str, str]:
    """
    Standardizes KYC risk segment to LOW, MEDIUM, HIGH, or UNKNOWN.
    """
    if pd.isna(val) or val is None:
        return "UNKNOWN", "MISSING_RISK_SEGMENT"
    
    s = str(val).strip().upper()
    if s in ('LOW', 'MEDIUM', 'HIGH'):
        return s, "VALID_RISK_SEGMENT"
    return "UNKNOWN", "STANDARDIZED_UNKNOWN_RISK"


# -----------------------------------------------------------------------------
# MERCHANT CATEGORY & MCC MAPPING
# -----------------------------------------------------------------------------

MCC_TO_CATEGORY = {
    '4131': 'Transportation',
    '4814': 'Telecom',
    '5311': 'Department Store',
    '5411': 'Grocery',
    '5699': 'Apparel',
    '5812': 'Restaurant',
    '5912': 'Pharmacy',
    '5942': 'Books & Stationery',
    '5999': 'Miscellaneous Retail',
    '7011': 'Hotel & Lodging'
}

CATEGORY_KEYWORDS = {
    'Transportation': ['transport', 'transprt', 'taxi', 'bus', 'travel'],
    'Telecom': ['telecom', 'phone', 'recharge', 'mobile'],
    'Department Store': ['dept', 'department', 'retail'],
    'Grocery': ['grocery', 'groceries', 'kirana', 'supermarket'],
    'Apparel': ['apparel', 'cloth', 'garment', 'fashion'],
    'Restaurant': ['restaurant', 'eating', 'food'],
    'Pharmacy': ['pharmacy', 'chemist', 'medical'],
    'Books & Stationery': ['book', 'stationery'],
    'Hotel & Lodging': ['hotel', 'lodging', 'hospitality'],
    'Miscellaneous Retail': ['misc', 'other']
}

def normalize_mcc(val: Any) -> Tuple[Optional[str], str]:
    """
    Normalizes MCC code to 4-digit string. Handles 'MCC-7011', '5311.0', '05411'.
    """
    if pd.isna(val) or val is None:
        return None, "MISSING_MCC"
    
    s = str(val).strip()
    digits = re.findall(r'\d+', s)
    if not digits:
        return None, "INVALID_MCC"
    
    code = digits[0].zfill(4)[-4:]
    return code, "VALID_MCC"


def normalize_merchant_category(raw_category: Any, mcc: Optional[str] = None) -> Tuple[str, str]:
    """
    Maps raw merchant category string and MCC to one of 10 canonical categories.
    """
    # 1. Direct MCC match
    if mcc and mcc in MCC_TO_CATEGORY:
        return MCC_TO_CATEGORY[mcc], "RESOLVED_FROM_MCC"
        
    if pd.isna(raw_category) or not raw_category:
        return "Miscellaneous Retail", "DEFAULTED_EMPTY_CATEGORY"
        
    s = str(raw_category).strip().lower()
    
    for canon_cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in s for kw in keywords):
            return canon_cat, "RESOLVED_FROM_KEYWORD"
            
    return "Miscellaneous Retail", "FALLBACK_MISC_RETAIL"


def normalize_merchant_status(val: Any) -> Tuple[str, str]:
    """
    Normalizes merchant status to ACTIVE, INACTIVE, or SUSPENDED.
    """
    if pd.isna(val) or val is None:
        return "INACTIVE", "MISSING_STATUS_DEFAULTED"
        
    s = str(val).strip().upper()
    if s in ('ACTIVE', 'LIVE', 'ENABLED', 'A'):
        return "ACTIVE", "MERCHANT_ACTIVE"
    elif s in ('INACTIVE', 'DISABLED', 'CLOSED', 'I'):
        return "INACTIVE", "MERCHANT_INACTIVE"
    elif s in ('SUSPENDED', 'HOLD', 'BLOCKED', 'S'):
        return "SUSPENDED", "MERCHANT_SUSPENDED"
    return "INACTIVE", "UNKNOWN_STATUS_DEFAULTED"


# -----------------------------------------------------------------------------
# DISPUTE / CHARGEBACK STANDARDIZATION
# -----------------------------------------------------------------------------

REASON_GROUP_MAP = {
    # Fraud & ATO
    'account hacked': 'Fraud & Account Takeover',
    'login compromised': 'Fraud & Account Takeover',
    'ato': 'Fraud & Account Takeover',
    'account takeover': 'Fraud & Account Takeover',
    'not done by me': 'Fraud & Account Takeover',
    'unauth txn': 'Fraud & Account Takeover',
    'unauthorized transaction': 'Fraud & Account Takeover',
    'unauthorized_transaction': 'Fraud & Account Takeover',
    'unauthorised': 'Fraud & Account Takeover',
    'fraud': 'Fraud & Account Takeover',
    'fraud suspected': 'Fraud & Account Takeover',
    'scam': 'Fraud & Account Takeover',
    'suspicious transaction': 'Fraud & Account Takeover',
    
    # Billing & Duplicates
    'charged twice': 'Duplicate Debit & Billing',
    'double debit': 'Duplicate Debit & Billing',
    'duplicate debit': 'Duplicate Debit & Billing',
    'dup_debit': 'Duplicate Debit & Billing',
    'extra amount deducted': 'Duplicate Debit & Billing',
    'amount mismatch': 'Duplicate Debit & Billing',
    'wrong amount': 'Duplicate Debit & Billing',
    'incorrect amount': 'Duplicate Debit & Billing',
    
    # Service & Delivery
    'merchant not delivered': 'Service & Delivery Failure',
    'not delivered': 'Service & Delivery Failure',
    'item not received': 'Service & Delivery Failure',
    'delivery issue': 'Service & Delivery Failure',
    'merchant service issue': 'Service & Delivery Failure',
    'no service': 'Service & Delivery Failure',
    'service failed': 'Service & Delivery Failure',
    'service not provided': 'Service & Delivery Failure',
    
    # General Disputes
    'customer issue': 'Customer General Dispute',
    'dispute raised': 'Customer General Dispute',
    'customer dispute': 'Customer General Dispute',
    'complaint': 'Customer General Dispute'
}

def normalize_dispute_reason(val: Any) -> Tuple[str, str]:
    if pd.isna(val) or val is None:
        return "Customer General Dispute", "MISSING_REASON"
    
    s = str(val).strip().lower()
    for raw_r, group in REASON_GROUP_MAP.items():
        if raw_r in s:
            return group, "STANDARDIZED_REASON"
    return "Customer General Dispute", "UNCLASSIFIED_REASON"


def normalize_dispute_severity(val: Any) -> Tuple[str, str]:
    if pd.isna(val) or val is None:
        return "Medium", "DEFAULTED_SEVERITY"
    s = str(val).strip().upper()
    if s in ('CRITICAL', 'CRIT', 'P1'):
        return "Critical", "SEVERITY_CRITICAL"
    elif s in ('HIGH', 'H', 'P2'):
        return "High", "SEVERITY_HIGH"
    elif s in ('MEDIUM', 'M', 'P3'):
        return "Medium", "SEVERITY_MEDIUM"
    elif s in ('LOW', 'L', 'P4'):
        return "Low", "SEVERITY_LOW"
    return "Medium", "FALLBACK_SEVERITY"


def normalize_resolution_status(val: Any) -> Tuple[str, str]:
    if pd.isna(val) or val is None:
        return "OPEN", "MISSING_STATUS"
    s = str(val).strip().upper()
    if s in ('CLOSED'):
        return "CLOSED", "STATUS_CLOSED"
    elif s in ('RESOLVED'):
        return "RESOLVED", "STATUS_RESOLVED"
    elif s in ('REJECTED'):
        return "REJECTED", "STATUS_REJECTED"
    elif s in ('OPEN', 'IN_PROGRESS', 'IN PROGRESS', 'WIP', 'PENDING BANK', 'PENDING_BANK'):
        return "IN_PROGRESS", "STATUS_IN_PROGRESS"
    return "OPEN", "FALLBACK_STATUS"
