import streamlit as st

# ページ初期化
if "page" not in st.session_state:
    st.session_state.page = "title"

# タイトル画面
if st.session_state.page == "title":
    st.title("タイトル画面")
    if st.button("次へ"):
        st.session_state.page = "difficulty"
        st.rerun()

# 難易度選択画面
elif st.session_state.page == "difficulty":
    st.title("難易度選択画面")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("戻る"):
            st.session_state.page = "title"
            st.rerun()
    with col2:
        if st.button("次へ"):
            st.session_state.page = "problem_select"
            st.rerun()

# 問題選択画面
elif st.session_state.page == "problem_select":
    st.title("問題選択画面")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("戻る"):
            st.session_state.page = "difficulty"
            st.rerun()
    with col2:
        if st.button("次へ"):
            st.session_state.page = "problem"
            st.rerun()

# 問題画面
elif st.session_state.page == "problem":
    st.title("問題画面")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("警告画面へ"):
            st.session_state.page = "warning"
            st.rerun()
    with col2:
        if st.button("解答する"):
            st.session_state.page = "answer"
            st.rerun()

# 警告画面
elif st.session_state.page == "warning":
    st.title("警告画面")
    st.write("未回答の問題があります")
    if st.button("問題に戻る"):
        st.session_state.page = "problem"
        st.rerun()

# 解答画面
elif st.session_state.page == "answer":
    st.title("解答画面")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("タイトルに戻る"):
            st.session_state.page = "title"
            st.rerun()
    with col2:
        if st.button("問題選択に戻る"):
            st.session_state.page = "problem_select"
            st.rerun()