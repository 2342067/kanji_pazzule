"""
評価実験の回答をGoogleスプレッドシートに書き込むための設定ファイルを作り、接続を確かめるスクリプト。

実行すると:
    1. サービスアカウントの鍵（JSONファイル）の場所を聞く
    2. スプレッドシートのURL（またはID）を聞く
    3. プロジェクト直下の .streamlit/secrets.toml に、鍵とスプレッドシートのIDを書き込む
       （このファイルは .gitignore に入っていて、GitHubには上がらない）
    4. スプレッドシートの1枚目のシートに「接続テスト」の行を1行追記して、書き込めることを確かめる
       書き込んだ範囲と、シートの今の中身を画面に表示する
    secrets.toml がすでにある場合は、1〜3を飛ばして4だけ行う

Streamlit Community Cloud で動かすときは、作られた secrets.toml の中身を
アプリの設定の「Secrets」欄にそのまま貼り付ける。

使い方:
    tools/survey_setup フォルダで python make_secrets.py
    gspread と google-auth が必要（入っていなければ py -m pip install gspread google-auth）
"""

import json
import os
import re
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# ==== パス ====
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SECRETS_DIR = os.path.join(PROJECT_DIR, ".streamlit")
SECRETS_PATH = os.path.join(SECRETS_DIR, "secrets.toml")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def ask_key_path():
    """鍵（JSONファイル）の場所を聞き、読み込んだ中身を返す"""
    while True:
        print("サービスアカウントの鍵（JSONファイル）の場所を入力してください（ファイルをこの画面にドラッグしても入力できます）")
        path = input("> ").strip().strip('"')
        if not os.path.isfile(path):
            print("ファイルが見つかりません。")
            continue
        with open(path, encoding="utf-8") as f:
            key = json.load(f)
        if key.get("type") != "service_account":
            print("サービスアカウントの鍵ではないようです。")
            continue
        return key


def ask_sheet_id():
    """スプレッドシートのURLまたはIDを聞き、IDを返す"""
    while True:
        print("スプレッドシートのURL（またはID）を入力してください")
        value = input("> ").strip()
        match = re.search(r"/d/([A-Za-z0-9_-]+)", value)
        if match:
            return match.group(1)
        if re.fullmatch(r"[A-Za-z0-9_-]{20,}", value):
            return value
        print("URLまたはIDとして読み取れませんでした。")


def write_secrets(key, sheet_id):
    """secrets.toml に、スプレッドシートのIDと鍵を書き込む"""
    os.makedirs(SECRETS_DIR, exist_ok=True)
    lines = [f"sheet_id = {json.dumps(sheet_id)}", "", "[gcp_service_account]"]
    for name, value in key.items():
        lines.append(f"{name} = {json.dumps(value)}")
    with open(SECRETS_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def read_secrets():
    """このスクリプトが作った secrets.toml を読み、(鍵, スプレッドシートのID) を返す"""
    key = {}
    sheet_id = None
    with open(SECRETS_PATH, encoding="utf-8") as f:
        for line in f:
            match = re.match(r"(\w+) = (.*)$", line.strip())
            if not match:
                continue
            if match.group(1) == "sheet_id":
                sheet_id = json.loads(match.group(2))
            else:
                key[match.group(1)] = json.loads(match.group(2))
    return key, sheet_id


def main():
    # 設定ファイルがすでにあれば、作り直さずに接続の確認だけ行う（作り直すときは secrets.toml を消してから実行する）
    if os.path.isfile(SECRETS_PATH):
        print(f"設定ファイルがすでにあるので、接続の確認だけ行います: {SECRETS_PATH}")
        key, sheet_id = read_secrets()
    else:
        key = ask_key_path()
        sheet_id = ask_sheet_id()
        write_secrets(key, sheet_id)
        print(f"設定ファイルを作りました: {SECRETS_PATH}")

    credentials = Credentials.from_service_account_info(key, scopes=SCOPES)
    sheet = gspread.authorize(credentials).open_by_key(sheet_id).sheet1
    row = [f"{datetime.now():%Y-%m-%d %H:%M:%S}", "接続テスト"]
    print(f"書き込む内容: {row}")
    result = sheet.append_row(row, value_input_option="RAW", table_range="A1")
    print(f"書き込んだ範囲: {result.get('updates', {}).get('updatedRange')}")
    print(f"シート「{sheet.title}」の今の中身: {sheet.get_all_values()}")


if __name__ == "__main__":
    main()
