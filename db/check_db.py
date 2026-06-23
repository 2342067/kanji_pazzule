import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "puzzle.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

result_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result.txt")

with open(result_path, "w", encoding="utf-8") as f:
    f.write("=== words ===\n")
    cur.execute("SELECT * FROM words")
    for row in cur.fetchall():
        f.write(str(row) + "\n")

    f.write("\n=== questions ===\n")
    cur.execute("SELECT * FROM questions")
    for row in cur.fetchall():
        f.write(str(row) + "\n")

    f.write("\n=== question_words ===\n")
    cur.execute("SELECT * FROM question_words")
    for row in cur.fetchall():
        f.write(str(row) + "\n")

conn.close()