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
    assert len(ratios) > 0
    # Winning category should be identified
    top_cat = ratios[0]
    assert 'category' in top_cat
    assert top_cat['chargeback_to_transaction_ratio_pct'] > 15.0

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
