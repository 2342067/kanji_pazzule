"""
output フォルダにある問題ファイル（generate.py で出力したCSV）について、
同じファイル内の問題どうしの類似度を求め、check フォルダにExcelファイルで出力するスクリプト。

【フォルダ運用】
    output/     類似度を調べる問題のCSVを置く場所（generate.py の出力先）
    check/      類似度のExcelファイルが出力される場所

類似度:
    2問に共通する熟語の数 ÷ 語数（同じファイル内の問題は語数が同じ）
    例：15語の問題どうしで3語が共通なら 20%
    表示は整数の%（四捨五入）
    ファイルをまたいだ比較はしない

実行すると:
    1. 色を付ける類似度（0〜100の整数、%）を聞く。空のままEnterなら色を付けない
    2. output フォルダ内のCSVをすべて読み込む
       ファイルは、ファイル名の中の数字を数として比べた順に並べる（w9、w15、w21 の順になる）
    3. ファイルごとに、すべての2問の組み合わせについて類似度を求める
    4. check フォルダに、類似度の表をExcelファイルで出力する（シートは1枚）
       ファイル名：similarity_日時.xlsx（例：similarity_20261108_1045.xlsx）
       ファイルごとに、ファイル名の行、平均空欄率の行、平均難度の行、問題番号の行、空欄率の行、難度の行、
       類似度の行を縦に並べ、ファイルの間に空行を1行入れる
       空欄率：空欄のマス ÷ 全部の文字のマス（整数の%、四捨五入）
       難度：その問題の難度と同じ難度の熟語の数 ÷ 語数（整数の%、四捨五入）
             熟語の難度は puzzle.db（プロジェクト直下）の words テーブルから、その問題の教科で探す
             ファイル内に puzzle.db で見つからない熟語が1つでもあれば、そのファイルの難度はすべて「?」にし、
             見つからなかった熟語を画面に表示する
       平均空欄率・平均難度：ファイル内の各問題の空欄率・難度の平均（1問ずつ同じ重みで平均する）
       各列は1つの問題で、その下に他の問題を「番号：類似度」の形で、類似度の高い順に並べる
       類似度が同じ場合は番号の小さい順
       類似度が0%の相手は書かない（その列はそこから下が空欄になる）
       一番上の類似度の行が、各問題の最大の類似度になる
       表示した類似度（整数の%）が指定の値以上のマスは、薄い赤で塗る
    5. ファイルごとに、すべての2問の組み合わせの類似度の平均と、最大の組を画面に表示する

使い方:
    tools/puzzle_generate フォルダで python similarity.py
    openpyxl が必要（入っていなければ py -m pip install openpyxl）
"""

import csv
import os
import re
import sqlite3
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import PatternFill

# ==== パス ====
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DB_PATH = os.path.join(PROJECT_DIR, "puzzle.db")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
CHECK_DIR = os.path.join(SCRIPT_DIR, "check")

# ==== 表示 ====
HIGHLIGHT_FILL = PatternFill(fill_type="solid", start_color="FFC7CE", end_color="FFC7CE")   # 薄い赤


def ask_threshold():
    """色を付ける類似度（0〜100の整数）を聞く。空のままEnterなら None を返す"""
    while True:
        print("色を付ける類似度（%）を入力してください（0〜100の整数。空のままEnterで色を付けない）")
        value = input("> ").strip()
        if value == "":
            return None
        if value.isdigit() and 0 <= int(value) <= 100:
            return int(value)
        print("0〜100の整数を入力するか、空のままEnterを押してください。")


def natural_key(name):
    """ファイル名の中の数字を数として比べるための並べ替えキー（例：w9 が w15 より先になる）"""
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name)]


def collect_csv_paths(folder):
    """フォルダ内のCSVファイルのパスを、ファイル名の中の数字を数として比べた順に返す"""
    names = sorted(
        (name for name in os.listdir(folder) if name.lower().endswith(".csv")),
        key=natural_key
    )
    return [os.path.join(folder, name) for name in names]


def load_word_difficulties():
    """puzzle.db の words テーブルから、{(教科, 熟語): 難度} を返す。DBがなければ空の辞書を返す"""
    if not os.path.exists(DB_PATH):
        print(f"注意: {DB_PATH} が見つからないため、難度は「?」になります。")
        return {}
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cur = conn.cursor()
    cur.execute("SELECT field, word, difficulty FROM words")
    difficulties = {(field, word): difficulty for field, word, difficulty in cur.fetchall()}
    conn.close()
    return difficulties


def load_questions(path):
    """
    問題ファイルを読み込み、[(番号, 語数, 熟語の集合), ...] と、問題ごとの情報 {番号: 情報} を返す。
    熟語と空欄の数は「データ」列（熟語:位置-番号,...|熟語:...）から取り出す。
    情報: {"field": 教科, "difficulty": 難度, "words": [熟語, ...], "chars": 文字のマス数, "blanks": 空欄のマス数}
    """
    questions = []
    infos = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            number = int(row["番号"])
            word_list = []
            blanks = 0
            for item in row["データ"].split("|"):
                word, positions = item.split(":")
                word_list.append(word)
                blanks += len([p for p in positions.split(",") if p])
            questions.append((number, int(row["語数"]), set(word_list)))
            infos[number] = {
                "field": row["分野"], "difficulty": int(row["難度"]), "words": word_list,
                "chars": sum(len(word) for word in word_list), "blanks": blanks,
            }
    return questions, infos


def blank_rate(info):
    """空欄率（空欄のマス ÷ 全部の文字のマス）を返す"""
    return info["blanks"] / info["chars"]


