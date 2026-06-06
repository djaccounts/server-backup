# Multi-Agent Slack Setup Guide

## Problem
You want two independent Hermes agents on Slack (e.g., one for general work, one for private/email work). Each needs its own channel and its own model provider.

## Why You Need Two Slack Apps
Slack's Socket Mode (`SLACK_APP_TOKEN`) allows only **one active WebSocket connection per app token**. If you try to run two Hermes gateways with the same tokens, the second gateway fails with:
```
Slack app token already in use (PID XXXXX). Stop the other gateway first.
```
This is a Slack platform limitation — there is no workaround. You must create a second Slack app.

## Step-by-Step: Creating the Second Slack App

### 1. Create the app
1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name it (e.g., "Private Agent") → select your workspace → **"Create App"**

### 2. Add bot token scopes
1. Left sidebar → **"OAuth & Permissions"**
2. Under **"Bot Token Scopes"**, add:
   - `channels:history`
   - `channels:read`
   - `chat:write`
   - `groups:history`
   - `groups:read`
   - `im:history`
   - `im:read`
   - `mpim:history`
   - `mpim:read`
3. Scroll up → **"Install to Workspace"** → approve
4. Copy the **"Bot User OAuth Token"** (`xoxb-...`)

### 3. Enable Socket Mode
1. Left sidebar → **"Socket Mode"** → toggle **on**
2. Under **"App-Level Tokens"** → **"Generate Token"**
3. Name it (e.g., "private-agent-token")
4. Add scope: `connections:write`
5. Copy the generated token (`xapp-1-...`)

### 4. Subscribe to events
1. Left sidebar → **"Event Subscriptions"**
2. Toggle **"Enable Events"** to on
3. Under **"Subscribe to bot events"**, add:
   - `message.channels`
   - `message.groups`
4. **"Save Changes"**

### 5. Add bot to channel
1. In Slack, open the target channel (e.g., #private-agent)
2. Type `/add @Private Agent` or use channel settings → Integrations → Add apps

### 6. Configure the private profile
Write the tokens to `~/.hermes/profiles/private/.env`:
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-1-...
SLACK_HOME_CHANNEL=C0XXXXXXXXX
SLACK_ALLOWED_CHANNELS=C0XXXXXXXXX
```

### 7. Restart the private gateway
```bash
systemctl --user restart hermes-gateway-private
```

### 8. Verify
```bash
journalctl --user -u hermes-gateway-private -n 20
```
Look for successful Slack connection messages (not "already in use" or "missing_scope" errors).

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Slack app token already in use` | Same tokens used by two gateways | Create a second Slack app |
| `missing_scope` | Bot needs additional OAuth scopes | Add scopes → Reinstall to workspace |
| `No messaging platforms enabled` | No Slack tokens in profile `.env` | Copy tokens to `~/.hermes/profiles/private/.env` |
| `not_in_channel` | Bot not added to the channel | `/add @BotName` in the channel |
