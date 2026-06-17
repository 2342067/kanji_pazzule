import streamlit as st

def show():
    st.title("難易度選択画面")

    if st.button("やさしい"):
        st.session_state.difficulty = 1
        st.session_state.page = "question_select"
        st.rerun()

    if st.button("ふつう"):
        st.session_state.difficulty = 2
        st.session_state.page = "question_select"
        st.rerun()

    if st.button("難しい"):
        st.session_state.difficulty = 3
        st.session_state.page = "question_select"
        st.rerun()

    if st.button("戻る"):
        st.session_state.page = "title"
        st.rerun()