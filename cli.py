#!/usr/bin/env python3
"""
e-Stat 家計調査 月次支出データ取得 CLI
2025年改定版の品目データをキャッシュから即座に検索・取得
"""

import json
import os
import re
import sys
from pathlib import Path

from data_fetcher import (
    ApiKeyNotFoundError,
    EStatApiError,
    count_stats_data,
    fetch_stats_data,
)

# キャッシュファイルのパス
CACHE_FILE = Path(__file__).parent / "cache" / "kakei_2025_cache.json"


def load_cache() -> dict:
    """キャッシュを読み込む"""
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_save_dir() -> Path:
    """保存先ディレクトリを取得する"""
    save_dir = os.getenv("DATA_SAVE_DIR", "./data")
    path = Path(save_dir)
    if not path.is_absolute():
        path = Path(__file__).parent / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def input_with_prompt(prompt: str) -> str:
    """プロンプト付きで入力を受け付ける"""
    print(prompt, end="")
    return input().strip()


def confirm_action(message: str) -> bool:
    """確認を求める（EnterでYes）"""
    response = input_with_prompt(f"{message} [Y/n] > ")
    return response == "" or response.upper() == "Y"


def search_items(items: list[dict], keyword: str) -> list[dict]:
    """品目をキーワードで検索"""
    return [item for item in items if keyword in item["display_name"]]


def select_item(items: list[dict], keyword: str) -> dict | None:
    """品目を選択"""
    matched = search_items(items, keyword)

    if not matched:
        print(f"「{keyword}」を含む品目が見つかりませんでした。")
        return None

    if len(matched) == 1:
        print(f"  → {matched[0]['display_name']}")
        return matched[0]

    # 複数候補
    print(f"「{keyword}」を含む品目:")
    for i, item in enumerate(matched[:10], 1):
        print(f"  [{i}] {item['display_name']}")

    if len(matched) > 10:
        print(f"  （他 {len(matched) - 10} 件）")

    while True:
        choice = input_with_prompt("番号を選択 > ")
        try:
            index = int(choice) - 1
            if 0 <= index < min(len(matched), 10):
                return matched[index]
        except ValueError:
            pass
        print("有効な番号を入力してください。")


def generate_filename(item_name: str) -> str:
    """ファイル名を生成"""
    safe_name = re.sub(r"[^\w\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]", "_", item_name)
    return f"家計調査_{safe_name}_月次"


def main() -> None:
    """メイン処理"""
    # キャッシュ読み込み
    try:
        cache = load_cache()
    except FileNotFoundError:
        print("エラー: キャッシュファイルが見つかりません。")
        print("kakei_2025_cache.json を配置してください。")
        sys.exit(1)

    stats_data_id = cache["stats_data_id"]
    items = cache["items"]
    households = cache["households"]
    areas = cache["areas"]

    # デフォルト選択
    default_household = next(
        (h for h in households if "二人以上の世帯" in h["name"] and "勤労者" not in h["name"]),
        households[0] if households else None,
    )
    default_area = next(
        (a for a in areas if a["name"] == "全国"),
        areas[0] if areas else None,
    )

    while True:
        print()
        print("━" * 50)
        print("  家計調査 月次支出データ取得（2025年改定）")
        print("━" * 50)
        print()

        keyword = input_with_prompt("品目名を入力（例: アイス、ビール、米） > ")
        if not keyword:
            continue

        # 品目を選択
        item = select_item(items, keyword)
        if item is None:
            if not confirm_action("続けますか？"):
                break
            continue

        # フィルター設定
        filters = {"cat01": item["code"]}
        if default_household:
            filters["cat02"] = default_household["code"]
        if default_area:
            filters["area"] = default_area["code"]

        # 条件表示
        print()
        print("━" * 50)
        print(f"  品目: {item['display_name']}")
        print(f"  世帯: {default_household['name'] if default_household else '全て'}")
        print(f"  地域: {default_area['name'] if default_area else '全て'}")
        print(f"  期間: 全期間")
        print("━" * 50)

        # 件数確認
        print()
        print("件数を確認中...")
        try:
            count = count_stats_data(stats_data_id, filters)
        except (ApiKeyNotFoundError, EStatApiError) as e:
            print(f"エラー: {e.message}")
            continue

        print(f"取得予定: {count:,} 行")

        if count == 0:
            print("データが存在しません。")
            continue

        if not confirm_action("取得しますか？"):
            continue

        # データ取得
        print()
        print("データを取得中...")
        try:
            df = fetch_stats_data(stats_data_id, filters)
        except (ApiKeyNotFoundError, EStatApiError) as e:
            print(f"エラー: {e.message}")
            continue

        print(f"取得完了: {len(df):,} 行")

        # 保存
        filename = generate_filename(item["display_name"])
        csv_path = get_save_dir() / f"{filename}.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")

        print()
        print("━" * 50)
        print(f"  保存完了: {csv_path}")
        print("━" * 50)

        print()
        if not confirm_action("別の品目を検索しますか？"):
            print()
            print("ご利用ありがとうございました。")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n中断されました。")
        sys.exit(0)