def level_rate(info, difficulties):
    """難度の割合（問題の難度と同じ難度の熟語の数 ÷ 語数）を返す"""
    same = sum(1 for word in info["words"] if difficulties[(info["field"], word)] == info["difficulty"])
    return same / len(info["words"])


def missing_words(infos, difficulties):
    """puzzle.db で見つからない熟語を、出てきた順に重複なく返す"""
    missing = []
    for info in infos.values():
        for word in info["words"]:
            if (info["field"], word) not in difficulties and word not in missing:
                missing.append(word)
    return missing


def calc_similarity(words_a, words_b, word_count):
    """2問の類似度（共通する熟語の数 ÷ 語数）を返す"""
    return len(words_a & words_b) / word_count


def to_percent(value):
    """割合（類似度・空欄率・難度）を整数の%にする（四捨五入、例：0.2 -> 20）"""
    return round(value * 100)


def build_table(questions):
    """
    1ファイル分の類似度を求める。
    戻り値:
        columns: {番号: [(相手の番号, 類似度), ...]}（類似度の高い順、同じなら番号の小さい順）
        pairs: [(番号A, 番号B, 類似度), ...]（すべての2問の組み合わせ）
    """
    columns = {number: [] for number, _count, _words in questions}
    pairs = []
    for i, (number_a, count_a, words_a) in enumerate(questions):
        for number_b, _count_b, words_b in questions[i + 1:]:
            value = calc_similarity(words_a, words_b, count_a)
            columns[number_a].append((number_b, value))
            columns[number_b].append((number_a, value))
            pairs.append((number_a, number_b, value))
    for number in columns:
        columns[number].sort(key=lambda item: (-item[1], item[0]))
    return columns, pairs


def write_table(sheet, start_row, filename, columns, infos, difficulties, show_level, threshold):
    """
    1ファイル分の表をシートの start_row 行目から書き込み、次に書ける行番号を返す。
    ファイル名の行の下に平均空欄率と平均難度の行、問題番号の行の下に空欄率と難度の行を入れる
    （show_level が False なら難度と平均難度は「?」）。
    類似度が0%の相手は書かない。threshold 以上のマスは薄い赤で塗る（threshold が None なら塗らない）。
    """
    numbers = sorted(columns)
    blank_rates = {number: blank_rate(infos[number]) for number in numbers}
    level_rates = {number: level_rate(infos[number], difficulties) for number in numbers} if show_level else {}

    average_blank = f"{to_percent(sum(blank_rates.values()) / len(numbers))}%"
    average_level = f"{to_percent(sum(level_rates.values()) / len(numbers))}%" if show_level else "?"
    sheet.cell(row=start_row, column=1, value=filename)
    sheet.cell(row=start_row + 1, column=1, value=f"平均空欄率 {average_blank}")
    sheet.cell(row=start_row + 2, column=1, value=f"平均難度 {average_level}")

    for col, number in enumerate(numbers, start=1):
        level = f"{to_percent(level_rates[number])}%" if show_level else "?"
        sheet.cell(row=start_row + 3, column=col, value=f"{number}番")
        sheet.cell(row=start_row + 4, column=col, value=f"空欄率 {to_percent(blank_rates[number])}%")
        sheet.cell(row=start_row + 5, column=col, value=f"難度 {level}")

    row = start_row + 6
    for rank in range(max((len(items) for items in columns.values()), default=0)):
        written = False
        for col, number in enumerate(numbers, start=1):
            if rank >= len(columns[number]):
                continue
            other, value = columns[number][rank]
            percent = to_percent(value)
            if percent == 0:
                continue
            cell = sheet.cell(row=row, column=col, value=f"{other}：{percent}%")
            if threshold is not None and percent >= threshold:
                cell.fill = HIGHLIGHT_FILL
            written = True
        if not written:
            break   # この順位で0%でない相手が1つもなければ、下の順位もすべて0%
        row += 1
    return row


def main():
    if not os.path.isdir(OUTPUT_DIR):
        print(f"エラー: {OUTPUT_DIR} フォルダが見つかりません。")
        return
    if not os.path.isdir(CHECK_DIR):
        print(f"エラー: {CHECK_DIR} フォルダが見つかりません。")
        return

    paths = collect_csv_paths(OUTPUT_DIR)
    if not paths:
        print("output フォルダに問題のCSVがありません。")
        return

    threshold = ask_threshold()
    difficulties = load_word_difficulties()

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "類似度"
    next_row = 1
    written_any = False

    for path in paths:
        filename = os.path.basename(path)
        questions, infos = load_questions(path)
        if len(questions) < 2:
            print(f"{filename}：問題が{len(questions)}問しかないため、類似度は求めません。")
            continue

        missing = missing_words(infos, difficulties)
        if missing and difficulties:
            print(f"{filename}：puzzle.db で見つからない熟語があるため、難度は「?」にします（{'、'.join(missing)}）")

        columns, pairs = build_table(questions)
        if written_any:
            next_row += 1   # ファイルの区切りに空行を入れる
        next_row = write_table(sheet, next_row, filename, columns, infos, difficulties, not missing, threshold)
        written_any = True

        average = sum(value for _a, _b, value in pairs) / len(pairs)
        maximum = max(value for _a, _b, value in pairs)
        max_pairs = "、".join(f"{a}番と{b}番" for a, b, value in pairs if value == maximum)
        print(f"{filename}：平均 {to_percent(average)}%、最大 {to_percent(maximum)}%（{max_pairs}）")

    if not written_any:
        print("出力するファイルはありません。")
        return

    output_path = os.path.join(CHECK_DIR, f"similarity_{datetime.now():%Y%m%d_%H%M}.xlsx")
    workbook.save(output_path)
    print(f"類似度を出力しました: {output_path}")


if __name__ == "__main__":
    main()
