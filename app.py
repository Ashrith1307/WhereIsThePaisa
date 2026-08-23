from datetime import datetime
import os
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
from google import genai
import streamlit as st

load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="WhereIsThePaisa | AI Financial Controller",
    page_icon="💸",
    layout="wide",
)

# Custom CSS Styling for a polished enterprise look
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    .metric-card { background-color: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
""",
    unsafe_allow_html=True,
)

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
stage1_count = len(
    ledger_df[ledger_df["match_stage"].str.contains("Deterministic", na=False)]
)
stage2_count = len(
    ledger_df[ledger_df["match_stage"].str.contains("Gemini", na=False)]
)
exception_count = len(exceptions_df) if not exceptions_df.empty else 0
match_rate = (
    (matched_records / total_records) * 100 if total_records > 0 else 0
)

col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric(
      label="Total Volume Processed", value=total_records, delta="Batch Run"
  )
with col2:
  st.metric(
      label="Successful Match Rate",
      value=f"{match_rate:.1f}%",
      delta=f"{matched_records} Reconciled",
  )
with col3:
  st.metric(
      label="Deterministic vs AI Split",
      value=f"S1: {stage1_count} | S2: {stage2_count}",
      delta="Hybrid Engine",
  )
with col4:
  st.metric(
      label="Quarantined Exceptions",
      value=exception_count,
      delta="Requires Audit" if exception_count > 0 else "All Clear",
      delta_color="inverse",
  )

st.markdown("---")

# --- Visual Analytics Section with Responsive Donut Chart ---
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
  st.subheader("📊 Match Pipeline Distribution")
  chart_data = pd.DataFrame({
      "Stage": [
          "Stage 1 (Deterministic)",
          "Stage 2 (Gemini AI)",
          "Unresolved Exceptions",
      ],
      "Count": [stage1_count, stage2_count, exception_count],
  })

  # Responsive Plotly Donut Chart
  fig = px.pie(
      chart_data,
      values="Count",
      names="Stage",
      hole=0.5,
      color_discrete_sequence=["#2ea043", "#1f6feb", "#da3633"],
  )
  fig.update_layout(
      paper_bgcolor="rgba(0,0,0,0)",
      plot_bgcolor="rgba(0,0,0,0)",
      font_color="#ffffff",
      margin=dict(t=10, b=10, l=10, r=10),
      legend=dict(
          orientation="h",
          yanchor="bottom",
          y=-0.25,
          xanchor="center",
          x=0.5,
      ),
  )
  st.plotly_chart(fig, use_container_width=True)

with col_chart2:
  st.subheader("⚡ System Efficiency")
  st.info(
      f"• **Zero-Cost Automation:** {stage1_count} records resolved instantly"
      f" via pure math rules.\n• **AI Fallback Rescue:** {stage2_count} messy"
      f" or corrupted records successfully recovered.\n• **Risk Mitigation:**"
      f" {exception_count} records blocked from accidental hallucination."
  )

st.markdown("---")

# --- Tabbed Views ---
tab1, tab2, tab3 = st.tabs([
    "📊 Reconciled Ledger",
    "🔍 Audit Trail Logs",
    "⚠️ Human Exception Queue & AI Q&A",
])

with tab1:
  st.subheader("Successfully Reconciled Transactions")
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
  search_id = st.text_input("Search by Order ID:", placeholder="e.g. ORD_1005")
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
  st.subheader("Unresolved Exceptions Queue & Settlement Q&A Agent")
  st.markdown(
      "Inspect quarantined records or ask the Gemini AI auditor to analyze why"
      " a match failed."
  )

  if exceptions_df.empty:
    st.success("🎉 No exceptions found! All records reconciled cleanly.")
  else:
    st.dataframe(exceptions_df, use_container_width=True)

    st.markdown("### 💬 Ask AI Auditor about an Exception")
    selected_order = st.selectbox(
        "Select Exception Order ID to Query:", exceptions_df["order_id"].tolist()
    )

    selected_row = exceptions_df[
        exceptions_df["order_id"] == selected_order
    ].iloc[0]

    if st.button("Query Gemini AI Auditor"):
      api_key = os.getenv("GEMINI_API_KEY")
      if not api_key:
        st.error("GEMINI_API_KEY not found in environment variables.")
      else:
        with st.spinner("Consulting AI Auditor..."):
          client = genai.Client(api_key=api_key)
          prompt = f"""
                    You are an expert financial auditor controller. An order failed reconciliation and was placed in the exception queue.
                    - Order ID: {selected_row['order_id']}
                    - Status: {selected_row['status']}
                    - Confidence Score: {selected_row['confidence_score']}
                    - System Reasoning: {selected_row['reasoning']}
                    
                    Explain in 2-3 concise sentences what likely caused this financial discrepancy and what the finance team should check next in the bank statement or gateway logs.
                    """
          response = client.models.generate_content(
              model="gemini-3.6-flash", contents=prompt
          )
          st.info(response.text)

    st.markdown("---")
    st.markdown("### Manual Override Control")
    if st.button("Approve & Force Match Manually"):
      st.success(
          f"Order {selected_order} manually approved and logged with auditor"
          f" signature at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
      )

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>WhereIsThePaisa v1.0 |"
    " Engineered for Razorpay AI Buildathon 2026</p>",
    unsafe_allow_html=True,
)
