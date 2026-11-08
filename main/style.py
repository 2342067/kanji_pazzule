import streamlit as st

# 全画面共通：Streamlitのヘッダーを消し、上の余白をなくす。部品同士の間隔も詰める
GLOBAL_CSS = """
header[data-testid="stHeader"] { display: none; }
[data-testid="stMainBlockContainer"] { padding-top: 0; }
[data-testid="stVerticalBlock"] { gap: 0.25rem; }
"""


def apply_style():
    """全画面共通のCSSをページに入れる"""
    st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)
