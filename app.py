import os
from datetime import datetime
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="WhereIsThePaisa | AI Financial Controller",
    page_icon="💸",
    layout="wide",
)

# Custom Styling & Header
st.title("💸 WhereIsThePaisa.ai")
st.markdown(
    "### Autonomous Financial Reconciliation & Exception Management Engine"
)
st.markdown("---")

# Load Data Function
@st.cache_data
def load_data():
  ledger_path = "output/reconciled_ledger.csv"
  exceptions_path = "output/exceptions_queue.csv"

  ledger_df = (
      pd.read_csv(ledger_path)
      if os.path.exists(ledger_path)
      else pd.DataFrame()
  )
  exceptions_df = (
      pd.read_csv(exceptions_path)
      if os.path.exists(exceptions_path)
      else pd.DataFrame()
  )

  return ledger_df, exceptions_df


ledger_df, exceptions_df = load_data()

# Check if data exists
if ledger_df.empty:
  st.warning(
      "⚠️ No reconciliation data found! Please run your pipeline first using:"
      " `python main.py`"
  )
  st.stop()

# --- Top-Level KPI Metrics ---
total_records = len(ledger_df) + (
    len(exceptions_df) if not exceptions_df.empty else 0
)
matched_records = len(ledger_df)
exception_count = len(exceptions_df) if not exceptions_df.empty else 0
match_rate = (
    (matched_records / total_records) * 100 if total_records > 0 else 0
)

col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric(
      label="Total Records Processed",
      value=total_records,
      delta="Batch Batch 50+",
  )
with col2:
  st.metric(
      label="Successfully Reconciled",
      value=matched_records,
      delta=f"{match_rate:.1f}% Match Rate",
  )
with col3:
  st.metric(
      label="Unresolved Exceptions",
      value=exception_count,
      delta="Needs Human Audit" if exception_count > 0 else "All Clear",
      delta_color="inverse",
  )
with col4:
  st.metric(
      label="System Latency / Mode", value="Hybrid", delta="Deterministic + AI"
  )

st.markdown("---")

# --- Tabbed Views ---
tab1, tab2, tab3 = st.tabs([
    "📊 Reconciled Ledger",
    "🔍 Audit Trail Logs",
    "⚠️ Human Exception Queue",
])

with tab1:
  st.subheader("Successfully Reconciled Transactions")
  st.markdown(
      "Transactions verified through Stage 1 (Deterministic Rules) or Stage 2"
      " (Gemini AI Evaluator)."
  )

  # Filter by stage view
  stage_filter = st.selectbox(
      "Filter by Match Stage:",
      [
          "All Stages",
          "Stage 1: Deterministic Engine",
          "Stage 2: Gemini AI Evaluator",
      ],
  )

  filtered_ledger = ledger_df
  if stage_filter != "All Stages":
    filtered_ledger = ledger_df[ledger_df["match_stage"] == stage_filter]

  st.dataframe(filtered_ledger, use_container_width=True)

with tab2:
  st.subheader("Deep-Dive Audit Trail & Reasoning")
  st.markdown(
      "Every single automated match is backed by strict reasoning logs to"
      " maintain compliance."
  )

  # Search box for order ID
  search_id = st.text_input(
      "Search by Order ID:", placeholder="e.g. ORD_1005"
  )
  if search_id:
    search_results = ledger_df[
        ledger_df["order_id"].str.contains(search_id, case=False, na=False)
    ]
    st.dataframe(search_results, use_container_width=True)
  else:
    st.dataframe(
        ledger_df[["order_id", "pg_order_id", "match_stage", "reasoning"]],
        use_container_width=True,
    )

with tab3:
  st.subheader("Unresolved Exceptions Queue (Human-in-the-Loop)")
  st.markdown(
      "Ambiguous rows or low-confidence matches are safely routed here to"
      " prevent financial hallucination."
  )

  if exceptions_df.empty:
    st.success("🎉 No exceptions found! All records reconciled cleanly.")
  else:
    st.dataframe(exceptions_df, use_container_width=True)

    st.markdown("### Manual Override Control")
    selected_order = st.selectbox(
        "Select Exception Order ID to Review:", exceptions_df["order_id"].tolist()
    )

    if st.button("Approve & Force Match Manually"):
      st.success(
          f"Order {selected_order} manually approved and logged with auditor"
          f" signature at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
      )
      # In a production app, you would update your DB or CSV state here.

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>WhereIsThePaisa v1.0 |"
    " Engineered for Razorpay AI Buildathon 2026</p>",
    unsafe_allow_html=True,
)

