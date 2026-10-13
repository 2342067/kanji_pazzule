import streamlit as st

# Streamlitのヘッダーを消し、上の余白を詰める
st.markdown("""
<style>
header[data-testid="stHeader"] { display: none; }
[data-testid="stMainBlockContainer"] { padding-top: 0; }
[data-testid="stVerticalBlock"] { gap: 0.25rem; }
</style>
""", unsafe_allow_html=True)

# テスト用の問題（21語）。"n" が空欄の番号、"c" が表示する漢字
WORDS = [
    [{"n": 1}, {"c": "池"}],
    [{"n": 1}, {"n": 2}],
    [{"c": "天"}, {"n": 2}],
    [{"n": 2}, {"c": "分"}],
    [{"c": "大"}, {"n": 3}, {"n": 4}],
    [{"n": 3}, {"c": "校"}],
    [{"n": 3}, {"n": 4}],
    [{"n": 4}, {"c": "活"}],
    [{"c": "大"}, {"n": 3}, {"c": "教"}, {"c": "授"}],
    [{"n": 5}, {"c": "道"}],
    [{"c": "海"}, {"n": 5}],
    [{"n": 5}, {"n": 6}, {"c": "発"}, {"n": 1}],
    [{"n": 1}, {"n": 6}],
    [{"n": 1}, {"n": 2}, {"c": "分"}, {"c": "解"}],
    [{"n": 6}, {"n": 3}],
    [{"n": 1}, {"c": "車"}],
    [{"n": 2}, {"c": "温"}],
    [{"n": 4}, {"c": "物"}],
    [{"n": 5}, {"c": "泳"}],
    [{"n": 3}, {"n": 6}],
    [{"n": 6}, {"c": "士"}],
]
ANSWER_KEY = {"1": "電", "2": "気", "3": "学", "4": "生", "5": "水", "6": "力"}

# 文字数の少ない順に並べる（同じ文字数なら元の順）
WORDS = sorted(WORDS, key=len)

HTML = '<div class="root"></div>'

CSS = """
.root { font-family: "Hiragino Sans", "Noto Sans JP", "Yu Gothic", sans-serif; }
.header {
    position: sticky; top: 0; z-index: 1;
    background: #fff; padding: 4px 0; border-bottom: 1px solid #ddd;
}
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
        parentElement.puzzleState = { answers: {}, drafts: {}, selected: null, warning: "" };
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

    // 上の解答欄：四角そのものが入力欄
    numbers.forEach((n) => {
        const box = document.createElement("div");
        box.className = "box";
        box.dataset.num = n;
        box.innerHTML = '<span class="n"></span><input autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" enterkeyhint="done">';
        box.querySelector(".n").textContent = n;
        const input = box.querySelector("input");
        input.addEventListener("focus", () => select(n));
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
                blank.addEventListener("click", () => select(ch.n));
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
    }

    function select(n) {
        state.selected = n;
        state.warning = "";
        render();
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
        render();
    }

    // 解答するボタン：全番号の値をまとめてPythonに送る
    submitButton.addEventListener("click", () => {
        setTriggerValue("submit", { answers: state.answers, drafts: state.drafts });
    });

    render();
}
"""

puzzle = st.components.v2.component("puzzle_test", html=HTML, css=CSS, js=JS)

result = puzzle(key="puzzle", data={"words": WORDS}, on_submit_change=lambda: None)

if result.submit is not None:
    st.session_state.submitted = result.submit

submitted = st.session_state.get("submitted")
if submitted:
    st.write("Pythonが受け取った値：", submitted)
    for n, correct in ANSWER_KEY.items():
        given = submitted["answers"].get(n, "")
        mark = "○" if given == correct else "×"
        st.write(f"{n}番：{given or '（未入力）'} {mark}")
