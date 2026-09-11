import os
import pytest
from backend.pipeline.audit_service import AuditRescueService

DATA_RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
DATA_PROC_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

@pytest.fixture(scope="module")
def audit_service():
    return AuditRescueService(DATA_RAW_DIR, DATA_PROC_DIR)

def test_curated_cases(audit_service):
    cases = audit_service.get_curated_cases()
    assert len(cases) >= 6
    entity_ids = [c['entity_id'] for c in cases]
    assert 'MCH7912' in entity_ids
    assert 'USR10043' in entity_ids
    assert 'USR10052' in entity_ids

def test_entity_search(audit_service):
    # Search by normalized ID
    results = audit_service.search_entities("USR10043")
    assert len(results) > 0
    assert results[0]['entity_id'] == 'USR10043'
    assert results[0]['entity_type'] == 'CUSTOMER'

    # Search by Merchant ID
    mch_results = audit_service.search_entities("MCH7912")
    assert len(mch_results) > 0
    assert any(r['entity_id'] == 'MCH7912' for r in mch_results)

def test_merchant_audit_diff(audit_service):
    audit = audit_service.get_entity_audit("MERCHANT", "MCH7912")
    assert audit is not None
    assert audit['entity_id'] == 'MCH7912'
    assert len(audit['raw_records']) == 6
    assert audit['resolution_type'] == 'CONFLICTING_MERCHANT_RECORD'
    assert len(audit['attribute_diffs']) >= 6
    
    # Check that settlement account diff exists
    settle_diff = next(d for d in audit['attribute_diffs'] if d['attribute'] == 'Settlement Account')
    assert settle_diff['conflict_detected'] is True

def test_customer_audit_diff(audit_service):
    audit = audit_service.get_entity_audit("CUSTOMER", "USR10043")
    assert audit is not None
    assert audit['entity_id'] == 'USR10043'
    assert len(audit['raw_records']) == 2
    assert audit['resolution_type'] == 'CONFLICTING_RECORD'
    
    # Name conflict check
    name_diff = next(d for d in audit['attribute_diffs'] if d['attribute'] == 'Full Name')
    assert name_diff['conflict_detected'] is True
