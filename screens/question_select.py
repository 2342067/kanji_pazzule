import streamlit as st

def show():
    st.title("問題選択画面")

    if st.button("設問1"):
        st.session_state.question = 1
        st.session_state.show_warning = False
        st.session_state.page = "question"
        st.rerun()

    if st.button("設問2"):
        st.session_state.question = 2
        st.session_state.show_warning = False
        st.session_state.page = "question"
        st.rerun()

    if st.button("設問3"):
        st.session_state.question = 3
        st.session_state.show_warning = False
        st.session_state.page = "question"
        st.rerun()

    if st.button("設問4"):
        st.session_state.question = 4
        st.session_state.show_warning = False
        st.session_state.page = "question"
        st.rerun()

    if st.button("戻る"):
        st.session_state.page = "title"
        st.rerun()