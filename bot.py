import json
import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

CONFIG_FILE = "config.json"
STATE_FILE = "state.json"
JOB_NAME = "recurring_post"


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_state(config):
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    else:
        state = {}
    state.setdefault("message_text", config["message_text"])
    state.setdefault("interval_minutes", config["interval_minutes"])
    state.setdefault("last_message_id", None)
    return state


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def is_owner(update: Update, config) -> bool:
    return bool(update.effective_user) and update.effective_user.id == config["owner_id"]


async def post_message(context: ContextTypes.DEFAULT_TYPE):
    config = context.bot_data["config"]
    state = context.bot_data["state"]
    channel_id = config["channel_id"]

    # Delete the previous message, if there is one
    if state.get("last_message_id"):
        try:
            await context.bot.delete_message(chat_id=channel_id, message_id=state["last_message_id"])
        except TelegramError as e:
            logger.warning(f"Could not delete previous message: {e}")

    # Send the new message
    try:
        msg = await context.bot.send_message(chat_id=channel_id, text=state["message_text"])
        state["last_message_id"] = msg.message_id
        save_state(state)
        logger.info("Posted new message and updated state.")
    except TelegramError as e:
        logger.error(f"Failed to send message: {e}")


def schedule_job(app: Application):
    state = app.bot_data["state"]
    for job in app.job_queue.get_jobs_by_name(JOB_NAME):
        job.schedule_removal()
    interval_seconds = max(int(float(state["interval_minutes"]) * 60), 10)
    app.job_queue.run_repeating(post_message, interval=interval_seconds, first=5, name=JOB_NAME)
    logger.info(f"Scheduled recurring post every {state['interval_minutes']} minute(s).")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = context.bot_data["config"]
    if not is_owner(update, config):
        return
    state = context.bot_data["state"]
    await update.message.reply_text(
        f"Interval: {state['interval_minutes']} minute(s)\n"
        f"Message:\n{state['message_text']}\n\n"
        f"Last message ID: {state['last_message_id']}"
    )


async def cmd_setinterval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = context.bot_data["config"]
    if not is_owner(update, config):
        return
    if not context.args or not context.args[0].replace(".", "", 1).isdigit():
        await update.message.reply_text("Usage: /setinterval <minutes>  e.g. /setinterval 30")
        return
    minutes = float(context.args[0])
    state = context.bot_data["state"]
    state["interval_minutes"] = minutes
    save_state(state)
    schedule_job(context.application)
    await update.message.reply_text(f"Interval updated to {minutes} minute(s).")


async def cmd_setmessage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = context.bot_data["config"]
    if not is_owner(update, config):
        return
    text = update.message.text.partition(" ")[2]
    if not text:
        await update.message.reply_text("Usage: /setmessage <your message text>")
        return
    state = context.bot_data["state"]
    state["message_text"] = text
    save_state(state)
    await update.message.reply_text("Message updated. It will be used on the next post.")


async def cmd_postnow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = context.bot_data["config"]
    if not is_owner(update, config):
        return
    await post_message(context)
    await update.message.reply_text("Posted.")


def main():
    config = load_config()
    state = load_state(config)

    app = Application.builder().token(config["bot_token"]).build()
    app.bot_data["config"] = config
    app.bot_data["state"] = state

    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("setinterval", cmd_setinterval))
    app.add_handler(CommandHandler("setmessage", cmd_setmessage))
    app.add_handler(CommandHandler("postnow", cmd_postnow))

    schedule_job(app)

    logger.info("Bot started.")
    app.run_polling()


if __name__ == "__main__":
    main()
