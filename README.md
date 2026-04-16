# ✨ Positive Diary / ポジティブ日記

> Reframe your day — an AI-powered journaling app that transforms negative experiences into positive perspectives.
>
> ネガティブな出来事をポジティブな視点に変換する、AI搭載の日記Webアプリ。

---

## What It Does / できること

ネガティブな日記を入力すると、OpenAI GPT が優しいカウンセラーとして同じ出来事をポジティブな言葉に言い換えます。元の文と変換後の文を横並びで表示し、気づきや別の見方を提示します。

Type in what happened today — no matter how frustrating — and the app uses OpenAI GPT to reframe it with warmth and care. The original and reframed text are shown side by side.

| Input（入力） | Output（出力） |
|---|---|
| 仕事でミスをして上司に注意された | 失敗を通じて成長するチャンスを得た日。上司が丁寧に指摘してくれたことは、あなたへの期待の裏返しかもしれません。 |
| I failed at work and got scolded | A day of learning. Being corrected means someone cares enough to help you grow. |

---

## Tech Stack / 技術構成

| Layer | Technology |
|---|---|
| Frontend / UI | [Streamlit](https://streamlit.io/) |
| AI / LLM | [OpenAI API](https://platform.openai.com/) (`gpt-4o-mini`) |
| Config | python-dotenv |
| Language | Python 3.10+ |

---

## Quick Start / セットアップ

**1. Clone & move into the project**
```bash
git clone <repository-url>
cd positive-diary
```

**2. Create a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate       # Mac / Linux
# venv\Scripts\activate        # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set your API key**
```bash
cp .env.example .env
# .env を開いて OPENAI_API_KEY に実際のキーを入力
```

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

**5. Run the app**
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Project Structure / ファイル構成

```
positive-diary/
├── app.py                  # Streamlit app (main logic)
├── requirements.txt        # Python dependencies
├── .env                    # API key (gitignored)
├── .env.example            # API key template
├── persona.example.md      # Persona template (copy to data/persona.md)
├── .gitignore
├── README.md
└── data/
    ├── .gitkeep
    ├── diary.db            # SQLite database (gitignored)
    └── persona.md          # Personal profile for context (gitignored)
```

---

## Roadmap / 今後の予定

- [x] **履歴保存** — 過去の変換をローカルに保存・一覧表示
- [x] **個人プロフィール反映** — persona.mdの人物像をシステムプロンプトに反映・自動更新
- [ ] **感情スコア表示** — 変換前後のポジティブ度をスコアで可視化
- [ ] **多言語対応** — 英語・中国語など他言語の入力にも対応
- [ ] **モデル選択** — GPT-4o / GPT-4o-mini など使用モデルをUI上で切り替え
- [ ] **Streamlit Cloud デプロイ** — ワンクリックで公開できるデプロイ手順を追加
- [ ] **テストコード** — `pytest` による API モック・ユニットテストの整備

---

## Changelog / 変更履歴

### v0.2.0 (2026-04-17)
- SQLiteによる変換履歴の保存・一覧表示
- persona.mdによる個人プロフィールの反映
- persona.mdのやり取り後自動更新

### v0.1.0 (2026-04-16)
- 初回リリース
- ネガティブ日記のポジティブ変換（OpenAI API）
- 元の文と変換後の並列表示

---

## License

MIT
