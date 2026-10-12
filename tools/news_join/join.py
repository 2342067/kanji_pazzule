"""
形態素分析後のCSVファイルを結合するスクリプト。

【フォルダ運用】
    input/      結合対象のCSVを置く場所（処理後もそのまま残る）
    output/     join_2002.CSVが出力される場所

実行すると:
    1. inputフォルダ内のCSVを読み込み、全てのファイルの重複する単語の出現回数を合算する
    2. 名詞を頻度順に並び替えjoin_2002.CSVでoutputに出力する
このスクリプトは words テーブルへの登録は行わない。
実際の登録（DB INSERT）は、頻度分布を見て難易度のしきい値や除外する語を決めたあとの次のステップで行う。

使い方:
    python join.py
"""

import csv
import os
from collections import Counter

INPUT_DIR = "input"
OUTPUT_DIR = "output"
OUTPUT_FILENAME = "join_2002.csv"


def collect_input_csv_paths(input_dir):
    """input フォルダ内のCSVファイル一覧を取得する"""
    if not os.path.isdir(input_dir):
        return []
    return sorted(
        os.path.join(input_dir, name)
        for name in os.listdir(input_dir)
        if name.lower().endswith(".csv")
    )


def load_freq_csv(csv_path):
    """word, frequency の2列CSVを読み込み、Counterとして返す"""
    counter = Counter()
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            counter[row["word"]] += int(row["frequency"])
    return counter


def write_join_csv(counter, output_path):
    """結合結果（word, frequency）を頻度降順で書き出す"""
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "frequency"])
        for word, freq in counter.most_common():
            writer.writerow([word, freq])


def main():
    if not os.path.isdir(INPUT_DIR):
        print(f"エラー: {INPUT_DIR} フォルダが見つかりません。")
        return
    if not os.path.isdir(OUTPUT_DIR):
        print(f"エラー: {OUTPUT_DIR} フォルダが見つかりません。")
        return

    csv_paths = collect_input_csv_paths(INPUT_DIR)
    if not csv_paths:
        print(f"{INPUT_DIR} に結合対象のCSVファイルがありません。")
        print("freq_<ファイル名>.csv をそのフォルダに置いてから、もう一度実行してください。")
        return

    print(f"対象ファイル数: {len(csv_paths)} 件")

    combined = Counter()
    for path in csv_paths:
        counter = load_freq_csv(path)
        combined.update(counter)
        print(f"  → {path} を読み込みました（{len(counter)} 語）")

    print(f"\n結合後のユニーク単語数: {len(combined)}")

    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    write_join_csv(combined, output_path)
    print(f"{output_path} に出力しました。")


if __name__ == "__main__":
    main()