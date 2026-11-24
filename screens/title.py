import streamlit as st
from db.sheet import is_enabled
from screens.ui_common import APP_TITLE, COMMON_CSS, COMMON_JS

FIELDS = ["理科", "社会", "教養"]
# 熟語難度は教科によって段階の数が違う
#   教養：新聞での頻度による3段階
#   理科・社会：学校段階による2段階（ボタンの文言は仮）
DIFFICULTIES = {1: "やさしい", 2: "ふつう", 3: "難しい"}
SCHOOL_DIFFICULTIES = {1: "小学範囲", 2: "小学〜中学範囲"}
FIELD_DIFFICULTIES = {"理科": SCHOOL_DIFFICULTIES, "社会": SCHOOL_DIFFICULTIES, "教養": DIFFICULTIES}
WORD_COUNTS = {9: "小", 15: "中", 21: "大"}


def difficulties_of(field):
    """その教科で選べる熟語難度（番号: 文言）を返す"""
    return FIELD_DIFFICULTIES.get(field, DIFFICULTIES)

HTML = '<div class="root"></div>'

# 教科のボタンは番号マスと同じ枠（2px、角丸8px）の3等分。押すとすぐ問題選択へ進む
# 押した瞬間は青くなる（ui_common の pressable）
# 前回選んだ教科は、選択中の青と混ざらないよう、濃い灰色で少しへこんだ（押したあとの）見た目にする
# 画面の高さいっぱいを使い、上から「ロゴ」「教科のボタン」「評価実験」の3つを間をあけて置く
# 間の比率は上から 3：2：4（ヘッダーとロゴの間：ロゴと教科の間：教科と評価実験の間）。評価実験の下は16pxだけあける
CSS = COMMON_CSS + """
.title-page { display: flex; flex-direction: column; min-height: calc(100dvh - 24px); }
.title-page .gap { flex-basis: 16px; }
.title-page .title-logo { margin: 0; }
.options { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.opt {
    height: 48px; font-size: 17px; border-radius: 8px; border: 2px solid var(--gray-border);
    background: var(--bg); color: var(--fg); font-family: inherit;
}
/* 前回選んだ教科：濃い灰色の地と枠に、内側の影で押したあとの感じを出す */
.opt.last { background: #e2e2e2; border-color: #555; box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.18); }
/* 前回の教科でも、押した瞬間はほかと同じ青にする */
.opt.last.pressed { background: #e6f1fb; border-color: #378ADD; box-shadow: none; }
/* 評価実験アンケートへの入口：教科のボタンから離し、線で区切って出す */
.survey-box { padding-top: 16px; border-top: 1px solid var(--card-border); }
.survey-heading { font-size: 14px; font-weight: bold; }
.survey-note { font-size: 13px; color: var(--sub); margin-top: 2px; }
/* アンケートのボタンは主な操作ではないので、白地に青の枠と文字にする */
.survey-button {
    margin-top: 8px; background: var(--bg); color: #185fa5; font-size: 14px; padding: 8px;
    font-weight: normal; letter-spacing: 0;
}
.survey-button:active { background: #e6f1fb; border-color: #378ADD; }
"""

JS = COMMON_JS + """
export default function(component) {
    const { parentElement, data, setTriggerValue } = component;
    const root = parentElement.querySelector(".root");
    root.innerHTML = "";
    const page = el("div", "title-page");
    root.appendChild(page);
    // 間をあける部品。grow は余った高さを分ける比率
    const gap = (grow) => {
        const g = el("div", "gap");
        g.style.flexGrow = grow;
        page.appendChild(g);
    };

    // ヘッダー：ロゴは出さず、右に「遊び方」。押すと今の画面に重ねて遊び方を出す
    // 評価実験の回答を送れる設定のときだけ、その左に「評価実験について」を出す（これも重ねて出す）
    const buttons = [[ICON_HELP, "遊び方", () => openOverlay(root, "遊び方", helpBody())]];
    if (data.evaluation) buttons.unshift([ICON_INFO, "評価実験について", () => openOverlay(root, "評価実験について", aboutBody(data.about))]);
    page.appendChild(makeHeader(null, buttons, false));

    // タイトルロゴ：中央揃えで大きく出す
    gap(3);
    const logo = el("div", "title-logo");
    logo.innerHTML = TITLE_LOGO;
    page.appendChild(logo);

    // 教科のボタン（見出しなし）。押すとその教科の問題選択へ進む
    gap(2);
    const row = el("div", "options");
    data.fields.forEach(([value, text]) => {
        const b = el("button", "opt", text);
        b.type = "button";
        b.classList.toggle("last", data.field === value);
        pressable(b, true);
        b.addEventListener("click", () => setTriggerValue("pick", value));
        row.appendChild(b);
    });
    page.appendChild(row);

    // 評価実験の回答を送れる設定のときだけ、アンケートのページへ進むボタンを出す
    gap(4);
    if (data.evaluation) {
        const box = el("div", "survey-box");
        box.appendChild(el("div", "survey-heading", "評価実験に参加している方へ"));
        box.appendChild(el("div", "survey-note", "問題を解き終わったら、最後に答えてください"));
        const survey = el("button", "submit survey-button", "評価実験アンケート");
        survey.type = "button";
        survey.addEventListener("click", () => setTriggerValue("survey", true));
        box.appendChild(survey);
        page.appendChild(box);
    }
    gap(0);
}
"""

title_screen = st.components.v2.component("title_screen", html=HTML, css=CSS, js=JS)


def show():
    # 評価実験の文は evaluation.py と同じものを使う（evaluation は title を読み込むので、ここで読み込む）
    from screens.evaluation import CONSENT_TITLE, CONSENT_TEXT, CONTACT

    result = title_screen(
        key="title_screen",
        data={
            "title": APP_TITLE,
            "fields": [[f, f] for f in FIELDS],
            "field": st.session_state.get("field"),
            "evaluation": is_enabled(),
            "about": {"consent_title": CONSENT_TITLE, "consent": CONSENT_TEXT, "contact": CONTACT},
        },
        on_pick_change=lambda: None,
        on_survey_change=lambda: None,
    )

    if result.survey:
        st.session_state.page = "survey"
        st.rerun()

    if result.pick is not None:
        # 前回と違う教科を選んだら、熟語難度と問題の大きさは未選択に戻す
        # （難度は教科によって段階も意味も違い、番号が同じでも別物のため。同じ教科なら前回の選択を残す）
        if result.pick != st.session_state.get("field"):
            st.session_state.difficulty = None
            st.session_state.word_count = None
        st.session_state.field = result.pick
        st.session_state.page = "question_select"
        st.rerun()
