import sqlite3
import os
import csv

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(base_dir, "puzzle.db")
csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "words.csv")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    field TEXT NOT NULL,
    difficulty INTEGER NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY,
    field TEXT NOT NULL,
    difficulty INTEGER NOT NULL,
    word_count INTEGER NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS question_words (
    id INTEGER PRIMARY KEY,
    question_id INTEGER NOT NULL,
    word_id INTEGER NOT NULL,
    blank_position INTEGER NOT NULL,
    blank_number INTEGER NOT NULL,
    FOREIGN KEY (question_id) REFERENCES questions(id),
    FOREIGN KEY (word_id) REFERENCES words(id)
)
""")

# 再実行しても重複しないように既存データをクリア（参照先から先に削除）
cur.execute("DELETE FROM question_words")
cur.execute("DELETE FROM questions")
cur.execute("DELETE FROM words")

with open(csv_path, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    words = [(row["word"], row["field"], int(row["difficulty"])) for row in reader]

cur.executemany("INSERT INTO words (word, field, difficulty) VALUES (?, ?, ?)", words)
conn.commit()

# 登録したwordsをidつきで取り直す
cur.execute("SELECT id, field, difficulty FROM words")
inserted_words = cur.fetchall()

# 1単語=1問として、questionsとquestion_wordsを生成（1文字目を空欄にする）
for word_id, field, difficulty in inserted_words:
    cur.execute(
        "INSERT INTO questions (field, difficulty, word_count) VALUES (?, ?, ?)",
        (field, difficulty, 1)
    )
    question_id = cur.lastrowid

    cur.execute(
        "INSERT INTO question_words (question_id, word_id, blank_position, blank_number) VALUES (?, ?, ?, ?)",
        (question_id, word_id, 0, 1)
    )

# テスト用：複数単語が同じ空欄番号を共有する問題（「電流」「電池」、ともに1文字目が「電」）
cur.execute("INSERT INTO words (word, field, difficulty) VALUES (?, ?, ?)", ("電流", "理科", 1))
word_id_a = cur.lastrowid
cur.execute("INSERT INTO words (word, field, difficulty) VALUES (?, ?, ?)", ("電池", "理科", 1))
word_id_b = cur.lastrowid

cur.execute(
    "INSERT INTO questions (field, difficulty, word_count) VALUES (?, ?, ?)",
    ("理科", 1, 2)
)
multi_question_id = cur.lastrowid

cur.executemany(
    "INSERT INTO question_words (question_id, word_id, blank_position, blank_number) VALUES (?, ?, ?, ?)",
    [
        (multi_question_id, word_id_a, 0, 1),
        (multi_question_id, word_id_b, 0, 1),
    ]
)

conn.commit()
conn.close()