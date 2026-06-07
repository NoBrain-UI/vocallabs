import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CUFINDER_API_KEY")


def find_similar_companies(domain: str) -> list[dict]:
    """
    Stage 1: Given a seed domain, returns lookalike company domains.
    Uses CUFinder API (file named ocean.py per project convention).
    Returns list of: { "name": str, "domain": str }
    """
    if not API_KEY:
        raise ValueError("CUFINDER_API_KEY not set in .env")

    try:
        response = requests.post(
            "https://api.cufinder.io/v2/fcl",
            headers={
                "x-api-key": API_KEY,
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={"query": domain},
            timeout=20
        )
    except requests.exceptions.Timeout:
        print(f"[Ocean] Timeout for domain: {domain}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"[Ocean] Request failed for {domain}: {e}")
        return []

    try:
        data = response.json()
    except Exception:
        print(f"[Ocean] Non-JSON response (HTTP {response.status_code}): {response.text[:200]}")
        return []

    if not data.get("success", True):
        print(f"[Ocean] API returned error for {domain}: {data}")
        return []

    companies = []
    for company in data.get("data", {}).get("companies", []):
        company_domain = company.get("domain", "").strip()
        name = company.get("name", "").strip()
        if not company_domain or company_domain.lower() == domain.lower():
            continue
        companies.append({"name": name, "domain": company_domain})

    print(f"[Ocean] Found {len(companies)} lookalike companies for '{domain}'")
    return companies