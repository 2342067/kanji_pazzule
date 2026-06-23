import streamlit as st
from db.db import get_questions, get_question_words

def show():
    st.title("問題画面")

    field = st.session_state.get("field")
    difficulty = st.session_state.get("difficulty")
    question_number = st.session_state.get("question")  # 1, 2, 3

    questions = get_questions(field, difficulty)

    if not questions or question_number is None or question_number > len(questions):
        st.write("問題が見つかりません")
        if st.button("戻る"):
            st.session_state.page = "question_select"
            st.rerun()
        return

    question_id = questions[question_number - 1][0]
    question_words = get_question_words(question_id)

    if "answers" not in st.session_state:
        st.session_state.answers = {}

    for i, (word, blank_position, blank_number) in enumerate(question_words):
        displayed = word[:blank_position] + "□" + word[blank_position + 1:]
        st.write(displayed)
        st.session_state.answers[i] = st.text_input(f"空欄{blank_number}", key=f"answer_{i}")

    if st.button("解答する"):
        unanswered = [i + 1 for i in range(len(question_words)) if not st.session_state.answers.get(i)]

        if unanswered:
            st.session_state.show_warning = True
            st.session_state.unanswered = unanswered
        else:
            st.session_state.show_warning = False
            st.session_state.page = "answer"
            st.rerun()

    if st.session_state.get("show_warning"):
        st.warning(f"未回答の問題があります：{', '.join(map(str, st.session_state.unanswered))}番")
        if st.button("このまま解答する"):
            st.session_state.show_warning = False
            st.session_state.page = "answer"
            st.rerun()

    if st.button("戻る"):
        st.session_state.page = "question_select"
        st.rerun()