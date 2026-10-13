import streamlit as st

st.title("漢字入力テスト")

HTML = """
<div class="puzzle">
  <div class="word">電<input class="cell" data-num="1" data-id="a"><span class="num">1</span></div>
  <div class="word"><input class="cell" data-num="1" data-id="b"><span class="num">1</span>池</div>
  <div class="word"><input class="cell" data-num="2" data-id="c"><span class="num">2</span>気</div>
</div>
<button class="submit">解答する</button>
<div class="log"></div>
"""

CSS = """
.puzzle { display: flex; flex-direction: column; gap: 12px; }
.word { font-size: 28px; display: flex; align-items: center; gap: 4px; }
.cell {
    width: 2em; height: 2em; font-size: 28px; text-align: center;
    border: 2px solid #888; border-radius: 6px;
}
.cell.error { border-color: #d33; background: #fee; }
.num { font-size: 14px; color: #666; }
.submit { margin-top: 16px; font-size: 18px; padding: 10px 24px; border-radius: 8px; }
.log { margin-top: 12px; font-size: 12px; color: #444; white-space: pre-wrap; max-height: 12em; overflow: auto; }
"""

JS = """
export default function(component) {
    const { parentElement, setTriggerValue } = component;
    const cells = parentElement.querySelectorAll(".cell");
    const button = parentElement.querySelector(".submit");
    const log = parentElement.querySelector(".log");

    function addLog(text) {
        log.textContent = text + "\\n" + log.textContent;
    }

    function collect() {
        const answers = {};
        cells.forEach((c) => { answers[c.dataset.id] = c.value; });
        return answers;
    }

    // マスから離れたときに、同じ番号のマスへ反映する
    function commit(cell) {
        const value = cell.value;
        cells.forEach((other) => {
            if (other.dataset.num === cell.dataset.num) {
                other.value = value;
                other.classList.toggle("error", value.length > 1);
            }
        });
        addLog("確定: [" + value + "]");
    }

    cells.forEach((cell) => {
        cell.setAttribute("autocomplete", "off");
        cell.setAttribute("autocorrect", "off");
        cell.setAttribute("autocapitalize", "off");
        cell.setAttribute("spellcheck", "false");

        cell.addEventListener("input", () => addLog("input: [" + cell.value + "]"));
        cell.addEventListener("change", () => commit(cell));
    });

    // 解答するボタンで、全マスの値をまとめてPythonに送る
    button.addEventListener("click", () => {
        const answers = collect();
        addLog("送信: " + JSON.stringify(answers));
        setTriggerValue("submit", answers);
    });
}
"""

puzzle_input = st.components.v2.component("puzzle_input_test", html=HTML, css=CSS, js=JS)

result = puzzle_input(key="custom", on_submit_change=lambda: None)

if result.submit is not None:
    st.session_state.submitted = result.submit

st.write("Pythonが受け取った値：", st.session_state.get("submitted"))