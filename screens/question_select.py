import streamlit as st
from db.db import get_questions
from screens.title import WORD_COUNTS, difficulties_of
from screens.ui_common import APP_TITLE, COMMON_CSS, COMMON_JS

HTML = '<div class="root"></div>'

# 上に熟語難度と問題の大きさのボタン、その下に設問を並べる
# 熟語難度と問題の大きさは番号マスと同じ枠（2px、角丸8px）で、選択肢の数で等分する。選んだものはロゴの青を薄めた色
# 設問は番号マスと同じ枠の四角を5列で並べる（熟語難度と問題の大きさを両方選ぶと出る）
# 開いた問題は灰色のチェック、全問正解した問題は緑のチェック（アプリを閉じるまで残る）
CSS = COMMON_CSS + """
.field-label { font-size: 14px; font-weight: bold; margin: 18px 0 8px; }
.options { display: grid; gap: 8px; }
.opt {
    height: 48px; font-size: 17px; border-radius: 8px; border: 2px solid var(--gray-border);
    background: var(--bg); color: var(--fg); font-family: inherit;
}
/* 選んだ項目：ロゴの青を薄めた色（黄色は問題画面の番号のハイライト専用にする） */
.opt.selected { background: #e6f1fb; border-color: #378ADD; color: #185fa5; font-weight: bold; }
.qgrid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
.qbtn {
    position: relative;
    height: 48px; border: 2px solid var(--gray-border); border-radius: 8px; background: var(--bg); color: var(--fg);
    font-size: 18px; font-family: inherit; font-variant-numeric: tabular-nums;
}
.qbtn .check {
    position: absolute; top: -7px; right: -7px; width: 18px; height: 18px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; background: var(--sub); color: var(--bg);
}
.qbtn .check svg { width: 11px; height: 11px; }
.qbtn.perfect { border-color: var(--ok); }
.qbtn.perfect .check { background: var(--ok); }
.legend { display: flex; gap: 16px; font-size: 12px; color: var(--sub); margin-top: 12px; }
.legend span { display: inline-flex; align-items: center; gap: 4px; }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; }
.legend .opened { background: var(--sub); }
.legend .perfect { background: var(--ok); }
"""

JS = COMMON_JS + """
export default function(component) {
    const { parentElement, data, setTriggerValue } = component;
    const root = parentElement.querySelector(".root");
    root.innerHTML = "";

    // ヘッダー：右に「戻る」と「遊び方」。「遊び方」は今の画面に重ねて出す
    root.appendChild(makeHeader(data.title, [
        [ICON_BACK, "戻る", () => setTriggerValue("back", true)],
        [ICON_HELP, "遊び方", () => openOverlay(root, "遊び方", helpBody())],
    ], false));
    // 見出しに、選んでいる教科をかっこで付ける（例：問題選択（教養））
    root.appendChild(el("div", "page-heading", "問題選択（" + data.field + "）"));

    // 熟語難度と問題の大きさ。押すと選び、もう一度押すと外す。選び直すたびに下の設問を出し直す
    const selected = { difficulty: data.difficulty, word_count: data.word_count };
    const group = (label, items, key) => {
        root.appendChild(el("div", "field-label", label));
        const row = el("div", "options");
        row.style.gridTemplateColumns = "repeat(" + items.length + ", 1fr)";
        items.forEach(([value, text]) => {
            const b = el("button", "opt", text);
            b.type = "button";
            b.classList.toggle("selected", selected[key] === value);
            pressable(b, true);
            b.addEventListener("click", () => {
                selected[key] = selected[key] === value ? null : value;
                setTriggerValue("condition", { difficulty: selected.difficulty, word_count: selected.word_count });
            });
            row.appendChild(b);
        });
        root.appendChild(row);
    };
    group("熟語難度", data.difficulties, "difficulty");
    group("問題の大きさ", data.word_counts, "word_count");

    // 設問は、熟語難度と問題の大きさを両方選んでから出す
    if (data.difficulty === null || data.word_count === null) return;

    root.appendChild(el("div", "field-label", "設問"));
    if (data.count === 0) {
        root.appendChild(el("div", "none", "問題がありません"));
        return;
    }

    const list = el("div", "qgrid");
    for (let i = 1; i <= data.count; i++) {
        const b = el("button", "qbtn", String(i));
        b.type = "button";
        pressable(b, true);
        const mark = data.progress[String(i)];
        let label = "設問" + i;
        if (mark) {
            const check = el("span", "check");
            check.innerHTML = ICON_CHECK;
            b.appendChild(check);
            if (mark === "perfect") b.classList.add("perfect");
            label += mark === "perfect" ? "（全問正解）" : "（開いた）";
        }
        b.setAttribute("aria-label", label);
        b.addEventListener("click", () => setTriggerValue("pick", i));
        list.appendChild(b);
    }
    root.appendChild(list);

    const legend = el("div", "legend");
    legend.innerHTML = '<span><i class="opened"></i>開いた問題</span><span><i class="perfect"></i>全問正解</span>';
    root.appendChild(legend);
}
"""

select_screen = st.components.v2.component("select_screen", html=HTML, css=CSS, js=JS)


def progress_key(field, difficulty, word_count, question_number):
    """問題ごとの記録（開いた・全問正解）のキー"""
    return f"{field}|{difficulty}|{word_count}|{question_number}"


def show():
    field = st.session_state.get("field")
    difficulty = st.session_state.get("difficulty")
    word_count = st.session_state.get("word_count")

    # 設問は、熟語難度と問題の大きさを両方選んでから出す
    questions = []
    if difficulty is not None and word_count is not None:
        questions = get_questions(field, difficulty, word_count)

    # 問題ごとの記録（"opened" または "perfect"）。session_state にあるのでアプリを閉じるまで残る
    all_progress = st.session_state.setdefault("progress", {})
    progress = {}
    for i in range(1, len(questions) + 1):
        mark = all_progress.get(progress_key(field, difficulty, word_count, i))
        if mark:
            progress[str(i)] = mark

    result = select_screen(
        key="select_screen",
        data={
            "title": APP_TITLE,
            "field": field,
            "difficulties": [[d, label] for d, label in difficulties_of(field).items()],
            "word_counts": [[n, label] for n, label in WORD_COUNTS.items()],
            "difficulty": difficulty,
            "word_count": word_count,
            "count": len(questions),
            "progress": progress,
        },
        on_condition_change=lambda: None,
        on_pick_change=lambda: None,
        on_back_change=lambda: None,
    )

    if result.condition is not None:
        st.session_state.difficulty = result.condition["difficulty"]
        st.session_state.word_count = result.condition["word_count"]
        st.rerun()

    if result.pick is not None:
        number = int(result.pick)
        key = progress_key(field, difficulty, word_count, number)
        if key not in all_progress:
            all_progress[key] = "opened"
        st.session_state.question = number
        st.session_state.page = "question"
        st.rerun()

    if result.back:
        st.session_state.page = "title"
        st.rerun()
