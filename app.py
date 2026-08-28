import streamlit as st
import pandas as pd
import json
import os
import sys
import plotly.express as px
import plotly.graph_objects as go

# Add the project root to sys.path to prevent import issues on Streamlit Cloud
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules from src
from src.dashboard_data import load_dashboard_stats
from src.rule_checker import run_all_checks
from src.review_workflow import load_reviews, save_review
from src.ai_diagnose import run_live, run_offline

# Page Configuration
st.set_page_config(
    page_title="NetSage AI — Network Troubleshooting Helper",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
    /* Main body background and font */
    .stApp {
        background-color: #0e1117;
        color: #e0e6ed;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    
    /* Header styling */
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        color: #ffffff;
    }
    
    /* Custom metric cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s, border-color 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 5px 0;
        color: #818cf8;
    }
    .metric-label {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #94a3b8;
    }
    
    /* Status badges */
    .badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-accepted { background-color: #065f46; color: #34d399; }
    .badge-edited { background-color: #78350f; color: #fbbf24; }
    .badge-rejected { background-color: #991b1b; color: #fca5a5; }
    .badge-unreviewed { background-color: #374151; color: #d1d5db; }
    
    /* Code box styling */
    .cisco-code {
        background-color: #181e29 !important;
        border: 1px solid #2d3748 !important;
        border-radius: 6px !important;
        font-family: 'Consolas', 'Courier New', monospace !important;
        color: #a0aec0 !important;
        padding: 15px !important;
        overflow-x: auto;
    }
    
    /* Subtitle styling */
    .section-title {
        border-bottom: 2px solid rgba(99, 102, 241, 0.3);
        padding-bottom: 8px;
        margin-top: 30px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to reload stats in session state
def refresh_stats():
    st.session_state.stats = load_dashboard_stats()
    st.session_state.reviews = load_reviews()

# Initialize session state variables
if "stats" not in st.session_state or "reviews" not in st.session_state:
    refresh_stats()

# Sidebar Navigation
with st.sidebar:
    st.image("https://img.icons8.com/color/96/artificial-intelligence.png", width=70)
    st.title("NetSage AI")
    st.markdown("*AI Network Assistant with Human Oversight*")
    st.markdown("---")
    
    tab_selection = st.radio(
        "Navigation",
        ["Dashboard Overview", "Case Browser", "Troubleshooting Workspace", "Rule Checker Sandbox", "Responsible AI Log"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### LLM Mode")
    
    api_key_set = os.environ.get("ANTHROPIC_API_KEY") or ""
    if api_key_set:
        st.success("Claude 3.5 API Key Configured")
        run_mode = st.toggle("Force Offline Mode", value=False)
    else:
        st.warning("No API Key - Running Offline Fallback")
        run_mode = True
        
    st.info("Human review is ALWAYS required before a diagnosis is finalized.")

# ----------------------------------------------------
# TAB 1: DASHBOARD OVERVIEW
# ----------------------------------------------------
if tab_selection == "Dashboard Overview":
    st.title("🔍 NetSage AI Dashboard Overview")
    st.markdown("A real-time tracking panel showing diagnostic performance, issue distributions, and human-AI agreement rates.")
    
    # Reload stats dynamically
    stats = load_dashboard_stats()
    
    # Key KPI Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Total Cases</div><div class="metric-value">{stats["total_cases"]}</div></div>', 
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Audited Cases</div><div class="metric-value">{stats["reviewed_cases"]}</div></div>', 
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Pending Review</div><div class="metric-value">{stats["unreviewed_cases"]}</div></div>', 
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">AI-Human Agreement</div><div class="metric-value">{stats["agreement_rate"]:.1f}%</div></div>', 
            unsafe_allow_html=True
        )
        
    st.markdown('<h3 class="section-title">Diagnostic Visualizations</h3>', unsafe_allow_html=True)
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Category breakdown
        cat_df = pd.DataFrame(list(stats["category_counts"].items()), columns=["Category", "Count"])
        fig_cat = px.bar(
            cat_df, 
            x="Count", 
            y="Category", 
            orientation="h",
            title="Troubleshooting Cases by Category",
            color="Count",
            color_continuous_scale="Viridis",
            labels={"Count": "Number of Cases"}
        )
        fig_cat.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e0e6ed',
            title_font_size=16
        )
        st.plotly_chart(fig_cat, use_container_width=True)
        
    with chart_col2:
        # Severity breakdown
        sev_df = pd.DataFrame(list(stats["severity_counts"].items()), columns=["Severity", "Count"])
        # Custom color map for severity
        color_map = {"Critical": "#ef4444", "High": "#f97316", "Medium": "#eab308", "Low": "#3b82f6"}
        fig_sev = px.pie(
            sev_df, 
            values="Count", 
            names="Severity", 
            title="Troubleshooting Cases by Severity",
            hole=0.4,
            color="Severity",
            color_discrete_map=color_map
        )
        fig_sev.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            font_color='#e0e6ed',
            title_font_size=16
        )
        st.plotly_chart(fig_sev, use_container_width=True)
        
    # Second chart row
    chart_col3, chart_col4 = st.columns(2)
    
    with chart_col3:
        # Audit review status breakdown
        status_counts = {"Accepted": stats["accepted_count"], "Disagreed (Edited/Rejected)": stats["disagreed_count"], "Unreviewed": stats["unreviewed_cases"]}
        status_df = pd.DataFrame(list(status_counts.items()), columns=["Status", "Count"])
        fig_status = px.pie(
            status_df,
            values="Count",
            names="Status",
            title="Audit Status Distribution",
            color="Status",
            color_discrete_map={"Accepted": "#10b981", "Disagreed (Edited/Rejected)": "#fbbf24", "Unreviewed": "#6b7280"}
        )
        fig_status.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#e0e6ed',
            title_font_size=16
        )
        st.plotly_chart(fig_status, use_container_width=True)
        
    with chart_col4:
        # OSI layer breakdown
        osi_counts = stats["cases_df"]["osi_layer"].value_counts().to_dict()
        osi_df = pd.DataFrame(list(osi_counts.items()), columns=["OSI Layer", "Count"])
        fig_osi = px.bar(
            osi_df,
            x="OSI Layer",
            y="Count",
            title="Troubleshooting Cases by OSI Layer",
            color="Count",
            color_continuous_scale="Magenta"
        )
        fig_osi.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e0e6ed',
            title_font_size=16
        )
        st.plotly_chart(fig_osi, use_container_width=True)

# ----------------------------------------------------
# TAB 2: CASE BROWSER
# ----------------------------------------------------
elif tab_selection == "Case Browser":
    st.title("📂 Cisco Packet Tracer Case Browser")
    st.markdown("Browse all 30+ generated configuration and troubleshooting scenarios.")
    
    stats = load_dashboard_stats()
    cases_df = stats["cases_df"]
    reviews = load_reviews()
    
    # Filter Row
    col1, col2, col3 = st.columns(3)
    with col1:
        cat_filter = st.selectbox("Filter by Category", ["All"] + list(cases_df["category"].unique()))
    with col2:
        sev_filter = st.selectbox("Filter by Severity", ["All"] + list(cases_df["severity"].unique()))
    with col3:
        osi_filter = st.selectbox("Filter by OSI Layer", ["All"] + list(cases_df["osi_layer"].unique()))
        
    # Apply filters
    filtered_df = cases_df.copy()
    if cat_filter != "All":
        filtered_df = filtered_df[filtered_df["category"] == cat_filter]
    if sev_filter != "All":
        filtered_df = filtered_df[filtered_df["severity"] == sev_filter]
    if osi_filter != "All":
        filtered_df = filtered_df[filtered_df["osi_layer"] == osi_filter]
        
    # Map review status for display
    def get_case_status(row):
        cid = row["case_id"]
        if cid in reviews:
            return reviews[cid]["status"]
        return "Unreviewed"
        
    filtered_df["Audit Status"] = filtered_df.apply(get_case_status, axis=1)
    
    # Render table
    st.write(f"Showing {len(filtered_df)} of {len(cases_df)} cases:")
    
    # Format case view
    display_cols = ["case_id", "category", "osi_layer", "severity", "concept_tag", "symptom", "Audit Status"]
    st.dataframe(
        filtered_df[display_cols],
        column_config={
            "case_id": st.column_config.TextColumn("Case ID", width="medium"),
            "category": "Category",
            "osi_layer": "OSI Layer",
            "severity": "Severity",
            "concept_tag": "Concept Tag",
            "symptom": st.column_config.TextColumn("Symptom", width="large"),
            "Audit Status": "Audit Status"
        },
        hide_index=True,
        use_container_width=True
    )

# ----------------------------------------------------
# TAB 3: TROUBLESHOOTING WORKSPACE
# ----------------------------------------------------
elif tab_selection == "Troubleshooting Workspace":
    st.title("🛠️ Troubleshooting Workspace (Human-in-the-Loop)")
    st.markdown("Select a networking issue, inspect Cisco command output evidence, view AI suggestions, and review/edit the diagnosis.")
    
    stats = load_dashboard_stats()
    cases_df = stats["cases_df"]
    reviews = load_reviews()
    
    # Load AI diagnoses
    ai_diagnoses = {}
    if os.path.exists("data/ai_diagnoses.json"):
        with open("data/ai_diagnoses.json", "r") as f:
            ai_diagnoses = json.load(f)
            
    # Case selector with visual audit status
    case_options = []
    for _, r in cases_df.iterrows():
        cid = r["case_id"]
        status = reviews[cid]["status"] if cid in reviews else "Unreviewed"
        case_options.append(f"{cid} - {r['category']} - {r['symptom'][:60]}... ({status})")
        
    selected_option = st.selectbox("Select a Troubleshooting Case to Inspect:", case_options)
    
    # Extract case ID
    selected_case_id = selected_option.split(" - ")[0]
    case_row = cases_df[cases_df["case_id"] == selected_case_id].iloc[0]
    
    # UI Columns: Case Details (Left) vs AI Diagnosis + Human Review (Right)
    left_col, right_col = st.columns(2)
    
    with left_col:
        st.markdown('<h3 class="section-title">Case Evidence</h3>', unsafe_allow_html=True)
        
        st.markdown(f"**Case ID:** `{case_row['case_id']}`")
        st.markdown(f"**Category:** `{case_row['category']}` | **Severity:** `{case_row['severity']}` | **OSI Layer:** `{case_row['osi_layer']}`")
        st.markdown(f"**Symptom:** *{case_row['symptom']}*")
        st.info(f"**Topology Context:** {case_row['topology_note']}")
        
        st.markdown("**Cisco CLI Show Commands Output:**")
        st.code(case_row["show_output"], language="routeros")
        
    with right_col:
        st.markdown('<h3 class="section-title">Diagnostic & Safety Review</h3>', unsafe_allow_html=True)
        
        # Load pre-generated or run live AI
        ai_diag = ai_diagnoses.get(selected_case_id)
        
        # Re-run Live AI Diagnostic Option
        if st.button("🔄 Trigger Live AI Re-Diagnosis"):
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                st.error("Cannot run live diagnosis: ANTHROPIC_API_KEY is not set.")
            else:
                with st.spinner("Calling Claude 3.5 Sonnet..."):
                    run_live("data/cases.csv", api_key, selected_case_id)
                    # Reload diagnoses
                    if os.path.exists("data/ai_diagnoses.json"):
                        with open("data/ai_diagnoses.json", "r") as f:
                            ai_diagnoses = json.load(f)
                        ai_diag = ai_diagnoses.get(selected_case_id)
                        st.success("Successfully completed live AI API round-trip diagnosis!")
                        
        if not ai_diag:
            st.warning("No pre-generated AI diagnosis found for this case. Generating offline stub...")
            run_offline("data/cases.csv", selected_case_id)
            with open("data/ai_diagnoses.json", "r") as f:
                ai_diagnoses = json.load(f)
            ai_diag = ai_diagnoses.get(selected_case_id)
            
        # Display AI output fields
        is_stub = ai_diag.get("_offline_stub", False)
        if is_stub:
            st.caption("⚠️ *Offline fall-back mode: Stub result matching known target is displayed.*")
        else:
            st.caption("✨ *Live Claude 3.5 Sonnet analysis output*")
            
        # UI showing what the AI proposed
        st.markdown(f"**AI Suggested Root Cause:**")
        st.write(ai_diag.get("root_cause", ""))
        
        st.markdown(f"**OSI Layer:** `{ai_diag.get('osi_layer', '')}` | **Confidence:** `{ai_diag.get('confidence', '')}`")
        
        st.markdown("**Supporting Evidence Quoted by AI:**")
        st.info(ai_diag.get("evidence", ""))
        
        st.markdown(f"**Verification Command:** `{ai_diag.get('next_command', '')}`")
        
        st.markdown("**AI Recommended CLI Fix Steps:**")
        st.code(ai_diag.get("fix_steps", ""), language="routeros")
        
        security_flag = ai_diag.get("security_issue", False)
        if security_flag:
            st.error("🛡️ AI flagged this issue as a potential Security Vulnerability!")
        else:
            st.success("🛡️ AI marked this issue as standard configuration (no security threat).")
            
        # Audit review section
        st.markdown('<h3 class="section-title">Human Oversight Audit Form</h3>', unsafe_allow_html=True)
        
        # Display current status if already reviewed
        current_review = reviews.get(selected_case_id)
        if current_review:
            status = current_review["status"]
            if status == "Accepted":
                st.success(f"Audit Status: ACCEPTED")
            elif status == "Edited":
                st.warning(f"Audit Status: EDITED")
            else:
                st.error(f"Audit Status: REJECTED")
            st.markdown(f"**Reviewer Note:** *{current_review['reviewer_note']}*")
            st.markdown("---")
            
        # Form to Accept / Edit / Reject
        with st.form("human_review_form"):
            st.write("Determine the validity of this diagnosis and submit the audit record:")
            audit_status = st.selectbox("Action", ["Accept", "Edit / Correct", "Reject"], index=0)
            reviewer_note = st.text_area("Reviewer Audit Log Note (explain why or details of correction):", 
                                          value=current_review["reviewer_note"] if current_review else "")
            
            # Edit fields (only active if Edit is selected)
            st.write("---")
            st.write("*(Below fields are only applied if 'Edit / Correct' is chosen)*")
            corrected_root_cause = st.text_input("Corrected Root Cause:", value=current_review.get("corrected_root_cause", ai_diag.get("root_cause", "")) if current_review else ai_diag.get("root_cause", ""))
            corrected_osi = st.selectbox("Corrected OSI Layer:", ["Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 7"], 
                                         index=["Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 7"].index(current_review.get("corrected_osi_layer", ai_diag.get("osi_layer", "Layer 3")) if current_review and current_review.get("corrected_osi_layer") in ["Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 7"] else ai_diag.get("osi_layer", "Layer 3")))
            corrected_conf = st.selectbox("Corrected Confidence:", ["High", "Medium", "Low"], 
                                          index=["High", "Medium", "Low"].index(current_review.get("corrected_confidence", ai_diag.get("confidence", "High")) if current_review and current_review.get("corrected_confidence") in ["High", "Medium", "Low"] else ai_diag.get("confidence", "High")))
            corrected_fix = st.text_area("Corrected CLI Fix Steps:", value=current_review.get("corrected_fix_steps", ai_diag.get("fix_steps", "")) if current_review else ai_diag.get("fix_steps", ""))
            corrected_sec = st.toggle("Corrected Security Vulnerability Flag", value=current_review.get("corrected_security_issue", str(ai_diag.get("security_issue", "False"))) == "True" if current_review else bool(ai_diag.get("security_issue", False)))
            
            submitted = st.form_submit_button("Submit Audit Decision")
            
            if submitted:
                if not reviewer_note.strip():
                    st.error("Error: Please provide a reviewer audit note before submitting.")
                else:
                    if audit_status == "Accept":
                        # Save review as Accepted, copying AI diagnosis
                        save_review(selected_case_id, "Accepted", reviewer_note, ai_diag)
                        st.success(f"Audit decision saved: Accepted case {selected_case_id}")
                    elif audit_status == "Reject":
                        # Save review as Rejected
                        save_review(selected_case_id, "Reject", reviewer_note)
                        st.success(f"Audit decision saved: Rejected case {selected_case_id}")
                    else:
                        # Save review as Edited with corrected values
                        edited_diag = {
                            "root_cause": corrected_root_cause,
                            "osi_layer": corrected_osi,
                            "confidence": corrected_conf,
                            "fix_steps": corrected_fix,
                            "security_issue": corrected_sec
                        }
                        save_review(selected_case_id, "Edited", reviewer_note, edited_diag)
                        st.success(f"Audit decision saved: Edited/Corrected case {selected_case_id}")
                        
                    # Refresh memory and statistics
                    refresh_stats()
                    st.rerun()

# ----------------------------------------------------
# TAB 4: RULE CHECKER SANDBOX
# ----------------------------------------------------
elif tab_selection == "Rule Checker Sandbox":
    st.title("🛡️ Deterministic Rule Checker Sandbox (Non-AI)")
    st.markdown("Upload or paste a Cisco Packet Tracer network state snapshot (JSON) to detect common configuration violations automatically.")
    
    # Seed state uploader
    upload_col, paste_col = st.columns(2)
    
    # Load sample state
    sample_path = "data/sample_network_state.json"
    sample_text = ""
    if os.path.exists(sample_path):
        with open(sample_path, "r") as f:
            sample_text = f.read()
            
    with upload_col:
        uploaded_file = st.file_uploader("Upload Network State JSON file:", type=["json"])
        
    with paste_col:
        input_json_text = st.text_area("Or, paste / edit Network State JSON here:", value=sample_text, height=350)
        
    # Execution button
    state_to_check = ""
    if uploaded_file is not None:
        state_to_check = uploaded_file.read().decode("utf-8")
    else:
        state_to_check = input_json_text
        
    if st.button("🚀 Run Rule-based Deterministic Audit"):
        if not state_to_check.strip():
            st.error("Error: Please provide valid JSON input.")
        else:
            with st.spinner("Analyzing JSON configuration structure..."):
                findings = run_all_checks(state_to_check)
                
            st.markdown('<h3 class="section-title">Deterministic Findings</h3>', unsafe_allow_html=True)
            
            if not findings:
                st.success("✅ No structural configuration violations detected in the provided state!")
            else:
                # Render results nicely
                st.warning(f"⚠️ Detected {len(findings)} structural issues in the network config:")
                
                # Convert to dataframe for table view
                findings_df = pd.DataFrame(findings)
                st.dataframe(
                    findings_df,
                    column_config={
                        "check": "Check Rule",
                        "severity": "Severity",
                        "detail": "Description of Violation",
                        "devices": "Devices Affected"
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Render styled warnings
                for f in findings:
                    sev = f["severity"]
                    if sev == "Critical":
                        st.error(f"🔴 **[CRITICAL] {f['check']}:** {f['detail']} (Devices: {', '.join(f['devices'])})")
                    elif sev == "High":
                        st.warning(f"🟠 **[HIGH] {f['check']}:** {f['detail']} (Devices: {', '.join(f['devices'])})")
                    elif sev == "Medium":
                        st.info(f"🟡 **[MEDIUM] {f['check']}:** {f['detail']} (Devices: {', '.join(f['devices'])})")
                    else:
                        st.success(f"🔵 **[LOW] {f['check']}:** {f['detail']} (Devices: {', '.join(f['devices'])})")

# ----------------------------------------------------
# TAB 5: RESPONSIBLE AI LOG
# ----------------------------------------------------
elif tab_selection == "Responsible AI Log":
    st.title("🛡️ Responsible AI Log")
    st.markdown("Documented audits showing where and why the AI model hallucinated or suggested unsafe changes, corrected live by human engineers.")
    
    log_path = "logs/responsible_ai_log.md"
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
        st.markdown(log_content)
    else:
        st.error("Responsible AI Log file not found at logs/responsible_ai_log.md. Please verify generation steps.")
