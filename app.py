import sqlite3
import os
from datetime import datetime, timedelta

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from streamlit_calendar import calendar

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


def save_diary(original: str, positive: str, save_date: str = None):
    if save_date is None:
        save_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO diary (date, original, positive) VALUES (?, ?, ?)",
        (save_date, original, positive),
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


def load_diary_dates() -> list[str]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT DISTINCT substr(date, 1, 10) FROM diary ORDER BY 1"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def load_history_by_date(date_str: str) -> list[tuple]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT date, original, positive FROM diary WHERE substr(date, 1, 10) = ? ORDER BY id DESC",
        (date_str,),
    ).fetchall()
    conn.close()
    return rows


def load_history_by_week(start_date: str, end_date: str) -> list[tuple]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT date, original, positive FROM diary "
        "WHERE substr(date, 1, 10) >= ? AND substr(date, 1, 10) <= ? ORDER BY id ASC",
        (start_date, end_date),
    ).fetchall()
    conn.close()
    return rows


def generate_weekly_review(entries: list[tuple], client: OpenAI) -> str:
    persona = load_persona()
    entries_text = "\n\n".join(
        f"【{d}】\n{orig}\n→ {pos}" for d, orig, pos in entries
    )
    system_content = (
        "優しく寄り添うカウンセラーとして、今週の日記を読んで、"
        "優しく寄り添うトーンで200字程度の振り返りコメントをしてください。"
    )
    if persona:
        system_content += f"\n\n以下はこの日記を書いている人物のプロフィールです。\n\n{persona}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"今週の日記です：\n\n{entries_text}"},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content


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

# --- セッションステート初期化 ---
if "writing_date" not in st.session_state:
    st.session_state.writing_date = datetime.now().date()
if "calendar_selected_date" not in st.session_state:
    st.session_state.calendar_selected_date = None
if "last_conversion" not in st.session_state:
    st.session_state.last_conversion = None
if "weekly_review" not in st.session_state:
    st.session_state.weekly_review = None
if "weekly_review_date" not in st.session_state:
    st.session_state.weekly_review_date = None

st.set_page_config(
    page_title="ポジティブ日記",
    page_icon="📔",
    layout="centered",
)

