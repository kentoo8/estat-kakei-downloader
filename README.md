# estat-kakei-downloader

e-Stat APIで家計調査（2025年改定）の月次支出データを取得するCLI/GUIツール。

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

- 検索で品目を絞り込み
- チェックボックスで選択
- 「表示中を全選択/全解除」で一括操作
- サイドバーから一括ダウンロード

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

## 出力データ

ダウンロードしたデータは2つのフォルダに保存されます：

| フォルダ | 内容 |
|----------|------|
| `data/raw/` | APIから取得した生データ |
| `data/processed/` | 加工済みデータ（推奨） |

### processed形式

| カラム | 例 |
|--------|-----|
| `year_month` | 2024-04 |
| `item` | アイスクリーム・シャーベット |
| `household` | 二人以上の世帯 |
| `area` | 全国 |
| `unit` | 円 |
| `value` | 529 |

## 仕様

- **対象データ**: 家計調査 2025年改定 月次データ
- **デフォルト条件**: 二人以上の世帯、全国、全期間
- **出力形式**: CSV（UTF-8 BOM付き）

## データ出典

このツールで取得するデータの出典：

- **出典**: 「家計調査」（総務省統計局）
- **データ提供元**: 政府統計の総合窓口 [e-Stat](https://www.e-stat.go.jp/)

本ツールを利用して取得したデータを公開・利用する際は、上記の出典を明記してください。
