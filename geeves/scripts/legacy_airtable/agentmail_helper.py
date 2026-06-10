#!/usr/bin/env python3
"""AgentMail helper for Geeves. Handles the key properly without shell mangling."""
import subprocess, sys, json, os, urllib.request

def get_key():
    with open("/root/.hermes/.env") as f:
        for line in f:
            line = line.strip()
            if line.startswith("AGENT_MAIL_API"):
                return line.split("=", 1)[1]
    return ""

def api(method, path, data=None):
    """Call AgentMail REST API directly."""
    key = get_key()
    url = f"https://api.agentmail.to/v0/{path}"
    body = json.dumps(data).encode() if data else None
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": json.loads(e.read()), "status": e.code}

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python3 agentmail_helper.py <cmd> [args...]")
        print("  create-inbox <name>")
        print("  list-inboxes")
        print("  send <to> <subject> <body>")
        return

    cmd = args[0]

    if cmd == "create-inbox":
        name = args[1] if len(args) > 1 else "Geeves"
        r = api("POST", "inboxes", {"display_name": name})
        print(json.dumps(r, indent=2))

    elif cmd == "list-inboxes":
        r = api("GET", "inboxes")
        print(json.dumps(r, indent=2))

    elif cmd == "send":
        if len(args) < 4:
            print("Usage: send <to> <subject> <body>")
            return
        to, subject, body_text = args[1], args[2], args[3]
        # Get the first inbox to send from
        inboxes = api("GET", "inboxes")
        if "error" in inboxes:
            print(f"Error: {inboxes}")
            return
        items = inboxes.get("data", inboxes) if isinstance(inboxes, dict) else inboxes
        if isinstance(items, dict):
            items = items.get("inboxes", items.get("data", []))
        if not items:
            print("No inboxes found. Create one first.")
            return
        from_inbox = items[0]["inbox_id"] if isinstance(items[0], dict) else items[0]
        r = api("POST", f"inboxes/{from_inbox}/messages/send", {
            "to": [to],
            "subject": subject,
            "text": body_text
        })
        print(json.dumps(r, indent=2))

    elif cmd == "list-threads":
        inbox_id = args[1] if len(args) > 1 else None
        if inbox_id:
            r = api("GET", f"inboxes/{inbox_id}/threads")
        else:
            r = api("GET", "threads")
        print(json.dumps(r, indent=2))

    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
