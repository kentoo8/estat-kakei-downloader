# AGENTS.md

このドキュメントはAIエージェント向けのプロジェクト説明です。

> **注意**: コード変更時は本ドキュメントも更新してください。

## 概要

家計調査（2025年改定）の月次支出データをe-Stat APIから取得するツール。
CLI版とGUI版（Streamlit）を提供。品目キャッシュにより高速な検索を実現。

## ファイル構成

```
├── app.py              # GUI（Streamlit）
├── cli.py              # CLI（対話処理）
├── data_fetcher.py     # e-Stat API通信
├── cache/
│   └── kakei_2025_cache.json  # 品目キャッシュ（689品目）
├── data/
│   ├── raw/            # APIから取得した生データ
│   └── processed/      # 加工済みデータ（人間が読める形式）
└── docs/               # 人間用ドキュメント
```

## 主要な関数

### app.py（GUI）

| 関数 | 役割 |
|------|------|
| `load_cache()` | キャッシュJSON読み込み |
| `get_default_filters()` | デフォルトフィルター取得 |
| `search_items()` | 品目をキーワード検索 |
| `parse_time()` | 時間コードをYYYY-MM形式に変換 |
| `process_dataframe()` | DataFrameを人間が読める形式に変換 |
| `download_item()` | 単一品目のダウンロード（raw + processed） |
| `get_selected_codes()` | チェックボックス状態から選択中コード取得 |
| `main()` | Streamlit UI |

### cli.py（CLI）

| 関数 | 役割 |
|------|------|
| `load_cache()` | キャッシュJSON読み込み |
| `search_items()` | 品目をキーワード検索 |
| `select_item()` | 品目選択UI |
| `main()` | メインループ |

### data_fetcher.py

| 関数 | 役割 |
|------|------|
| `count_stats_data()` | データ件数取得 |
| `fetch_stats_data()` | データ取得（ページング対応） |
| `_build_dimension_params()` | 次元フィルター変換 |

## キャッシュ構造

```json
{
  "stats_data_id": "0004023601",
  "revision": "2025年改定",
  "items": [
    {"code": "...", "name": "...", "display_name": "..."}
  ],
  "households": [...],
  "areas": [...]
}
```

## デフォルト設定

- **世帯**: 二人以上の世帯（2000年～）
- **地域**: 全国
- **期間**: 全期間

## API仕様

- **エンドポイント**: `https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData`
- **認証**: `ESTAT_APP_ID`（.envから読み込み）
- **ページング**: 10万件単位

## 例外クラス（data_fetcher.py）

- `ApiKeyNotFoundError`: APIキー未設定
- `EStatApiError`: APIエラー

## コード規約

- 型ヒント: モダン形式（`list[dict]`, `str | None`）
- パス操作: `pathlib`のみ
- 文字列: ダブルクォート
- print: `cli.py`のみ許容

## 拡張時の注意

1. **品目追加**: `cache/kakei_2025_cache.json`を更新
2. **新しい統計表**: `stats_data_id`を変更
3. **フィルター追加**: `_build_dimension_params()`を確認
4. **GUI機能追加**: `app.py`のStreamlitコンポーネントを編集
