import streamlit as st
from screens.ui_common import COMMON_CSS, COMMON_JS

HTML = '<div class="root"></div>'

CSS = COMMON_CSS + """
.box input {
    width: 100%; border: none; background: transparent; outline: none;
    font-size: 24px; text-align: center; padding: 0; font-family: inherit; color: var(--fg);
}
.box.selected { background: var(--sel-bg); border-color: var(--sel-border); }
.box.error { border-color: var(--err); background: var(--err-bg); }
.box.error input { color: var(--err); font-size: 16px; }
.blank.selected { background: var(--sel-bg); border-color: var(--sel-border); }
"""

JS = COMMON_JS + """
export default function(component) {
    const { parentElement, data, setTriggerValue } = component;
    const root = parentElement.querySelector(".root");

    // 再実行されても入力を失わないよう、状態は parentElement に持たせる
    if (!parentElement.puzzleState) {
        parentElement.puzzleState = { answers: {}, drafts: {}, selected: null, warning: "", confirm: false, backConfirm: false };
    }
    const state = parentElement.puzzleState;

    const words = data.words;
    const numbers = [];
    words.forEach((w) => w.forEach((ch) => {
        if (ch.n !== undefined && !numbers.includes(ch.n)) numbers.push(ch.n);
    }));
    numbers.sort((a, b) => a - b);

    root.innerHTML = "";
    // ヘッダー：右に「遊び方」（遊び方画面は未作成。押しても何も起きない）と「戻る」
    const header = makeHeader(data.title || "", [[ICON_BACK, "戻る", null], [ICON_HELP, "遊び方", null]], false);
    const backButton = header.buttons[0];
    const bar = el("div", "bar");
    const warning = el("div", "warning");
    header.appendChild(bar);
    header.appendChild(warning);
    root.appendChild(header);
    const grid = el("div", "grid");
    grid.style.gridTemplateRows = "repeat(" + Math.ceil(words.length / 3) + ", auto)";
    root.appendChild(grid);
    const submitButton = el("button", "submit", "解答する");
    submitButton.type = "button";
    root.appendChild(submitButton);

    // 上の解答欄：四角そのものが入力欄
    numbers.forEach((n) => {
        const box = document.createElement("div");
        box.className = "box";
        box.dataset.num = n;
        box.innerHTML = '<span class="n"></span><input autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" enterkeyhint="done">';
        box.querySelector(".n").textContent = n;
        const input = box.querySelector("input");
        input.addEventListener("focus", () => select(n));
        // 選択中の番号の四角をもう一度タップしたら、ハイライトを消す（キーボードは出さない）
        // 入力中（その四角にカーソルがあるとき）は、何もせず入力を続けられるようにする
        const deselect = (e) => {
            if (String(state.selected) !== String(n)) return;
            if (document.activeElement === input || parentElement.activeElement === input) return;
            e.preventDefault();
            state.selected = null;
            state.warning = "";
            state.confirm = false;
            state.backConfirm = false;
            render();
        };
        box.addEventListener("touchstart", deselect, { passive: false });
        box.addEventListener("mousedown", deselect);
        input.addEventListener("blur", () => check(n, input.value));
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.isComposing) input.blur();
        });
        bar.appendChild(box);
    });

    // 問題（熟語）：空欄の番号は四角の下に出す
    words.forEach((w) => {
        const word = el("div", "word");
        w.forEach((ch) => {
            const slot = el("div", "slot");
            const num = el("span", "n");
            if (ch.n !== undefined) {
                const blank = el("span", "blank");
                blank.dataset.num = ch.n;
                blank.addEventListener("click", () => toggle(ch.n));
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

    function render() {
        root.querySelectorAll(".box").forEach((box) => {
            const n = box.dataset.num;
            const input = box.querySelector("input");
            if (document.activeElement !== input && parentElement.activeElement !== input) {
                input.value = state.answers[n] || state.drafts[n] || "";
            }
            box.classList.toggle("error", state.drafts[n] !== undefined);
            box.classList.toggle("selected", String(state.selected) === n);
        });
        root.querySelectorAll(".blank").forEach((blank) => {
            const n = blank.dataset.num;
            blank.textContent = state.answers[n] || "";
            blank.classList.toggle("selected", String(state.selected) === n);
        });
        const hasError = Object.keys(state.drafts).length > 0;
        warning.textContent = state.warning || (hasError ? "漢字1文字で入力してください" : "");
        backButton.classList.toggle("confirm", state.backConfirm);
    }

    function select(n) {
        state.selected = n;
        state.warning = "";
        state.confirm = false;
        state.backConfirm = false;
        render();
    }

    // 問題側の空欄：同じ番号をもう一度タップしたらハイライトを消す
    function toggle(n) {
        if (String(state.selected) === String(n)) {
            state.selected = null;
            state.warning = "";
            state.confirm = false;
            state.backConfirm = false;
            render();
        } else {
            select(n);
        }
    }

    // 入力状態から戻ったときにチェックする
    function check(n, raw) {
        const key = String(n);
        const value = raw.trim();
        if (value === "") {
            delete state.answers[key];
            delete state.drafts[key];
        } else if (/^\\p{Script=Han}$/u.test(value)) {
            state.answers[key] = value;
            delete state.drafts[key];
        } else {
            delete state.answers[key];
            state.drafts[key] = value;
        }
        state.warning = "";
        state.confirm = false;
        state.backConfirm = false;
        render();
    }

    // 解答するボタン
    submitButton.addEventListener("click", () => {
        state.backConfirm = false;
        // 漢字1文字でない入力が残っている間は解答させない
        if (Object.keys(state.drafts).length > 0) {
            state.warning = "漢字1文字で入力してください";
            state.confirm = false;
            render();
            return;
        }
        // 未回答があれば1回目は警告だけ出し、もう一度押したら解答する
        const empty = numbers.filter((n) => !state.answers[String(n)]);
        if (empty.length > 0 && !state.confirm) {
            state.confirm = true;
            state.warning = "未回答があります（" + empty.join("、") + "番）。もう一度押すと解答します";
            render();
            return;
        }
        state.confirm = false;
        setTriggerValue("submit", { answers: state.answers });
    });

    // 戻るボタン：入力があるときは、1回目は警告だけ出し、もう一度押したら問題選択に戻る
    // 何も入力していないときは、警告なしですぐ戻る
    backButton.addEventListener("click", () => {
        const hasInput = Object.keys(state.answers).length > 0 || Object.keys(state.drafts).length > 0;
        if (hasInput && !state.backConfirm) {
            state.backConfirm = true;
            state.confirm = false;
            state.warning = "入力は消えます。もう一度押すと戻ります";
            render();
            return;
        }
        state.backConfirm = false;
        setTriggerValue("back", true);
    });

    render();
}
"""

puzzle = st.components.v2.component("kanji_puzzle", html=HTML, css=CSS, js=JS)
