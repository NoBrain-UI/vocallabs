"""
Vocallabs Automated Cold-Outreach Pipeline
==========================================
Input  : one seed company domain (e.g. "wise.com")
Stages : Ocean → Prospeo → Eazyreach → Brevo
Output : personalized emails sent to decision-makers at lookalike companies
"""

import sys
from services.ocean      import find_similar_companies
from services.prospeo    import find_decision_makers
from services.eazyreach  import resolve_emails_bulk
from services.brevo      import send_outreach_bulk

# ── Config ───────────────────────────────────────────────
MAX_COMPANIES = 5
MAX_CONTACTS  = 3

# Only these seniorities get emailed — filters out Seniors/Analysts
SENIOR_SENIORITIES = {"C-Suite", "Vice President", "Founder/Owner", "Director"}

# ── Helpers ──────────────────────────────────────────────
def print_stage(n, title):
    print(f"\n{'='*55}")
    print(f"  STAGE {n}: {title}")
    print(f"{'='*55}")

def is_decision_maker(person: dict) -> bool:
    return person.get("seniority", "") in SENIOR_SENIORITIES

def safety_checkpoint(contacts: list[dict]) -> bool:
    print(f"\n{'─'*55}")
    print(f"  ⚠️   SAFETY CHECKPOINT — {len(contacts)} email(s) queued")
    print(f"{'─'*55}")
    for i, c in enumerate(contacts, 1):
        print(f"  {i:>2}. {c.get('full_name','Unknown'):<28}"
              f"  {c.get('seniority',''):<16}"
              f"  {c.get('email','')}")
    print(f"{'─'*55}")
    answer = input("\nSend all emails? [y/N]: ").strip().lower()
    return answer == "y"

# ── Pipeline ─────────────────────────────────────────────
def run_pipeline(seed_domain: str):
    print(f"\n🚀  Starting pipeline for seed domain: {seed_domain}\n")

    # Stage 1: Lookalike companies
    print_stage(1, "Finding lookalike companies (Ocean / CUFinder)")
    companies = find_similar_companies(seed_domain)
    if not companies:
        print("❌  No lookalike companies found. Exiting.")
        sys.exit(1)

    companies = companies[:MAX_COMPANIES]
    print(f"\n→ Processing {len(companies)} companies:")
    for c in companies:
        print(f"    • {c['name']} ({c['domain']})")

    # Stage 2: Decision-makers
    print_stage(2, "Finding decision-makers (Prospeo)")
    all_persons = []
    for company in companies:
        persons = find_decision_makers(company["domain"])
        # Filter to true decision-makers only, cap per company
        decision_makers = [p for p in persons if is_decision_maker(p)]
        all_persons.extend(persons[:MAX_CONTACTS])

    if not all_persons:
        print("❌  No decision-makers found. Exiting.")
        sys.exit(1)

    print(f"\n→ Total decision-makers found: {len(all_persons)}")

    # Stage 3: Email resolution
    print_stage(3, "Resolving work emails (Eazyreach)")
    enriched_contacts = resolve_emails_bulk(all_persons)
    if not enriched_contacts:
        print("❌  No verified emails resolved. Exiting.")
        sys.exit(1)

    print(f"\n→ Contacts with verified emails: {len(enriched_contacts)}")

    # Safety checkpoint
    confirmed = safety_checkpoint(enriched_contacts)
    if not confirmed:
        print("\n⛔  Aborted by user. No emails sent.")
        sys.exit(0)

    # Stage 4: Send outreach
    print_stage(4, "Sending outreach emails (Brevo)")
    summary = send_outreach_bulk(enriched_contacts)

    print(f"\n✅  Pipeline complete!")
    print(f"    Sent:   {summary['sent']}")
    print(f"    Failed: {summary['failed']}")

# ── Entry point ──────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <seed_domain>")
        print("Example: python main.py wise.com")
        sys.exit(1)

    seed = sys.argv[1].strip().lower()
    seed = seed.replace("https://", "").replace("http://", "").rstrip("/")
    run_pipeline(seed)