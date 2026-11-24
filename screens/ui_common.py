"""全画面で共通に使う見た目（CSS）と部品（JS）

各画面の部品（st.components.v2）の CSS と JS の先頭に、ここの内容をつなげて使う。

タイトルロゴは screens/logo の SVG を読み込んで使う（文字は図形に変換済み。フォントの読み込みは不要）
    title.svg  : タイトル画面の大きいロゴ（字間4.5px）
    header.svg : ヘッダーの小さいロゴ（字間0.5px）
    ロゴの文字は currentColor で塗っているので、文字色（--fg）に合わせて表示される。「抜」のマスとピースの青、「抜」の白い字は固定

「遊び方」と「評価実験について」は、今の画面の上に重ねて出す（後ろを暗くし、中央に白いカードを出す）
    文章はこのファイルの GUIDE_HELP と GUIDE_ABOUT に書く。カードを出す部品は JS の openOverlay
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

# ==== 「遊び方」の文章 ====
# rules：ルール、example：例題の図（c は見える漢字、n は空欄の番号）と答え、sections：見出しと箇条書き
GUIDE_HELP = {
    "rules": [
        "熟語の空欄に入る漢字を考えるパズルです",
        "同じ番号の空欄には、同じ漢字が入ります",
        "番号が違えば、入る漢字も違います",
    ],
    "example": {
        "words": [
            [{"n": 2}, {"n": 1}],
            [{"c": "母"}, {"n": 1}],
            [{"c": "入"}, {"n": 2}],
            [{"c": "科"}, {"n": 2}],
        ],
        "answers": {"1": "校", "2": "学"},
    },
    "sections": [
        {
            "heading": "入力のしかた",
            "items": [
                "画面の上に並んだ番号のマスをタップして、漢字を1文字入力します",
                "入力した漢字は、同じ番号の空欄すべてに入ります",
                "熟語の空欄をタップすると、同じ番号のマスと空欄に色が付きます",
                "熟語の空欄を長押しすると、その番号の入力に移ります",
            ],
        },
        {
            "heading": "解答する",
            "items": [
                "「解答する」を押すと、正解数と模範解答が出ます",
                "違う番号に同じ漢字が入っていると、解答できません",
                "未解答があるときは、もう一度押すと解答します",
                "模範解答と違っても、すべての熟語が成り立っていれば正解です（別解）",
            ],
        },
        {
            "heading": "経過時間",
            "items": [
                "右上の時間は、問題を開いてからの時間です",
                "遊び方を開いている間は止まります",
            ],
        },
    ],
}

# ==== 「評価実験について」の文章 ====
# 回答の利用についての文と問い合わせ先は、アンケートのページ（evaluation.py）と同じものを画面側から渡す
GUIDE_ABOUT = {
    "intro": "卒業研究で作った「漢字抜け熟語パズル」を実際に解いてもらい、問題の難しさや使いやすさを調べる実験です。",
    "steps_heading": "流れ",
    "steps": [
        "教科を選び、熟語難度と問題の大きさを選んで、問題を解きます",
        "解答したら、解答の画面の下にある「解答を送信」から、その問題の記録を送ります（1問解くごとに送ります）",
        "解き終わったら、タイトルの画面の「評価実験アンケート」に答えます（最後に1回だけ）",
    ],
    "notes_heading": "お願い",
    "notes": [
        "解答の記録とアンケートは名前で結びつけます。毎回同じ名前を入力してください",
    ],
}

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
/* 押した感：押すと画面が変わるボタン（教科、熟語難度・大きさ、設問の番号、ヘッダー）は、指が触れた瞬間に少し縮めて色を付ける
   .pressed は JS の pressable で付ける。教科・難度・大きさ・設問はロゴの青を薄めた色、ヘッダーは灰色 */
.opt, .qbtn, .hbtn { transition: transform 0.08s, background-color 0.08s; -webkit-tap-highlight-color: transparent; }
.opt.pressed, .qbtn.pressed { transform: scale(0.95); background: #e6f1fb; border-color: #378ADD; color: #185fa5; }
.hbtn.pressed { transform: scale(0.95); background: var(--gray-bg); }
.hbtn.confirm { border-color: var(--err); color: var(--err); background: var(--err-bg); }
/* 解答画面のボタンは文字が長いので、幅の狭いスマホでは小さくしてタイトルが切れないようにする */
@media (max-width: 400px) {
    .head-buttons.compact .hbtn { font-size: 12px; padding: 6px 7px 6px 4px; gap: 0; }
    .head-buttons.compact .hbtn svg { width: 12px; height: 12px; }
}

.page-heading { font-size: 16px; font-weight: bold; margin: 12px 0 8px; }
.none { font-size: 14px; color: var(--sub); }
/* 各画面の主な操作のボタン（次へ、解答する、解答を送信）：ロゴと同じ青で塗る。押せないときは灰色 */
.submit {
    margin-top: 16px; width: 100%; font-size: 16px; padding: 12px; font-family: inherit;
    border-radius: 999px; border: 1px solid #378ADD; background: #378ADD; color: #fff;
    font-weight: bold; letter-spacing: 0.1em;
}
.submit:active { background: #2f77c0; border-color: #2f77c0; }
.submit:disabled { background: var(--gray-bg); border-color: var(--card-border); color: var(--sub); }

/* 番号マスと熟語カード（問題画面と解答画面で共通） */
.question-info { display: flex; justify-content: space-between; align-items: center; font-size: 14px; color: var(--sub); margin-bottom: 4px; }
.timer { display: inline-flex; align-items: center; gap: 3px; font-variant-numeric: tabular-nums; }
.timer svg { width: 14px; height: 14px; }
.bar { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 2px; }
.box {
    flex: 0 0 auto; width: 48px; height: 60px; border: 2px solid var(--gray-border); border-radius: 8px;
    display: flex; flex-direction: column; align-items: center; justify-content: center; box-sizing: border-box;
}
.box .n { font-size: 12px; color: var(--sub); line-height: 1; }
.warning { color: var(--err); font-size: 14px; min-height: 1.2em; margin-top: 4px; white-space: pre-line; }
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
    line-height: 1;   /* 行の高さを決めておかないと、フォントによって四角の中の文字が上に寄る */
}

/* 重ねて出す画面（遊び方、評価実験について）：後ろを暗くし、中央に白いカードを出す。長いときはカードの中をスクロールする */
.overlay {
    position: fixed; inset: 0; z-index: 1000; background: rgba(0, 0, 0, 0.45);
    display: flex; align-items: center; justify-content: center; padding: 16px; box-sizing: border-box;
}
.overlay-card {
    background: var(--bg); color: var(--fg); border-radius: 12px; width: 100%; max-width: 420px; max-height: 100%;
    display: flex; flex-direction: column; box-shadow: 0 8px 28px rgba(0, 0, 0, 0.25);
}
.overlay-head { display: flex; justify-content: space-between; align-items: center; padding: 12px 10px 8px 16px; font-size: 16px; font-weight: bold; }
.overlay-close {
    width: 32px; height: 32px; border-radius: 50%; border: none; background: transparent; color: var(--sub);
    display: flex; align-items: center; justify-content: center; padding: 0;
}
.overlay-close svg { width: 16px; height: 16px; }
.overlay-close:active { background: var(--gray-bg); }
.overlay-body { overflow-y: auto; overscroll-behavior: contain; padding: 0 16px; font-size: 14px; line-height: 1.7; }
.overlay-foot { padding: 12px 16px 16px; }
.overlay-ok {
    width: 100%; font-size: 14px; padding: 8px; font-family: inherit; border-radius: 999px;
    border: 1px solid #378ADD; background: var(--bg); color: #185fa5;
}
.overlay-ok:active { background: #e6f1fb; }
.guide-heading { font-size: 14px; font-weight: bold; color: #185fa5; margin: 14px 0 2px; }
.guide-heading:first-child { margin-top: 0; }
.guide-text { margin: 0; }
.guide-list { margin: 0; padding-left: 1.3em; }
.guide-list li { margin: 2px 0; }
.guide-small { font-size: 12px; color: var(--sub); margin: 14px 0 0; }
/* 遊び方の例題の図：上に問題、下に答えを入れた形を出す
   熟語カードは問題画面と同じ部品・同じ大きさ（.word、.slot、.blank）をそのまま使い、字の大きさや位置は変えない
   答えを入れた空欄は、問題画面で選んだ番号と同じ黄色にする */
.example { border: 1px solid var(--card-border); border-radius: 8px; padding: 8px 10px 10px; margin: 8px 0 0; }
.example-label { font-size: 12px; color: var(--sub); line-height: 1.4; }
.example-words { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin: 4px 0 8px; line-height: normal; }
.example-words:last-child { margin-bottom: 0; }
.example .blank { cursor: default; }
.example .blank.filled { background: var(--sel-bg); border-color: var(--sel-border); }
"""

