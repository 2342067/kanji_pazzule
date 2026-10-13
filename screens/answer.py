import html
import streamlit as st
from main.style import show_page_heading
from db.db import get_questions, get_question_words

RESULT_CSS = """
<style>
.result-table { border-collapse: collapse; width: 100%; max-width: 360px; margin: 4px 0 16px; font-size: 16px; }
.result-table th, .result-table td { border: 1px solid #ccc; padding: 4px 8px; text-align: center; }
.result-table th { background: #f4f4f4; font-size: 14px; }
.result-table .kanji { font-size: 22px; }
.result-table .ok { color: #1a7f37; font-weight: bold; }
.result-table .ng { color: #d33; font-weight: bold; }
</style>
"""


def get_correct_answers(question_id):
    """問題の空欄番号ごとの模範解答を {番号: 漢字} の形で、番号順に返す"""
    correct = {}
    for word, blank_position, blank_number in get_question_words(question_id):
        correct[blank_number] = word[blank_position]
    return dict(sorted(correct.items()))


def result_table_html(correct, answers):
    """番号ごとに、自分の答え・模範解答・正誤を並べた表をHTMLで作る"""
    rows = ""
    for number, kanji in correct.items():
        mine = answers.get(str(number), "")
        mark = '<span class="ok">○</span>' if mine == kanji else '<span class="ng">×</span>'
        mine_text = html.escape(mine) if mine else "－"
        rows += (
            f'<tr><td>{number}</td><td class="kanji">{mine_text}</td>'
            f'<td class="kanji">{kanji}</td><td>{mark}</td></tr>'
        )
    return (
        '<table class="result-table">'
        "<tr><th>番号</th><th>あなたの答え</th><th>模範解答</th><th>結果</th></tr>"
        f"{rows}</table>"
    )


def show():
    show_page_heading("解答画面")

    field = st.session_state.get("field")
    difficulty = st.session_state.get("difficulty")
    question_number = st.session_state.get("question")
    questions = get_questions(field, difficulty)

    if questions and question_number is not None and question_number <= len(questions):
        question_id = questions[question_number - 1][0]
        correct = get_correct_answers(question_id)
        answers = st.session_state.get("answers", {})
        st.markdown(RESULT_CSS + result_table_html(correct, answers), unsafe_allow_html=True)
    else:
        st.write("問題が見つかりません")

    if st.button("タイトルに戻る"):
        st.session_state.page = "title"
        st.rerun()
    if st.button("問題選択に戻る"):
        st.session_state.page = "question_select"
        st.rerun()
