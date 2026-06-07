import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("PROSPEO_API_KEY")


def resolve_email(person: dict) -> dict | None:
    """
    Stage 3: Resolves a verified work email for a decision-maker.
    Uses Prospeo /enrich-person with person_id or linkedin_url.
    Returns enriched dict with "email" key, or None if not found.
    """
    if not API_KEY:
        raise ValueError("PROSPEO_API_KEY not set in .env")

    data_payload = {}
    if person.get("person_id"):
        data_payload["person_id"] = person["person_id"]
    elif person.get("linkedin_url"):
        data_payload["linkedin_url"] = person["linkedin_url"]
    else:
        print(f"[Eazyreach] Skipping {person.get('full_name')}: no person_id or linkedin_url")
        return None

    payload = {
        "only_verified_email": True,
        "data": data_payload
    }

    try:
        response = requests.post(
            "https://api.prospeo.io/enrich-person",
            headers={
                "X-KEY": API_KEY,
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=20
        )
    except requests.exceptions.Timeout:
        print(f"[Eazyreach] Timeout for {person.get('full_name')}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[Eazyreach] Request failed for {person.get('full_name')}: {e}")
        return None

    try:
        data = response.json()
    except Exception:
        print(f"[Eazyreach] Non-JSON response (HTTP {response.status_code}): {response.text[:200]}")
        return None

    if data.get("error"):
        code = data.get("error_code", "UNKNOWN")
        if code == "NO_MATCH":
            print(f"[Eazyreach] No verified email for {person.get('full_name')} @ {person.get('domain')}")
        elif code == "INSUFFICIENT_CREDITS":
            print(f"[Eazyreach] Insufficient credits — stopping enrichment.")
        else:
            print(f"[Eazyreach] API error for {person.get('full_name')}: {code}")
        return None

    email_obj    = data.get("person", {}).get("email", {}) or {}
    email_addr   = email_obj.get("email", "")
    email_status = email_obj.get("status", "")

    if not email_addr or email_status != "VERIFIED":
        print(f"[Eazyreach] Unverified/missing email for {person.get('full_name')}")
        return None

    enriched = {**person, "email": email_addr}
    print(f"[Eazyreach] ✓ {person.get('full_name')} → {email_addr}")
    return enriched


def resolve_emails_bulk(persons: list[dict]) -> list[dict]:
    enriched = []
    for person in persons:
        result = resolve_email(person)
        if result:
            enriched.append(result)
    print(f"[Eazyreach] Resolved {len(enriched)}/{len(persons)} emails")
    return enriched