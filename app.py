import sqlite3
import os
from datetime import datetime

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = "優しく寄り添うカウンセラーとして、入力された出来事をポジティブな視点で言い換えてください。元の気持ちを否定せず、同じ出来事の別の見方や、そこから得られる気づきを温かい言葉で伝えてください。"

DB_PATH = "data/diary.db"
PERSONA_PATH = "data/persona.md"


def load_persona() -> str:
    if os.path.exists(PERSONA_PATH):
        with open(PERSONA_PATH, encoding="utf-8") as f:
            return f.read().strip()
    return ""


def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS diary (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            date      TEXT NOT NULL,
            original  TEXT NOT NULL,
            positive  TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_diary(original: str, positive: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO diary (date, original, positive) VALUES (?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M"), original, positive),
    )
    conn.commit()
    conn.close()


def load_history() -> list[tuple]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT date, original, positive FROM diary ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return rows


def update_persona(diary_text: str, client: OpenAI):
    if not os.path.exists(PERSONA_PATH):
        return

    with open(PERSONA_PATH, encoding="utf-8") as f:
        current = f.read()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "日記の内容を読み、その人物の状況・感情・出来事を1行（40文字以内）で要約してください。"
                    "「- 」で始まる箇条書き1行のみを返してください。余計な説明は不要です。"
                ),
            },
            {"role": "user", "content": diary_text},
        ],
        temperature=0.3,
    )
    new_line = response.choices[0].message.content.strip()

    today = datetime.now().strftime("%Y-%m-%d")
    entry = f"- {today}：{new_line.lstrip('- ')}"

    updated = current.replace(
        "## 最近の出来事",
        f"## 最近の出来事\n{entry}",
    )
    with open(PERSONA_PATH, "w", encoding="utf-8") as f:
        f.write(updated)


def convert_to_positive(text: str, client: OpenAI) -> str:
    persona = load_persona()
    system_content = SYSTEM_PROMPT
    if persona:
        system_content += f"\n\n以下はこの日記を書いている人物のプロフィールです。必ずこの人物像を踏まえた上で、具体的な状況に寄り添った返答をしてください。\n\n{persona}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": text},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content


init_db()

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
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                positive_text = convert_to_positive(diary_input, client)
                save_diary(diary_input, positive_text)
                update_persona(diary_input, client)

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

# --- 過去の変換履歴 ---
st.divider()
st.subheader("📖 過去の変換履歴")

history = load_history()

if not history:
    st.caption("まだ履歴がありません。変換するとここに記録されます。")
else:
    for date, original, positive in history:
        with st.expander(f"🗓 {date}　{original[:30]}{'…' if len(original) > 30 else ''}"):
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown("**📝 元の日記**")
                st.info(original)
            with col_right:
                st.markdown("**🌟 ポジティブに変換**")
                st.success(positive)
