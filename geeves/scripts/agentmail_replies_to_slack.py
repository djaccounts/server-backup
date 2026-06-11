#!/usr/bin/env python3
"""
agentmail_replies_to_slack.py — Check AgentMail inbox for new replies and post to Slack.

Runs as a cron job every 15 minutes.
Fetches unread/received threads from AgentMail, posts new messages to Slack,
and marks them as read to avoid duplicates.
"""
import json, urllib.request, urllib.error, subprocess, os, time
from datetime import datetime, timezone

ENV_PATH = "/root/.hermes/.env"
STATE_FILE = "/root/Geeves/agentmail_replies_state.json"

def get_env_key(var_name):
    r = subprocess.run(["grep", var_name, ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def api(method, path, data=None, api_type="agentmail"):
    if api_type == "agentmail":
        key = get_env_key("AGENT_MAIL_API")
        base = "https://api.agentmail.to/v0"
    else:
        key = get_env_key("SLACK_BOT_TOKEN")
        base = "https://slack.com/api"
    url = f"{base}/{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": json.loads(e.read()), "status": e.code}

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"processed_thread_ids": [], "last_check": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def get_thread_messages(inbox_id, thread_id):
    """Get all messages in a thread."""
    result = api("GET", f"inboxes/{inbox_id}/threads/{thread_id}/messages")
    return result.get("messages", result.get("data", []))

def mark_thread_read(inbox_id, thread_id):
    """Mark a thread as read."""
    result = api("POST", f"inboxes/{inbox_id}/threads/{thread_id}/read")
    return result

def post_to_slack(channel, text):
    """Post a message to Slack."""
    result = api("POST", "chat.postMessage", {
        "channel": channel,
        "text": text,
        "unfurl_links": False
    }, api_type="slack")
    return result

def main():
    state = load_state()
    inbox_id = "davidj@agentmail.to"
    slack_channel = get_env_key("SLACK_HOME_CHANNEL") or "C0B7C89HKQ9"

    # List threads — look for received (not just sent) threads
    threads_result = api("GET", f"inboxes/{inbox_id}/threads?limit=50")
    threads = threads_result.get("threads", threads_result.get("data", []))

    if not threads:
        print(f"[{datetime.now().isoformat()}] No threads found.")
        return

    new_replies = []

    for thread in threads:
        thread_id = thread.get("threadId")
        labels = thread.get("labels", [])
        subject = thread.get("subject", "")
        preview = thread.get("preview", "")
        senders = thread.get("senders", [])

        # Skip if already processed
        if thread_id in state["processed_thread_ids"]:
            continue

        # Skip sent-only threads (no replies)
        if labels == ["sent"]:
            state["processed_thread_ids"].append(thread_id)
            continue

        # Skip the morning digest thread
        if "Morning Digest" in subject or "digest" in subject.lower():
            state["processed_thread_ids"].append(thread_id)
            continue

        # Skip test emails
        if subject.strip() == "Test":
            state["processed_thread_ids"].append(thread_id)
            continue

        # This is a reply — get the full messages
        messages = get_thread_messages(inbox_id, thread_id)
        
        # Find the reply message (not our sent invite)
        reply_messages = []
        for msg in messages:
            sender = msg.get("from", msg.get("sender", ""))
            # Skip messages from our own inbox
            if inbox_id in str(sender) or "davidj@agentmail" in str(sender):
                continue
            reply_messages.append(msg)

        if reply_messages:
            for reply in reply_messages:
                sender_name = reply.get("from_name", reply.get("sender_name", "Unknown"))
                sender_email = reply.get("from_email", reply.get("sender_email", ""))
                body = reply.get("text", reply.get("body", preview))
                # Truncate long bodies
                if len(body) > 500:
                    body = body[:500] + "..."
                
                slack_msg = f"📬 *Dinner Party Reply*\n*From:* {sender_name} ({sender_email})\n*Subject:* {subject}\n\n{body}"
                
                result = post_to_slack(slack_channel, slack_msg)
                if result.get("ok"):
                    print(f"[{datetime.now().isoformat()}] Posted reply from {sender_name} to Slack")
                else:
                    print(f"[{datetime.now().isoformat()}] Slack post failed: {result}")

                new_replies.append({
                    "from": sender_name,
                    "email": sender_email,
                    "subject": subject,
                    "time": datetime.now().isoformat()
                })

        # Mark as processed and read
        state["processed_thread_ids"].append(thread_id)
        mark_thread_read(inbox_id, thread_id)

    state["last_check"] = datetime.now().isoformat()
    save_state(state)

    if not new_replies:
        print(f"[{datetime.now().isoformat()}] No new replies.")
    else:
        print(f"[{datetime.now().isoformat()}] Processed {len(new_replies)} new reply(ies).")

if __name__ == "__main__":
    main()
