────────────────────────────

e-Stat 半自動データ取得アプリ
仕様指示書（GUI 版）
プロジェクト名: estat-kakei-downloader
目的

ユーザー操作に基づき e-Stat API から家計調査（2025 年改定）の月次支出データを取得し、
CSV として保存する Streamlit GUI アプリケーションを提供する。

1. 技術スタック・基本方針

Python 3.10+

requests / pandas / python-dotenv / pathlib / streamlit

API キーは .env 内の ESTAT_APP_ID から読み込む

.env.example を用意し、.env は .gitignore

型ヒントはモダン形式（例：list[str], str | None）

コードは責務ごとにモジュール分離

e-Stat REST v3.0（JSON）を使用

ページングは 10 万件単位で自動処理

print は原則禁止（必要なら st.write などを使用）

2. ディレクトリ構成
project_root/
    app.py
    data_fetcher.py
    cache/
        kakei_2025_cache.json
    data/
        raw/
        processed/
    .env.example
    README.md
    AGENTS.md

3. dotenv

.env.example

ESTAT_APP_ID=""
DATA_SAVE_DIR="./data"

起動時に python-dotenv で読み込む。

4. API クライアント仕様（data_fetcher.py）

Spec 1: count_stats_data

Input:

stats_data_id: str

dimension_filters: dict[str, str]

Behavior:

/getStatsData を limit=1 で呼び出し TOTAL_NUMBER を取得

Output: int（件数）

Spec 2: fetch_stats_data

Input:

stats_data_id: str

dimension_filters: dict[str, str]

Behavior:

ページング処理で全件取得

Output: pandas.DataFrame

5. GUI 仕様（app.py）

- 品目キャッシュからの検索（キーワード一致）
- チェックボックスで品目を複数選択
- サイドバーから一括ダウンロード
- raw/processed に保存

6. 出力仕様

- data/raw に API の生データを保存
- data/processed に読みやすい形式で保存
- processed には year_month, item, household, area, unit, value を含む

7. エラー設計

- ApiKeyNotFoundError
- EStatApiError

GUI ではエラーを読みやすく表示する。

8. README

- セットアップ（.env, python-dotenv）
- GUI の使い方（streamlit run app.py）
- 出力形式の説明

────────────────────────────
