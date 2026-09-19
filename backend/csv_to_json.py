"""
One-time converter: real participant CSV -> our user JSON format.
Run once: python -m backend.csv_to_json
"""
import csv
import json

INPUT_CSV = "data/Dataset for PS-3 (Ignite Room) (1).csv"
OUTPUT_JSON = "data/real_users.json"

def convert():
    users = []
    with open(INPUT_CSV, encoding="utf-8-sig") as f:  # utf-8-sig strips the BOM
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 15:  # sirf pehle 15 users, time bachane ke liye
                break
            users.append({
                "user_id": f"u{i+1}",
                "name": f"{row.get('first_name','').strip()} {row.get('last_name','').strip()}".strip(),
                "linkedin_url": row.get("What is your LinkedIn profile?", "").strip(),
                "github_username": row.get("What is your GitHub username?", "").strip(),
                "company_or_college": row.get("What company do you work for? (if student then write your college name)", "").strip(),
                "job_title": row.get("What is your job title?", "").strip(),
            })
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"users": users}, f, indent=2)
    print(f"Converted {len(users)} users -> {OUTPUT_JSON}")

if __name__ == "__main__":
    convert()