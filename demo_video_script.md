# NetSage AI — Demo Video Script
**Duration:** ~6 minutes
**Roles:** presenter (Network Engineer)

---

### [00:00 - 01:00] Intro & Problem Statement
*   **Visual:** Show the presenter on screen, then transition to the NetSage AI Dashboard Overview.
*   **Audio (Presenter):** "Hello, today I'll walk you through NetSage AI, a troubleshooting assistant for Cisco Packet Tracer labs designed to help junior network engineers identify faults safely. In multi-VLAN networks, a simple symptom like 'Host cannot ping a server' can be caused by VLAN pruning, HSRP standby group mismatches, DNS issues, or NAT rules. NetSage AI combines deterministic local rules with LLM analysis, enforcing a strict human-in-the-loop safety workflow."

### [01:00 - 02:00] Deterministic Rule Checker
*   **Visual:** Click on the "Rule Checker Sandbox" tab. Paste the content of `data/sample_network_state.json`. Click "Run Rule-based Deterministic Audit". Show the warnings.
*   **Audio (Presenter):** "Before calling the AI, we can run deterministic configuration checks locally with zero network access. I'll paste a sample network topology JSON here and run the audit. Instantly, we see multiple critical issues: Host A and B have duplicate IPs, there is a subnet mask mismatch between Host C and Router 1, and Switchport 5 is assigned to a VLAN that does not exist in the switch database. This lets junior engineers catch basic config bugs instantly before engaging the AI."

### [02:00 - 03:30] AI Diagnosis in Action
*   **Visual:** Switch to the "Troubleshooting Workspace" tab. Select case `VLAN-001`. Show the symptom, topology note, and Cisco CLI show output code block.
*   **Audio (Presenter):** "Now, let's look at the troubleshooting workspace. We'll select case `VLAN-001`. A junior engineer has submitted a ticket: Host A cannot ping Host B. We have the cisco `show interfaces trunk` outputs. Right away, the AI has generated a diagnosis. It suggests that there is a trunk encapsulation mismatch and recommends changing the switchport trunk mode to dynamic auto. But wait, is that correct? Looking at the show output, we see that Switch 1 has native VLAN 10 and Switch 2 has native VLAN 99. The real issue is a native VLAN mismatch!"

### [03:30 - 04:30] Human Review & Audit Correction
*   **Visual:** Scroll down to the "Human Oversight Audit Form". Change the Action to "Edit / Correct". Explain the change. Type the audit note: "AI missed the native VLAN configuration difference (10 vs 99) in show interfaces trunk and hallucinated encapsulation mode mismatch. Correcting." Correct the Root Cause to "Native VLAN mismatch" and update the CLI fix. Click "Submit Audit Decision".
*   **Audio (Presenter):** "This is where our safety guardrail comes in. The AI proposed an incorrect and dynamic configuration. As the senior auditor, I'll select 'Edit / Correct'. I'll log a note explaining the AI's mistake. I will correct the root cause to 'Native VLAN mismatch' and adjust the fix commands to configure native VLAN 10 on Switch 2's Gi0/1 interface. I'll click submit. The audit is instantly recorded, updating our dataset."

### [04:30 - 05:30] Responsible AI Logs & Dashboard Update
*   **Visual:** Navigate to the "Responsible AI Log" tab to show the markdown rendered output. Then navigate back to the "Dashboard Overview" tab and show the updated stats (reviewed cases is now 7, agreement rate is calculated, pie charts adjusted).
*   **Audio (Presenter):** "All edits are logged in our Responsible AI Log, which tracks where and why the model fell short—critical for tuning our prompts and monitoring safety risks. If we look at the dashboard overview, we can see the live KPIs have updated: we now have 7 audited cases, and our AI-Human agreement rate is reflecting the corrections. The Plotly charts give us an active view of categories and severity levels across our lab scenarios."

### [05:30 - 06:00] Live API Check & Outro
*   **Visual:** Go back to workspace. Click "Trigger Live AI Re-Diagnosis". Show success. Presenter on screen.
*   **Audio (Presenter):** "If an API key is provided, we can trigger a live re-diagnosis on the fly. The pipeline connects to Claude 3.5 Sonnet to fetch fresh insights. NetSage AI is deployed and reachable via a public URL, with setup instructions in the README. Thank you for watching!"
