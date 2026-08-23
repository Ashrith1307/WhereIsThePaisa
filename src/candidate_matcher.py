from rapidfuzz import fuzz, process
import pandas as pd


def find_candidates(unmatched_orders_df: pd.DataFrame, settlements_df: pd.DataFrame, threshold: float = 60.0):
    """
    Uses RapidFuzz to find close reference ID matches for unmatched orders,
    reducing the search space before calling the Gemini AI agent.
    """
    candidates = []
    
    valid_ref_ids = settlements_df["ref_order_id"].tolist()

    for _, order in unmatched_orders_df.iterrows():
        order_id = order["order_id"]
        
        match_result = process.extractOne(order_id, valid_ref_ids, scorer=fuzz.partial_ratio)
        
        if match_result:
            matched_ref_id, score, _ = match_result
            
            if score >= threshold:
                settlement_row = settlements_df[settlements_df["ref_order_id"] == matched_ref_id].iloc[0]
                
                candidates.append({
                    "order_id": order_id,
                    "order_amount_paise": order["base_amount_paise"],
                    "order_timestamp": order["timestamp_utc"],
                    "candidate_pg_id": settlement_row["pg_order_id"],
                    "candidate_ref_id": matched_ref_id,
                    "candidate_payout_paise": settlement_row["net_payout_paise"],
                    "candidate_fee_paise": settlement_row["fee_paise"],
                    "candidate_tax_paise": settlement_row["tax_paise"],
                    "string_similarity_score": score
                })

    return pd.DataFrame(candidates)
