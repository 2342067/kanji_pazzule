"""
words テーブルに登録された熟語から、指定した条件の問題を生成し、CSVに出力するスクリプト。

【フォルダ運用】
    output/     生成した問題のCSVが出力される場所
    record/     良い問題のCSVを手動で置いておく場所（このスクリプトは触らない）

実行すると:
    1. 教科（1〜3）、難度（1〜3）、語数（9・15・21）、問題数を順に聞く
    2. puzzle.db（プロジェクト直下）の words テーブルから、その教科で難度が指定以下の語を読み込む（累積）
    3. 指定の問題数に届くまで問題を生成する
       指定の語数に届かなかった問題は捨てて作り直す
       試行回数が上限に達した場合は、作れた分だけで終える
    4. 生成した問題を output フォルダにCSVで出力する（1行=1問）
       ファイル名：教科_d難度_w語数_n作れた問題数_日時.csv（例：kyoyo_d2_w15_n10_20261027_1035.csv）

このスクリプトはDBへの登録は行わない。

使い方:
    tools/puzzle_create フォルダで python generate_questions.py
"""

import csv
import os
import sqlite3
from datetime import datetime

from puzzle_logic import generate_puzzle

FIELDS = {"1": "理科", "2": "社会", "3": "教養"}
FIELD_CODES = {"理科": "rika", "社会": "shakai", "教養": "kyoyo"}
DIFFICULTIES = [1, 2, 3]
WORD_COUNTS = [9, 15, 21]

# ==== パラメータ ====
MAX_TOTAL_ATTEMPTS = 10000   # 全体の試行回数の上限

# ==== パス ====
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DB_PATH = os.path.join(PROJECT_DIR, "puzzle.db")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")

HEADER = ["番号", "分野", "難度", "語数", "問題", "答え", "データ"]


def ask_choice(message, choices):
    """choices のどれかが入力されるまで聞き、入力された文字列を返す"""
    while True:
        print(message)
        value = input("> ").strip()
        if value in choices:
            return value
        print(f"{'、'.join(choices)}のいずれかを入力してください。")


def ask_positive_int(message):
    """1以上の整数が入力されるまで聞き、その値を返す"""
    while True:
        print(message)
        value = input("> ").strip()
        if value.isdigit() and int(value) >= 1:
            return int(value)
        print("1以上の整数を入力してください。")


def load_words(field, difficulty):
    """words テーブルから、指定教科で難度が指定以下の語を読み込む"""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cur = conn.cursor()
    cur.execute(
        "SELECT word FROM words WHERE field=? AND difficulty<=?",
        (field, difficulty)
    )
    words = [row[0] for row in cur.fetchall()]
    conn.close()
    return words


def format_question(puzzle_words):
    """
    1問分を、確認用の表示と登録用のデータに変換する。
    戻り値: (問題, 答え, データ)
        問題: 空欄を[番号]にした熟語をスペース区切りで並べたもの（例：[1]池 [1][2] 天[2]）
        答え: 番号ごとの漢字（例：1=電 2=気）
        データ: 熟語:位置-番号,位置-番号|熟語:... の形式（例：電池:0-1|電気:0-1,1-2）
    """
    shown = []
    answers = {}
    data = []
    for entry in puzzle_words:
        word = entry["word"]
        blanks = entry["blanks"]
        shown.append("".join(
            f"[{blanks[i][1]}]" if i in blanks else ch
            for i, ch in enumerate(word)
        ))
        for kanji, number in blanks.values():
            answers[number] = kanji
        data.append(word + ":" + ",".join(
            f"{position}-{number}" for position, (kanji, number) in sorted(blanks.items())
        ))
    answer_text = " ".join(f"{n}={answers[n]}" for n in sorted(answers))
    return " ".join(shown), answer_text, "|".join(data)


def main():
    field = FIELDS[ask_choice("教科を選んでください（1：理科、2：社会、3：教養）", list(FIELDS.keys()))]
    difficulty = int(ask_choice("難度を選んでください（1、2、3）", [str(d) for d in DIFFICULTIES]))
    word_count = int(ask_choice("語数を入力してください（9、15、21）", [str(n) for n in WORD_COUNTS]))
    target = ask_positive_int("生成する問題数を入力してください")

    words = load_words(field, difficulty)
    if not words:
        print(f"{field}の難度{difficulty}以下の語が登録されていません。先に register_words.py で語を登録してください。")
        return
    print(f"{field}・難度{difficulty}以下：{len(words)}語を使用")

    rows = []
    attempts = 0
    while len(rows) < target and attempts < MAX_TOTAL_ATTEMPTS:
        attempts += 1
        puzzle_words, stats = generate_puzzle(words, word_count)
        if not stats["reached"]:
            continue
        shown, answer_text, data = format_question(puzzle_words)
        rows.append([len(rows) + 1, field, difficulty, word_count, shown, answer_text, data])

    created = len(rows)
    if created < target:
        print(f"指定の{target}問のうち、{created}問しか作れませんでした（試行回数の上限 {MAX_TOTAL_ATTEMPTS}回に達しました）。")
    if created == 0:
        print("出力するファイルはありません。")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = (
        f"{FIELD_CODES[field]}_d{difficulty}_w{word_count}_n{created}_"
        f"{datetime.now():%Y%m%d_%H%M}.csv"
    )
    output_path = os.path.join(OUTPUT_DIR, filename)
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(rows)
    print(f"{created}問を出力しました（試行回数 {attempts}回）: {output_path}")


if __name__ == "__main__":
    main()