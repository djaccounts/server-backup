#!/usr/bin/env python3
"""
send_dinner_party_email.py — Email dinner party PDFs via AgentMail REST API.

Usage:
    python3 send_dinner_party_email.py <event-name> <recipient> [recipient ...]

Example:
    python3 send_dinner_party_email.py jill-adam-20june daverj1987@gmail.com

Prerequisites:
    - AGENT_MAIL_API key in /root/.hermes/.env
    - PDFs exist at /root/<event-name>-cooking.pdf and /root/<event-name>-guest.pdf
"""
import base64, json, urllib.request, subprocess, sys

ENV_PATH = "/root/.hermes/.env"

def get_env_key(var_name):
    r = subprocess.run(["grep", var_name, ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def api(method, path, data=None):
    key = get_env_key("AGENT_MAIL_API")
    url = f"https://api.agentmail.to/v0/{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": json.loads(e.read()), "status": e.code}

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 send_dinner_party_email.py <event-name> <recipient> [recipient ...]")
        sys.exit(1)

    event_name = sys.argv[1]
    recipients = sys.argv[2:]

    # Read & encode PDFs
    try:
        with open(f"/root/{event_name}-cooking.pdf", "rb") as f:
            pdf_cooking_b64 = base64.b64encode(f.read()).decode()
        with open(f"/root/{event_name}-guest.pdf", "rb") as f:
            pdf_guest_b64 = base64.b64encode(f.read()).decode()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Generate PDFs first with: weasyprint <file.html> <file.pdf>")
        sys.exit(1)

    # Get inbox
    inboxes = api("GET", "inboxes")
    items = inboxes.get("data", inboxes) if isinstance(inboxes, dict) else inboxes
    if isinstance(items, dict):
        items = items.get("inboxes", items.get("data", []))
    if not items:
        print("No inboxes found.")
        sys.exit(1)
    from_inbox = items[0]["inbox_id"] if isinstance(items[0], dict) else items[0]

    # Send
    result = api("POST", f"inboxes/{from_inbox}/messages/send", {
        "to": recipients,
        "subject": f"Dinner Party Invitation",
        "text": "You're invited! Please see the attached invitation.\n\nCome hungry. Leave happy.",
        "attachments": [
            {"filename": f"{event_name}-guest.pdf", "content": pdf_guest_b64, "type": "application/pdf"},
            {"filename": f"{event_name}-cooking.pdf", "content": pdf_cooking_b64, "type": "application/pdf"}
        ]
    })

    if "error" in result:
        print(f"Error: {result}")
        sys.exit(1)
    else:
        print(f"✅ Sent to {', '.join(recipients)}")
        print(f"Message ID: {result.get('message_id', 'N/A')}")

if __name__ == "__main__":
    main()
