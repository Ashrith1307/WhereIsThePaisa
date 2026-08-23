import pandas as pd


def load_and_normalize_data(data_dir="data"):
  """Ingests raw CSV transaction files, normalizes timestamps, cleans string whitespace,

  and casts monetary amounts strictly to integer Paise to prevent float math
  errors.
  """
  orders_df = pd.read_csv(f"{data_dir}/internal_orders.csv")
  settlements_df = pd.read_csv(f"{data_dir}/razorpay_settlements.csv")
  bank_df = pd.read_csv(f"{data_dir}/bank_statements.csv")

  # Clean String Fields (strip trailing spaces or typos)
  orders_df["order_id"] = orders_df["order_id"].astype(str).str.strip()
  settlements_df["ref_order_id"] = (
      settlements_df["ref_order_id"].astype(str).str.strip()
  )
  settlements_df["pg_order_id"] = (
      settlements_df["pg_order_id"].astype(str).str.strip()
  )
  bank_df["pg_order_id"] = bank_df["pg_order_id"].astype(str).str.strip()

  # Datetime Normalization (UTC parsing)
  orders_df["timestamp_utc"] = pd.to_datetime(orders_df["timestamp_utc"])
  settlements_df["timestamp_utc"] = pd.to_datetime(
      settlements_df["timestamp_utc"]
  )
  bank_df["timestamp_utc"] = pd.to_datetime(bank_df["timestamp_utc"])

  # Ensure Paise amounts are strictly cast to integers
  orders_df["base_amount_paise"] = orders_df["base_amount_paise"].astype(int)
  settlements_df["base_amount_paise"] = settlements_df[
      "base_amount_paise"
  ].astype(int)
  settlements_df["net_payout_paise"] = settlements_df[
      "net_payout_paise"
  ].astype(int)
  bank_df["credit_amount_paise"] = bank_df["credit_amount_paise"].astype(int)

  return orders_df, settlements_df, bank_df
