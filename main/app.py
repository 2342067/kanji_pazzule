import streamlit as st
import sys
import os

# 親フォルダ（kanji_puzzle）をパスに追加する
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main.style import apply_style, show_header
from screens import title, question_select, question, answer

apply_style()

if "page" not in st.session_state:
    st.session_state.page = "title"

if st.session_state.page == "title":
    # 遊び方画面は未作成。今はボタンを置くだけで、押しても何も起きない
    show_header(button_label="遊び方")
elif st.session_state.page != "question":
    show_header()

if st.session_state.page == "title":
    title.show()
elif st.session_state.page == "question_select":
    question_select.show()
elif st.session_state.page == "question":
    question.show()
elif st.session_state.page == "answer":
    answer.show()