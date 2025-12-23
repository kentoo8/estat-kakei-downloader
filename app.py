"""
家計調査 月次支出データ取得 GUI（Streamlit）
検索で絞り込み → チェックボックスで選択 → 一括ダウンロード
"""

import json
from pathlib import Path

import streamlit as st

from data_fetcher import (
    ApiKeyNotFoundError,
    EStatApiError,
    fetch_stats_data,
)

# キャッシュファイルのパス
CACHE_FILE = Path(__file__).parent / "cache" / "kakei_2025_cache.json"
DATA_DIR = Path(__file__).parent / "data"


def load_cache() -> dict:
    """キャッシュを読み込む"""
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_default_filters(cache: dict) -> dict[str, str]:
    """デフォルトフィルターを取得"""
    households = cache["households"]
    areas = cache["areas"]

    filters: dict[str, str] = {}

    # 二人以上の世帯
    for h in households:
        if "二人以上の世帯" in h["name"] and "勤労者" not in h["name"]:
            filters["cat02"] = h["code"]
            break

    # 全国
    for a in areas:
        if a["name"] == "全国":
            filters["area"] = a["code"]
            break

    return filters


def search_items(items: list[dict], keyword: str) -> list[dict]:
    """品目を検索"""
    if not keyword:
        return items
    keyword = keyword.lower()
    return [item for item in items if keyword in item["display_name"].lower()]


def parse_time(time_code: str) -> str:
    """時間コードをYYYY-MM形式に変換"""
    # "2000000101" → "2000-01"
    year = time_code[:4]
    month = time_code[6:8]
    return f"{year}-{month}"


def process_dataframe(df, item: dict, cache: dict) -> "pd.DataFrame":
    """DataFrameを加工して人間が読める形式に変換"""
    import pandas as pd

    required_cols = ["time", "cat01", "cat02", "area", "unit", "value"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = pd.NA

    # マッピング作成
    item_map = {it["code"]: it["display_name"] for it in cache["items"]}
    household_map = {h["code"]: h["name"] for h in cache["households"]}
    area_map = {a["code"]: a["name"] for a in cache["areas"]}

    def format_time(value) -> str:
        return parse_time(value) if isinstance(value, str) else ""

    # 加工
    processed = pd.DataFrame()
    processed["year_month"] = df["time"].apply(format_time)
    processed["item"] = df["cat01"].map(item_map).fillna(item["display_name"])
    processed["household"] = df["cat02"].map(household_map)
    processed["area"] = df["area"].map(area_map)
    processed["unit"] = df["unit"]
    processed["value"] = df["value"]

    return processed


def download_item(
    stats_data_id: str, item: dict, filters: dict[str, str], cache: dict
) -> Path | None:
    """品目データをダウンロード（processedのみ）"""
    item_filters = {**filters, "cat01": item["code"]}

    try:
        df = fetch_stats_data(stats_data_id, item_filters)
        if df.empty:
            return None

        # ファイル名の安全化
        safe_name = item["display_name"].replace("/", "_").replace("\\", "_")
        filename = f"家計調査_{safe_name}_月次.csv"

        # processed保存
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        processed_df = process_dataframe(df, item, cache)
        processed_path = DATA_DIR / filename
        processed_df.to_csv(processed_path, index=False, encoding="utf-8-sig")

        return processed_path
    except (ApiKeyNotFoundError, EStatApiError) as e:
        st.error(f"エラー: {e.message}")
        return None


def get_selected_codes(items: list[dict]) -> set[str]:
    """チェックボックスの状態から選択中のコードを取得"""
    selected = set()
    for item in items:
        if st.session_state.get(f"cb_{item['code']}", False):
            selected.add(item["code"])
    return selected


def main() -> None:
    st.set_page_config(
        page_title="家計調査データ取得",
        page_icon="📊",
        layout="wide",
    )

    st.title("📊 家計調査 月次支出データ取得")
    st.caption("2025年改定版 | 二人以上の世帯 | 全国")

    # データ出典（フッター）
    st.sidebar.markdown("---")
    st.sidebar.caption(
        "出典：「家計調査」（総務省統計局）\n\n"
        "政府統計の総合窓口 [e-Stat](https://www.e-stat.go.jp/)"
    )

    # キャッシュ読み込み
    try:
        cache = load_cache()
    except FileNotFoundError:
        st.error("キャッシュファイルが見つかりません。")
        return

    stats_data_id = cache["stats_data_id"]
    items = cache["items"]
    default_filters = get_default_filters(cache)

    # 検索キーの初期化
    if "search_key" not in st.session_state:
        st.session_state.search_key = 0

    # 選択中のコードを取得
    selected_codes = get_selected_codes(items)

    # サイドバー: 選択状況とダウンロード
    with st.sidebar:
        st.header("選択中の品目")
        selected_count = len(selected_codes)
        st.metric("選択数", selected_count)

        if selected_count > 0:
            st.divider()
            selected_items_list = [it for it in items if it["code"] in selected_codes]
            for item in selected_items_list[:10]:
                st.text(f"• {item['display_name']}")
            if selected_count > 10:
                st.text(f"... 他 {selected_count - 10} 件")

            st.divider()

            if st.button("🗑️ 選択をクリア"):
                for item in items:
                    st.session_state[f"cb_{item['code']}"] = False
                st.rerun()

            if st.button("📥 ダウンロード", type="primary"):
                progress = st.progress(0)
                status = st.empty()

                downloaded = []
                codes_list = list(selected_codes)

                for i, code in enumerate(codes_list):
                    item = next((it for it in items if it["code"] == code), None)
                    if item:
                        status.text(f"ダウンロード中: {item['display_name']}")
                        filepath = download_item(stats_data_id, item, default_filters, cache)
                        if filepath:
                            downloaded.append(filepath)
                    progress.progress((i + 1) / len(codes_list))

                status.empty()
                progress.empty()

                if downloaded:
                    st.success(f"✅ {len(downloaded)}件完了")
                    for fp in downloaded:
                        st.text(f"  {fp.name}")

    # メイン: 検索と品目リスト
    search_keyword = st.text_input(
        "🔍 品目を検索（空欄で全件表示）",
        placeholder="例: アイス、ビール、米",
        key=f"search_{st.session_state.search_key}",
    )

    if search_keyword and st.button("🔍 検索をクリア", type="secondary"):
        st.session_state.search_key += 1
        st.rerun()

    # 検索結果をフィルタリング
    filtered_items = search_items(items, search_keyword)

    # 検索結果の操作ボタン
    col1, col2, col3 = st.columns([2, 2, 6])
    with col1:
        if st.button("✅ 表示中を全選択"):
            for item in filtered_items:
                st.session_state[f"cb_{item['code']}"] = True
            st.rerun()
    with col2:
        if st.button("⬜ 表示中を全解除"):
            for item in filtered_items:
                st.session_state[f"cb_{item['code']}"] = False
            st.rerun()

    st.subheader(f"品目一覧（{len(filtered_items)}件）")

    if not filtered_items:
        st.info("該当する品目がありません。")
        return

    # グリッド表示（3列）
    num_cols = 3
    rows = [filtered_items[i : i + num_cols] for i in range(0, len(filtered_items), num_cols)]

    for row_items in rows:
        cols = st.columns(num_cols)
        for col_idx, item in enumerate(row_items):
            with cols[col_idx]:
                st.checkbox(item["display_name"], key=f"cb_{item['code']}")


if __name__ == "__main__":
    main()
