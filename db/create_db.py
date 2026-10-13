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

# テスト用：21語の問題（教養・ふつうの設問1になる）
# 各熟語の空欄を (位置, 空欄番号) で指定する。答えは 1電 2気 3学 4生 5水 6力
TEST_ANSWERS = {1: "電", 2: "気", 3: "学", 4: "生", 5: "水", 6: "力"}
TEST_QUESTION = [
    ("電池", [(0, 1)]),
    ("電気", [(0, 1), (1, 2)]),
    ("天気", [(1, 2)]),
    ("気分", [(0, 2)]),
    ("大学生", [(1, 3), (2, 4)]),
    ("学校", [(0, 3)]),
    ("学生", [(0, 3), (1, 4)]),
    ("生活", [(0, 4)]),
    ("大学教授", [(1, 3)]),
    ("水道", [(0, 5)]),
    ("海水", [(1, 5)]),
    ("水力発電", [(0, 5), (1, 6), (3, 1)]),
    ("電力", [(0, 1), (1, 6)]),
    ("電気分解", [(0, 1), (1, 2)]),
    ("力学", [(0, 6), (1, 3)]),
    ("電車", [(0, 1)]),
    ("気温", [(0, 2)]),
    ("生物", [(0, 4)]),
    ("水泳", [(0, 5)]),
    ("学力", [(0, 3), (1, 6)]),
    ("力士", [(0, 6)]),
]

cur.execute(
    "INSERT INTO questions (field, difficulty, word_count) VALUES (?, ?, ?)",
    ("教養", 2, len(TEST_QUESTION))
)
test_question_id = cur.lastrowid

for word, blanks in TEST_QUESTION:
    cur.execute("INSERT INTO words (word, field, difficulty) VALUES (?, ?, ?)", (word, "教養", 2))
    word_id = cur.lastrowid
    for blank_position, blank_number in blanks:
        # 空欄の位置の漢字が、その番号の答えと一致しているか確認する
        assert word[blank_position] == TEST_ANSWERS[blank_number], (word, blank_position, blank_number)
        cur.execute(
            "INSERT INTO question_words (question_id, word_id, blank_position, blank_number) VALUES (?, ?, ?, ?)",
            (test_question_id, word_id, blank_position, blank_number)
        )

conn.commit()
conn.close()