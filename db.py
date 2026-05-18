import sqlite3

db = sqlite3.connect("data.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user TEXT,
category TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS posts(
id TEXT
)
""")

db.commit()


def add(user, category):
    cur.execute(
        "INSERT INTO users VALUES(?,?)",
        (user, category)
    )
    db.commit()


def remove(user):
    cur.execute(
        "DELETE FROM users WHERE user=?",
        (user,)
    )
    db.commit()


def list_users():
    cur.execute(
        "SELECT * FROM users"
    )
    return cur.fetchall()


def seen(pid):

    cur.execute(
        "SELECT * FROM posts WHERE id=?",
        (pid,)
    )

    return cur.fetchone()


def save(pid):

    cur.execute(
        "INSERT INTO posts VALUES(?)",
        (pid,)
    )

    db.commit()
