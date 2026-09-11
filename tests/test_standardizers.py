import pytest
import numpy as np
from backend.pipeline.standardizers import (
    normalize_user_id,
    normalize_merchant_id,
    normalize_txn_id,
    parse_amount,
    parse_timestamp,
    normalize_txn_status,
    normalize_utr,
    normalize_pan,
    normalize_aadhaar,
    normalize_kyc_status,
    normalize_merchant_category
)

def test_user_id_normalization():
    assert normalize_user_id("USR12345")[0] == "USR12345"
    assert normalize_user_id("usr12345")[0] == "USR12345"
    assert normalize_user_id("USR-12345")[0] == "USR12345"
    assert normalize_user_id("USR 12345")[0] == "USR12345"
    assert normalize_user_id("usr_12345")[0] == "USR12345"
    assert normalize_user_id("12345")[0] == "USR12345"
    assert normalize_user_id(None)[0] is None

def test_merchant_id_normalization():
    assert normalize_merchant_id("MCH1234")[0] == "MCH1234"
    assert normalize_merchant_id("mch1234")[0] == "MCH1234"
    assert normalize_merchant_id("MCH-1234")[0] == "MCH1234"
    assert normalize_merchant_id("MCH 1234")[0] == "MCH1234"
    assert normalize_merchant_id("1234")[0] == "MCH1234"
    assert normalize_merchant_id(None)[0] is None

def test_amount_parsing():
    assert parse_amount("15722.34")[0] == 15722.34
    assert parse_amount("Rs. 6362.9")[0] == 6362.9
    assert parse_amount("₹16,466.93")[0] == 16466.93
    assert parse_amount("INR 13,312")[0] == 13312.0
    val, flag = parse_amount("-23820.57")
    assert val == -23820.57
    assert flag == "REFUND_OR_REVERSAL_NEGATIVE"
    val_k, _ = parse_amount("27.3k")
    assert val_k == 27300.0

def test_timestamp_parsing():
    ts1, flag1 = parse_timestamp("2026-01-15 00:11:30")
    assert ts1 == "2026-01-15 00:11:30"
    ts2, flag2 = parse_timestamp("1770063471")
    assert ts2 is not None
    assert flag2 == "UNIX_EPOCH_CONVERTED"
    ts3, _ = parse_timestamp("25/02/2026 00:53:02")
    assert ts3 == "2026-02-25 00:53:02"

def test_txn_status_normalization():
    assert normalize_txn_status("SUCCESS")[0] == "SUCCESS"
    assert normalize_txn_status("COMPLETED")[0] == "SUCCESS"
    assert normalize_txn_status("TXN_SUCCESS")[0] == "SUCCESS"
    assert normalize_txn_status("S")[0] == "SUCCESS"
    assert normalize_txn_status("TXN_FAILED")[0] == "FAILED"
    assert normalize_txn_status("Fail")[0] == "FAILED"
    assert normalize_txn_status("Declined")[0] == "FAILED"
    assert normalize_txn_status("Initiated")[0] == "PENDING"
    assert normalize_txn_status("Pending")[0] == "PENDING"

def test_utr_normalization():
    u1, flag1 = normalize_utr("UTR6498104698")
    assert u1 == "UTR6498104698"
    assert flag1 == "VALID_UTR"
    u2, flag2 = normalize_utr("UTR 2787678319")
    assert u2 == "UTR2787678319"
    assert flag2 == "RESCUED_UTR_SPACES_REMOVED"
    assert normalize_utr(None)[0] is None

def test_pan_and_aadhaar():
    pan, p_flag = normalize_pan("SEJAA8194O")
    assert pan == "SEJAA8194O"
    assert p_flag == "VALID_PAN"
    
    a1, a1_flag = normalize_aadhaar("715658320763")
    assert a1 == "715658320763"
    assert a1_flag == "VALID_12_DIGIT_AADHAAR"
    
    a2, a2_flag = normalize_aadhaar("XXXX-XXXX-5406")
    assert a2_flag == "MASKED_AADHAAR"

def test_category_normalization():
    cat1, _ = normalize_merchant_category("grocery stores", mcc="5411")
    assert cat1 == "Grocery"
    cat2, _ = normalize_merchant_category("hotel_lodging", mcc="7011")
    assert cat2 == "Hotel & Lodging"
    cat3, _ = normalize_merchant_category("MEDICAL_STORE", mcc="5912")
    assert cat3 == "Pharmacy"
