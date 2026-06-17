import streamlit as st

def show():
    st.title("問題画面")

    # ダミーデータ（後でDBから取得する形に変える）
    dummy_questions = ["ダミー設問1", "ダミー設問2", "ダミー設問3"]

    if "answers" not in st.session_state:
        st.session_state.answers = {}

    for i, q in enumerate(dummy_questions):
        st.write(q)
        st.session_state.answers[i] = st.text_input(f"答え（{i+1}）", key=f"answer_{i}")

    if st.button("解答する"):
        # 未回答チェック
        unanswered = [i+1 for i, q in enumerate(dummy_questions) if not st.session_state.answers.get(i)]

        if unanswered:
            st.session_state.show_warning = True
            st.session_state.unanswered = unanswered
        else:
            st.session_state.show_warning = False
            st.session_state.page = "answer"
            st.rerun()

    # 警告表示（画面遷移せず、その場に出る）
    if st.session_state.get("show_warning"):
        st.warning(f"未回答の問題があります：{', '.join(map(str, st.session_state.unanswered))}番")
        if st.button("このまま解答する"):
            st.session_state.show_warning = False
            st.session_state.page = "answer"
            st.rerun()

    if st.button("戻る"):
        st.session_state.page = "question_select"
        st.rerun()