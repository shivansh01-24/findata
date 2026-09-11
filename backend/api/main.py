"""
FastAPI Backend Application.
Serves RESTful endpoints for Executive Overview, Fraud Rings, Merchant Risk,
Customer Identity Risk, Data Rescue Audits, and the Agentic Graph AI.
"""

import os
import sys
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.intelligence.fraud_rings import FraudRingEngine
from backend.intelligence.merchant_risk import MerchantRiskEngine
from backend.intelligence.customer_risk import CustomerRiskEngine
from backend.intelligence.chargeback_analytics import ChargebackAnalyticsEngine
from backend.pipeline.audit_service import AuditRescueService
from backend.intelligence.fiu_str_generator import FiuStrGenerator
from backend.intelligence.policy_simulator import PolicySimulatorEngine
from backend.api.agent.domain_guard import validate_query_domain
from backend.api.agent.deterministic_engine import DeterministicQueryEngine
from backend.api.agent.openrouter_client import OpenRouterAgentClient

DATA_RAW_DIR = os.path.join(ROOT_DIR, "data", "raw")
DATA_PROC_DIR = os.path.join(ROOT_DIR, "data", "processed")

# Initialize engines
fraud_engine = FraudRingEngine(DATA_PROC_DIR)
merchant_engine = MerchantRiskEngine(DATA_PROC_DIR)
customer_engine = CustomerRiskEngine(DATA_PROC_DIR)
chargeback_engine = ChargebackAnalyticsEngine(DATA_PROC_DIR)
audit_service = AuditRescueService(DATA_RAW_DIR, DATA_PROC_DIR)
fiu_generator = FiuStrGenerator(DATA_PROC_DIR)
policy_simulator = PolicySimulatorEngine(DATA_PROC_DIR)
deterministic_engine = DeterministicQueryEngine(DATA_PROC_DIR)
openrouter_client = OpenRouterAgentClient()

app = FastAPI(
    title="TransOrg UPI Fraud Intelligence API",
    description="Production-grade API for UPI Payment Analytics, Fraud Rings, and Agentic Graph AI",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentQueryRequest(BaseModel):
    query: str
    api_key: Optional[str] = None


class KeyUpdateRequest(BaseModel):
    api_key: str


class PolicySimulateRequest(BaseModel):
    chargeback_threshold_pct: float = 20.0
    ticket_multiplier: float = 2.0
    mule_sharing_threshold: int = 2
    min_txns_evaluated: int = 3


# -----------------------------------------------------------------------------
# SYSTEM & HEALTH
# -----------------------------------------------------------------------------

@app.get("/api/health")
def get_health():
    import json
    metrics_path = os.path.join(DATA_PROC_DIR, "pipeline_metrics.json")
    pipeline_metrics = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r', encoding='utf-8') as f:
            pipeline_metrics = json.load(f)

    return {
        "status": "healthy",
        "service": "UPI Fraud Intelligence Platform",
        "openrouter_key_configured": bool(openrouter_client.api_key),
        "available_models": openrouter_client.models,
        "trusted_counts": pipeline_metrics.get("counts", {})
    }


@app.post("/api/settings/openrouter-key")
def update_openrouter_key(payload: KeyUpdateRequest):
    if not payload.api_key.strip():
        raise HTTPException(status_code=400, detail="API key cannot be empty")
    openrouter_client.set_api_key(payload.api_key.strip())
    return {"status": "success", "message": "OpenRouter API key updated successfully."}


# -----------------------------------------------------------------------------
# EXECUTIVE OVERVIEW
# -----------------------------------------------------------------------------

@app.get("/api/analytics/overview")
def get_overview_analytics():
    kpis = chargeback_engine.get_summary_kpis()
    ratios = chargeback_engine.get_category_chargeback_ratios()
    reasons = chargeback_engine.get_reason_distribution()
    severities = chargeback_engine.get_severity_distribution()
    channels = chargeback_engine.get_channel_distribution()
    resolutions = chargeback_engine.get_resolution_distribution()

    # Calculate daily transaction volume for trends
    df_txns = chargeback_engine.df_txns
    daily = df_txns.groupby('txn_date').agg(
        volume=('amount', lambda x: round(float(x.abs().sum()), 2)),
        count=('txn_id', 'count')
    ).reset_index().sort_values('txn_date')
    daily_data = daily.to_dict(orient='records')

    return {
        "kpis": kpis,
        "category_ratios": ratios,
        "daily_trends": daily_data,
        "reasons": reasons,
        "severities": severities,
        "channels": channels,
        "resolutions": resolutions
    }


# -----------------------------------------------------------------------------
# FRAUD RINGS & GRAPH
# -----------------------------------------------------------------------------

@app.get("/api/analytics/fraud-rings")
def get_fraud_rings(
    ring_type: Optional[str] = Query(None, description="Filter by ring type"),
    min_score: float = Query(0.0, description="Minimum risk score"),
    limit: int = Query(50, description="Max number of rings to return")
):
    rings = fraud_engine.get_all_rings()
    if ring_type and ring_type != 'ALL':
        rings = [r for r in rings if r['ring_type'].lower() == ring_type.lower()]
    if min_score > 0:
        rings = [r for r in rings if r['risk_score'] >= min_score]
    return rings[:limit]


@app.get("/api/analytics/fraud-rings/{ring_id}")
def get_fraud_ring_detail(ring_id: str):
    ring = fraud_engine.get_ring_by_id(ring_id)
    if not ring:
        raise HTTPException(status_code=404, detail="Fraud ring not found")
    return ring


@app.get("/api/analytics/fraud-rings/{ring_id}/graph")
def get_fraud_ring_graph(ring_id: str):
    graph = fraud_engine.get_ring_graph(ring_id)
    if not graph or not graph['nodes']:
        raise HTTPException(status_code=404, detail="Fraud ring graph not found")
    return graph


# -----------------------------------------------------------------------------
# MERCHANT RISK
# -----------------------------------------------------------------------------

@app.get("/api/analytics/merchants")
def get_merchants(
    category: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100)
):
    return merchant_engine.get_ranked_merchants(
        category=category,
        risk_level=risk_level,
        status=status,
        limit=limit
    )


