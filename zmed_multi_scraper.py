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
    print("🔍 Scraping official zMed careers page...")
    jobs = []
    try:
        url = "https://www.zmed.tech/careers"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(resp.text, 'lxml')

        # Find all job headings
        sections = soup.find_all(['h3', 'h2'])

        for sec in sections:
            title = clean_text(sec.get_text())
            if len(title) < 8 or any(x in title.lower() for x in ["opening", "current", "join"]):
                continue

            # Improved description extraction - get more content
            desc_parts = []
            sibling = sec.find_next_sibling()
            
            while sibling and sibling.name not in ['h3', 'h2']:
                text = clean_text(sibling.get_text())
                if text and len(text) > 10:
                    desc_parts.append(text)
                sibling = sibling.find_next_sibling()

            full_description = " ".join(desc_parts)

            # Fallback if description is too short
            if len(full_description) < 50:
                full_description = clean_text(sec.find_next('p').get_text()) if sec.find_next('p') else title

            experience = re.search(r'(\d+)\+?\s*years?', full_description, re.I)
            exp_str = f"{experience.group(1)}+ years" if experience else "Not specified"

            jobs.append({
                "Job_name": title,
                "Job_description": full_description[:950],
                "Posting_date": datetime.now().strftime("%d_%m_%Y"),
                "Experience": exp_str,
                "Location": "Chennai / Bengaluru",
                "Company_name": COMPANY_NAME,
                "Job_application_link": "https://www.zmed.tech/apply",   # No individual links available
                "Type": "onsite"
            })
    except Exception as e:
        print(f"Official page error: {e}")
    return jobs


def google_jobs_search():
    print("🔍 Searching via Google Jobs...")
    try:
        params = {
            "engine": "google_jobs",
            "q": "zMed Healthcare OR zmed.tech (job OR hiring OR vacancy OR engineer OR developer OR \"AI-Native\")",
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
    all_jobs = scrape_official_careers()

    # Add Google Jobs results (with better individual links)
    google_results = google_jobs_search()
    for job in google_results:
        title = clean_text(job.get("title"))
        if not title or len(title) < 5:
            continue
            
        all_jobs.append({
            "Job_name": title,
            "Job_description": clean_text(job.get("description", ""))[:950],
            "Posting_date": datetime.now().strftime("%d_%m_%Y"),
            "Experience": "Not specified",
            "Location": clean_text(job.get("location")),
            "Company_name": COMPANY_NAME,
            "Job_application_link": job.get("apply_link") or job.get("link", "https://www.zmed.tech/apply"),
            "Type": "onsite"
        })

    # Remove duplicates
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        if job["Job_name"] not in seen:
            seen.add(job["Job_name"])
            unique_jobs.append(job)

    if unique_jobs:
        df = pd.DataFrame(unique_jobs)
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"zmed_jobs_{date_str}.csv"
        
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\n✅ SUCCESS! Saved {len(unique_jobs)} jobs to {filename}")
        print(df[['Job_name', 'Location', 'Experience', 'Type']])
    else:
        print("No jobs found.")

if __name__ == "__main__":
    main()
