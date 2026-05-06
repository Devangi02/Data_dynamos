import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
from serpapi import GoogleSearch

# ========================= CONFIG =========================
SERPAPI_KEY = "f73488469e610c1c734369347885c6f7d890e0e95aeeb18ff6d8b841f96256c3"   # ← Replace with your key
COMPANY_NAME = "Texplorers Inc"
DAYS_BACK = 30
# =======================================================

def clean_text(text):
    return re.sub(r'\s+', ' ', str(text).strip()) if text else ""

def scrape_official_careers():
    print("🔍 Scraping official Texplorers careers page...")
    jobs = []
    try:
        urls = ["https://www.texplorers.com/careers/", "https://www.texplorers.com/careers-2/"]
        
        for url in urls:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if resp.status_code != 200:
                continue
                
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Find all job titles (h3 or strong tags)
            job_elements = soup.find_all(['h3', 'h2', 'strong'])
            
            for elem in job_elements:
                title = clean_text(elem.get_text())
                if len(title) < 10 or any(x in title.lower() for x in ["featured", "current opening", "telecommuting"]):
                    continue

                # Extract description
                desc = clean_text(elem.find_next(['p', 'div', 'ul']).get_text() if elem.find_next(['p', 'div', 'ul']) else "")

                exp_match = re.search(r'(\d+)\+?\s*years?', desc + title, re.I)
                experience = f"{exp_match.group(1)}+ years" if exp_match else "Not specified"

                # Location detection
                location = "Lewisville, TX / USA"
                if "mechanicsville" in (desc + title).lower():
                    location = "Mechanicsville, VA / USA"
                elif "hyderabad" in (desc + title).lower():
                    location = "Hyderabad, India"

                # Job Type
                job_type = "onsite"
                if "remote" in (desc + title).lower():
                    job_type = "remote"

                jobs.append({
                    "Job_name": title,
                    "Job_description": desc[:900],
                    "Posting_date": datetime.now().strftime("%d_%m_%Y"),
                    "Experience": experience,
                    "Location": location,
                    "Company_name": COMPANY_NAME,
                    "Job_application_link": url,
                    "Type": job_type
                })
    except Exception as e:
        print(f"Official scrape error: {e}")
    return jobs


def google_jobs_search():
    print("🔍 Searching via Google Jobs (SerpApi)...")
    try:
        params = {
            "engine": "google_jobs",
            "q": "Texplorers Inc OR TexplorersInc (job OR hiring OR vacancy OR engineer)",
            "hl": "en",
            "gl": "us",
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

    # Add Google Jobs results if official gave few results
    if len(all_jobs) < 5:
        google_results = google_jobs_search()
        for job in google_results:
            title = clean_text(job.get("title"))
            if not title:
                continue
            all_jobs.append({
                "Job_name": title,
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
        filename = f"texplorers_jobs_{date_str}.csv"
        
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\n🎉 SUCCESS! Found {len(all_jobs)} jobs at Texplorers Inc")
        print(f"📁 File saved: {filename}\n")
        print(df[['Job_name', 'Location', 'Experience', 'Type']])
    else:
        print("No jobs found.")

if __name__ == "__main__":
    main()
