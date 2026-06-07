# debug_prospeo.py
import os, requests
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("PROSPEO_API_KEY")

payload = {
    "page": 1,
    "filters": {
        "company": {"websites": {"include": ["cred.club"]}},
        "person_seniority": {"include": ["C-Suite", "Vice President", "Founder/Owner", "Director"]}
    }
}

response = requests.post(
    "https://api.prospeo.io/search-person",
    headers={"X-KEY": API_KEY, "Content-Type": "application/json"},
    json=payload, timeout=20
)
data = response.json()

for item in data.get("results", [])[:5]:
    person = item.get("person", {})
    print(f"{person.get('full_name')} | seniority: {repr(person.get('seniority'))}")