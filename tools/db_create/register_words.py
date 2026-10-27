"""
input フォルダにある用語リスト（CSV）を、選んだ教科の熟語として words テーブルに登録するスクリプト。

【フォルダ運用】
    input/      登録するCSVを1つだけ置く場所（処理後もそのまま残る）
    record/     登録したCSVを手動で置いておく場所（このスクリプトは触らない）

実行すると:
    1. 教科を番号で選ぶ
    2. input フォルダ内のCSVを読み込む（列：語,頻度,難度。1行目は見出し）
       CSVがない、または2つ以上ある場合は中止する
    3. その教科の既存の語と問題を削除してよいか確認する（y で実行）
       語を登録し直すと語のidが変わり、既存の問題が参照できなくなるため、その教科の問題も一緒に削除する
       他の教科のデータは残す
    4. 熟語を words テーブルに登録する（各語は1回だけ、CSVの難度で登録）

使い方:
    tools/db_create フォルダで python register_words.py
"""

import csv
import os
import sqlite3

FIELDS = {"1": "理科", "2": "社会", "3": "教養"}

# ==== パス ====
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
INPUT_DIR = os.path.join(SCRIPT_DIR, "input")
DB_PATH = os.path.join(PROJECT_DIR, "puzzle.db")


def ask_field():
    """教科を番号で選ばせ、教科名を返す"""
    while True:
        print("教科を選んでください（1：理科、2：社会、3：教養）")
        key = input("> ").strip()
        if key in FIELDS:
            return FIELDS[key]
        print("1、2、3のいずれかを入力してください。")


def collect_input_csv_paths(input_dir):
    """input フォルダ内のCSVファイル一覧を取得する"""
    if not os.path.isdir(input_dir):
        return []
    return sorted(
        os.path.join(input_dir, name)
        for name in os.listdir(input_dir)
        if name.lower().endswith(".csv")
    )


def load_words(csv_path):
    """用語リストを読み込み、[(熟語, 難度), ...] を返す（1行目は見出し）"""
    words = []
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)  # 見出し
        for row in reader:
            if not row or not row[0]:
                continue
            word, _frequency, difficulty = row[0], row[1], row[2]
            words.append((word, int(difficulty)))
    return words


def create_tables(cur):
    """テーブルがなければ作成する"""
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


def delete_field_data(cur, field):
    """指定した教科の語と問題を削除する（参照先から先に削除）"""
    cur.execute("""
        DELETE FROM question_words
        WHERE question_id IN (SELECT id FROM questions WHERE field=?)
           OR word_id IN (SELECT id FROM words WHERE field=?)
    """, (field, field))
    cur.execute("DELETE FROM questions WHERE field=?", (field,))
    cur.execute("DELETE FROM words WHERE field=?", (field,))


def insert_words(cur, field, words):
    """熟語を words に登録する"""
    for word, difficulty in words:
        cur.execute(
            "INSERT INTO words (word, field, difficulty) VALUES (?, ?, ?)",
            (word, field, difficulty)
        )


def main():
    field = ask_field()

    csv_paths = collect_input_csv_paths(INPUT_DIR)
    if not csv_paths:
        print(f"{INPUT_DIR} に登録するCSVがありません。")
        return
    if len(csv_paths) > 1:
        print(f"{INPUT_DIR} にCSVが{len(csv_paths)}つあります。1つだけにしてから、もう一度実行してください。")
        for path in csv_paths:
            print(f"  {os.path.basename(path)}")
        return

    csv_path = csv_paths[0]
    words = load_words(csv_path)

    print(f"{field}の既存の語と問題をすべて削除してから、{os.path.basename(csv_path)} の{len(words)}語を登録します。")
    answer = input("実行しますか？（y で実行）> ").strip()
    if answer != "y":
        print("中止しました。DBは変更していません。")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    create_tables(cur)
    delete_field_data(cur, field)
    insert_words(cur, field, words)
    conn.commit()
    conn.close()

    print(f"{field}: {len(words)}語を登録しました")
    for difficulty in sorted({d for _, d in words}):
        count = sum(1 for _, d in words if d == difficulty)
        print(f"  難度{difficulty}: {count}語")
    print("登録したCSVは手動で record に移してください。")


if __name__ == "__main__":
    main()