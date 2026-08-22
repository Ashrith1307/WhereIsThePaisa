import os
import random
import csv
from datetime import datetime, timedelta


def generate_synthetic_data(num_records: int = 50, output_dir: str = "data") -> None:
    """
    Generates synthetic datasets for internal orders, Razorpay settlements,
    and bank statements with clean matches and synthetic edge cases.
    """
    os.makedirs(output_dir, exist_ok=True)
    random.seed(42)

    start_time = datetime(2026, 8, 22, 10, 0, 0)

    orders = []
    settlements = []
    bank_statements = []

    for i in range(1, num_records + 1):
        order_id = f"ORD_{1000 + i}"
        pg_order_id = f"pay_RZP_{5000 + i}"
        utr_no = f"UTR_ICICI_{9000 + i}"

        # Store currency strictly in Paise (integers) to prevent float precision bugs
        base_amount_paise = random.randint(500, 50000) * 100
        fee_paise = int(base_amount_paise * 0.02)  # 2% gateway fee
        tax_paise = int(fee_paise * 0.18)          # 18% GST on fee
        net_payout_paise = base_amount_paise - fee_paise - tax_paise

        timestamp = start_time + timedelta(minutes=random.randint(1, 300))

        # Edge case classification
        if i % 7 == 0:
            case_type = "UNMATCHED"      # Missing in PG/Bank -> Routes to UNRESOLVED_EXCEPTION
        elif i % 5 == 0:
            case_type = "CORRUPTED_ID"  # String noise -> Target for RapidFuzz + Gemini API
        else:
            case_type = "CLEAN"         # Standard exact match

        # 1. Internal Orders Database Entry
        orders.append({
            "order_id": order_id,
            "customer_id": f"CUST_{i}",
            "base_amount_paise": base_amount_paise,
            "timestamp_utc": timestamp.isoformat()
        })

        # 2. Razorpay Settlement & Bank Statement Entries
        if case_type != "UNMATCHED":
            settlement_ref_id = f"{order_id}_ERR" if case_type == "CORRUPTED_ID" else order_id

            settlements.append({
                "pg_order_id": pg_order_id,
                "ref_order_id": settlement_ref_id,
                "base_amount_paise": base_amount_paise,
                "fee_paise": fee_paise,
                "tax_paise": tax_paise,
                "net_payout_paise": net_payout_paise,
                "timestamp_utc": (timestamp + timedelta(seconds=12)).isoformat()
            })

            bank_statements.append({
                "bank_utr": utr_no,
                "pg_order_id": pg_order_id,
                "credit_amount_paise": net_payout_paise,
                "timestamp_utc": (timestamp + timedelta(minutes=2)).isoformat()
            })

    # Save outputs to CSV files without requiring third-party dependencies.
    def write_csv(filename: str, rows: list[dict]) -> None:
        with open(f"{output_dir}/{filename}", "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=rows[0].keys() if rows else [])
            writer.writeheader()
            writer.writerows(rows)

    write_csv("internal_orders.csv", orders)
    write_csv("razorpay_settlements.csv", settlements)
    write_csv("bank_statements.csv", bank_statements)

    print(f"✓ Successfully generated {num_records} synthetic records in '{output_dir}/' directory.")


if __name__ == "__main__":
    generate_synthetic_data()
