import streamlit as st
from screens.title import APP_TITLE

# 全画面共通：Streamlitのヘッダーを消し、上の余白をなくす
GLOBAL_CSS = """
header[data-testid="stHeader"] { display: none; }
[data-testid="stMainBlockContainer"] { padding-top: 0; }
.page-heading { font-size: 16px; font-weight: bold; margin: 4px 0 8px; }
"""

# 問題画面以外の画面のタイトル行（問題画面と同じ位置・大きさ）
HEADER_HTML = """
<div class="app-header">
    <div class="app-title"></div>
    <button class="app-header-button" hidden></button>
</div>
"""

HEADER_CSS = GLOBAL_CSS + """
.app-header {
    padding-top: 8px; height: 32px; margin-bottom: 4px;
    display: flex; justify-content: space-between; align-items: center;
    font-family: "Hiragino Sans", "Noto Sans JP", "Yu Gothic", sans-serif;
}
.app-title { font-size: 18px; font-weight: bold; }
.app-header-button {
    font-size: 14px; padding: 4px 12px; border-radius: 6px;
    border: 1px solid #888; background: #f4f4f4; font-family: inherit;
}
.app-header-button[hidden] { display: none; }
"""

HEADER_JS = """
export default function(component) {
    const { parentElement, data, setTriggerValue } = component;
    parentElement.querySelector(".app-title").textContent = data.title;
    const button = parentElement.querySelector(".app-header-button");
    if (data.button) {
        button.textContent = data.button;
        button.hidden = false;
        button.onclick = () => setTriggerValue("click", true);
    } else {
        button.hidden = true;
        button.onclick = null;
    }
}
"""

# isolate_styles=False にして、共通のCSSをページ全体に効かせる
app_header = st.components.v2.component(
    "app_header", html=HEADER_HTML, css=HEADER_CSS, js=HEADER_JS, isolate_styles=False
)


def apply_style():
    pass


def show_header(button_label=None):
    """問題画面以外の画面の一番上にタイトルを表示する

    button_label を渡すと、タイトルの右端にボタンを出す。押されたら True を返す。
    """
    result = app_header(
        key="app_header",
        data={"title": APP_TITLE, "button": button_label},
        on_click_change=lambda: None,
    )
    return bool(result.click)


def show_page_heading(text):
    """各画面の見出しを、タイトルより小さく表示する"""
    st.markdown(f'<div class="page-heading">{text}</div>', unsafe_allow_html=True)
