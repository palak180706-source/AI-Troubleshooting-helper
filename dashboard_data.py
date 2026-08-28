import pandas as pd
import json
import os

def load_dashboard_stats():
    # Load cases
    cases_df = pd.read_csv("data/cases.csv")
    
    # Load diagnoses
    diagnoses = {}
    if os.path.exists("data/ai_diagnoses.json"):
        with open("data/ai_diagnoses.json", "r") as f:
            diagnoses = json.load(f)
            
    # Load human reviews
    reviews = {}
    reviews_df = pd.DataFrame()
    if os.path.exists("data/human_review.csv"):
        reviews_df = pd.read_csv("data/human_review.csv")
        for _, row in reviews_df.iterrows():
            reviews[row["case_id"]] = row.to_dict()
            
    # Calculate stats
    total_cases = len(cases_df)
    reviewed_cases = len(reviews)
    
    # Counts by category
    category_counts = cases_df["category"].value_counts().to_dict()
    
    # Counts by severity
    severity_counts = cases_df["severity"].value_counts().to_dict()
    
    # Agreement rate calculation:
    # Statuses: Accepted vs (Edited / Rejected)
    # Agreement = status is "Accepted"
    agreement_rate = 100.0
    accepted_count = 0
    disagreed_count = 0
    
    if reviewed_cases > 0:
        accepted_count = sum(1 for cid, rev in reviews.items() if rev["status"] == "Accepted")
        disagreed_count = reviewed_cases - accepted_count
        agreement_rate = (accepted_count / reviewed_cases) * 100.0
        
    return {
        "total_cases": total_cases,
        "reviewed_cases": reviewed_cases,
        "unreviewed_cases": total_cases - reviewed_cases,
        "accepted_count": accepted_count,
        "disagreed_count": disagreed_count,
        "agreement_rate": agreement_rate,
        "category_counts": category_counts,
        "severity_counts": severity_counts,
        "reviews_df": reviews_df,
        "cases_df": cases_df
    }
