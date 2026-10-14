import sqlite3
from datetime import datetime
from pathlib import Path

CATEGORIES = [
    "Наука и инновации", "Образование", "Студенческая жизнь", "Спорт",
    "Культура и творчество", "Международная деятельность",
    "Сотрудничество и партнёрство", "Объявления и события",
    "Абитуриентам", "Без категории",
]
UNIVERSITIES = ["РАНХиГС", "РЭУ", "МАИ"]


def connect(path):
    conn = sqlite3.connect(path, timeout=20)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_news_db(path="news.db"):
    Path(path).parent.mkdir(parents=True, exist_ok=True) if str(Path(path).parent) not in (".", "") else None
    with connect(path) as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            link TEXT UNIQUE NOT NULL,
            published_date TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            university_id INTEGER NOT NULL,
            added_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY(category_id) REFERENCES news_categories(category_id),
            FOREIGN KEY(university_id) REFERENCES universities(university_id)
        );
        CREATE TABLE IF NOT EXISTS news_categories (
            category_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS universities (
            university_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        CREATE INDEX IF NOT EXISTS idx_news_added_at ON news(added_at);
        CREATE INDEX IF NOT EXISTS idx_news_category ON news(category_id);
        """)
        for idx, name in enumerate(CATEGORIES, 1):
            con.execute("INSERT OR IGNORE INTO news_categories(category_id,name) VALUES (?,?)", (idx, name))
        for idx, name in enumerate(UNIVERSITIES, 1):
            con.execute("INSERT OR IGNORE INTO universities(university_id,name) VALUES (?,?)", (idx, name))


def init_users_db(path="users.db", seed=True):
    with connect(path) as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS news_categories (
            category_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT
        );
        CREATE TABLE IF NOT EXISTS user_categories (
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            PRIMARY KEY(user_id, category_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(category_id) REFERENCES news_categories(category_id)
        );
        """)
        for idx, name in enumerate(CATEGORIES, 1):
            con.execute("INSERT OR IGNORE INTO news_categories(category_id,name) VALUES (?,?)", (idx, name))
        if seed and con.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            users = [
                (1, "Анна", "anna@example.com", [1, 9]),
                (2, "Иван", "ivan@example.com", [2, 4]),
                (3, "Мария", "maria@example.com", [3, 5, 8]),
                (4, "Дмитрий", "dmitry@example.com", [6, 7]),
                (5, "Екатерина", "ekaterina@example.com", [3, 9, 10]),
            ]
            for uid, name, email, categories in users:
                con.execute("INSERT INTO users(id,name,email) VALUES (?,?,?)", (uid, name, email))
                con.executemany("INSERT INTO user_categories(user_id,category_id) VALUES (?,?)",
                                [(uid, cid) for cid in categories])


def category_id_for(con, category):
    category = category if category in CATEGORIES else "Без категории"
    return con.execute("SELECT category_id FROM news_categories WHERE name=?", (category,)).fetchone()[0]


def university_id_for(con, university):
    row = con.execute("SELECT university_id FROM universities WHERE name=?", (university,)).fetchone()
    if row:
        return row[0]
    con.execute("INSERT OR IGNORE INTO universities(name) VALUES (?)", (university,))
    return con.execute("SELECT university_id FROM universities WHERE name=?", (university,)).fetchone()[0]


def save_news(path, records):
    inserted = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with connect(path) as con:
        for item in records:
            title = (item.get("title") or "Без заголовка").strip()
            link = (item.get("link") or "").strip()
            if not link:
                continue
            category_id = category_id_for(con, item.get("category", "Без категории"))
            university_id = university_id_for(con, item.get("university", "Неизвестный вуз"))
            cur = con.execute("""
                INSERT OR IGNORE INTO news
                (title, content, link, published_date, category_id, university_id, added_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, item.get("content", ""), link,
                  item.get("published_date") or "Не указана", category_id, university_id, now))
            if cur.rowcount == 1:
                row = con.execute("""SELECT n.id,n.title,n.link,n.published_date,c.name,u.name
                    FROM news n JOIN news_categories c USING(category_id)
                    JOIN universities u USING(university_id) WHERE n.id=?""", (cur.lastrowid,)).fetchone()
                inserted.append({"id": row[0], "title": row[1], "link": row[2],
                                 "published_date": row[3], "category": row[4], "university": row[5]})
    return inserted


def users_with_categories(path):
    with connect(path) as con:
        rows = con.execute("""SELECT u.id,u.name,uc.category_id FROM users u
                              LEFT JOIN user_categories uc ON uc.user_id=u.id ORDER BY u.id""").fetchall()
    result = {}
    for uid, name, cid in rows:
        result.setdefault(uid, {"name": name, "categories": set()})
        if cid is not None:
            result[uid]["categories"].add(cid)
    return result


def category_ids_for_news(path, news_ids):
    if not news_ids:
        return {}
    marks = ",".join("?" for _ in news_ids)
    with connect(path) as con:
        rows = con.execute(f"SELECT id,category_id FROM news WHERE id IN ({marks})", list(news_ids)).fetchall()
    return dict(rows)
