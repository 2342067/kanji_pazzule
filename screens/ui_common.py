"""全画面で共通に使う見た目（CSS）と部品（JS）

各画面の部品（st.components.v2）の CSS と JS の先頭に、ここの内容をつなげて使う。

タイトルロゴは screens/logo の SVG を読み込んで使う（文字は図形に変換済み。フォントの読み込みは不要）
    title.svg  : タイトル画面の大きいロゴ（字間4.5px）
    header.svg : ヘッダーの小さいロゴ（字間0.5px）
    ロゴの文字は currentColor で塗っているので、文字色（--fg）に合わせて表示される。「抜」のマスとピースの青、「抜」の白い字は固定
"""

import json
import os

APP_TITLE = "漢字抜け熟語パズル"

LOGO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo")


def _read_logo(name):
    with open(os.path.join(LOGO_DIR, name), encoding="utf-8") as f:
        return f.read().strip()


TITLE_LOGO_SVG = _read_logo("title.svg")
HEADER_LOGO_SVG = _read_logo("header.svg")

COMMON_CSS = """
.root {
    --bg: #fff;
    --fg: #222;
    --gray-border: #888;
    --gray-bg: #f4f4f4;
    --sub: #666;
    --card-border: #ccc;
    --sel-bg: #fff3b0;
    --sel-border: #e0a800;
    --err: #d33;
    --err-bg: #fee;
    --ok: #16a34a;
    font-family: "Hiragino Sans", "Noto Sans JP", "Yu Gothic", sans-serif;
    color: var(--fg);
}

/* ヘッダー：左にタイトル、右にボタン。画面上部に固定 */
.header { position: sticky; top: 0; z-index: 1; background: var(--bg); padding: 4px 0; }
.title-row { display: flex; justify-content: space-between; align-items: center; height: 32px; margin-bottom: 4px; }
.title { font-size: 18px; font-weight: bold; flex: 1 1 auto; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
/* ヘッダーのロゴ：文字18px相当の大きさ（ロゴの高さ35 × 18/26） */
.title svg { display: block; height: 24.23px; width: auto; }
/* タイトル画面の大きいロゴ：文字26px相当。画面より広いときは縮める */
.title-logo { text-align: center; margin: 24px 0; }
.title-logo svg { display: inline-block; width: 281.54px; max-width: 100%; height: auto; }
.head-buttons { display: flex; gap: 4px; flex: 0 0 auto; }
.hbtn {
    display: inline-flex; align-items: center; gap: 3px;
    font-size: 13px; line-height: 1; padding: 6px 10px 6px 8px; border-radius: 999px;
    border: 1px solid var(--card-border); background: var(--bg); color: var(--fg); font-family: inherit;
}
.hbtn svg { width: 14px; height: 14px; flex: 0 0 auto; }
.hbtn:active { background: var(--gray-bg); }
.hbtn.confirm { border-color: var(--err); color: var(--err); background: var(--err-bg); }
/* 解答画面のボタンは文字が長いので、幅の狭いスマホでは小さくしてタイトルが切れないようにする */
@media (max-width: 400px) {
    .head-buttons.compact .hbtn { font-size: 12px; padding: 6px 7px 6px 4px; gap: 0; }
    .head-buttons.compact .hbtn svg { width: 12px; height: 12px; }
}

.page-heading { font-size: 16px; font-weight: bold; margin: 12px 0 8px; }
.none { font-size: 14px; color: var(--sub); }
.submit {
    margin-top: 16px; width: 100%; font-size: 16px; padding: 10px;
    border-radius: 8px; border: 1px solid var(--gray-border); background: var(--gray-bg); font-family: inherit;
}
.submit:disabled { opacity: 0.5; }

/* 番号マスと熟語カード（問題画面と解答画面で共通） */
.bar { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 2px; }
.box {
    flex: 0 0 auto; width: 48px; height: 60px; border: 2px solid var(--gray-border); border-radius: 8px;
    display: flex; flex-direction: column; align-items: center; justify-content: center; box-sizing: border-box;
}
.box .n { font-size: 12px; color: var(--sub); line-height: 1; }
.warning { color: var(--err); font-size: 14px; min-height: 1.2em; margin-top: 4px; }
/* 熟語は縦に並べてから次の列へ進む（文字数順に並べるので、文字数の多い熟語ほど右の列に来る）。行数は JS で語数から決める */
.grid { display: grid; grid-template-columns: repeat(3, 1fr); grid-auto-flow: column; gap: 8px; margin-top: 6px; }
.word {
    display: flex; justify-content: center; align-items: flex-start; gap: 2px;
    border: 1px solid var(--card-border); border-radius: 8px; padding: 6px 2px 2px; font-size: 22px;
}
.slot { display: flex; flex-direction: column; align-items: center; }
.slot .ch { height: 1.3em; line-height: 1.3em; }
.slot .n { font-size: 10px; color: var(--sub); height: 12px; line-height: 12px; }
.blank {
    width: 1.3em; height: 1.3em; border: 2px solid var(--gray-border); border-radius: 4px; box-sizing: border-box;
    display: flex; align-items: center; justify-content: center; cursor: pointer;
}
"""

# 各画面の JS の先頭に置く共通の関数（export default より前に書く）
COMMON_JS = """
const ICON_HELP = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M6.2 6.2a1.9 1.9 0 1 1 2.6 1.8c-.5.2-.8.6-.8 1.1v.4" stroke-linecap="round"/><circle cx="8" cy="11.6" r=".6" fill="currentColor" stroke="none"/></svg>';
const ICON_BACK = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M10 3.5 5.5 8l4.5 4.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const ICON_HOME = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M2.5 7.5 8 3l5.5 4.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M4 6.5V13h3v-3.5h2V13h3V6.5" stroke-linejoin="round"/></svg>';
const ICON_CHECK = '<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M2.5 6.2 5 8.6l4.5-5" stroke-linecap="round" stroke-linejoin="round"/></svg>';

function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
}

function headerButton(icon, label) {
    const b = el("button", "hbtn");
    b.type = "button";
    b.innerHTML = icon;
    b.appendChild(el("span", null, label));
    return b;
}

// ヘッダーを作る。title があれば左にヘッダー用のロゴを出し、なければ空にする
// buttons は [アイコン, 文字, 押したときの処理] の並び。compact は解答画面用
function makeHeader(title, buttons, compact) {
    const h = el("div", "header");
    const row = el("div", "title-row");
    const titleBox = el("div", "title");
    if (title) titleBox.innerHTML = HEADER_LOGO;
    row.appendChild(titleBox);
    const group = el("div", "head-buttons");
    if (compact) group.classList.add("compact");
    h.buttons = buttons.map(([icon, label, onClick]) => {
        const b = headerButton(icon, label);
        if (onClick) b.addEventListener("click", onClick);
        group.appendChild(b);
        return b;
    });
    row.appendChild(group);
    h.appendChild(row);
    return h;
}
"""

# ロゴの SVG を JS の定数として渡す
COMMON_JS += "\nconst TITLE_LOGO = " + json.dumps(TITLE_LOGO_SVG, ensure_ascii=False) + ";\n"
COMMON_JS += "const HEADER_LOGO = " + json.dumps(HEADER_LOGO_SVG, ensure_ascii=False) + ";\n"