@app.get("/api/analytics/merchants/{merchant_id}")
def get_merchant_detail(merchant_id: str):
    mch = merchant_engine.get_merchant_dossier(merchant_id)
    if not mch:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return mch


# -----------------------------------------------------------------------------
# CUSTOMER & IDENTITY RISK
# -----------------------------------------------------------------------------

@app.get("/api/analytics/customers")
def get_customers(
    kyc_status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    limit: int = Query(100)
):
    return customer_engine.get_ranked_customers(
        kyc_status=kyc_status,
        risk_level=risk_level,
        limit=limit
    )


@app.get("/api/analytics/customers/{user_id}")
def get_customer_detail(user_id: str):
    cust = customer_engine.get_customer_dossier(user_id)
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")
    return cust


# -----------------------------------------------------------------------------
# DATA RESCUE & QUALITY AUDIT
# -----------------------------------------------------------------------------

@app.get("/api/analytics/data-quality")
def get_data_quality_report():
    import json
    report_json_path = os.path.join(DATA_PROC_DIR, "data_quality_report.json")
    metrics_path = os.path.join(DATA_PROC_DIR, "pipeline_metrics.json")
    
    report = {}
    metrics = {}
    if os.path.exists(report_json_path):
        with open(report_json_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r', encoding='utf-8') as f:
            metrics = json.load(f)

    return {
        "profiling_report": report,
        "pipeline_metrics": metrics
    }


@app.get("/api/audit/search")
def search_audit_entities(
    q: str = Query("", description="Query by ID, name, PAN, or settlement account"),
    limit: int = Query(15, description="Max entities to return")
):
    return audit_service.search_entities(q, limit=limit)


@app.get("/api/audit/entity/{entity_type}/{entity_id}")
def get_audit_entity(entity_type: str, entity_id: str):
    res = audit_service.get_entity_audit(entity_type, entity_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found in audit index")
    return res


@app.get("/api/audit/curated-cases")
def get_curated_audit_cases():
    return audit_service.get_curated_cases()


# -----------------------------------------------------------------------------
# FIU-IND REGULATORY STR DOSSIERS
# -----------------------------------------------------------------------------

@app.get("/api/reports/str/ring/{ring_id}")
def get_ring_str_report(ring_id: str):
    rep = fiu_generator.generate_ring_str(ring_id)
    if not rep:
        raise HTTPException(status_code=404, detail=f"Fraud ring '{ring_id}' not found")
    return rep


@app.get("/api/reports/str/merchant/{merchant_id}")
def get_merchant_str_report(merchant_id: str):
    rep = fiu_generator.generate_merchant_str(merchant_id)
    if not rep:
        raise HTTPException(status_code=404, detail=f"Merchant '{merchant_id}' not found")
    return rep


# -----------------------------------------------------------------------------
# RISK POLICY & THRESHOLD SIMULATOR
# -----------------------------------------------------------------------------

@app.post("/api/analytics/simulate-policy")
def simulate_risk_policy(payload: PolicySimulateRequest):
    return policy_simulator.simulate(payload.model_dump())


# -----------------------------------------------------------------------------
# AGENTIC GRAPH AI ENDPOINT
# -----------------------------------------------------------------------------

@app.post("/api/agent/query")
def process_agent_query(payload: AgentQueryRequest):
    query = payload.query.strip()
    
    # 1. Strict Domain & Prompt-Injection Guardrail
    is_valid, message, meta = validate_query_domain(query)
    if not is_valid:
        return {
            "success": False,
            "query": query,
            "error_type": meta.get("status"),
            "answer": message,
            "chart": None,
            "supporting_metrics": {},
            "business_interpretation": None,
            "model_info": {
                "source": "domain_guardrail",
                "status": meta.get("status")
            }
        }

    # 2. Deterministic Analytical Query Execution (Grounded Numbers)
    grounded_result = deterministic_engine.answer_query(query)

    # 3. OpenRouter Free-Model Fallback or Runtime Key
    client = openrouter_client
    if payload.api_key and payload.api_key.strip():
        client = OpenRouterAgentClient(api_key=payload.api_key.strip())

    llm_synthesis = client.generate_grounded_response(query, grounded_result)

    return {
        "success": True,
        "query": query,
        "intent": grounded_result.get("intent"),
        "answer": llm_synthesis.get("summary", grounded_result.get("answer_text")),
        "chart": grounded_result.get("chart"),
        "supporting_metrics": grounded_result.get("supporting_metrics", {}),
        "business_interpretation": llm_synthesis.get("business_interpretation", grounded_result.get("interpretation")),
        "model_info": {
            "source": llm_synthesis.get("source"),
            "model_used": llm_synthesis.get("model_used"),
            "fallback_history": llm_synthesis.get("fallback_history", [])
        }
    }


# -----------------------------------------------------------------------------
# FRONTEND STATIC FILES & SPA FALLBACK
# -----------------------------------------------------------------------------

frontend_dist = os.path.join(ROOT_DIR, "frontend", "dist")
if os.path.exists(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        target = os.path.join(frontend_dist, full_path)
        if os.path.exists(target) and os.path.isfile(target):
            return FileResponse(target)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
