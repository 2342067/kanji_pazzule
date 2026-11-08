"""
words テーブルに登録された熟語から、指定した条件の問題を生成し、CSVに出力するスクリプト。

【フォルダ運用】
    output/     生成した問題のCSVが出力される場所
    record/     良い問題のCSVを手動で置いておく場所（このスクリプトは触らない）

実行すると:
    1. 教科、難度、語数、問題数を順に聞く
       難度は 1：やさしい、2：普通、3：難しい、4：全て
       語数は 1：9語、2：15語、3：21語、4：全て
       問題数は1条件（難度×語数）あたりの数
    2. 選んだ条件ごとに、以下を行う（全てを選んだ場合は、その分の条件をすべて順に行う）
       a. puzzle.db（プロジェクト直下）の words テーブルから、その教科で難度が指定以下の語を読み込む（累積）
       b. 指定の問題数に届くまで問題を生成する（1問の作り方は logic.py の generate_puzzle）
          教科が NO_SHARED_PAIR_FIELDS に入っている場合は、同じ2文字の並びを持つ熟語を同じ問題に入れない
          次のどれかに当てはまる問題は捨てて作り直す
            - 指定の語数に届かなかった
            - 見える文字のマスが、全部の文字のマスの MIN_VISIBLE_RATIO 未満
            - 教科が LEVEL_RATIO_FIELDS に入っていて難度が2以上のとき、
              その難度の熟語が語数の LEVEL_RATIO（切り上げ）未満
          試行回数の上限は条件ごとに数える
       c. 生成した問題ごとに、空欄の番号をランダムに入れ替え、熟語を並べ替える
          熟語は文字数の少ない順に並べ、同じ文字数の中はランダムにする
       d. 生成した問題を output フォルダにCSVで出力する（1行=1問、1条件=1ファイル）
          ファイル名：教科_d難度_w語数_n作れた問題数_日時.csv（例：kyoyo_d2_w15_n10_20261027_1035.csv）
    3. 試行回数が上限に達して、指定の問題数に届かなかった場合
       難度と語数をどちらも1つに決めた場合：作れた分だけで出力する
       難度か語数のどちらかに「全て」を選んだ場合：その条件は出力せず、残りの条件を続ける
       出力しなかった条件は、最後にまとめて表示する

このスクリプトはDBへの登録は行わない。

使い方:
    tools/puzzle_generate フォルダで python generate.py
"""

import csv
import math
import os
import random
import sqlite3
from datetime import datetime

from logic import generate_puzzle

FIELDS = {"1": "理科", "2": "社会", "3": "教養"}
FIELD_CODES = {"理科": "rika", "社会": "shakai", "教養": "kyoyo"}
DIFFICULTY_CHOICES = {"1": [1], "2": [2], "3": [3], "4": [1, 2, 3]}
WORD_COUNT_CHOICES = {"1": [9], "2": [15], "3": [21], "4": [9, 15, 21]}
ALL_CHOICE = "4"

# ==== パラメータ ====
MAX_TOTAL_ATTEMPTS = 10000          # 1条件あたりの試行回数の上限
NO_SHARED_PAIR_FIELDS = {"教養"}    # 同じ2文字の並びを持つ熟語を同じ問題に入れない教科
MIN_VISIBLE_RATIO = 0.3             # 見える文字のマスの割合の下限
LEVEL_RATIO_FIELDS = {"教養"}       # 指定難度の熟語の割合を保証する教科
LEVEL_RATIO = 0.3                   # 難度2以上の問題で、指定難度の熟語が占める割合の下限

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
    """words テーブルから、指定教科で難度が指定以下の語を読み込み、{熟語: 難度} を返す"""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cur = conn.cursor()
    cur.execute(
        "SELECT word, difficulty FROM words WHERE field=? AND difficulty<=?",
        (field, difficulty)
    )
    words = {word: word_difficulty for word, word_difficulty in cur.fetchall()}
    conn.close()
    return words


def visible_ratio(puzzle_words):
    """見える文字のマスが、全部の文字のマスに占める割合を返す"""
    total = sum(len(entry["word"]) for entry in puzzle_words)
    blanks = sum(len(entry["blanks"]) for entry in puzzle_words)
    return (total - blanks) / total


def meets_level_ratio(puzzle_words, words, field, difficulty, word_count):
    """指定難度の熟語の割合の下限を満たすか（対象外の教科・難度1なら常に満たす）"""
    if field not in LEVEL_RATIO_FIELDS or difficulty < 2:
        return True
    required = math.ceil(word_count * LEVEL_RATIO)
    return sum(1 for entry in puzzle_words if words[entry["word"]] == difficulty) >= required


