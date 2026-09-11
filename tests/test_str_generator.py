import os
import pytest
from backend.intelligence.fiu_str_generator import FiuStrGenerator

DATA_PROC_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

@pytest.fixture(scope="module")
def fiu_generator():
    return FiuStrGenerator(DATA_PROC_DIR)

def test_ring_str_generation(fiu_generator):
    report = fiu_generator.generate_ring_str("RING-SETTLE-001")
    assert report is not None
    assert "report_metadata" in report
    assert "FIU-IND" in report['report_metadata']['report_reference']
    assert "PMLA" in report['report_metadata']['statutory_framework']
    assert report['target_syndicate']['ring_id'] == "RING-SETTLE-001"
    assert len(report['grounds_of_suspicion']) >= 2
    assert len(report['statutory_directives']) >= 3
    assert len(report['markdown_dossier']) > 500

def test_merchant_str_generation(fiu_generator):
    # Test with top risk merchant
    report = fiu_generator.generate_merchant_str("MCH4473")
    if not report:
        # Fallback to any valid merchant in registry
        report = fiu_generator.generate_merchant_str("MCH7912")
    assert report is not None
    assert "report_metadata" in report
    assert "MCH-" in report['report_metadata']['report_reference']
    assert len(report['markdown_dossier']) > 300
