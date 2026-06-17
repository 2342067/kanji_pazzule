import streamlit as st

def show():
    st.title("解答画面")
    if st.button("タイトルに戻る"):
        st.session_state.page = "title"
        st.rerun()
    if st.button("問題選択に戻る"):
        st.session_state.page = "question_select"
        st.rerun()