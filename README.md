# 家計調査 月次支出データ取得ツール

e-Stat APIを使用して、家計調査（2025年改定）の月次支出データを取得するツールです。
CLI版とGUI版（Streamlit）を提供。

## セットアップ

1. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

2. `.env`ファイルを作成し、APIキーを設定

```bash
cp .env.example .env
```

`.env`を編集して`ESTAT_APP_ID`に[e-Stat](https://www.e-stat.go.jp/)で取得したアプリケーションIDを設定してください。

## 使い方

### GUI版（推奨）

```bash
streamlit run app.py
```

チェックボックスで品目を選択して一括ダウンロード。

### CLI版

```bash
python cli.py
```

対話形式で品目を検索・ダウンロード。

## ファイル構成

| ファイル | 説明 |
|----------|------|
| `app.py` | GUI（Streamlit） |
| `cli.py` | CLI |
| `data_fetcher.py` | e-Stat API通信 |
| `cache/kakei_2025_cache.json` | 品目キャッシュ（689品目） |
| `docs/品目一覧_2025年改定.md` | 品目一覧（人間用） |

## 仕様

- **対象データ**: 家計調査 2025年改定 月次データ
- **デフォルト条件**: 二人以上の世帯、全国、全期間
- **出力形式**: CSV（UTF-8 BOM付き）
- **保存先**: `./data`
