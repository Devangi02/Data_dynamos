import pandas as pd
from datetime import datetime
import re
from serpapi import GoogleSearch

# ========================= CONFIG =========================
SERPAPI_KEY = "afc25acb7af16710922a9be7302fd464b5c86d8058a59d9b545590cb8bfc7553"
COMPANY_NAME = "MKS Inc"
DAYS_BACK = 30
# =======================================================

def clean_text(text):
    return re.sub(r'\s+', ' ', str(text).strip()) if text else ""

def google_jobs_search():
    print(f"🔍 Searching Google for MKS jobs (last {DAYS_BACK} days)...")
    try:
        date_map = {1: "today", 2: "3days", 7: "week", 30: "month"}
        date_filter = date_map.get(DAYS_BACK, "month")

        params = {
            "engine": "google_jobs",
            "q": '"MKS" OR "MKS Instruments" OR "MKS Inc" (Engineer OR Analyst OR Manager OR Technician OR Developer)',
            "hl": "en",
            "gl": "us",           # Changed to US because most jobs are in USA
            "chips": f"date_posted:{date_filter}",
            "api_key": SERPAPI_KEY
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        jobs_results = results.get("jobs_results", [])
        
        print(f"✅ Google returned {len(jobs_results)} job listings")
        return jobs_results

    except Exception as e:
        print(f"❌ SerpApi Error: {e}")
        return []


def main():
    all_jobs = []
    google_results = google_jobs_search()

    for job in google_results:
        title = clean_text(job.get("title"))
        if not title:
            continue

        description = clean_text(job.get("description", ""))[:1000]
        location = clean_text(job.get("location"))

        exp_match = re.search(r'(\d+)\+?\s*years?', description + title, re.I)
        experience = f"{exp_match.group(1)}+ years" if exp_match else "Not specified"

        text_lower = (title + description).lower()
        job_type = "remote" if "remote" in text_lower else "hybrid" if "hybrid" in text_lower else "onsite"

        all_jobs.append({
            "Job_name": title,
            "Job_description": description,
            "Posting_date": datetime.now().strftime("%d_%m_%Y"),
            "Experience": experience,
            "Location": location or "USA",
            "Company_name": COMPANY_NAME,
            "Job_application_link": job.get("apply_link") or job.get("link", ""),
            "Type": job_type
        })

    if all_jobs:
        df = pd.DataFrame(all_jobs)
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"mks_jobs_{date_str}.csv"
        
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\n🎉 SUCCESS! Saved {len(all_jobs)} jobs to {filename}")
        print(df[['Job_name', 'Location', 'Type']].head(10))
    else:
        print("\n❌ Still 0 jobs found.")
        print("This usually means Google has not indexed MKS jobs well in the last 30 days.")
        print("Recommendation: Use Playwright to scrape their Workday page directly.")

if __name__ == "__main__":
    main()
