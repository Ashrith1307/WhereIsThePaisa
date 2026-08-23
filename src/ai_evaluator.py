import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import pandas as pd


class ReconciliationDecision(BaseModel):
    matched: bool = Field(description="True if the transaction pair matches completely, false otherwise.")
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0.")
    reasoning: str = Field(description="Explanation of why this match is valid or rejected.")


def evaluate_with_gemini(candidate_row: pd.Series) -> dict:
    """
    Passes a single candidate pair to Gemini API for context verification.
    Enforces strict safety guardrails against financial hallucination.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")

    client = genai.Client(api_key=api_key)

    base = candidate_row["order_amount_paise"]
    fee = candidate_row["candidate_fee_paise"]
    tax = candidate_row["candidate_tax_paise"]
    expected_net = base - fee - tax
    actual_payout = candidate_row["candidate_payout_paise"]

    prompt = f"""
    You are a strict financial auditor AI controller for an automated ledger system.
    Evaluate if the following Internal Order matches the Gateway Settlement record.
    
    - Internal Order ID: {candidate_row["order_id"]}
    - Gateway Ref ID: {candidate_row["candidate_ref_id"]} (Note: may contain string noise)
    - Order Base Amount (Paise): {base}
    - Calculated Expected Net Payout (Base - Fee - Tax): {expected_net}
    - Actual Gateway Net Payout (Paise): {actual_payout}
    - String Similarity Score: {candidate_row["string_similarity_score"]}%
    
    Rules for matching:
    1. The reference IDs represent the same transaction if string noise is minor (e.g. trailing '_ERR').
    2. The math MUST balance precisely: Expected Net Payout == Actual Gateway Net Payout.
    3. If there is any doubt or financial discrepancy, you MUST return matched=false. Never guess or hallucinate matches.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ReconciliationDecision,
                temperature=0.0
            ),
        )
        
        result = json.loads(response.text)
        
        # Hard code guardrail threshold (< 0.85 forced to exception)
        if result.get("confidence_score", 0.0) < 0.85 or not result.get("matched", False):
            return {
                "status": "UNRESOLVED_EXCEPTION",
                "confidence": result.get("confidence_score", 0.0),
                "reasoning": f"Rejected by guardrail: {result.get('reasoning', 'Low confidence or math mismatch.')}"
            }
            
        return {
            "status": "MATCHED_AI",
            "confidence": result.get("confidence_score"),
            "reasoning": result.get("reasoning")
        }

    except Exception as e:
        return {
            "status": "UNRESOLVED_EXCEPTION",
            "confidence": 0.0,
            "reasoning": f"API Evaluation Error: {str(e)}"
        }
