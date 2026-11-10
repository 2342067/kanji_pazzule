from datetime import datetime, timedelta, timezone

import streamlit as st
from db.sheet import append_row
from screens.question import question_info

JST = timezone(timedelta(hours=9))

# ==== スプレッドシート ====
# 解答の記録（1問ごと）と、全体のアンケート（1人1回）は別のシートに書く。2つは名前で結びつける
ANSWER_SHEET = "解答"
ANSWER_HEADER = [
    "送信日時", "名前", "学年", "教科", "難度", "語数", "設問番号", "問題ID",
    "空欄の数", "正解数", "別解", "解答時間（秒）", "解答", "知らない熟語の数", "知らない熟語", "感じた難しさ",
]
SURVEY_SHEET = "アンケート"
SURVEY_HEADER = [
    "送信日時", "名前", "学年", "面白さ", "使いやすさ", "今後の利用", "理科", "社会", "改善案や要望、感想",
]

# ==== 選択肢 ====
GRADES = (
    [f"中学{i}年生" for i in (1, 2, 3)] + [f"高校{i}年生" for i in (1, 2, 3)]
    + [f"大学{i}年生" for i in (1, 2, 3, 4)] + [f"大学院{i}年生" for i in (1, 2)]
    + ["社会人", "その他"]
)
NO_UNKNOWN = "知らない熟語はなかった"
FEELINGS = ["とてもやさしい", "やさしい", "ちょうどよい", "難しい", "とても難しい"]
SCALE = ["1", "2", "3", "4", "5"]
REUSE = ["ぜひ使いたい", "時間があれば使いたい", "あまり使いたくない", "使いたくない"]
STRENGTHS = ["得意", "ふつう", "苦手"]

CONSENT_TEXT = (
    "この回答は、卒業研究（漢字抜け熟語パズル）の評価のために使います。"
    "名前と学年は回答の整理のためだけに使い、論文や発表では個人がわかる形で公表しません。"
)
# 問い合わせ先：ページのいちばん下に小さく出す。空のままなら出さない
CONTACT = ""


def now_text():
    return f"{datetime.now(JST):%Y-%m-%d %H:%M:%S}"


def ask_person():
    """名前・学年を聞き、(名前, 学年) を返す。一度送ると、続けて使っている間は入力済みになる

    名前は、解答の記録とアンケートを結びつけるのに使うので、空白をすべて取り除いたものを返す。
    """
    name = st.text_input("名前", value=st.session_state.get("evaluation_name", ""))
    saved = st.session_state.get("evaluation_grade")
    grade = st.selectbox("学年", GRADES, index=GRADES.index(saved) if saved in GRADES else None,
                         placeholder="選んでください")
    return "".join(name.split()), grade


def ask_consent():
    """同意の文とチェックを出し、チェックされているかを返す"""
    st.write(CONSENT_TEXT)
    return st.checkbox("上の内容に同意します", value=st.session_state.get("evaluation_consent", False))


def show_contact():
    if CONTACT:
        st.caption(f"問い合わせ先：{CONTACT}")


def send(sheet_name, header, row, name, grade):
    """1行送る。送れたら名前・学年・同意を入力済みとして残し、True を返す"""
    try:
        append_row(sheet_name, header, row)
    except Exception:
        st.error("送信できませんでした。通信の状態を確かめて、もう一度「送信する」を押してください")
        return False
    st.session_state.evaluation_name = name
    st.session_state.evaluation_grade = grade
    st.session_state.evaluation_consent = True
    return True


def back_button(label, page):
    if st.button(label):
        st.session_state.page = page
        st.rerun()


def result_key(result):
    """同じ解答を2回送らないための目印（どの問題を、何秒で、どう解答したか）"""
    return f"{result['question_id']}|{result['seconds']}|{result['answers_text']}"


