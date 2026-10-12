"""
新聞記事CSVから本文を形態素解析し、教養分野の熟語候補を頻度付きで抽出するスクリプト。

【フォルダ運用】
    input/      解析対象のCSVを置く場所（処理後もそのまま残る）
    output/     freq_<同名>.CSVが出力される場所

実行すると:
    1. inputフォルダ内のCSVを読み込み、形態素解析して漢字のみの一般名詞・サ変接続名詞を抽出する
    2. 抽出した名詞を頻度順に並び替えfreq_<同名>.CSVでoutputに出力する
    3. inputフォルダ内全てのCSVに対して同手順を行う

このスクリプトは words テーブルへの登録は行わない。
実際の登録（DB INSERT）は、頻度分布を見て難易度のしきい値や
除外する語を決めたあとの次のステップで行う。
複数の解析後ファイルの加算統合は別プログラムで行う

使い方:
    python extract.py
"""

import csv
import os
import re
from collections import Counter

from janome.tokenizer import Tokenizer

# 漢字のみ・2文字以上で構成された語を対象とする
KANJI_ONLY = re.compile(r'^[\u4E00-\u9FFF]{2,}$')

# 本文テキストデータの列名（CSVのヘッダーに合わせる）
TEXT_COLUMN = "本文テキストデータ"

INPUT_DIR = "input"
OUTPUT_DIR = "output"


def extract_kanji_nouns(text, tokenizer):
    """本文テキストから、漢字のみで構成された一般名詞・サ変接続名詞を抽出する"""
    nouns = []
    for token in tokenizer.tokenize(text):
        pos = token.part_of_speech.split(",")
        # 名詞・一般 と 名詞・サ変接続 を対象（固有名詞・数・非自立などは除く）
        if pos[0] == "名詞" and pos[1] in ("一般", "サ変接続"):
            surface = token.surface
            if KANJI_ONLY.match(surface):
                nouns.append(surface)
    return nouns


def count_words_in_csv(csv_path, tokenizer):
    """1つのCSVファイルを読み込み、熟語の出現頻度をCounterとして返す"""
    counter = Counter()
    with open(csv_path, encoding="shift_jis", errors="replace") as f:
        reader = csv.DictReader(f)
        if TEXT_COLUMN not in reader.fieldnames:
            print(f"警告: {csv_path} に列 '{TEXT_COLUMN}' が見つかりません。スキップします。")
            return counter

        row_count = 0
        for row in reader:
            text = row.get(TEXT_COLUMN, "")
            if not text:
                continue
            row_count += 1
            for word in extract_kanji_nouns(text, tokenizer):
                counter[word] += 1

    print(f"  → {row_count} 行を処理しました（ユニーク熟語数: {len(counter)}）")
    return counter


def write_freq_csv(counter, output_path):
    """頻度付きCSV（word, frequency）を頻度降順で書き出す"""
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "frequency"])
        for word, freq in counter.most_common():
            writer.writerow([word, freq])


def collect_input_csv_paths(input_dir):
    """input フォルダ内のCSVファイル一覧を取得する"""
    if not os.path.isdir(input_dir):
        return []
    return sorted(
        os.path.join(input_dir, name)
        for name in os.listdir(input_dir)
        if name.lower().endswith(".csv")
    )


def main():
    if not os.path.isdir(INPUT_DIR):
        print(f"エラー: {INPUT_DIR} フォルダが見つかりません。")
        return
    if not os.path.isdir(OUTPUT_DIR):
        print(f"エラー: {OUTPUT_DIR} フォルダが見つかりません。")
        return

    csv_paths = collect_input_csv_paths(INPUT_DIR)
    if not csv_paths:
        print(f"{INPUT_DIR} に未処理のCSVファイルがありません。")
        print("新聞記事CSVをそのフォルダに置いてから、もう一度実行してください。")
        return

    print(f"対象ファイル数: {len(csv_paths)} 件")

    tokenizer = Tokenizer()

    for path in csv_paths:
        print(f"\n読み込み中: {path}")
        counter = count_words_in_csv(path, tokenizer)

        filename = os.path.basename(path)
        freq_path = os.path.join(OUTPUT_DIR, f"freq_{filename}")
        write_freq_csv(counter, freq_path)
        print(f"  → {freq_path} に出力しました")

    print("\n完了しました。複数ファイルの頻度を合算するには別プログラムを使ってください。")


if __name__ == "__main__":
    main()