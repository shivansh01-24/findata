import os
import pytest
from backend.intelligence.policy_simulator import PolicySimulatorEngine

DATA_PROC_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

@pytest.fixture(scope="module")
def policy_sim():
    return PolicySimulatorEngine(DATA_PROC_DIR)

def test_policy_simulation_defaults(policy_sim):
    res = policy_sim.simulate({
        'chargeback_threshold_pct': 20.0,
        'ticket_multiplier': 2.0,
        'mule_sharing_threshold': 2
    })
    assert "baseline_metrics" in res
    assert "simulated_metrics" in res
    assert "delta_impact" in res
    assert res['simulated_metrics']['flagged_merchants'] > 0
    assert res['simulated_metrics']['dispute_volume_contained'] > 0

def test_policy_simulation_sensitivity(policy_sim):
    # Tightening threshold to 10% should flag MORE merchants and contain MORE disputes
    lenient = policy_sim.simulate({'chargeback_threshold_pct': 30.0, 'ticket_multiplier': 3.0})
    strict = policy_sim.simulate({'chargeback_threshold_pct': 10.0, 'ticket_multiplier': 1.5})

    assert strict['simulated_metrics']['flagged_merchants'] >= lenient['simulated_metrics']['flagged_merchants']
    assert strict['simulated_metrics']['dispute_volume_contained'] >= lenient['simulated_metrics']['dispute_volume_contained']