def fix_unknown(key):
    """知らなかった熟語の選択を整える：「知らない熟語はなかった」と熟語は同時に選べないようにする

    「なかった」を選んだら熟語の選択を外し、熟語を選んだら「なかった」を外す。
    """
    current = st.session_state.get(key) or []
    previous = st.session_state.get(key + "_previous", [])
    if NO_UNKNOWN in current and NO_UNKNOWN not in previous:
        current = [NO_UNKNOWN]
    elif NO_UNKNOWN in current and len(current) > 1:
        current = [word for word in current if word != NO_UNKNOWN]
    st.session_state[key] = current
    st.session_state[key + "_previous"] = current


def show():
    """解答の送信ページ：解答画面の「解答を送信」から開く。今回解いた問題の記録を1行送る"""
    result = st.session_state.get("result")
    if result is None:
        st.write("解答の記録が見つかりません")
        back_button("問題選択に戻る", "question_select")
        return

    st.subheader("解答を送信")
    st.caption(question_info())

    if st.session_state.get("evaluation_sent") == result_key(result):
        st.success("送信しました。ご協力ありがとうございます。")
        back_button("問題選択に戻る", "question_select")
        return

    name, grade = ask_person()
    unknown_key = f"unknown_{result['question_id']}_{result['seconds']}"
    unknown = st.pills(
        "知らなかった熟語を選んでください（いくつでも）", result["words"] + [NO_UNKNOWN],
        selection_mode="multi", key=unknown_key, on_change=fix_unknown, args=(unknown_key,),
    )
    feeling = st.radio("この問題の難しさはどうでしたか", FEELINGS, index=None, horizontal=True)
    consent = ask_consent()

    if st.button("送信する", type="primary"):
        if not name or grade is None:
            st.error("名前と学年を入力してください")
        elif not unknown:
            st.error("知らなかった熟語を選んでください。なければ「知らない熟語はなかった」を選んでください")
        elif feeling is None:
            st.error("問題の難しさを選んでください")
        elif not consent:
            st.error("同意のチェックを入れてください")
        else:
            unknown_words = [word for word in result["words"] if word in unknown]   # 問題の並び順にそろえる
            row = [
                now_text(), name, grade,
                result["field"], result["difficulty"], result["word_count"], result["question"], result["question_id"],
                result["blank_count"], result["ok_count"], "別解" if result["alt"] else "",
                result["seconds"], result["answers_text"],
                len(unknown_words), " ".join(unknown_words), feeling,
            ]
            if send(ANSWER_SHEET, ANSWER_HEADER, row, name, grade):
                st.session_state.evaluation_sent = result_key(result)
                st.rerun()

    back_button("解答に戻る", "answer")
    show_contact()


def show_survey():
    """アンケートのページ：タイトル画面の「評価実験アンケート」から開く。全体の感想を1行送る"""
    st.subheader("評価実験アンケート")

    if st.session_state.get("survey_sent"):
        st.success("送信しました。ご協力ありがとうございます。")
        back_button("タイトルに戻る", "title")
        return

    name, grade = ask_person()
    fun = st.radio("面白かったですか（1：まったく面白くなかった 〜 5：とても面白かった）",
                   SCALE, index=None, horizontal=True)
    usability = st.radio("使いやすかったですか（1：とても使いにくかった 〜 5：とても使いやすかった）",
                         SCALE, index=None, horizontal=True)
    reuse = st.radio("今後も利用したいですか", REUSE, index=None)
    science = st.radio("理科は得意ですか", STRENGTHS, index=None, horizontal=True)
    social = st.radio("社会は得意ですか", STRENGTHS, index=None, horizontal=True)
    comment = st.text_area("改善案や要望、感想など（自由に書いてください）")
    consent = ask_consent()

    if st.button("送信する", type="primary"):
        if not name or grade is None:
            st.error("名前と学年を入力してください")
        elif None in (fun, usability, reuse, science, social):
            st.error("すべての質問に答えてください（感想は空でも送れます）")
        elif not consent:
            st.error("同意のチェックを入れてください")
        else:
            row = [now_text(), name, grade, int(fun), int(usability), reuse, science, social, comment.strip()]
            if send(SURVEY_SHEET, SURVEY_HEADER, row, name, grade):
                st.session_state.survey_sent = True
                st.rerun()

    back_button("タイトルに戻る", "title")
    show_contact()
