import os
import csv
import json

REVIEW_FILE = "data/human_review.csv"

# Pre-seeded reviews corresponding to the 6 deliberate AI mistakes
SEEDED_REVIEWS = [
    {
        "case_id": "VLAN-001",
        "status": "Edited",
        "reviewer_note": "AI hallucinated a trunk encapsulation mismatch and suggested dynamic trunking mode. It completely missed the Native VLAN configuration mismatch (10 vs 99) shown in the show interface trunk output.",
        "corrected_root_cause": "Native VLAN mismatch on the trunk link between Switch 1 (Native VLAN 10) and Switch 2 (Native VLAN 99).",
        "corrected_osi_layer": "Layer 2",
        "corrected_confidence": "High",
        "corrected_fix_steps": "Switch2# configure terminal\nSwitch2(config)# interface Gi0/1\nSwitch2(config-if)# switchport trunk native vlan 10\nSwitch2(config-if)# end",
        "corrected_security_issue": "True"
    },
    {
        "case_id": "GW-001",
        "status": "Edited",
        "reviewer_note": "AI misidentified a normal priority/preempt configuration as a fault. The true issue is that R1 and R2 are in mismatched standby groups (Group 1 vs Group 2), causing both to become Active gateways.",
        "corrected_root_cause": "HSRP group ID mismatch (Group 1 on R1 vs Group 2 on R2) preventing standby communication.",
        "corrected_osi_layer": "Layer 3",
        "corrected_confidence": "High",
        "corrected_fix_steps": "R2# configure terminal\nR2(config)# interface Gi0/0.10\nR2(config-subif)# no standby 2 ip 192.168.1.254\nR2(config-subif)# standby 1 ip 192.168.1.254\nR2(config-subif)# end",
        "corrected_security_issue": "False"
    },
    {
        "case_id": "DHCP-001",
        "status": "Edited",
        "reviewer_note": "AI suggested setting up a local DHCP pool on the router itself. This is an over-specification error; in a real environment with a central DHCP server, the correct solution is adding an 'ip helper-address' pointing to the server.",
        "corrected_root_cause": "Missing DHCP helper-address pointing to central DHCP Server (10.100.1.50) on interface Gi0/0.30.",
        "corrected_osi_layer": "Layer 3",
        "corrected_confidence": "High",
        "corrected_fix_steps": "R1# configure terminal\nR1(config)# interface GigabitEthernet0/0.30\nR1(config-subif)# ip helper-address 10.100.1.50\nR1(config-subif)# end",
        "corrected_security_issue": "False"
    },
    {
        "case_id": "RT-001",
        "status": "Edited",
        "reviewer_note": "AI claimed a Hello/Dead timer mismatch. The timers are actually matching. The real issue is that R1's port is in Area 0 and R2's port is in Area 10, which prevents OSPF neighbor adjacencies.",
        "corrected_root_cause": "OSPF Area mismatch (Area 0 on R1 vs Area 10 on R2) preventing neighbor adjacency.",
        "corrected_osi_layer": "Layer 3",
        "corrected_confidence": "High",
        "corrected_fix_steps": "R2# configure terminal\nR2(config)# router ospf 1\nR2(config-router)# no network 10.1.12.0 0.0.0.3 area 10\nR2(config-router)# network 10.1.12.0 0.0.0.3 area 0\nR2(config-router)# end",
        "corrected_security_issue": "False"
    },
    {
        "case_id": "ACL-001",
        "status": "Edited",
        "reviewer_note": "AI proposed removing the entire Access Control List (BLOCK_WEB) from the interface, which introduces a massive security vulnerability. The proper fix is to modify the ACL to remove only the blocking sequence line (no 10).",
        "corrected_root_cause": "Access Control List BLOCK_WEB rule 10 explicitly denies HTTPS (port 443) traffic.",
        "corrected_osi_layer": "Layer 4",
        "corrected_confidence": "High",
        "corrected_fix_steps": "R1# configure terminal\nR1(config)# ip access-list extended BLOCK_WEB\nR1(config-ext-nacl)# no 10\nR1(config-ext-nacl)# end",
        "corrected_security_issue": "True"
    },
    {
        "case_id": "NAT-002",
        "status": "Edited",
        "reviewer_note": "AI assumed the NAT access list (ACL 1) was completely missing and suggested a broad permit rule. The real issue is the missing 'overload' keyword on the NAT statement, preventing dynamic port address translation (PAT).",
        "corrected_root_cause": "Missing 'overload' keyword in the ip nat statement on Router 1, causing single-IP translation exhaustion.",
        "corrected_osi_layer": "Layer 3",
        "corrected_confidence": "High",
        "corrected_fix_steps": "R1# configure terminal\nR1(config)# no ip nat inside source list 1 interface GigabitEthernet0/1\nR1(config)# ip nat inside source list 1 interface GigabitEthernet0/1 overload\nR1(config)# end",
        "corrected_security_issue": "False"
    }
]

def load_reviews():
    reviews = {}
    if not os.path.exists(REVIEW_FILE) or os.path.getsize(REVIEW_FILE) == 0:
        initialize_seeded_reviews()
        
    with open(REVIEW_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            reviews[row["case_id"]] = row
    return reviews

def initialize_seeded_reviews():
    os.makedirs("data", exist_ok=True)
    fieldnames = [
        "case_id", "status", "reviewer_note", 
        "corrected_root_cause", "corrected_osi_layer", 
        "corrected_confidence", "corrected_fix_steps", 
        "corrected_security_issue"
    ]
    with open(REVIEW_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rev in SEEDED_REVIEWS:
            writer.writerow(rev)
    print(f"Initialized human_review.csv with {len(SEEDED_REVIEWS)} pre-seeded reviews.")

def save_review(case_id, status, reviewer_note, edited_diagnosis=None):
    reviews = load_reviews()
    
    # Build the review record
    review_record = {
        "case_id": case_id,
        "status": status,
        "reviewer_note": reviewer_note,
        "corrected_root_cause": "",
        "corrected_osi_layer": "",
        "corrected_confidence": "",
        "corrected_fix_steps": "",
        "corrected_security_issue": ""
    }
    
    if edited_diagnosis:
        review_record["corrected_root_cause"] = edited_diagnosis.get("root_cause", "")
        review_record["corrected_osi_layer"] = edited_diagnosis.get("osi_layer", "")
        review_record["corrected_confidence"] = edited_diagnosis.get("confidence", "")
        review_record["corrected_fix_steps"] = edited_diagnosis.get("fix_steps", "")
        review_record["corrected_security_issue"] = str(edited_diagnosis.get("security_issue", ""))
        
    reviews[case_id] = review_record
    
    # Save all back
    fieldnames = [
        "case_id", "status", "reviewer_note", 
        "corrected_root_cause", "corrected_osi_layer", 
        "corrected_confidence", "corrected_fix_steps", 
        "corrected_security_issue"
    ]
    with open(REVIEW_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for key in sorted(reviews.keys()):
            writer.writerow(reviews[key])
            
    print(f"Saved review for case {case_id}")
    return review_record

if __name__ == "__main__":
    # Test initialization
    load_reviews()
