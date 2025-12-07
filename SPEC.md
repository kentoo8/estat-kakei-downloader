────────────────────────────

e-Stat 半自動データ取得アプリ
完全版仕様指示書（few-shot 統合版）
目的

ユーザーの入力に基づき e-Stat API から統計表データを取得し、
CSV/Parquet として保存する CLI アプリケーションを構築する。
本仕様は SDD（Spec Driven Development）を前提とし、
UX を実用的で上品なものにするための few-shot を含む。

1. 技術スタック・基本方針

Python 3.10+

requests / pandas / python-dotenv / pathlib

API キーは .env 内の ESTAT_APP_ID から読み込む

.env.example を必ず用意し、.env は .gitignore

型ヒントはモダン形式（例：list[str], str | None）

コードは責務ごとにモジュール分離

e-Stat REST v3.0（JSON）を使用

ページングは 10 万件単位で自動処理

CLI 以外で print を使わない

2. ディレクトリ構成（固定）
project_root/
    cli.py
    estat_client.py
    meta_parser.py
    data_fetcher.py
    utils/
        __init__.py
    .env.example
    README.md
    agents.md（任意）

3. dotenv

.env.example

ESTAT_APP_ID=""
DATA_SAVE_DIR="./data"


起動時に python-dotenv で読み込む。

4. API クライアント仕様（Spec）
Spec 1: getStatsList

Input:

search_word: str

limit: int = 1000

Behavior:

/getStatsList を呼び出し、統計表一覧を返す

Output: list[dict]（各 dict に必ず "ID" が含まれる）

Error:

API キー未設定 → ApiKeyNotFoundError

API エラー → EStatApiError

Spec 2: getMetaInfo

Input: stats_data_id: str

Behavior: /getMetaInfo を呼び出し分類階層を取得

Output: dict（メタ JSON）

5. メタ情報解析（Spec）
Spec 3: parseMetaInfo

Input: meta_json

Behavior:

time / area / cat01 / cat02 / cat03 … を抽出

それぞれ list[{code, name}] へ変換

Output: dict[str, list[dict[str, str]]]

6. データ取得（Spec）
Spec 4: fetchStatsData

Input:

stats_data_id

dimension_filters: dict[str, str]

Behavior:

ページング処理で全件取得

Output: pandas.DataFrame

DataFrame 必須列：time, value + 指定分類

7. 件数プレビュー（Spec）
Spec 5: countStatsData

Input: stats_data_id, dimension_filters

Behavior:

/getStatsData を limit=1 で呼び出し TOTAL_NUMBER を取得

Output: int（件数）

CLI は実行前に件数を自然に提示すればよい。

8. CLI（対話仕様）
基本フロー

キーワード入力

getStatsList → 統計表候補表示

統計表を選択

メタ情報を解析し次元選択 UI

countStatsData で件数を提示

ユーザーが承認したら fetchStatsData を実行

CSV／Parquet 保存

入力に対する注意点

無効入力は再入力

保存先は DATA_SAVE_DIR

time・cat02 の選択はユーザーの意思を尊重

1 行であっても件数説明だけして問題なし

9. エラー設計

ApiKeyNotFoundError

EStatApiError

MetaParseError

CLI では優雅にメッセージ表示

10. コード規約

pathlib 統一（os.path 禁止）

ロジックと UI 交差禁止

print は cli.py 内のみ許容

関数は testable に設計

11. Few-shot（UX例：アイス検索）

以下は、ユーザーが「アイス」と入力した際の望ましい CLI 体験を示す。

■ Few-shot 1：キーワード入力

ユーザー：

> アイス


CLI：

getStatsList で候補表を提示

ユーザーが “品目分類を含む表” を選択

■ Few-shot 2：品目名の部分一致検索

getMetaInfo → meta_parser の結果、
cat02 に以下が含まれると仮定。

アイスクリーム (code: 017)
アイス類その他 (code: 018)


CLI：

「アイス」を含む品目分類が見つかりました：

[1] アイスクリーム (017)
[2] アイス類その他 (018)

選択してください：
> 1

■ Few-shot 3：選択条件の提示
以下の条件でデータをご用意いたしますわ：

- 品目：アイスクリーム
- 地域：全国
- 世帯区分：ユーザーの選択（または標準）
- 期間：ユーザーの選択した範囲

件数を確認いたします……

■ Few-shot 4：件数プレビューと実行
取得予定の行数：60 行
こちらでよろしゅうございますか？
[Y] 実行する / [N] 条件を変更する
> Y

■ Few-shot 5：保存完了
保存が完了いたしましたわ：
./data/icecream_2020-2024.csv

続けて別の品目を検索なさいますか？
[Y/N]

12. README

セットアップ（.env, python-dotenv）

CLI の使い方

キーワード → 表選択 → 品目選択 → 実行 の流れ

ページング仕様

保存形式について

必要最小限にとどめる。プロジェクト構造などは不要

────────────────────────────
