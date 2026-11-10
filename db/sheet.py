import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def is_enabled():
    """評価実験の回答を送れる設定（スプレッドシートのIDと鍵）があるかどうかを返す"""
    try:
        return "sheet_id" in st.secrets and "gcp_service_account" in st.secrets
    except Exception:
        return False


@st.cache_resource
def get_spreadsheet():
    """評価実験の回答を書き込むスプレッドシートを返す

    鍵とスプレッドシートのIDは Streamlit の secrets から読む
    （手元では .streamlit/secrets.toml、Streamlit Community Cloud では設定の Secrets 欄）。
    """
    credentials = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=SCOPES)
    return gspread.authorize(credentials).open_by_key(st.secrets["sheet_id"])


def append_row(sheet_name, header, values):
    """スプレッドシートの sheet_name という名前のシートの最後に1行追記する

    シートがなければ作る。1行目が列の名前（header）でなければ、1行目に列の名前の行を入れる。
    """
    spreadsheet = get_spreadsheet()
    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(header))
    if sheet.row_values(1) != header:
        sheet.insert_row(header, 1, value_input_option="RAW")
    sheet.append_row(values, value_input_option="RAW", table_range="A1")