# --- カスタムCSS ---
st.markdown("""
<style>
    .block-container {
        padding-top: 3rem;
        padding-bottom: 4rem;
        max-width: 780px;
    }
    h1 {
        font-weight: 600;
        letter-spacing: -0.03em;
        margin-bottom: 0.25rem;
    }
    h2 {
        font-weight: 500;
        letter-spacing: -0.01em;
        margin-top: 0;
        margin-bottom: 0.5rem;
    }
    .stTextArea textarea {
        font-size: 0.95rem;
        line-height: 1.7;
    }
    .stExpander {
        border: none !important;
        border-bottom: 1px solid rgba(49, 51, 63, 0.1) !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

st.title("ポジティブ日記")
st.caption("今日のできごとを書いてみてください。別の視点からリフレーミングします。")

st.write("")

# --- 記録日付の選択 ---
today = datetime.now().date()


def _reset_to_today():
    today_ = datetime.now().date()
    st.session_state.writing_date = today_
    st.session_state["date_picker"] = today_


col_date, col_reset = st.columns([3, 1])
with col_date:
    selected_write_date = st.date_input(
        "記録する日付",
        value=st.session_state.writing_date,
        max_value=today,
        key="date_picker",
    )
    st.session_state.writing_date = selected_write_date
with col_reset:
    st.write("")
    if selected_write_date != today:
        st.button("今日に戻す", use_container_width=True, on_click=_reset_to_today)

if selected_write_date != today:
    st.info(f"**{selected_write_date.strftime('%Y年%m月%d日')}** の日記として記録します")

st.write("")

diary_input = st.text_area(
    "あったこと",
    placeholder="例：仕事でミスをしてしまい、上司に注意された。落ち込んでいる。",
    height=180,
    label_visibility="visible",
)

st.write("")

convert_btn = st.button("変換する", type="primary", use_container_width=True)

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
                save_date_str = st.session_state.writing_date.strftime("%Y-%m-%d") + " " + datetime.now().strftime("%H:%M")
                save_diary(diary_input, positive_text, save_date_str)
                update_persona(diary_input, client)
                st.session_state.last_conversion = {
                    "original": diary_input,
                    "positive": positive_text,
                }
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# 変換結果
if st.session_state.last_conversion:
    result = st.session_state.last_conversion
    st.write("")
    st.divider()
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("今日のできごと")
        st.info(result["original"])
    with col_right:
        st.subheader("今日のリフレーミング")
        st.success(result["positive"])

# --- 週次振り返り（土曜日のみ）---
if today.weekday() == 5:
    days_since_sunday = (today.weekday() + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)
    week_entries = load_history_by_week(
        week_start.strftime("%Y-%m-%d"),
        today.strftime("%Y-%m-%d"),
    )
    if week_entries and os.getenv("OPENAI_API_KEY"):
        st.write("")
        st.divider()
        st.subheader("今週のあなたへ")
        st.caption(f"{week_start.strftime('%-m/%-d')}（日）〜 {today.strftime('%-m/%-d')}（土）")
        st.write("")

        if st.session_state.weekly_review_date != today or st.session_state.weekly_review is None:
            with st.spinner("今週の振り返りを生成中..."):
                try:
                    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    review = generate_weekly_review(week_entries, client)
                    st.session_state.weekly_review = review
                    st.session_state.weekly_review_date = today
                except Exception as e:
                    st.error(f"振り返りの生成に失敗しました: {e}")

        if st.session_state.weekly_review:
            st.success(st.session_state.weekly_review)

# --- カレンダー ---
st.write("")
st.divider()
st.subheader("カレンダー")
st.caption("日記のある日は緑色で表示されます。日付をクリックするとその日の記録を確認できます。")
st.write("")

diary_dates = load_diary_dates()
calendar_events = [
    {
        "title": "●",
        "start": d,
        "end": d,
        "backgroundColor": "#4CAF50",
        "borderColor": "#388E3C",
        "textColor": "#ffffff",
    }
    for d in diary_dates
]

calendar_options = {
    "initialView": "dayGridMonth",
    "locale": "ja",
    "height": 420,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "",
    },
    "selectable": True,
    "eventDisplay": "block",
}

cal_result = calendar(events=calendar_events, options=calendar_options, key="diary_calendar")

# クリックされた日付を取得
clicked_date_str = None
if cal_result:
    cb = cal_result.get("callback")
    if cb == "dateClick" or cal_result.get("dateClick"):
        dc = cal_result.get("dateClick", {})
        raw = dc.get("date", "")
        if raw:
            try:
                import datetime as dt
                utc_dt = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
                local_dt = utc_dt.astimezone()
                clicked_date_str = local_dt.strftime("%Y-%m-%d")
            except Exception:
                clicked_date_str = raw[:10]
    elif cb == "eventClick" or cal_result.get("eventClick"):
        ec = cal_result.get("eventClick", {})
        clicked_date_str = ec.get("event", {}).get("start", "")[:10]

if clicked_date_str:
    try:
        clicked = datetime.strptime(clicked_date_str, "%Y-%m-%d").date()
        if clicked > today:
            st.warning("未来の日付には日記を書けません。")
        else:
            st.session_state.calendar_selected_date = clicked_date_str
            st.session_state.writing_date = clicked
    except ValueError:
        pass

# --- 選択日の記録 ---
if st.session_state.calendar_selected_date:
    sel = st.session_state.calendar_selected_date
    sel_date = datetime.strptime(sel, "%Y-%m-%d").date()
    st.write("")
    st.divider()
    st.subheader(f"{sel_date.strftime('%-m月%-d日')}の記録")
    st.write("")
    date_records = load_history_by_date(sel)
    if date_records:
        for entry_date, original, positive in date_records:
            with st.expander(f"{entry_date}　{original[:30]}{'…' if len(original) > 30 else ''}"):
                col_left, col_right = st.columns(2)
                with col_left:
                    st.markdown("**今日のできごと**")
                    st.info(original)
                with col_right:
                    st.markdown("**今日のリフレーミング**")
                    st.success(positive)
    else:
        st.caption("この日の記録はありません。")

# --- 過去の変換履歴 ---
st.write("")
st.divider()
st.subheader("過去の変換履歴")
st.write("")

history = load_history()

if not history:
    st.caption("まだ履歴がありません。変換するとここに記録されます。")
else:
    for entry_date, original, positive in history:
        with st.expander(f"{entry_date}　{original[:30]}{'…' if len(original) > 30 else ''}"):
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown("**今日のできごと**")
                st.info(original)
            with col_right:
                st.markdown("**今日のリフレーミング**")
                st.success(positive)
