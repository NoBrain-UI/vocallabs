import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("PROSPEO_API_KEY")


def find_decision_makers(domain: str) -> list[dict]:
    """
    Stage 2: Given a company domain, returns C-suite/VP decision-makers.
    Uses Prospeo Search Person API with company.websites filter.

    Returns list of:
    {
        "person_id": str,
        "first_name": str,
        "last_name": str,
        "full_name": str,
        "title": str,
        "seniority": str,
        "linkedin_url": str,
        "company_name": str,
        "domain": str
    }
    """
    if not API_KEY:
        raise ValueError("PROSPEO_API_KEY not set in .env")

    payload = {
        "page": 1,
        "filters": {
            "company": {
                "websites": {
                    "include": [domain]
                }
            },
            "person_seniority": {
                "include": [
                    "C-Suite",
                    "Vice President",
                    "Founder/Owner",
                    "Director"
                ]
            }
        }
    }

    try:
        response = requests.post(
            "https://api.prospeo.io/search-person",
            headers={
                "X-KEY": API_KEY,
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=20
        )
    except requests.exceptions.Timeout:
        print(f"[Prospeo] Timeout for domain: {domain}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"[Prospeo] Request failed for {domain}: {e}")
        return []

    # Always try to parse JSON first — Prospeo returns error details in the body
    try:
        data = response.json()
    except Exception:
        print(f"[Prospeo] Non-JSON response for {domain} (HTTP {response.status_code}): {response.text[:200]}")
        return []

    # Handle API-level errors returned in the body
    if data.get("error"):
        code = data.get("error_code", "UNKNOWN")
        if code == "NO_RESULTS":
            print(f"[Prospeo] No decision-makers found for {domain}")
        elif code == "INVALID_FILTERS":
            print(f"[Prospeo] Invalid filters for {domain}: {data.get('filter_error', '')}")
        elif code == "INSUFFICIENT_CREDITS":
            print(f"[Prospeo] Insufficient credits — stopping.")
        else:
            print(f"[Prospeo] API error for {domain}: {code}")
        return []

    decision_makers = []
    for item in data.get("results", []):
        person  = item.get("person", {}) or {}
        company = item.get("company", {}) or {}

        linkedin_url = person.get("linkedin_url", "")
        if not linkedin_url:
            continue

        decision_makers.append({
            "person_id":    person.get("id"),
            "first_name":   person.get("first_name", ""),
            "last_name":    person.get("last_name", ""),
            "full_name":    person.get("full_name") or f"{person.get('first_name','')} {person.get('last_name','')}".strip(),
            "title":        person.get("current_job_title") or person.get("job_title", ""),
            "seniority":    person.get("seniority", ""),
            "linkedin_url": linkedin_url,
            "company_name": company.get("name", ""),
            "domain":       domain
        })

    print(f"[Prospeo] Found {len(decision_makers)} decision-makers for '{domain}'")
    return decision_makers