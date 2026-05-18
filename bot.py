import asyncio
import threading
import feedparser
import aiohttp

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from deep_translator import GoogleTranslator

from config import TOKEN, CHANNEL, CHECK_INTERVAL
from db import list_users, add, remove, seen, save


translator = GoogleTranslator(
    source="auto",
    target="fa"
)

START_MSG = "🚀 TwitterForIran Online"


def tr(text):
    try:
        return translator.translate(text)
    except:
        return text


def rss(user):
    return f"https://nitter.net/{user}/rss"


async def fetch(session, url):
    try:
        async with session.get(url, timeout=20) as r:
            return await r.text()
    except:
        return None


async def get_posts(session, user):

    data = await fetch(
        session,
        rss(user)
    )

    if not data:
        return []

    return feedparser.parse(data).entries[:2]


async def send_post(app, item, user, category):

    if seen(item.id):
        return

    save(item.id)

    text = f"""
🔥 {category.upper()}

👤 @{user}

📝 {tr(item.title)}

🔗 {item.link}

📢 @Twitterforiran
"""

    try:

        await app.bot.send_message(
            chat_id=CHANNEL,
            text=text
        )

        print("POST SENT:", user)

    except Exception as e:
        print("SEND ERROR:", e)


async def worker(app):

    async with aiohttp.ClientSession() as session:

        while True:

            users = list_users()

            for user, category in users:

                try:

                    posts = await get_posts(
                        session,
                        user
                    )

                    for item in posts:

                        await send_post(
                            app,
                            item,
                            user,
                            category
                        )

                except Exception as e:
                    print("FETCH ERROR:", e)

            await asyncio.sleep(
                CHECK_INTERVAL
            )


# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        START_MSG
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    users = len(list_users())

    txt = f"""
✅ Bot Online

📡 Accounts: {users}

⏱ Check: {CHECK_INTERVAL}s

📢 Channel: {CHANNEL}
"""

    await update.message.reply_text(txt)


async def categories(update: Update, context: ContextTypes.DEFAULT_TYPE):

    txt = """
📂 Categories

• politics
• sports
• crypto
• tech
• news
"""

    await update.message.reply_text(txt)


async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    users = list_users()

    if not users:

        await update.message.reply_text(
            "❌ Empty"
        )

        return

    txt = "📡 Accounts:\n\n"

    for user, cat in users:

        txt += f"• @{user} → {cat}\n"

    await update.message.reply_text(txt)


async def add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        user = context.args[0]
        category = context.args[1]

        add(user, category)

        await update.message.reply_text(
            f"✅ Added @{user}"
        )

    except:

        await update.message.reply_text(
            "/add username category"
        )


async def del_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        user = context.args[0]

        remove(user)

        await update.message.reply_text(
            f"❌ Deleted @{user}"
        )

    except:

        await update.message.reply_text(
            "/del username"
        )


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        msg = " ".join(context.args)

        await context.bot.send_message(
            chat_id=CHANNEL,
            text=msg
        )

        await update.message.reply_text(
            "✅ Sent"
        )

    except:

        await update.message.reply_text(
            "/broadcast text"
        )


async def normal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 دستور نامعتبر"
    )


def main():

    app = Application.builder() \
        .token(TOKEN) \
        .build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("status", status)
    )

    app.add_handler(
        CommandHandler("categories", categories)
    )

    app.add_handler(
        CommandHandler("list", list_cmd)
    )

    app.add_handler(
        CommandHandler("add", add_cmd)
    )

    app.add_handler(
        CommandHandler("del", del_cmd)
    )

    app.add_handler(
        CommandHandler("broadcast", broadcast)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT,
            normal
        )
    )

    def run_worker():
        asyncio.run(worker(app))

    threading.Thread(
        target=run_worker,
        daemon=True
    ).start()

    print("BOT STARTED")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
