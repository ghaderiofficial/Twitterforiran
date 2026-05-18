import asyncio
import threading
import sqlite3
import feedparser
import aiohttp

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from deep_translator import GoogleTranslator


# ================= CONFIG =================

TOKEN = "توکن_ربات"
CHANNEL = "@Twitterforiran"

CHECK_INTERVAL = 120

# ==========================================


translator = GoogleTranslator(
    source="auto",
    target="fa"
)


# ================= DATABASE =================

db = sqlite3.connect(
    "data.db",
    check_same_thread=False
)

cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    category TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS sent(
    post_id TEXT PRIMARY KEY
)
""")

db.commit()


def add_user(username, category):

    try:

        cur.execute(
            "INSERT OR IGNORE INTO users VALUES(?,?)",
            (username, category)
        )

        db.commit()

    except:
        pass


def remove_user(username):

    cur.execute(
        "DELETE FROM users WHERE username=?",
        (username,)
    )

    db.commit()


def get_users():

    cur.execute(
        "SELECT username, category FROM users"
    )

    return cur.fetchall()


def seen(post_id):

    cur.execute(
        "SELECT post_id FROM sent WHERE post_id=?",
        (post_id,)
    )

    return cur.fetchone()


def save_post(post_id):

    try:

        cur.execute(
            "INSERT INTO sent VALUES(?)",
            (post_id,)
        )

        db.commit()

    except:
        pass


# ================= DEFAULT USERS =================

DEFAULT_USERS = [

    ("elonmusk", "tech"),
    ("realDonaldTrump", "politics"),
    ("BarackObama", "politics"),
    ("Cristiano", "sports"),
    ("neymarjr", "sports"),
    ("KMbappe", "sports"),
    ("Reuters", "news"),
    ("BBCWorld", "news"),
    ("cnnbrk", "news"),
    ("ethereum", "crypto"),
    ("cz_binance", "crypto"),
    ("VitalikButerin", "crypto"),
]

for u, c in DEFAULT_USERS:
    add_user(u, c)


# ================= HELPERS =================

def translate(text):

    try:
        return translator.translate(text)

    except:
        return text


def rss_url(user):

    return f"https://nitter.net/{user}/rss"


async def fetch_feed(session, user):

    try:

        async with session.get(
            rss_url(user),
            timeout=20
        ) as r:

            text = await r.text()

            return feedparser.parse(text).entries[:2]

    except Exception as e:

        print("RSS ERROR:", e)

        return []


async def send_post(app, item, username, category):

    if seen(item.id):
        return

    save_post(item.id)

    text = f"""
🔥 {category.upper()}

👤 @{username}

📝 {translate(item.title)}

🔗 {item.link}

📢 @Twitterforiran
"""

    try:

        await app.bot.send_message(
            chat_id=CHANNEL,
            text=text
        )

        print("POST:", username)

    except Exception as e:

        print("SEND ERROR:", e)


# ================= WORKER =================

async def worker(app):

    async with aiohttp.ClientSession() as session:

        while True:

            users = get_users()

            for username, category in users:

                posts = await fetch_feed(
                    session,
                    username
                )

                for item in posts:

                    await send_post(
                        app,
                        item,
                        username,
                        category
                    )

            await asyncio.sleep(
                CHECK_INTERVAL
            )


# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    txt = """
🚀 TwitterForIran Online

دستورات:

/status
/list
/add username category
/del username
/categories
"""

    await update.message.reply_text(txt)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    count = len(get_users())

    txt = f"""
✅ ONLINE

📡 Accounts: {count}

⏱ Interval: {CHECK_INTERVAL}s

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

    users = get_users()

    if not users:

        await update.message.reply_text(
            "❌ Empty"
        )

        return

    txt = "📡 Accounts:\n\n"

    for u, c in users:

        txt += f"• @{u} → {c}\n"

    await update.message.reply_text(txt)


async def add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        username = context.args[0]
        category = context.args[1]

        add_user(username, category)

        await update.message.reply_text(
            f"✅ Added @{username}"
        )

    except:

        await update.message.reply_text(
            "/add username category"
        )


async def del_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        username = context.args[0]

        remove_user(username)

        await update.message.reply_text(
            f"❌ Deleted @{username}"
        )

    except:

        await update.message.reply_text(
            "/del username"
        )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "❓ دستور نامعتبر"
    )


# ================= MAIN =================

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
        MessageHandler(
            filters.TEXT,
            unknown
        )
    )

    def run_worker():

        asyncio.run(
            worker(app)
        )

    threading.Thread(
        target=run_worker,
        daemon=True
    ).start()

    print("BOT STARTED")

    app.run_polling(
        drop_pending_updates=True,
        close_loop=False
    )


if __name__ == "__main__":
    main()
