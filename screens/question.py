import streamlit as st
from db.db import get_questions, get_question_words
from screens.puzzle_component import puzzle
from screens.title import WORD_COUNTS, difficulties_of
from screens.ui_common import APP_TITLE


def build_words(question_words, with_answers=False):
    """DBの (word, blank_position, blank_number) の行を、画面表示用の形に変換する

    同じ熟語に空欄が複数ある場合は、同じ熟語の行が複数あるものとしてまとめる。
    空欄の位置は {"n": 空欄番号}、それ以外の文字は {"c": 漢字} にする。
    with_answers が True のときは、空欄にも {"a": 正解の漢字} を付ける（解答画面用）。
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
                ch = {"n": blanks[word][i]}
                if with_answers:
                    ch["a"] = c
                chars.append(ch)
            else:
                chars.append({"c": c})
        words.append(chars)

    return sorted(words, key=len)


def current_question_id():
    """選んでいる問題のidを返す。見つからなければ None"""
    questions = get_questions(
        st.session_state.get("field"),
        st.session_state.get("difficulty"),
        st.session_state.get("word_count"),
    )
    number = st.session_state.get("question")
    if not questions or number is None or number > len(questions):
        return None
    return questions[number - 1][0]


def question_info():
    """選んでいる問題を「教科・熟語難度・問題の大きさ・設問番号」の形で返す（例：教養・難しい・大・設問10）"""
    return "・".join([
        str(st.session_state.get("field")),
        difficulties_of(st.session_state.get("field")).get(st.session_state.get("difficulty"), ""),
        WORD_COUNTS.get(st.session_state.get("word_count"), ""),
        "設問" + str(st.session_state.get("question")),
    ])


def show():
    question_id = current_question_id()

    if question_id is None:
        st.write("問題が見つかりません")
        if st.button("戻る"):
            st.session_state.page = "question_select"
            st.rerun()
        return

    words = build_words(get_question_words(question_id))

    result = puzzle(key=f"puzzle_{question_id}", data={"title": APP_TITLE, "info": question_info(), "words": words}, on_submit_change=lambda: None, on_back_change=lambda: None)

    if result.submit is not None:
        st.session_state.answers = result.submit["answers"]
        st.session_state.seconds = result.submit.get("seconds", 0)
        st.session_state.page = "answer"
        st.rerun()

    if result.back:
        st.session_state.page = "question_select"
        st.rerun()
