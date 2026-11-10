import streamlit as st
from db.db import get_question_words, get_words
from screens.question import build_words, current_question_id, question_info
from screens.question_select import progress_key
from db.sheet import is_enabled
from screens.ui_common import APP_TITLE, COMMON_CSS, COMMON_JS

HTML = '<div class="root"></div>'

# 問題画面と同じ見た目で、番号マスに自分の解答、熟語カードの□に正解の漢字を入れて表示する
# 正解は緑枠、不正解は赤枠、番号の横に○×
# 別解で正解のときは全部を緑枠にし、模範解答と違う漢字の番号には○の代わりに※を付ける
# 熟語カードは「模範解答」と「自分の解答」をボタンで切り替えられる（上の番号マスは自分の解答のまま）
CSS = COMMON_CSS + """
.box.ok { border-color: var(--ok); }
.box.ng { border-color: var(--err); }
.box .kanji { font-size: 24px; line-height: 1.2; }
.mark.ok { color: var(--ok); font-weight: bold; }
.mark.ng { color: var(--err); font-weight: bold; }
.blank.ok { border-color: var(--ok); cursor: default; }
.blank.ng { border-color: var(--err); cursor: default; }
.score { font-size: 14px; min-height: 1.2em; margin-top: 4px; }
.score-row { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; }
.score-row .score { margin-top: 0; min-height: 0; line-height: 24px; }
.view-switch { display: inline-flex; background: var(--gray-bg); border-radius: 999px; padding: 2px; }
.view-switch button {
    border: none; background: transparent; color: var(--sub); font-family: inherit; font-size: 13px;
    line-height: 20px; padding: 0 12px; border-radius: 999px; cursor: pointer;
}
.view-switch button.on { background: #e6f1fb; color: #185fa5; font-weight: bold; }
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
    // 別解で正解（data.alt）のときは、模範解答と違う漢字の番号も正解として扱う
    const isModel = (n) => answers[String(n)] === correct[n];
    const isOk = (n) => data.alt || isModel(n);
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
        top.appendChild(el("span", "mark " + (isOk(n) ? "ok" : "ng"), isModel(n) ? "○" : (isOk(n) ? "※" : "×")));
        box.appendChild(top);
        // 上の番号マスは自分の解答のまま出す（未回答は空。高さをそろえるため空白を入れる）
        box.appendChild(el("span", "kanji", answers[String(n)] || "\u00a0"));
        bar.appendChild(box);
    });
    header.appendChild(makeQuestionInfo(data.info, data.seconds || 0));
    header.appendChild(bar);
    // 正解数の行：右端に、熟語カードの表示を切り替えるボタン
    const scoreRow = el("div", "score-row");
    scoreRow.appendChild(el("div", "score", okCount === numbers.length ? (data.alt ? "全問正解！（別解）" : "全問正解！") : numbers.length + "問中" + okCount + "問正解"));
    const viewSwitch = el("div", "view-switch");
    const viewButtons = {};
    [["model", "模範解答"], ["mine", "自分の解答"]].forEach(([view, label]) => {
        const b = el("button", null, label);
        b.type = "button";
        b.addEventListener("click", () => { parentElement.answerView = view; render(); });
        viewButtons[view] = b;
        viewSwitch.appendChild(b);
    });
    scoreRow.appendChild(viewSwitch);
    header.appendChild(scoreRow);
    root.appendChild(header);

    const grid = el("div", "grid");
    grid.style.gridTemplateRows = "repeat(" + Math.ceil(words.length / 3) + ", auto)";
    words.forEach((w) => {
        const word = el("div", "word");
        w.forEach((ch) => {
            const slot = el("div", "slot");
            const num = el("span", "n");
            if (ch.n !== undefined) {
                const blank = el("span", "blank " + (isOk(ch.n) ? "ok" : "ng"));
                blank.dataset.num = ch.n;
                slot.appendChild(blank);
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

    // 評価実験の回答を送れる設定のときだけ、解答を送信するページへ進むボタンを出す
    if (data.evaluation) {
        const evalButton = el("button", "submit", "解答を送信");
        evalButton.type = "button";
        evalButton.addEventListener("click", () => setTriggerValue("to_evaluation", true));
        root.appendChild(evalButton);
    }

    // 熟語カードの空欄に、選んでいる表示（模範解答か自分の解答）の漢字を入れる
    // 自分の解答で未回答の空欄は空のままにする。枠の色（正解は緑、不正解は赤）はどちらの表示でも同じ
    function render() {
        const view = parentElement.answerView || "model";
        Object.keys(viewButtons).forEach((v) => viewButtons[v].classList.toggle("on", v === view));
        root.querySelectorAll(".blank").forEach((blank) => {
            const n = blank.dataset.num;
            blank.textContent = view === "mine" ? (answers[n] || "") : correct[n];
        });
    }
    render();
}
"""

