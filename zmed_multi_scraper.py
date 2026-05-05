import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
from serpapi import GoogleSearch

# ========================= CONFIG =========================
SERPAPI_KEY = "f73488469e610c1c734369347885c6f7d890e0e95aeeb18ff6d8b841f96256c3"
COMPANY_NAME = "zMed Healthcare"
# =======================================================

def clean_text(text):
    return re.sub(r'\s+', ' ', str(text).strip()) if text else ""

def scrape_official_careers():
    """Scrape official zMed careers page - Most reliable source"""
    print("🔍 Scraping official careers page...")
    jobs = []
    try:
        url = "https://www.zmed.tech/careers"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(resp.text, 'lxml')

        sections = soup.find_all(['h3', 'h2'])
        
        for sec in sections:
            title = clean_text(sec.get_text())
            if len(title) < 8 or "opening" in title.lower():
                continue

            # Get description
            desc = ""
            sibling = sec.find_next_sibling()
            while sibling and sibling.name not in ['h3', 'h2']:
                desc += clean_text(sibling.get_text()) + " "
                sibling = sibling.find_next_sibling()

            experience = re.search(r'(\d+)\+?\s*years?', desc, re.I)
            exp_str = f"{experience.group(1)}+ years" if experience else "Not specified"

            jobs.append({
                "Job_name": title,
                "Job_description": desc[:900],
                "Posting_date": datetime.now().strftime("%d_%m_%Y"),
                "Experience": exp_str,
                "Location": "Chennai / Bengaluru",
                "Company_name": COMPANY_NAME,
                "Job_application_link": "https://www.zmed.tech/apply",
                "Type": "onsite"
            })
    except Exception as e:
        print(f"Official page error: {e}")
    return jobs


def google_jobs_search():
    """Try SerpApi with better query"""
    print("🔍 Searching via Google Jobs...")
    try:
        params = {
            "engine": "google_jobs",
            "q": "zMed Healthcare OR zmed.tech OR \"zMed Healthcare Technologies\" (job OR hiring OR vacancy OR engineer OR developer)",
            "hl": "en",
            "gl": "in",
            "chips": "date_posted:month",
            "api_key": SERPAPI_KEY
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        return results.get("jobs_results", [])
    except Exception as e:
        print(f"SerpApi error: {e}")
        return []


def main():
    all_jobs = []

    # Priority 1: Official Website
    official_jobs = scrape_official_careers()
    all_jobs.extend(official_jobs)

    # Priority 2: Google Jobs (SerpApi)
    if len(all_jobs) < 5:   # Only if official gave few results
        google_results = google_jobs_search()
        for job in google_results:
            # Convert to our format
            all_jobs.append({
                "Job_name": clean_text(job.get("title")),
                "Job_description": clean_text(job.get("description", ""))[:900],
                "Posting_date": datetime.now().strftime("%d_%m_%Y"),
                "Experience": "Not specified",
                "Location": clean_text(job.get("location")),
                "Company_name": COMPANY_NAME,
                "Job_application_link": job.get("apply_link") or job.get("link", ""),
                "Type": "onsite"
            })

    # Save to CSV
    if all_jobs:
        df = pd.DataFrame(all_jobs)
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"zmed_jobs_{date_str}.csv"
        
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\n✅ SUCCESS! Saved {len(all_jobs)} jobs to {filename}")
        print(df[['Job_name', 'Location', 'Experience', 'Type']])
    else:
        print("❌ Still no jobs found. The company might not have public indexed jobs right now.")

if __name__ == "__main__":
    main()