def shuffle_question(puzzle_words):
    """
    1問分について、空欄の番号をランダムに入れ替え、熟語を並べ替えたものを返す。
    番号：1〜空欄の数をランダムに並べ替えて割り当て直す
    並び：文字数の少ない順に並べ、同じ文字数の中はランダムにする
    """
    numbers = sorted({number for entry in puzzle_words for _kanji, number in entry["blanks"].values()})
    shuffled = numbers[:]
    random.shuffle(shuffled)
    new_number = dict(zip(numbers, shuffled))

    renumbered = []
    for entry in puzzle_words:
        blanks = {
            position: (kanji, new_number[number])
            for position, (kanji, number) in entry["blanks"].items()
        }
        renumbered.append({"word": entry["word"], "blanks": blanks})

    random.shuffle(renumbered)
    renumbered.sort(key=lambda entry: len(entry["word"]))   # 並べ替え前の順（ランダム）を保ったまま文字数順にする
    return renumbered


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


def generate_condition(words, field, difficulty, word_count, target):
    """
    1条件（教科・難度・語数）分の問題を、指定の問題数に届くまで生成する。
    words は {熟語: 難度}。
    指定の語数に届かなかった問題、見える文字の割合や指定難度の熟語の割合が下限に届かない問題は捨てて作り直し、
    試行回数が上限に達したら作れた分だけで終える。
    戻り値: (rows, attempts)
        rows: CSVに書く行のリスト（1行=1問）
        attempts: 試行回数
    """
    word_list = list(words)
    no_shared_pair = field in NO_SHARED_PAIR_FIELDS
    rows = []
    attempts = 0
    while len(rows) < target and attempts < MAX_TOTAL_ATTEMPTS:
        attempts += 1
        puzzle_words, stats = generate_puzzle(word_list, word_count, no_shared_pair=no_shared_pair)
        if not stats["reached"]:
            continue
        if visible_ratio(puzzle_words) < MIN_VISIBLE_RATIO:
            continue
        if not meets_level_ratio(puzzle_words, words, field, difficulty, word_count):
            continue
        shown, answer_text, data = format_question(shuffle_question(puzzle_words))
        rows.append([len(rows) + 1, field, difficulty, word_count, shown, answer_text, data])
    return rows, attempts


def write_condition(rows, field, difficulty, word_count):
    """1条件分の問題を output フォルダにCSVで出力し、出力先のパスを返す"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = (
        f"{FIELD_CODES[field]}_d{difficulty}_w{word_count}_n{len(rows)}_"
        f"{datetime.now():%Y%m%d_%H%M}.csv"
    )
    output_path = os.path.join(OUTPUT_DIR, filename)
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(rows)
    return output_path


def main():
    field = FIELDS[ask_choice("教科を選んでください（1：理科、2：社会、3：教養）", list(FIELDS.keys()))]
    difficulty_key = ask_choice(
        "難度を選んでください（1：やさしい、2：普通、3：難しい、4：全て）", list(DIFFICULTY_CHOICES.keys())
    )
    word_count_key = ask_choice(
        "語数を選んでください（1：9語、2：15語、3：21語、4：全て）", list(WORD_COUNT_CHOICES.keys())
    )
    target = ask_positive_int("1条件あたりの問題数を入力してください")

    is_all = ALL_CHOICE in (difficulty_key, word_count_key)
    skipped = []   # 出力しなかった条件：(難度, 語数, 作れた問題数)

    for difficulty in DIFFICULTY_CHOICES[difficulty_key]:
        words = load_words(field, difficulty)
        if not words:
            print(f"{field}の難度{difficulty}以下の語が登録されていません。先に register_words.py で語を登録してください。")
            if not is_all:
                return
            for word_count in WORD_COUNT_CHOICES[word_count_key]:
                skipped.append((difficulty, word_count, 0))
            continue
        print(f"{field}・難度{difficulty}以下：{len(words)}語を使用")

        for word_count in WORD_COUNT_CHOICES[word_count_key]:
            rows, attempts = generate_condition(words, field, difficulty, word_count, target)
            created = len(rows)

            if is_all:
                if created < target:
                    print(f"  難度{difficulty}・語数{word_count}：{target}問のうち{created}問しか作れなかったため、出力しません"
                          f"（試行回数の上限 {MAX_TOTAL_ATTEMPTS}回に達しました）。")
                    skipped.append((difficulty, word_count, created))
                    continue
                output_path = write_condition(rows, field, difficulty, word_count)
                print(f"  難度{difficulty}・語数{word_count}：{created}問を出力しました（試行回数 {attempts}回）: {output_path}")
            else:
                if created < target:
                    print(f"指定の{target}問のうち、{created}問しか作れませんでした（試行回数の上限 {MAX_TOTAL_ATTEMPTS}回に達しました）。")
                if created == 0:
                    print("出力するファイルはありません。")
                    return
                output_path = write_condition(rows, field, difficulty, word_count)
                print(f"{created}問を出力しました（試行回数 {attempts}回）: {output_path}")

    if is_all and skipped:
        print("出力しなかった条件:")
        for difficulty, word_count, created in skipped:
            print(f"  難度{difficulty}・語数{word_count}（作れた問題数 {created}問）")


if __name__ == "__main__":
    main()
