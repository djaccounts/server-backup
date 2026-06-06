# AgentMail Setup Reference

## Why AgentMail over Gmail OAuth
- Google OAuth requires External consent screen + test user setup — `org_internal` error for personal Gmail
- AgentMail: create inbox in one API call, no OAuth, no SMTP config
- Free tier available, no credit card

## Setup Steps
1. Get API key from https://console.agentmail.to
2. Add to Hermes `.env`: `AGENT_MAIL_API_KEY=*** Install CLI: `npm install -g agentmail-cli`
4. Add MCP server to `~/.hermes/config.yaml`:
   ```yaml
   mcp_servers:
     agentmail:
       command: "npx"
       args: ["-y", "agentmail-mcp"]
       env:
         AGENTMAIL_API_KEY: "${AGENT_MAIL_API_KEY}"
   ```
5. Reload MCP: `/reload-mcp` in Hermes chat
6. Create inbox: `agentmail inboxes create --display-name "Geeves"`

## Sending Email (Python — avoids shell quoting issues)
```python
import subprocess, os, json

def send_email(to, subject, body):
    with open("/root/.hermes/.env") as f:
        for line in f:
            if line.strip().startswith("AGENT_MAIL_API_KEY"):
                key = line.strip().split("=", 1)[1]
                break
    env = os.environ.copy()
    env["AGENTMAIL_API_KEY"] = key
    result = subprocess.run(
        ["agentmail", "message", "send",
         "--to", to, "--subject", subject, "--body", body],
        capture_output=True, text=True, env=env
    )
    return result.stdout
```

## Key Quirk
The API key contains characters (`+`, `/`, `=`) that break shell interpolation.
**Never** use `$KEY` in curl/bash. Always use Python subprocess with env dict.
