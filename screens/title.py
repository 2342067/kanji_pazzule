import streamlit as st

APP_TITLE = "漢字抜け熟語パズル"

FIELDS = ["理科", "社会", "教養"]
DIFFICULTIES = {1: "やさしい", 2: "ふつう", 3: "難しい"}
WORD_COUNTS = {9: "小", 15: "中", 21: "大"}


def show():

    field = st.segmented_control(
        "分野",
        FIELDS,
        default=st.session_state.get("field"),
        key="field_input",
    )

    difficulty = st.segmented_control(
        "熟語難度",
        list(DIFFICULTIES.keys()),
        format_func=lambda d: DIFFICULTIES[d],
        default=st.session_state.get("difficulty"),
        key="difficulty_input",
    )

    word_count = st.segmented_control(
        "問題の大きさ",
        list(WORD_COUNTS.keys()),
        format_func=lambda n: WORD_COUNTS[n],
        default=st.session_state.get("word_count"),
        key="word_count_input",
    )

    all_selected = field is not None and difficulty is not None and word_count is not None

    if st.button("次へ", disabled=not all_selected):
        st.session_state.field = field
        st.session_state.difficulty = difficulty
        st.session_state.word_count = word_count
        st.session_state.page = "question_select"
        st.rerun()