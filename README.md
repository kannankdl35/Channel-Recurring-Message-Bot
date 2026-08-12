# Recurring Channel Poster Bot

Posts a message to your Telegram channel on a timer, deleting the previous
post each time it sends a new one.

## Setup

1. **Create the bot**
   - Message [@BotFather](https://t.me/BotFather) → `/newbot` → follow the prompts.
   - Copy the token it gives you.

2. **Add the bot to your channel**
   - Open your channel → Administrators → Add Admin → add your bot.
   - Make sure it has **"Post messages"** and **"Delete messages"** permissions.

3. **Get your channel ID**
   - If your channel has a public username, use `@yourchannelname`.
   - If it's private, forward any message from the channel to
     [@userinfobot](https://t.me/userinfobot) or [@JsonDumpBot](https://t.me/JsonDumpBot)
     to get the numeric ID (looks like `-1001234567890`).

4. **Get your own user ID (the owner)**
   - Message [@userinfobot](https://t.me/userinfobot) — it replies with your numeric user ID.
   - This restricts the control commands (interval/message changes) to only you.

5. **Fill in `config.json`**
   - `bot_token`: from step 1
   - `channel_id`: from step 3
   - `owner_id`: from step 4
   - `message_text`: default message to post
   - `interval_minutes`: how often to post

6. **Install & run**
   ```bash
   pip install -r requirements.txt
   python bot.py
   ```
   Keep it running (e.g. on a small VPS, or with `pm2`/`systemd`/`screen`) so it
   keeps posting on schedule.

## Controlling the bot

Message the bot **privately** (not in the channel) — only your `owner_id` can use these:

| Command | What it does |
|---|---|
| `/status` | Shows current interval, message, and last post ID |
| `/setinterval 30` | Changes the interval to 30 minutes (takes effect immediately) |
| `/setmessage Hello everyone!` | Changes the message used for future posts |
| `/postnow` | Posts immediately (also deletes the previous post) |

Settings persist in an auto-created `state.json`, so they survive restarts.

## Notes

- The bot can only delete messages it sent itself, which is exactly what this
  does — each new post's ID is remembered so the old one can be removed first.
- If the bot loses admin rights or the previous message was already deleted
  manually, it just logs a warning and posts the new message anyway.
