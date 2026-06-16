import sqlite3

conn = sqlite3.connect("puzzle.db")
cur = conn.cursor()

# 熟語テーブル
cur.execute("""
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    field TEXT NOT NULL,
    difficulty INTEGER NOT NULL
)
""")

# ダミー熟語データ（分野：理科、難易度：1）
words = [
    ("光合成", "理科", 1),
    ("蒸発", "理科", 1),
    ("電流", "理科", 1),
    ("磁石", "理科", 1),
    ("光線", "理科", 1),
    ("合唱", "教養", 1),
    ("石合", "教養", 1),
]

cur.executemany("INSERT INTO words (word, field, difficulty) VALUES (?, ?, ?)", words)
conn.commit()
conn.close()

print("DB作成完了")