"""
Domain & Prompt-Injection Guardrails.
Independent application-level filter ensuring strict domain boundaries and zero credential leakage.
Operates BEFORE any LLM prompt is constructed.
"""

import re
from typing import Tuple, Dict, Any

# Strict Payment/UPI/Fraud Domain Keywords
ALLOWED_DOMAIN_KEYWORDS = [
    'transaction', 'txn', 'upi', 'payment', 'chargeback', 'dispute',
    'merchant', 'mch', 'customer', 'user', 'usr', 'kyc', 'fraud',
    'ring', 'syndicate', 'risk', 'volume', 'amount', 'ratio', 'rate',
    'settlement', 'account', 'utr', 'mcc', 'category', 'status',
    'failed', 'success', 'pending', 'aadhaar', 'pan', 'ticket', 'delay',
    'quarter', 'trend', 'day', 'hour', 'severity', 'channel', 'resolution',
    'highest', 'top', 'lowest', 'rank', 'breakdown', 'distribution',
    'cluster', 'network', 'bipartite', 'graph', 'investigate', 'dossier',
    'data rescue', 'duplicate', 'missing', 'profiling', 'audit', 'synthetic',
    'important', 'importance', 'impact', 'significance', 'meaning',
    'explain', 'interpretation', 'business', 'consequence', 'why is it important'
]

# Prompt-Injection & System Exfiltration Blacklist
INJECTION_PATTERNS = [
    r'ignore (all|your|previous|above|the)?\s*(instructions|rules|prompts|guidelines)',
    r'forget (the|your|all)?\s*(dataset|rules|instructions|system prompt|role|context)',
    r'act as (a|an)?\s*(general assistant|dan|jailbreak|unrestricted|hacker|pirate)',
    r'dan\s*mode',
    r'disregard (all)?\s*(instructions|rules|guidelines)',
    r'system\s*(prompt|instructions|override)',
    r'developer\s*(instructions|prompt|mode)',
    r'reveal (the|your)?\s*(prompt|instructions|api key|secret|env|environment|credentials)',
    r'what (are|is) your (system prompt|hidden instructions|api key|secret|credentials)',
    r'show (me)?\s*(the)?\s*(api key|env|password|token|secret|credentials|developer instructions)',
    r'override (system|safety|security|domain|filter)',
    r'print (your)?\s*(prompt|secret|token|api_key|credentials|admin)',
    r'expose (keys|credentials|variables|secrets)',
    r'admin\s*(credentials|password|access)',
    r'who created you',
    r'tell me a (joke|poem|story|recipe)',
    r'write (a|an)?\s*(python script|poem|essay|code|script) for',
    r'capital of',
    r'weather in',
    r'who won the',
    r'translate to'
]

INJECTION_REGEXES = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def validate_query_domain(query: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates user question against domain restrictions and prompt injection attacks.
    Returns: (is_valid, response_or_cleaned_query, metadata)
    """
    if not query or not query.strip():
        return False, "Please enter a valid analytical question regarding UPI payments or fraud telemetry.", {'status': 'EMPTY_QUERY'}
    
    cleaned = query.strip()
    
    # 1. Prompt-Injection Check
    for regex in INJECTION_REGEXES:
        if regex.search(cleaned):
            return False, (
                "Security Alert: That request attempts to override system safety guardrails or access non-domain resources. "
                "I am strictly constrained to UPI transactions, fraud intelligence, merchant risk, KYC, and chargeback analytics."
            ), {'status': 'PROMPT_INJECTION_BLOCKED'}
            
    # 2. Strict Domain Keyword & Intent Check
    lowered = cleaned.lower()
    
    # Check if query contains at least one recognized payment/fraud/dashboard domain concept
    matched_keywords = [kw for kw in ALLOWED_DOMAIN_KEYWORDS if kw in lowered]
    
    if not matched_keywords:
        return False, (
            "That is outside my field. I can only assist with UPI transactions, fraud, "
            "KYC/identity risk, merchant risk, chargebacks, and related analytics in this platform."
        ), {'status': 'OUT_OF_DOMAIN_BLOCKED'}
        
    return True, cleaned, {'status': 'DOMAIN_APPROVED', 'matched_keywords': matched_keywords}
