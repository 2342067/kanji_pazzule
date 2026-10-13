import streamlit as st

HTML = '<div class="root"></div>'

CSS = """
.root { font-family: "Hiragino Sans", "Noto Sans JP", "Yu Gothic", sans-serif; }
.header {
    position: sticky; top: 0; z-index: 1;
    background: #fff; padding: 4px 0; border-bottom: 1px solid #ddd;
}
.title-row { display: flex; justify-content: space-between; align-items: center; height: 32px; margin-bottom: 4px; }
.title { font-size: 18px; font-weight: bold; }
.back { font-size: 14px; padding: 4px 12px; border-radius: 6px; border: 1px solid #888; background: #f4f4f4; }
.back.confirm { border-color: #d33; color: #d33; background: #fee; }
.bar { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 2px; }
.box {
    flex: 0 0 auto; width: 48px; height: 60px; border: 2px solid #888; border-radius: 8px;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.box .n { font-size: 12px; color: #666; line-height: 1; }
.box input {
    width: 100%; border: none; background: transparent; outline: none;
    font-size: 24px; text-align: center; padding: 0; font-family: inherit;
}
.box.selected { background: #fff3b0; border-color: #e0a800; }
.box.error { border-color: #d33; background: #fee; }
.box.error input { color: #d33; font-size: 16px; }
.warning { color: #d33; font-size: 14px; min-height: 1.2em; margin-top: 4px; }
.grid {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 6px;
}
.word {
    display: flex; justify-content: center; align-items: flex-start; gap: 2px;
    border: 1px solid #ccc; border-radius: 8px; padding: 6px 2px 2px; font-size: 22px;
}
.slot { display: flex; flex-direction: column; align-items: center; }
.slot .ch { height: 1.3em; line-height: 1.3em; }
.slot .n { font-size: 10px; color: #666; height: 12px; line-height: 12px; }
.blank {
    width: 1.3em; height: 1.3em; border: 2px solid #888; border-radius: 4px; box-sizing: border-box;
    display: flex; align-items: center; justify-content: center; cursor: pointer;
}
.blank.selected { background: #fff3b0; border-color: #e0a800; }
.submit {
    margin-top: 16px; width: 100%; font-size: 16px; padding: 10px;
    border-radius: 8px; border: 1px solid #888; background: #f4f4f4;
}
"""

JS = """
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

    root.innerHTML = `
        <div class="header">
            <div class="title-row">
                <div class="title"></div>
                <button class="back">戻る</button>
            </div>
            <div class="bar"></div>
            <div class="warning"></div>
        </div>
        <div class="grid"></div>
        <button class="submit">解答する</button>
    `;
    const bar = root.querySelector(".bar");
    const grid = root.querySelector(".grid");
    const warning = root.querySelector(".warning");
    const submitButton = root.querySelector(".submit");
    const backButton = root.querySelector(".back");
    root.querySelector(".title").textContent = data.title || "";

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
        const word = document.createElement("div");
        word.className = "word";
        w.forEach((ch) => {
            const slot = document.createElement("div");
            slot.className = "slot";
            const num = document.createElement("span");
            num.className = "n";
            if (ch.n !== undefined) {
                const blank = document.createElement("span");
                blank.className = "blank";
                blank.dataset.num = ch.n;
                blank.addEventListener("click", () => toggle(ch.n));
                slot.appendChild(blank);
                num.textContent = ch.n;
            } else {
                const span = document.createElement("span");
                span.className = "ch";
                span.textContent = ch.c;
                slot.appendChild(span);
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
