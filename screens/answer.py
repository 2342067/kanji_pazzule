import streamlit as st
from db.db import get_question_words
from screens.question import build_words, current_question_id
from screens.question_select import progress_key
from screens.ui_common import APP_TITLE, COMMON_CSS, COMMON_JS

HTML = '<div class="root"></div>'

# 問題画面と同じ見た目で、番号マスと熟語カードの□に正解の漢字を入れて表示する
# 正解は緑枠、不正解は赤枠、番号の横に○×
CSS = COMMON_CSS + """
.box.ok { border-color: var(--ok); }
.box.ng { border-color: var(--err); }
.box .kanji { font-size: 24px; line-height: 1.2; }
.mark.ok { color: var(--ok); font-weight: bold; }
.mark.ng { color: var(--err); font-weight: bold; }
.blank.ok { border-color: var(--ok); cursor: default; }
.blank.ng { border-color: var(--err); cursor: default; }
.score { font-size: 14px; min-height: 1.2em; margin-top: 4px; }
.result-table { border-collapse: collapse; width: 100%; max-width: 360px; margin: 4px 0 16px; font-size: 16px; }
.result-table th, .result-table td { border: 1px solid var(--card-border); padding: 4px 8px; text-align: center; }
.result-table th { background: var(--gray-bg); font-size: 14px; }
.result-table .kanji { font-size: 22px; }
"""

JS = COMMON_JS + """
export default function(component) {
    const { parentElement, data, setTriggerValue } = component;
    const root = parentElement.querySelector(".root");
    root.innerHTML = "";

    const words = data.words;
    const answers = data.answers || {};
    const numbers = [];
    const correct = {};
    words.forEach((w) => w.forEach((ch) => {
        if (ch.n === undefined) return;
        if (!numbers.includes(ch.n)) numbers.push(ch.n);
        correct[ch.n] = ch.a;
    }));
    numbers.sort((a, b) => a - b);
    const isOk = (n) => answers[String(n)] === correct[n];
    const okCount = numbers.filter(isOk).length;

    // ヘッダー：右に「タイトル」「問題選択」
    const header = makeHeader(data.title, [
        [ICON_HOME, "タイトルへ", () => setTriggerValue("to_title", true)],
        [ICON_BACK, "問題選択", () => setTriggerValue("to_select", true)],
    ], true);

    const bar = el("div", "bar");
    numbers.forEach((n) => {
        const box = el("div", "box " + (isOk(n) ? "ok" : "ng"));
        const top = el("span", "n");
        top.appendChild(document.createTextNode(n + " "));
        top.appendChild(el("span", "mark " + (isOk(n) ? "ok" : "ng"), isOk(n) ? "○" : "×"));
        box.appendChild(top);
        box.appendChild(el("span", "kanji", correct[n]));
        bar.appendChild(box);
    });
    header.appendChild(bar);
    header.appendChild(el("div", "score", numbers.length + "マス中" + okCount + "マス正解"));
    root.appendChild(header);

    const grid = el("div", "grid");
    grid.style.gridTemplateRows = "repeat(" + Math.ceil(words.length / 3) + ", auto)";
    words.forEach((w) => {
        const word = el("div", "word");
        w.forEach((ch) => {
            const slot = el("div", "slot");
            const num = el("span", "n");
            if (ch.n !== undefined) {
                slot.appendChild(el("span", "blank " + (isOk(ch.n) ? "ok" : "ng"), ch.a));
                num.textContent = ch.n;
            } else {
                slot.appendChild(el("span", "ch", ch.c));
            }
            slot.appendChild(num);
            word.appendChild(slot);
        });
        grid.appendChild(word);
    });
    root.appendChild(grid);

    root.appendChild(el("div", "page-heading", "間違えたマス"));
    const wrong = numbers.filter((n) => !isOk(n));
    if (wrong.length === 0) {
        root.appendChild(el("div", "none", "間違えたマスはありません"));
    } else {
        const table = el("table", "result-table");
        const head = el("tr");
        ["番号", "自分の答え", "正解"].forEach((t) => head.appendChild(el("th", null, t)));
        table.appendChild(head);
        wrong.forEach((n) => {
            const tr = el("tr");
            tr.appendChild(el("td", null, String(n)));
            tr.appendChild(el("td", "kanji", answers[String(n)] || "－"));
            tr.appendChild(el("td", "kanji", correct[n]));
            table.appendChild(tr);
        });
        root.appendChild(table);
    }
}
"""

answer_screen = st.components.v2.component("answer_screen", html=HTML, css=CSS, js=JS)


def get_correct_answers(question_id):
    """問題の空欄番号ごとの模範解答を {番号: 漢字} の形で返す"""
    correct = {}
    for word, blank_position, blank_number in get_question_words(question_id):
        correct[blank_number] = word[blank_position]
    return correct


def show():
    question_id = current_question_id()

    if question_id is None:
        st.write("問題が見つかりません")
        if st.button("問題選択に戻る"):
            st.session_state.page = "question_select"
            st.rerun()
        return

    answers = st.session_state.get("answers", {})

    # 全問正解なら、問題選択画面の印を緑にする（一度全問正解したら緑のまま）
    correct = get_correct_answers(question_id)
    if all(answers.get(str(n)) == kanji for n, kanji in correct.items()):
        key = progress_key(
            st.session_state.get("field"),
            st.session_state.get("difficulty"),
            st.session_state.get("word_count"),
            st.session_state.get("question"),
        )
        st.session_state.setdefault("progress", {})[key] = "perfect"

    words = build_words(get_question_words(question_id), with_answers=True)
    result = answer_screen(
        key=f"answer_{question_id}",
        data={"title": APP_TITLE, "words": words, "answers": answers},
        on_to_title_change=lambda: None,
        on_to_select_change=lambda: None,
    )

    if result.to_title:
        st.session_state.page = "title"
        st.rerun()
    if result.to_select:
        st.session_state.page = "question_select"
        st.rerun()
