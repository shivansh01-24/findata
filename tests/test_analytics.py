import os
import pytest
from backend.intelligence.chargeback_analytics import ChargebackAnalyticsEngine
from backend.intelligence.merchant_risk import MerchantRiskEngine
from backend.intelligence.customer_risk import CustomerRiskEngine

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "processed"))

def test_summary_kpis():
    engine = ChargebackAnalyticsEngine(DATA_DIR)
    kpis = engine.get_summary_kpis()
    assert kpis['total_transactions'] == 20000
    assert kpis['total_chargebacks'] == 2800
    assert kpis['success_rate_pct'] > 80.0
    assert kpis['chargeback_ratio_pct'] == 14.0

def test_category_chargeback_ratios():
    engine = ChargebackAnalyticsEngine(DATA_DIR)
    ratios = engine.get_category_chargeback_ratios()
    assert len(ratios) == 10
    
    # Expected authoritative source-of-truth rankings & ratios
    expected_table = [
        ('Apparel', 145, 44, 30.34),
        ('Miscellaneous Retail', 1632, 308, 18.87),
        ('Department Store', 173, 31, 17.92),
        ('Transportation', 2975, 443, 14.89),
        ('Telecom', 126, 18, 14.29),
        ('Restaurant', 3000, 419, 13.97),
        ('Grocery', 5840, 767, 13.13),
        ('Pharmacy', 3004, 385, 12.82),
        ('Hotel & Lodging', 2964, 369, 12.45),
        ('Books & Stationery', 141, 16, 11.35)
    ]
    
    for i, (cat, exp_tx, exp_cb, exp_ratio) in enumerate(expected_table):
        actual = ratios[i]
        assert actual['category'] == cat, f"Rank {i+1} category mismatch: expected {cat}, got {actual['category']}"
        assert actual['transaction_count'] == exp_tx, f"{cat} txn count mismatch: expected {exp_tx}, got {actual['transaction_count']}"
        assert actual['chargeback_count'] == exp_cb, f"{cat} CB count mismatch: expected {exp_cb}, got {actual['chargeback_count']}"
        assert actual['chargeback_to_transaction_ratio_pct'] == exp_ratio, f"{cat} ratio mismatch: expected {exp_ratio}, got {actual['chargeback_to_transaction_ratio_pct']}"

    # Sum of transactions across all 10 categories must exactly equal 20,000
    assert sum(r['transaction_count'] for r in ratios) == 20000
    # Sum of chargebacks across all 10 categories must exactly equal 2,800
    assert sum(r['chargeback_count'] for r in ratios) == 2800

def test_merchant_risk_rankings():
    engine = MerchantRiskEngine(DATA_DIR)
    ranked = engine.get_ranked_merchants(limit=10)
    assert len(ranked) == 10
    # Verify scores are sorted descending
    scores = [m['risk_score'] for m in ranked]
    assert scores == sorted(scores, reverse=True)
    assert ranked[0]['risk_score'] >= 80.0
    assert ranked[0]['risk_level'] in ('CRITICAL', 'HIGH')

def test_customer_risk_rankings():
    engine = CustomerRiskEngine(DATA_DIR)
    ranked = engine.get_ranked_customers(limit=10)
    assert len(ranked) == 10
    scores = [c['risk_score'] for c in ranked]
    assert scores == sorted(scores, reverse=True)
