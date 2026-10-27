"""
record フォルダにある問題ファイル（generate_questions.py で出力したCSV）を、DBに登録するスクリプト。

【フォルダ運用】
    record/     登録する問題のCSVを置く場所（登録後もそのまま残る）

実行すると:
    1. record フォルダ内のCSVをすべて読み込む
       教科はファイル名の先頭（rika_ / shakai_ / kyoyo_）で判断する
    2. 次の場合は、DBを変更せずに中止する
       - ファイル名の先頭が rika_ / shakai_ / kyoyo_ のどれでもない
       - ファイル名の教科と、CSV内の分野が違う行がある
       - 熟語が words テーブルのその教科に登録されていない
       - 熟語の難度が、問題の難度より高い
    3. 同じ問題が複数あった場合は1つだけ残す
    4. 登録する教科ごとに、既存の問題を削除してよいか確認する（y で実行）
       record にファイルがない教科の問題は変更しない
    5. 問題を questions と question_words に登録する

使い方:
    tools/puzzle_create フォルダで python register_questions.py
"""

import csv
import os
import sqlite3

FIELD_BY_CODE = {"rika": "理科", "shakai": "社会", "kyoyo": "教養"}

# ==== パス ====
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DB_PATH = os.path.join(PROJECT_DIR, "puzzle.db")
RECORD_DIR = os.path.join(SCRIPT_DIR, "record")


def collect_record_csv_paths(record_dir):
    """record フォルダ内のCSVファイル一覧を取得する"""
    if not os.path.isdir(record_dir):
        return []
    return sorted(
        os.path.join(record_dir, name)
        for name in os.listdir(record_dir)
        if name.lower().endswith(".csv")
    )


def field_from_filename(path):
    """ファイル名の先頭（rika_ / shakai_ / kyoyo_）から教科名を返す。判断できなければ None"""
    code = os.path.basename(path).split("_")[0]
    return FIELD_BY_CODE.get(code)


def parse_data(text):
    """データ列（熟語:位置-番号,位置-番号|...）を [(熟語, [(位置, 番号), ...]), ...] に変換する"""
    entries = []
    for part in text.split("|"):
        word, blanks_text = part.split(":")
        blanks = []
        for blank in blanks_text.split(","):
            if blank:
                position, number = blank.split("-")
                blanks.append((int(position), int(number)))
        entries.append((word, blanks))
    return entries


def load_questions(path):
    """問題ファイルを読み込み、[(分野, 難度, 語数, データ), ...] を返す（1行目は見出し）"""
    questions = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("データ"):
                continue
            questions.append((
                row["分野"],
                int(row["難度"]),
                int(row["語数"]),
                row["データ"],
            ))
    return questions


def main():
    paths = collect_record_csv_paths(RECORD_DIR)
    if not paths:
        print(f"{RECORD_DIR} に登録する問題のCSVがありません。")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    errors = []
    questions_by_field = {}   # 教科 -> [(難度, 語数, データ文字列), ...]（重複なし）
    duplicate_count = 0

    for path in paths:
        filename = os.path.basename(path)
        field = field_from_filename(path)
        if field is None:
            errors.append(f"{filename}: ファイル名から教科を判断できません（先頭は rika_ / shakai_ / kyoyo_）")
            continue

        cur.execute("SELECT word, difficulty FROM words WHERE field=?", (field,))
        word_difficulty = dict(cur.fetchall())

        loaded = load_questions(path)
        print(f"読み込み: {filename}（{field}、{len(loaded)}問）")

        bucket = questions_by_field.setdefault(field, [])
        for line_no, (row_field, difficulty, word_count, data) in enumerate(loaded, start=2):
            if row_field != field:
                errors.append(f"{filename} {line_no}行目: 分野が「{row_field}」で、ファイル名の教科（{field}）と違います")
                continue
            for word, _blanks in parse_data(data):
                if word not in word_difficulty:
                    errors.append(f"{filename} {line_no}行目: 「{word}」が{field}の語に登録されていません")
                elif word_difficulty[word] > difficulty:
                    errors.append(
                        f"{filename} {line_no}行目: 「{word}」の難度（{word_difficulty[word]}）が"
                        f"問題の難度（{difficulty}）より高くなっています"
                    )
            key = (difficulty, word_count, data)
            if key in bucket:
                duplicate_count += 1
                continue
            bucket.append(key)

    if errors:
        print("登録できない問題があります。")
        for message in errors:
            print(f"  {message}")
        print("中止しました。DBは変更していません。")
        conn.close()
        return

    if duplicate_count:
        print(f"同じ問題が{duplicate_count}問あったため、1つずつにまとめました。")

    # ---- 置き換えの確認 ----
    for field, questions in questions_by_field.items():
        cur.execute("SELECT COUNT(*) FROM questions WHERE field=?", (field,))
        existing = cur.fetchone()[0]
        print(f"{field}: 既存の問題{existing}問を削除して、{len(questions)}問を登録します。")
    answer = input("実行しますか？（y で実行）> ").strip()
    if answer != "y":
        print("中止しました。DBは変更していません。")
        conn.close()
        return

    # ---- 教科ごとに置き換えて登録 ----
    for field, questions in questions_by_field.items():
        cur.execute("SELECT word, id FROM words WHERE field=?", (field,))
        word_ids = dict(cur.fetchall())

        cur.execute("""
            DELETE FROM question_words
            WHERE question_id IN (SELECT id FROM questions WHERE field=?)
        """, (field,))
        cur.execute("DELETE FROM questions WHERE field=?", (field,))

        for difficulty, word_count, data in questions:
            cur.execute(
                "INSERT INTO questions (field, difficulty, word_count) VALUES (?, ?, ?)",
                (field, difficulty, word_count)
            )
            question_id = cur.lastrowid
            for word, blanks in parse_data(data):
                for position, number in blanks:
                    cur.execute(
                        "INSERT INTO question_words (question_id, word_id, blank_position, blank_number) VALUES (?, ?, ?, ?)",
                        (question_id, word_ids[word], position, number)
                    )

    conn.commit()
    conn.close()
    for field, questions in questions_by_field.items():
        print(f"{field}: {len(questions)}問を登録しました")


if __name__ == "__main__":
    main()