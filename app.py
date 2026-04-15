import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

SYSTEM_PROMPT = "優しく寄り添うカウンセラーとして、入力された出来事をポジティブな視点で言い換えてください。元の気持ちを否定せず、同じ出来事の別の見方や、そこから得られる気づきを温かい言葉で伝えてください。"


def convert_to_positive(text: str) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content


st.set_page_config(
    page_title="ポジティブ日記",
    page_icon="✨",
    layout="centered",
)

st.title("✨ ポジティブ日記")
st.caption("今日あったことをそのまま書いてみてください。ポジティブな視点に変換します。")

st.divider()

diary_input = st.text_area(
    "今日あったこと",
    placeholder="例：仕事でミスをしてしまい、上司に注意された。落ち込んでいる。",
    height=180,
    label_visibility="visible",
)

convert_btn = st.button("変換する ✨", type="primary", use_container_width=True)

if convert_btn:
    if not diary_input.strip():
        st.warning("テキストを入力してください。")
    elif not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY が設定されていません。.env ファイルを確認してください。")
    else:
        with st.spinner("変換中..."):
            try:
                positive_text = convert_to_positive(diary_input)

                st.divider()
                col_left, col_right = st.columns(2)

                with col_left:
                    st.subheader("📝 元の日記")
                    st.info(diary_input)

                with col_right:
                    st.subheader("🌟 ポジティブに変換")
                    st.success(positive_text)

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
