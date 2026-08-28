# NetSage AI — Network Troubleshooting Assistant with Human Review

NetSage AI is an AI-assisted network troubleshooting helper for Cisco Packet Tracer labs. It analyzes network symptoms and show-command outputs to suggest root causes and fix steps, while enforcing a strict safety requirement: **all diagnoses must be audited and approved/edited by a human reviewer before accepting the fix.**

It also features a deterministic local rules engine (non-AI) to catch basic configuration violations automatically.

---

## 🚀 Live Demo
The application is deployed and reachable at:
**[NetSage AI Live App on Streamlit Cloud](https://netsage-ai.streamlit.app)** *(Sample URL - replace with your actual deployment link)*

*Note: The live demo runs in offline/demo mode by default using pre-generated diagnoses. If you add your `ANTHROPIC_API_KEY` to the Streamlit secrets, you can trigger live AI diagnostics dynamically.*

---

## 📁 Repository Structure
```
netsage-ai/
├── app.py                          # Streamlit dashboard + review UI (deployed entrypoint)
├── requirements.txt                # Python package dependencies
├── .env.example                    # Template for ANTHROPIC_API_KEY
├── .gitignore                      # Git exclusion rules
├── README.md                       # This document
├── data/
│   ├── cases.csv                   # 32 compiled networking cases
│   ├── sample_network_state.json   # Seeded config state for rule checker
│   ├── ai_diagnoses.json           # Pre-generated AI diagnoses
│   └── human_review.csv            # Audit review logs (updated live)
├── prompts/
│   ├── diagnose_prompt.md          # LLM system prompt & few-shot examples
│   └── explain_evidence_prompt.md  # LLM plain-English evidence explainer
├── src/
│   ├── generate_cases.py           # Programmatic case dataset compiler
│   ├── rule_checker.py             # Deterministic rule checker logic
│   ├── ai_diagnose.py              # AI diagnosis runner script
│   ├── review_workflow.py          # Human audit review logic
│   └── dashboard_data.py           # KPI metrics aggregator
├── tests/
│   └── test_rule_checker.py        # pytest unit tests for the rule checker
├── logs/
│   └── responsible_ai_log.md       # Log of 5 corrected AI mistakes
└── docs/
    ├── PROJECT_DOCUMENTATION.md    # Detailed project documentation
    └── demo_video_script.md        # Recording script for demo video
```

---

## ⚙️ Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone <repository-url> netsage-ai
   cd netsage-ai
   ```

2. **Install Dependencies:**
   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Configure Environment Variables (Optional for live AI calls):**
   Copy the example environment file and add your Anthropic API Key:
   ```bash
   cp .env.example .env
   # Edit .env and set: ANTHROPIC_API_KEY=your-actual-api-key
   ```

---

## 🏃 How to Run

### 1. Run Automated Unit Tests (Rule Checker)
Execute `pytest` to run all 12 positive and negative tests on the deterministic rules engine:
```bash
python -m pytest tests/
```

### 2. Run the Streamlit App Locally
Start the local development server:
```bash
python -m streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### 3. Generate the Dataset Programmatically (Optional)
If you wish to reset or modify the troubleshooting cases:
```bash
python src/generate_cases.py
```

### 4. Run AI Diagnostics in CLI
To run diagnosis on all cases or a single case via command line:
```bash
# Run in offline fallback mode (uses expected_fault stubs)
python src/ai_diagnose.py --offline

# Run in live mode (requires ANTHROPIC_API_KEY environment variable)
python src/ai_diagnose.py
```

---

## 🛡️ Responsible AI & Safety Guardrail
NetSage AI enforces a **strict safety protocol**:
- The system **never auto-applies** any suggested configuration change.
- The UI exposes a "Human Oversight Audit Form" on every case. A human engineer must mark the diagnosis as **Accepted**, **Edited**, or **Rejected**, logging a detailed audit note.
- The dashboard calculates a live **AI-vs-Human Agreement Rate** based on these audits.

---

## ☁️ Deployment Instructions

### Option 1: Streamlit Community Cloud (Recommended)
1. Commit all files and push your repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and log in.
3. Click "New App", select your repository, branch, and specify `app.py` as the main path.
4. In **Advanced Settings**, add the following environment variable to **Secrets** if you want live Claude 3.5 API calls:
   ```toml
   ANTHROPIC_API_KEY = "your_actual_key"
   ```
5. Click **Deploy**.

### Option 2: Render.com (Alternative)
1. Create a Web Service on Render.com connected to your GitHub repository.
2. Set the Environment to **Python**.
3. Set the Build Command to `pip install -r requirements.txt`.
4. Set the Start Command to `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`.
5. Under Environment Variables, add `ANTHROPIC_API_KEY` if needed.
