"""
家計調査 月次支出データ取得 GUI（Streamlit）
チェックボックスで品目を選択して一括ダウンロード
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


@st.cache_data
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


def download_item(stats_data_id: str, item: dict, filters: dict[str, str]) -> Path | None:
    """品目データをダウンロード"""
    item_filters = {**filters, "cat01": item["code"]}

    try:
        df = fetch_stats_data(stats_data_id, item_filters)
        if df.empty:
            return None

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"家計調査_{item['display_name']}_月次.csv"
        # ファイル名の安全化
        filename = filename.replace("/", "_").replace("\\", "_")
        filepath = DATA_DIR / filename
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        return filepath
    except (ApiKeyNotFoundError, EStatApiError) as e:
        st.error(f"エラー: {e.message}")
        return None


def main() -> None:
    st.set_page_config(
        page_title="家計調査データ取得",
        page_icon="📊",
        layout="wide",
    )

    st.title("📊 家計調査 月次支出データ取得")
    st.caption("2025年改定版 | 二人以上の世帯 | 全国")

    # キャッシュ読み込み
    try:
        cache = load_cache()
    except FileNotFoundError:
        st.error("キャッシュファイルが見つかりません。")
        return

    stats_data_id = cache["stats_data_id"]
    items = cache["items"]
    default_filters = get_default_filters(cache)

    # セッション状態の初期化
    if "selected_items" not in st.session_state:
        st.session_state.selected_items = set()

    # サイドバー: 選択状況
    with st.sidebar:
        st.header("選択中の品目")
        selected_count = len(st.session_state.selected_items)
        st.metric("選択数", selected_count)

        if selected_count > 0:
            if st.button("🗑️ 選択をクリア"):
                st.session_state.selected_items = set()
                st.rerun()

            st.divider()

            if st.button("📥 選択した品目をダウンロード", type="primary"):
                progress = st.progress(0)
                status = st.empty()

                downloaded = []
                selected_codes = list(st.session_state.selected_items)

                for i, code in enumerate(selected_codes):
                    item = next((it for it in items if it["code"] == code), None)
                    if item:
                        status.text(f"ダウンロード中: {item['display_name']}")
                        filepath = download_item(stats_data_id, item, default_filters)
                        if filepath:
                            downloaded.append(filepath)
                    progress.progress((i + 1) / len(selected_codes))

                status.empty()
                progress.empty()

                if downloaded:
                    st.success(f"✅ {len(downloaded)}件ダウンロード完了")
                    for fp in downloaded:
                        st.text(f"  {fp.name}")

    # メイン: 品目リスト
    st.subheader(f"品目一覧（{len(items)}件）")

    # グリッド表示（3列）
    cols = st.columns(3)

    for i, item in enumerate(items):
        col = cols[i % 3]
        code = item["code"]
        display_name = item["display_name"]

        with col:
            checked = code in st.session_state.selected_items
            if st.checkbox(display_name, value=checked, key=f"item_{code}"):
                st.session_state.selected_items.add(code)
            else:
                st.session_state.selected_items.discard(code)


if __name__ == "__main__":
    main()
