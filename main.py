import os
from dotenv import load_dotenv
import pandas as pd

from src.ai_evaluator import evaluate_with_gemini
from src.candidate_matcher import find_candidates
from src.data_generator import generate_synthetic_data
from src.deterministic import run_deterministic_stage
from src.ingestion import load_and_normalize_data

# Load environment variables (such as GEMINI_API_KEY from .env file
load_dotenv()


def main():
  print("=" * 60)
  print(" 💸 RUNNING: WhereIsThePaisa - AI Financial Reconciliation Engine 💸")
  print("=" * 60)

  # Step 1: Generate synthetic data if not already present
  if not os.path.exists("data/internal_orders.csv"):
    print("\n[Step 1] Generating synthetic transactions...")
    generate_synthetic_data(num_records=50)
  else:
    print("\n[Step 1] Synthetic data files found in 'data/' directory.")

  # Step 2: Load and Normalize Ingestion Layer
  print("\n[Step 2] Loading and normalizing datasets...")
  orders_df, settlements_df, bank_df = load_and_normalize_data()
  print(
      f"Loaded -> Orders: {len(orders_df)} | Settlements:"
      f" {len(settlements_df)} | Bank Feeds: {len(bank_df)}"
  )

  # Step 3: Run Stage 1 (Deterministic Matcher)
  print("\n[Step 3] Executing Stage 1: Deterministic Engine...")
  matched_stage1, unmatched_orders = run_deterministic_stage(
      orders_df, settlements_df, bank_df
  )

  # Step 4: Run Stage 2 (Agentic Fallback Engine with RapidFuzz & Gemini)
  print(
      "\n[Step 4] Executing Stage 2: Agentic Fallback Engine (RapidFuzz +"
      " Gemini AI)..."
  )

  ai_matched_df = pd.DataFrame()
  exceptions_df = pd.DataFrame()

  if unmatched_orders.empty:
    print("No unmatched records remaining from Stage 1. Skipping Stage 2.")
    final_matched_df = matched_stage1
  else:
    print("Finding candidate pairs via RapidFuzz string distance...")
    candidates_df = find_candidates(
        unmatched_orders, settlements_df, threshold=50.0
    )
    print(f"Found {len(candidates_df)} candidate pairs for AI verification.")

    ai_matched_records = []
    unresolved_exceptions = []

    # Process each candidate through Gemini API evaluation with guardrails
    for _, candidate in candidates_df.iterrows():
      print(
          f"Evaluating Order: {candidate['order_id']} against PG Ref:"
          f" {candidate['candidate_ref_id']}..."
      )
      decision = evaluate_with_gemini(candidate)

      if decision["status"] == "MATCHED_AI":
        ai_matched_records.append({
            "order_id": candidate["order_id"],
            "pg_order_id": candidate["candidate_pg_id"],
            "bank_utr": "N/A (AI Resolved)",
            "status": "MATCHED_AI",
            "match_stage": "Stage 2: Gemini AI Evaluator",
            "discrepancy_paise": 0,
            "confidence_score": decision["confidence"],
            "reasoning": decision["reasoning"],
        })
      else:
        unresolved_exceptions.append({
            "order_id": candidate["order_id"],
            "status": "UNRESOLVED_EXCEPTION",
            "confidence_score": decision["confidence"],
            "reasoning": decision["reasoning"],
        })

    ai_matched_df = pd.DataFrame(ai_matched_records)
    exceptions_df = pd.DataFrame(unresolved_exceptions)

    # Combine exact matches and AI-resolved matches
    final_matched_df = pd.concat(
        [matched_stage1, ai_matched_df], ignore_index=True
    )

  # Step 5: Final Summary Report
  print("\n" + "=" * 60)
  print(" 📊 WHEREISPAISA - FINAL RECONCILIATION REPORT")
  print("=" * 60)

  total_orders = len(orders_df)
  total_matched = len(final_matched_df)
  total_exceptions = (
      len(exceptions_df) if not exceptions_df.empty else len(unmatched_orders)
  )
  match_rate = (total_matched / total_orders) * 100 if total_orders > 0 else 0

  print(f"• Total Records Processed: {total_orders}")
  print(f"• Successfully Reconciled: {total_matched} ({match_rate:.2f}%)")
  print(f"  - Stage 1 (Deterministic): {len(matched_stage1)}")
  print(f"  - Stage 2 (Gemini AI):    {len(ai_matched_df)}")
  print(
      f"• Unresolved Exceptions:     {total_exceptions} (Routed to Human"
      " Review Queue)"
  )
  print("=" * 60)

  # Step 6: Export Outputs for Streamlit Dashboard
  os.makedirs("output", exist_ok=True)
  final_matched_df.to_csv("output/reconciled_ledger.csv", index=False)
  if not exceptions_df.empty:
    exceptions_df.to_csv("output/exceptions_queue.csv", index=False)

  print(
      "\n✓ Output logs saved successfully to 'output/' folder for the Streamlit"
      " dashboard!"
  )


if __name__ == "__main__":
  main()
