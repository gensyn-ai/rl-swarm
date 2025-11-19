# Monitoring RL-Swarm from Telegram on WSL2

This guide explains how to set up a simple Telegram bot that checks whether an RL-Swarm node is running inside **WSL2 + Ubuntu**.

The bot responds to a `/status` command and reports either:
- `"🚀 RL-Swarm is RUNNING!"`
- `"⚠️ RL-Swarm is NOT running!"`

---

## 1. Create a Telegram Bot

1. Open Telegram and start a chat with **@BotFather**.
2. Send: `/newbot`
3. Follow the prompts to choose a name and username.
4. BotFather will provide a token such as:1234567890:ABCDEF...


Save this as your **TELEGRAM_BOT_TOKEN**.

### Get your Chat ID

1. Send a message to your newly created bot.
2. Use `@userinfobot`, or call Telegram's `getUpdates` API, to get your numeric chat ID:123456789


Save this as **TELEGRAM_CHAT_ID**.

---

## 2. Example bot script (Python)

Create a Python script at:  
`~/telegram_bot.py`

Paste the following:

```python
import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if TELEGRAM_TOKEN is None or TELEGRAM_CHAT_ID is None:
    raise RuntimeError("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")

def is_swarm_running() -> bool:
    """Check whether RL-Swarm is running."""
    try:
        out = subprocess.check_output(["ps", "aux"], text=True)
        return "code_gen_exp.runner.swarm_launcher" in out
    except:
        return False

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    running = is_swarm_running()
    msg = "🚀 RL-Swarm is RUNNING!" if running else "⚠️ RL-Swarm is NOT running!"
    await context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("status", status))
    print("Telegram bot is running… Press Ctrl+C to stop.")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

3. Running the bot

Set your environment variables:

export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
export TELEGRAM_CHAT_ID="YOUR_CHAT_ID"


Run the bot:

python ~/telegram_bot.py


Now open Telegram and send your bot:

/status


You should receive:

🚀 RL-Swarm is RUNNING!


or:

⚠️ RL-Swarm is NOT running!
