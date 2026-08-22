import pandas as pd


def run_deterministic_stage(orders_df: pd.DataFrame, settlements_df: pd.DataFrame, bank_df: pd.DataFrame):
    """
    Stage 1: Deterministic Engine
    Performs strict primary key lookups and mathematical validation:
    Base Amount - Fee - Tax == Net Payout == Bank Credit UTR
    """
    matched_records = []
    unmatched_orders = []

    # Merge Razorpay settlements with Bank Statements on PG Order ID
    merged_pg_bank = pd.merge(
        settlements_df, bank_df, on="pg_order_id", how="inner", suffixes=("_pg", "_bank")
    )

    for _, order in orders_df.iterrows():
        order_id = order["order_id"]
        base_amt = order["base_amount_paise"]

        # Search for candidate rows matching the exact reference order ID
        candidate = merged_pg_bank[merged_pg_bank["ref_order_id"] == order_id]

        if not candidate.empty:
            row = candidate.iloc[0]

            # Financial integrity math check in integer Paise
            calculated_net = row["base_amount_paise"] - row["fee_paise"] - row["tax_paise"]
            math_valid = (
                (calculated_net == row["net_payout_paise"]) and 
                (row["net_payout_paise"] == row["credit_amount_paise"])
            )

            if math_valid:
                matched_records.append({
                    "order_id": order_id,
                    "pg_order_id": row["pg_order_id"],
                    "bank_utr": row.get("bank_utr", "N/A"),
                    "status": "MATCHED_EXACT",
                    "match_stage": "Stage 1: Deterministic Engine",
                    "discrepancy_paise": 0,
                    "confidence_score": 1.0,
                    "reasoning": "Exact primary key match across DB, PG, and Bank with fully verified fee arithmetic."
                })
                continue

        # If exact match or math fails, route to unmatched pool for Stage 2
        unmatched_orders.append(order)

    matched_df = pd.DataFrame(matched_records)
    unmatched_df = pd.DataFrame(unmatched_orders) if unmatched_orders else pd.DataFrame(columns=orders_df.columns)

    print(f"✓ Stage 1 Complete: {len(matched_df)} exact matches found. {len(unmatched_df)} records routed to Stage 2.")
    return matched_df, unmatched_df
