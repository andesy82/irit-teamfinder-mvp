import sqlite3
from pathlib import Path

DB_PATH = Path("teamfinder.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                skills TEXT NOT NULL,
                tg_username TEXT NOT NULL
            )
        """)

def add_user(name: str, role: str, skills: str, tg_username: str) -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "INSERT INTO users (name, role, skills, tg_username) VALUES (?, ?, ?, ?)",
            (name, role, skills, tg_username)
        )
        return {"id": cursor.lastrowid, "name": name, "role": role, "skills": skills, "tg_username": tg_username}

def get_all_users() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]
