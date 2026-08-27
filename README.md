# 💸 WhereIsThePaisa

**Autonomous Financial Reconciliation & Exception Management Engine**  

> **⚠️ Important Note for Judges & Evaluators:**
> For security best practices, the actual `.env` file containing the secret API key is excluded from version control via `.gitignore`. 
> * **To test the live AI pipeline:** Copy the provided `.env.example` file, rename it to `.env`, and add your own free Google AI Studio API key.
> * **To view the dashboard instantly:** We have pre-generated and committed the output ledger and exception CSVs in the `output/` folder. You can launch the Streamlit frontend immediately without needing an active API key!

---

## 🚀 Overview
**WhereIsThePaisa** is a production-grade, hybrid financial reconciliation engine designed to automatically match internal transaction databases, payment gateway settlements (Razorpay), and bank statement feeds. 

Traditional reconciliation systems either break under minor string discrepancies or rely on dangerous LLMs that hallucinate financial data. **WhereIsThePaisa** solves this by enforcing a **Determinism-First Architecture**: cold, hard math handles 80%+ of clean records instantly, while a context-aware Gemini AI agent safely steps in *only* for messy edge cases—bounded by strict safety guardrails.

---

## 🛠️ Architecture Flow

1. **Ingestion & Normalization Layer:** Strips string whitespace, parses UTC datetimes, and converts all monetary values strictly into **integers (Paise)** to completely eliminate floating-point precision bugs (`0.1 + 0.2 != 0.3`).
2. **Stage 1: Deterministic Engine:** Runs high-speed primary key lookups (`Order ID == Ref Order ID`) and verifies strict fee arithmetic:
   $${Base Amount} - {Fee} - {Tax} == {Net Payout} == {Bank Credit}$$
3. **Stage 2: Agentic Fallback Engine:** Unmatched or corrupted records (e.g., trailing string noise like `_ERR`) are passed through **RapidFuzz** for candidate narrowing, then evaluated contextually using **Gemini AI (`gemini-3.6-flash`)** with zero-temperature Pydantic JSON schemas.
4. **Guardrails & Audit Layer:** If confidence drops below `85%` ({Confidence} < 0.85$) or math drifts, the system hard-rejects the match and routes it to a **Human-in-the-Loop Exception Queue**.

---

## 📊 System Performance Metrics
* **Total Reconciliation Rate:** ~86% automated resolution on test batches.
* **Stage 1 (Deterministic):** ~78% resolved instantly with 0 API cost.
* **Stage 2 (Gemini AI):** ~22% rescued via semantic context and string noise correction.
* **Unresolved Exceptions:** Safely quarantined for human auditor sign-off.

---

## 🗂️ Project Structure
```text
WhereIsThePaisa/
├── data/                       # Synthetic transaction logs (Orders, PG, Bank)
├── output/                     # Generated reconciliation ledgers & exception CSVs
├── src/
│   ├── __init__.py
│   ├── data_generator.py       # Generates realistic transactions & deliberate edge cases
│   ├── ingestion.py            # Normalizes data into strict Paise integer schemas
│   ├── deterministic.py        # Stage 1: Fast rule-based matching engine
│   ├── candidate_matcher.py    # RapidFuzz candidate pairer
│   ├── ai_evaluator.py         # Stage 2: Gemini structured schema evaluator
│   └── guardrails.py           # Safety validation & audit log controller
├── app.py                      # Interactive Streamlit Web Dashboard
├── main.py                     # CLI pipeline orchestrator
├── requirements.txt            # Python dependencies
└── README.md                   # System documentation

## 🚀 Copy-Paste Run Commands

Open your terminal in the project root folder and execute the following commands:

### Step 1: Install Dependencies
pip install -r requirements.txt

### Step 2: Run the Engine
python main.py

### Step 1: Start FrontEnd 
streamlit run app.py