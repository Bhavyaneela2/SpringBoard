import sqlite3

def get_user(username):
    # Safer example: use a parameterized query.
    with sqlite3.connect("demo.db") as conn:
        return conn.execute(
            "SELECT * FROM users WHERE name = ?",
            (username,)
        ).fetchall()