# 各画面の JS の先頭に置く共通の関数（export default より前に書く）
COMMON_JS = """
const ICON_HELP = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M6.2 6.2a1.9 1.9 0 1 1 2.6 1.8c-.5.2-.8.6-.8 1.1v.4" stroke-linecap="round"/><circle cx="8" cy="11.6" r=".6" fill="currentColor" stroke="none"/></svg>';
const ICON_INFO = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M8 7.2v4" stroke-linecap="round"/><circle cx="8" cy="4.8" r=".6" fill="currentColor" stroke="none"/></svg>';
const ICON_BACK = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M10 3.5 5.5 8l4.5 4.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const ICON_HOME = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M2.5 7.5 8 3l5.5 4.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M4 6.5V13h3v-3.5h2V13h3V6.5" stroke-linejoin="round"/></svg>';
const ICON_TIMER = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="8" cy="9" r="5.5"/><path d="M6.5 1.5h3M8 1.5v2M8 6v3" stroke-linecap="round"/></svg>';
const ICON_CLOSE = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M3.5 3.5l9 9M12.5 3.5l-9 9" stroke-linecap="round"/></svg>';
const ICON_CHECK = '<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M2.5 6.2 5 8.6l4.5-5" stroke-linecap="round" stroke-linejoin="round"/></svg>';

function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
}

// 秒数を 分:秒（例：00:01）の形にする
function formatTime(seconds) {
    const s = Math.max(0, Math.floor(seconds));
    return String(Math.floor(s / 60)).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0");
}

// 問題の情報の行：左に問題の情報、右端にストップウォッチのマークと経過時間
// 経過時間の文字は row.time で書き換えられる
function makeQuestionInfo(info, seconds) {
    const row = el("div", "question-info");
    row.appendChild(el("span", null, info || ""));
    const timer = el("span", "timer");
    timer.innerHTML = ICON_TIMER;
    row.time = el("span", null, formatTime(seconds));
    timer.appendChild(row.time);
    row.appendChild(timer);
    return row;
}

// 押した感を付ける。指（またはマウス）が触れた瞬間に .pressed を付け、離したら外す
// iPhone の Safari では CSS の :active が効かないことがあるので、JS で付ける
// 素早く押したときも見えるよう、付けてから最低 120ms は残す。スクロールで指が動いたとき（pointercancel）も外す
// keep が true のボタンは、押したら次の画面に切り替わるまで .pressed を残す（画面を作り直すと消える）
function pressable(b, keep) {
    let since = 0;
    let held = false;
    const release = () => {
        if (held) return;
        const wait = Math.max(0, 120 - (Date.now() - since));
        setTimeout(() => { if (!held) b.classList.remove("pressed"); }, wait);
    };
    b.addEventListener("pointerdown", () => {
        since = Date.now();
        b.classList.add("pressed");
    });
    b.addEventListener("pointerup", release);
    b.addEventListener("pointercancel", release);
    b.addEventListener("pointerleave", release);
    if (keep) {
        b.addEventListener("click", () => {
            held = true;
            b.classList.add("pressed");
        });
    }
    return b;
}

// ヘッダーのボタン。押した感を付ける（「戻る」の確認や遊び方のように画面が変わらないこともあるので、離したら外す）
function headerButton(icon, label) {
    const b = el("button", "hbtn");
    b.type = "button";
    b.innerHTML = icon;
    b.appendChild(el("span", null, label));
    pressable(b, false);
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

// 今の画面の上に重ねてカードを出す。右上の×、下の「閉じる」、カードの外（暗い部分）のどれかを押すと閉じる
// body はカードの中身、onClose は閉じたときの処理（なくてもよい）
function openOverlay(root, title, body, onClose) {
    const overlay = el("div", "overlay");
    const card = el("div", "overlay-card");
    card.setAttribute("role", "dialog");
    card.setAttribute("aria-modal", "true");
    card.setAttribute("aria-label", title);
    const close = () => {
        overlay.remove();
        if (onClose) onClose();
    };

    const head = el("div", "overlay-head");
    head.appendChild(el("span", null, title));
    const x = el("button", "overlay-close");
    x.type = "button";
    x.innerHTML = ICON_CLOSE;
    x.setAttribute("aria-label", "閉じる");
    x.addEventListener("click", close);
    head.appendChild(x);
    card.appendChild(head);

    const bodyBox = el("div", "overlay-body");
    bodyBox.appendChild(body);
    card.appendChild(bodyBox);

    const foot = el("div", "overlay-foot");
    const ok = el("button", "overlay-ok", "閉じる");
    ok.type = "button";
    ok.addEventListener("click", close);
    foot.appendChild(ok);
    card.appendChild(foot);

    overlay.appendChild(card);
    overlay.addEventListener("click", (e) => { if (e.target === overlay) close(); });
    root.appendChild(overlay);
}

// 見出しと箇条書き（ordered が true なら番号付き）を box に足す
function addGuideList(box, heading, items, ordered) {
    if (heading) box.appendChild(el("div", "guide-heading", heading));
    const list = el(ordered ? "ol" : "ul", "guide-list");
    items.forEach((text) => list.appendChild(el("li", null, text)));
    box.appendChild(list);
}

// 例題の熟語を並べる。作り方は問題画面の熟語と同じ。answers があれば空欄に答えの漢字を入れる
function exampleWords(words, answers) {
    const row = el("div", "example-words");
    words.forEach((w) => {
        const word = el("div", "word");
        w.forEach((ch) => {
            const slot = el("div", "slot");
            const num = el("span", "n");
            if (ch.n !== undefined) {
                const blank = el("span", "blank", answers ? answers[String(ch.n)] : "");
                if (answers) blank.classList.add("filled");
                slot.appendChild(blank);
                num.textContent = ch.n;
            } else {
                slot.appendChild(el("span", "ch", ch.c));
            }
            slot.appendChild(num);
            word.appendChild(slot);
        });
        row.appendChild(word);
    });
    return row;
}

// 「遊び方」の中身：ルール、例題の図、操作の説明
function helpBody() {
    const box = el("div");
    addGuideList(box, "ルール", GUIDE_HELP.rules, false);
    const example = el("div", "example");
    example.appendChild(el("div", "example-label", "例題"));
    example.appendChild(exampleWords(GUIDE_HELP.example.words, null));
    const answers = GUIDE_HELP.example.answers;
    const answerText = Object.keys(answers).map((n) => n + "は「" + answers[n] + "」").join("、");
    example.appendChild(el("div", "example-label", "答え（" + answerText + "）"));
    example.appendChild(exampleWords(GUIDE_HELP.example.words, answers));
    box.appendChild(example);
    GUIDE_HELP.sections.forEach((section) => addGuideList(box, section.heading, section.items, false));
    return box;
}

// 「評価実験について」の中身：説明、流れ、お願い、回答の利用について、問い合わせ先
// extra は { consent_title, consent, contact }（アンケートのページと同じ文を画面側から渡す）
function aboutBody(extra) {
    const box = el("div");
    box.appendChild(el("p", "guide-text", GUIDE_ABOUT.intro));
    addGuideList(box, GUIDE_ABOUT.steps_heading, GUIDE_ABOUT.steps, true);
    addGuideList(box, GUIDE_ABOUT.notes_heading, GUIDE_ABOUT.notes, false);
    box.appendChild(el("div", "guide-heading", extra.consent_title));
    box.appendChild(el("p", "guide-text", extra.consent));
    if (extra.contact) box.appendChild(el("p", "guide-small", "問い合わせ先：" + extra.contact));
    return box;
}
"""

# ロゴの SVG を JS の定数として渡す
COMMON_JS += "\nconst TITLE_LOGO = " + json.dumps(TITLE_LOGO_SVG, ensure_ascii=False) + ";\n"
# 「遊び方」「評価実験について」の文章を JS の定数として渡す
COMMON_JS += "const GUIDE_HELP = " + json.dumps(GUIDE_HELP, ensure_ascii=False) + ";\n"
COMMON_JS += "const GUIDE_ABOUT = " + json.dumps(GUIDE_ABOUT, ensure_ascii=False) + ";\n"
COMMON_JS += "const HEADER_LOGO = " + json.dumps(HEADER_LOGO_SVG, ensure_ascii=False) + ";\n"

