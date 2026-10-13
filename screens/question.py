import streamlit as st
from db.db import get_questions, get_question_words
from screens.puzzle_component import puzzle
from screens.title import APP_TITLE
from main.style import GLOBAL_CSS

# 全画面共通のCSSに加えて、部品同士の間隔を詰める（問題画面のみ）
PAGE_CSS = f"""
<style>
{GLOBAL_CSS}
[data-testid="stVerticalBlock"] {{ gap: 0.25rem; }}
</style>
"""


def build_words(question_words):
    """DBの (word, blank_position, blank_number) の行を、画面表示用の形に変換する

    同じ熟語に空欄が複数ある場合は、同じ熟語の行が複数あるものとしてまとめる。
    空欄の位置は {"n": 空欄番号}、それ以外の文字は {"c": 漢字} にする。
    熟語は文字数の少ない順に並べる。
    """
    blanks = {}
    order = []
    for word, blank_position, blank_number in question_words:
        if word not in blanks:
            blanks[word] = {}
            order.append(word)
        blanks[word][blank_position] = blank_number

    words = []
    for word in order:
        chars = []
        for i, c in enumerate(word):
            if i in blanks[word]:
                chars.append({"n": blanks[word][i]})
            else:
                chars.append({"c": c})
        words.append(chars)

    return sorted(words, key=len)


def show():
    st.markdown(PAGE_CSS, unsafe_allow_html=True)

    field = st.session_state.get("field")
    difficulty = st.session_state.get("difficulty")
    question_number = st.session_state.get("question")  # 1, 2, 3, 4

    questions = get_questions(field, difficulty)

    if not questions or question_number is None or question_number > len(questions):
        st.write("問題が見つかりません")
        if st.button("戻る"):
            st.session_state.page = "question_select"
            st.rerun()
        return

    question_id = questions[question_number - 1][0]
    words = build_words(get_question_words(question_id))

    result = puzzle(key=f"puzzle_{question_id}", data={"title": APP_TITLE, "words": words}, on_submit_change=lambda: None, on_back_change=lambda: None)

    if result.submit is not None:
        st.session_state.answers = result.submit["answers"]
        st.session_state.page = "answer"
        st.rerun()

    if result.back:
        st.session_state.page = "question_select"
        st.rerun()
