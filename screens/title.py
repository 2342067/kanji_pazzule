import streamlit as st

def show():
    st.title("タイトル画面")
    st.write("分野を選んでください")

    if st.button("理科"):
        st.session_state.field = "理科"
        st.session_state.page = "difficulty"
        st.rerun()

    if st.button("社会"):
        st.session_state.field = "社会"
        st.session_state.page = "difficulty"
        st.rerun()

    if st.button("教養"):
        st.session_state.field = "教養"
        st.session_state.page = "difficulty"
        st.rerun()