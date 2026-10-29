import sqlite3

def get_user(username):
    # Intentionally vulnerable training example: do not use in production.
    conn = sqlite3.connect("demo.db")
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    return conn.execute(query).fetchall()
