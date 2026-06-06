# Geeves Messaging Abstraction Layer
#
# Wraps messaging behind a tiny interface so swapping Slack -> Telegram later
# requires zero logic changes -- just swap the backend.
#
# Current backend: Slack (via Hermes send_message tool)
# Future backend: Telegram (swap the CHANNELS map)
#
# Hermes note: This module is reference + importable library.
# In Hermes tool calls, use send_message() directly with target patterns below.

# -- Target patterns ----------------------------------------------------------
# Slack channel:  "slack:#channel-name"  or  "slack:channel_id"
# Slack DM:       "slack:user:U0B73K4QWP5"
# Telegram:       "telegram:chat_id"       (future)
# Email:          use hermes email tools   (future)

# -- Sender IDs ---------------------------------------------------------------
DAVID_SLACK_ID = "U0B73K4QWP5"
WIFE_SLACK_ID = "FILL_IN_when_known"

# -- Channel map --------------------------------------------------------------
CHANNELS = {
    "general": "slack:#geeves",          # main Geeves channel
    "data": "slack:#geeves-data",        # data collection channel (create when ready)
}

# -- Guidelines ---------------------------------------------------------------
# 1. ALWAYS use CHANNELS map or named targets -- never hardcode IDs in logic.
# 2. When swapping to Telegram, only this file's CHANNELS map needs to change.
#    All skills/cron jobs call send() and never touch raw IDs.


def resolve(target: str) -> str:
    """Resolve a named target to a send_message-compatible string.

    Passing a raw target (e.g. 'slack:#geeves') through is fine --
    this function passes through anything that looks like 'platform:...'.
    Named shortcuts like 'general' or 'data' are looked up in CHANNELS.
    """
    if target in CHANNELS:
        return CHANNELS[target]
    if ":" in target:
        return target
    raise ValueError(f"Unknown target: {target!r}. Use a CHANNELS name or 'platform:id'.")


if __name__ == "__main__":
    # Quick self-test
    print("general ->", resolve("general"))
    print("data    ->", resolve("data"))
    print("raw     ->", resolve("slack:#geeves"))
    try:
        resolve("unknown")
    except ValueError as e:
        print("error   ->", e)
