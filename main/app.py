import streamlit as st
import sys
import os

# 親フォルダ（kanji_puzzle）をパスに追加する
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main.style import apply_style
from screens import title, question_select, question, answer

apply_style()

if "page" not in st.session_state:
    st.session_state.page = "title"

if st.session_state.page == "title":
    title.show()
elif st.session_state.page == "question_select":
    question_select.show()
elif st.session_state.page == "question":
    question.show()
elif st.session_state.page == "answer":
    answer.show()