answer_screen = st.components.v2.component("answer_screen", html=HTML, css=CSS, js=JS)


def get_correct_answers(question_id):
    """問題の空欄番号ごとの模範解答を {番号: 漢字} の形で返す"""
    correct = {}
    for word, blank_position, blank_number in get_question_words(question_id):
        correct[blank_number] = word[blank_position]
    return correct


def is_alt_answer(question_words, answers, field):
    """
    模範解答とは違うが、別解として正解かどうかを返す。
    問題全体で判定する（番号ごと、熟語ごとの部分的な判定はしない）。次のすべてを満たせば別解とする。
        - すべての番号に解答がある
        - 違う番号に同じ漢字を入れていない（番号と漢字は1対1）
        - 解答を入れた熟語が、すべてその教科の語（難度は問わない）として words テーブルにある
        - 解答を入れた熟語どうしが同じにならない
    """
    numbers = {blank_number for _word, _position, blank_number in question_words}
    kanji = {number: answers.get(str(number)) for number in numbers}
    if not all(kanji.values()):
        return False
    if len(set(kanji.values())) != len(numbers):
        return False

    # 空欄に解答の漢字を入れた熟語を作る
    filled = {}
    for word, blank_position, blank_number in question_words:
        chars = filled.setdefault(word, list(word))
        chars[blank_position] = kanji[blank_number]
    filled_words = ["".join(chars) for chars in filled.values()]
    if len(set(filled_words)) != len(filled_words):
        return False

    vocabulary = {word for _id, word, _field, _difficulty in get_words(field=field)}
    return all(word in vocabulary for word in filled_words)


def show():
    question_id = current_question_id()

    if question_id is None:
        st.write("問題が見つかりません")
        if st.button("問題選択に戻る"):
            st.session_state.page = "question_select"
            st.rerun()
        return

    answers = st.session_state.get("answers", {})

    # 全問正解（別解での正解も含む）なら、問題選択画面の印を緑にする（一度全問正解したら緑のまま）
    question_words = get_question_words(question_id)
    correct = get_correct_answers(question_id)
    is_model = all(answers.get(str(n)) == kanji for n, kanji in correct.items())
    alt = not is_model and is_alt_answer(question_words, answers, st.session_state.get("field"))
    if is_model or alt:
        key = progress_key(
            st.session_state.get("field"),
            st.session_state.get("difficulty"),
            st.session_state.get("word_count"),
            st.session_state.get("question"),
        )
        st.session_state.setdefault("progress", {})[key] = "perfect"

    # 評価実験のページで送る、この解答の記録
    st.session_state.result = {
        "field": st.session_state.get("field"),
        "difficulty": st.session_state.get("difficulty"),
        "word_count": st.session_state.get("word_count"),
        "question": st.session_state.get("question"),
        "question_id": question_id,
        "blank_count": len(correct),
        "ok_count": len(correct) if alt else sum(1 for n, kanji in correct.items() if answers.get(str(n)) == kanji),
        "alt": alt,
        "seconds": st.session_state.get("seconds", 0),
        # 熟語（空欄を埋めた完成形）。問題画面と同じ並び（文字数の少ない順）
        "words": sorted(dict.fromkeys(word for word, _position, _number in question_words), key=len),
        "answers_text": " ".join(f"{n}={answers.get(str(n), '')}" for n in sorted(correct)),
    }

    words = build_words(question_words, with_answers=True)
    result = answer_screen(
        key=f"answer_{question_id}",
        data={"title": APP_TITLE, "info": question_info(), "words": words, "answers": answers, "alt": alt,
              "seconds": st.session_state.get("seconds", 0), "evaluation": is_enabled()},
        on_to_title_change=lambda: None,
        on_to_select_change=lambda: None,
        on_to_evaluation_change=lambda: None,
    )

    if result.to_title:
        st.session_state.page = "title"
        st.rerun()
    if result.to_evaluation:
        st.session_state.page = "evaluation"
        st.rerun()
    if result.to_select:
        st.session_state.page = "question_select"
        st.rerun()
