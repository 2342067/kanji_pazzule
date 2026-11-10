import streamlit as st
from db.sheet import is_enabled
from screens.ui_common import APP_TITLE, COMMON_CSS, COMMON_JS

FIELDS = ["理科", "社会", "教養"]
DIFFICULTIES = {1: "やさしい", 2: "ふつう", 3: "難しい"}
WORD_COUNTS = {9: "小", 15: "中", 21: "大"}

HTML = '<div class="root"></div>'

# 選択肢は番号マスと同じ枠（2px、角丸8px）の3等分。選んだものは番号マスの選択中と同じ黄色
CSS = COMMON_CSS + """
.field-label { font-size: 14px; font-weight: bold; margin: 18px 0 8px; }
.options { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.opt {
    height: 48px; font-size: 17px; border-radius: 8px; border: 2px solid var(--gray-border);
    background: var(--bg); color: var(--fg); font-family: inherit;
}
.opt.selected { background: var(--sel-bg); border-color: var(--sel-border); font-weight: bold; }
.title-next { margin-top: 24px; }
"""

JS = COMMON_JS + """
export default function(component) {
    const { parentElement, data, setTriggerValue } = component;
    const root = parentElement.querySelector(".root");

    // 選択中の値。前回の選択（data）から始める
    if (!parentElement.titleState) {
        parentElement.titleState = { field: data.field, difficulty: data.difficulty, word_count: data.word_count };
    }
    const state = parentElement.titleState;

    function render() {
        root.innerHTML = "";
        // ヘッダー：ロゴは出さず、右に「遊び方」だけ（遊び方画面は未作成。押しても何も起きない）
        root.appendChild(makeHeader(null, [[ICON_HELP, "遊び方", null]], false));
        // タイトルロゴ：ヘッダーの下に中央揃えで大きく出す
        const logo = el("div", "title-logo");
        logo.innerHTML = TITLE_LOGO;
        root.appendChild(logo);

        const group = (label, items, key) => {
            root.appendChild(el("div", "field-label", label));
            const row = el("div", "options");
            items.forEach(([value, text]) => {
                const b = el("button", "opt", text);
                b.type = "button";
                b.classList.toggle("selected", state[key] === value);
                b.addEventListener("click", () => {
                    state[key] = state[key] === value ? null : value;
                    render();
                });
                row.appendChild(b);
            });
            root.appendChild(row);
        };
        group("分野", data.fields, "field");
        group("熟語難度", data.difficulties, "difficulty");
        group("問題の大きさ", data.word_counts, "word_count");

        const next = el("button", "submit title-next", "次へ");
        next.type = "button";
        next.disabled = !(state.field && state.difficulty && state.word_count);
        next.addEventListener("click", () => {
            setTriggerValue("next", { field: state.field, difficulty: state.difficulty, word_count: state.word_count });
        });
        root.appendChild(next);

        // 評価実験の回答を送れる設定のときだけ、アンケートのページへ進むボタンを出す
        if (data.evaluation) {
            const survey = el("button", "submit", "評価実験アンケート");
            survey.type = "button";
            survey.addEventListener("click", () => setTriggerValue("survey", true));
            root.appendChild(survey);
        }
    }

    render();
}
"""

title_screen = st.components.v2.component("title_screen", html=HTML, css=CSS, js=JS)


def show():
    result = title_screen(
        key="title_screen",
        data={
            "title": APP_TITLE,
            "fields": [[f, f] for f in FIELDS],
            "difficulties": [[d, label] for d, label in DIFFICULTIES.items()],
            "word_counts": [[n, label] for n, label in WORD_COUNTS.items()],
            "field": st.session_state.get("field"),
            "difficulty": st.session_state.get("difficulty"),
            "word_count": st.session_state.get("word_count"),
            "evaluation": is_enabled(),
        },
        on_next_change=lambda: None,
        on_survey_change=lambda: None,
    )

    if result.survey:
        st.session_state.page = "survey"
        st.rerun()

    if result.next is not None:
        st.session_state.field = result.next["field"]
        st.session_state.difficulty = result.next["difficulty"]
        st.session_state.word_count = result.next["word_count"]
        st.session_state.page = "question_select"
        st.rerun()
