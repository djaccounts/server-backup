---
name: apple-integrations
description: "Apple ecosystem integrations: Apple Notes, Apple Reminders, Find My, iMessage, and macOS computer use. Use when interacting with Apple services from the terminal — managing notes/reminders, locating devices, sending iMessage, or controlling macOS via computer use."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [apple, macos, notes, reminders, findmy, imessage, computer-use]
    related_skills: [apple-integrations]
---

# Apple Ecosystem Integrations

Apple services integration for macOS.

---

## Apple Notes

Manage Apple Notes from the terminal.

```bash
# List notes:
osascript -e 'tell application "Notes" to get name of every note'

# Create note:
osascript -e 'tell application "Notes" to make new note with properties {name:"Title", body:"Content"}'

# Search notes:
osascript -e 'tell application "Notes" to get name of every note whose name contains "keyword"'
```

---

## Apple Reminders

Manage Apple Reminders from the terminal.

```bash
# List reminders:
osascript -e 'tell application "Reminders" to get name of every reminder'

# Create reminder:
osascript -e 'tell application "Reminders" to make new reminder with properties {name:"Task", body:"Details"}'

# Complete reminder:
osascript -e 'tell application "Reminders" to set completed of reminder "Task" to true'
```

---

## Find My

Locate Apple devices.

```bash
# Requires Find My to be open or use shortcut
# Typically accessed via Shortcuts app or Find My CLI tools
```

---

## iMessage

Send and manage iMessages.

```bash
# Send iMessage:
osascript -e 'tell application "Messages" to send "Hello" to buddy "phone@email.com" of service "E:email@gmail.com"'

# List conversations:
osascript -e 'tell application "Messages" to get name of every chat'
```

---

## macOS Computer Use

Control macOS via accessibility APIs.

```bash
# Click at coordinates:
cliclick c:100,200

# Type text:
cliclick t:"Hello World"

# Requires Accessibility permissions in System Preferences → Privacy & Security
```
