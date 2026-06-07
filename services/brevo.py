import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")   # your verified Brevo sender email
SENDER_NAME  = os.getenv("SENDER_NAME", "Vocallabs Team")


def build_email_html(person: dict) -> tuple[str, str]:
    """
    Build a personalized subject + HTML body for cold outreach.
    Customize this copy to match your pitch.
    """
    first_name   = person.get("first_name") or person.get("full_name", "there").split()[0]
    company_name = person.get("company_name", "your company")
    title        = person.get("title", "")

    subject = f"Quick question for {first_name} re: {company_name}"

    body = f"""
<html>
<body style="font-family: Arial, sans-serif; font-size: 15px; color: #222; max-width: 600px;">
  <p>Hi {first_name},</p>

  <p>
    I came across {company_name} and was genuinely impressed by what you're building.
    {'As ' + title + ', I thought' if title else 'I thought'} you'd be the right person to reach out to.
  </p>

  <p>
    We're <strong>Vocallabs</strong> — we help sales teams automate their entire outreach pipeline,
    from sourcing lookalike companies to sending personalized emails, with zero manual steps in between.
  </p>

  <p>
    A lot of teams we work with were spending 3–4 hours a day on prospecting.
    After using our pipeline, that dropped to under 10 minutes.
  </p>

  <p>
    Would you be open to a quick 15-minute call this week to see if this is relevant for {company_name}?
    Happy to share a short demo if that's easier.
  </p>

  <p>
    Best,<br>
    <strong>{SENDER_NAME}</strong><br>
    Vocallabs
  </p>

  <p style="font-size: 12px; color: #888;">
    If this isn't relevant for you, just reply and I'll make sure not to follow up.
  </p>
</body>
</html>
""".strip()

    return subject, body


def send_outreach_email(person: dict) -> bool:
    """
    Stage 4: Send a personalized cold outreach email to a single contact via Brevo.

    person dict must have: email, first_name / full_name, company_name

    Returns True on success, False on failure.
    """
    if not API_KEY:
        raise ValueError("BREVO_API_KEY not set in .env")
    if not SENDER_EMAIL:
        raise ValueError("SENDER_EMAIL not set in .env — add your verified Brevo sender email")

    recipient_email = person.get("email", "").strip()
    if not recipient_email:
        print(f"[Brevo] Skipping {person.get('full_name')}: no email address")
        return False

    recipient_name = person.get("full_name") or (
        f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
    )

    subject, html_body = build_email_html(person)

    payload = {
        "sender": {
            "name":  SENDER_NAME,
            "email": SENDER_EMAIL
        },
        "to": [
            {
                "email": recipient_email,
                "name":  recipient_name or recipient_email
            }
        ],
        "subject":     subject,
        "htmlContent": html_body
    }

    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key":      API_KEY,
                "Content-Type": "application/json",
                "accept":       "application/json"
            },
            json=payload,
            timeout=20
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print(f"[Brevo] Timeout sending to {recipient_email}")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"[Brevo] HTTP error for {recipient_email}: {e.response.status_code} — {e.response.text}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[Brevo] Request failed for {recipient_email}: {e}")
        return False

    message_id = response.json().get("messageId", "unknown")
    print(f"[Brevo] ✓ Sent to {recipient_name} <{recipient_email}> | messageId: {message_id}")
    return True


def send_outreach_bulk(contacts: list[dict]) -> dict:
    """
    Send outreach emails to a list of enriched contacts.
    Returns summary: { "sent": int, "failed": int }
    """
    sent, failed = 0, 0
    for contact in contacts:
        success = send_outreach_email(contact)
        if success:
            sent += 1
        else:
            failed += 1

    print(f"\n[Brevo] Done — {sent} sent, {failed} failed")
    return {"sent": sent, "failed": failed}
