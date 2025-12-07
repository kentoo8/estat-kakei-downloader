"""
データ取得モジュール
e-Stat APIからデータを取得しDataFrameとして返す
"""

import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv(Path(__file__).parent / ".env")


class ApiKeyNotFoundError(Exception):
    """APIキーが設定されていない場合に発生する例外"""

    def __init__(self, message: str = "ESTAT_APP_ID が設定されていません"):
        self.message = message
        super().__init__(self.message)


class EStatApiError(Exception):
    """e-Stat API からエラーレスポンスが返された場合に発生する例外"""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


BASE_URL = "https://api.e-stat.go.jp/rest/3.0/app/json"
PAGE_SIZE = 100000  # 10万件単位でページング


def _get_app_id() -> str:
    """APIキーを取得する"""
    app_id = os.getenv("ESTAT_APP_ID")
    if not app_id:
        raise ApiKeyNotFoundError()
    return app_id


def _build_dimension_params(dimension_filters: dict[str, str]) -> dict[str, str]:
    """
    次元フィルターをAPIパラメータに変換する

    Args:
        dimension_filters: 次元フィルター（例: {"cat01": "001", "area": "00000"}）

    Returns:
        APIパラメータ辞書
    """
    params: dict[str, str] = {}
    for key, value in dimension_filters.items():
        if key == "time":
            param_key = "cdTime"
        elif key == "area":
            param_key = "cdArea"
        elif key == "tab":
            param_key = "cdTab"
        elif key.startswith("cat"):
            num = key[3:]
            param_key = f"cdCat{num.zfill(2)}"
        else:
            param_key = f"cd{key.capitalize()}"
        params[param_key] = value
    return params


def _check_api_response(data: dict) -> None:
    """
    APIレスポンスのエラーをチェックする

    Args:
        data: APIレスポンスJSON

    Raises:
        EStatApiError: APIエラーの場合
    """
    result = data.get("GET_STATS_DATA", {}).get("RESULT", {})
    status = result.get("STATUS")
    if status != 0:
        error_msg = result.get("ERROR_MSG", "不明なエラー")
        raise EStatApiError(f"e-Stat API エラー: {error_msg}", status)


def count_stats_data(stats_data_id: str, dimension_filters: dict[str, str]) -> int:
    """
    データ件数を取得する

    Args:
        stats_data_id: 統計表ID
        dimension_filters: 次元フィルター

    Returns:
        データ件数
    """
    params = {
        "appId": _get_app_id(),
        "statsDataId": stats_data_id,
        "limit": 1,
        **_build_dimension_params(dimension_filters),
    }

    response = requests.get(f"{BASE_URL}/getStatsData", params=params, timeout=30)

    if response.status_code != 200:
        raise EStatApiError(
            f"APIリクエストに失敗しました: HTTP {response.status_code}",
            response.status_code,
        )

    data = response.json()
    _check_api_response(data)

    statistical_data = data.get("GET_STATS_DATA", {}).get("STATISTICAL_DATA", {})
    result_inf = statistical_data.get("RESULT_INF", {})
    return int(result_inf.get("TOTAL_NUMBER", 0))


def fetch_stats_data(
    stats_data_id: str, dimension_filters: dict[str, str]
) -> pd.DataFrame:
    """
    統計データを取得しDataFrameとして返す

    Args:
        stats_data_id: 統計表ID
        dimension_filters: 次元フィルター

    Returns:
        統計データのDataFrame
    """
    app_id = _get_app_id()
    dimension_params = _build_dimension_params(dimension_filters)

    all_data: list[dict] = []
    start_position = 1

    while True:
        params = {
            "appId": app_id,
            "statsDataId": stats_data_id,
            "limit": PAGE_SIZE,
            "startPosition": start_position,
            **dimension_params,
        }

        response = requests.get(f"{BASE_URL}/getStatsData", params=params, timeout=60)

        if response.status_code != 200:
            raise EStatApiError(
                f"APIリクエストに失敗しました: HTTP {response.status_code}",
                response.status_code,
            )

        data = response.json()
        _check_api_response(data)

        statistical_data = data.get("GET_STATS_DATA", {}).get("STATISTICAL_DATA", {})
        data_inf = statistical_data.get("DATA_INF", {})
        values = data_inf.get("VALUE", [])

        if isinstance(values, dict):
            values = [values]

        if not values:
            break

        all_data.extend(values)

        result_inf = statistical_data.get("RESULT_INF", {})
        total_number = int(result_inf.get("TOTAL_NUMBER", 0))

        if start_position + PAGE_SIZE > total_number:
            break

        start_position += PAGE_SIZE

    return _convert_to_dataframe(all_data)


def _convert_to_dataframe(data: list[dict]) -> pd.DataFrame:
    """APIレスポンスデータをDataFrameに変換する"""
    if not data:
        return pd.DataFrame()

    rows = []
    for item in data:
        row = {}
        for key, value in item.items():
            if key.startswith("@"):
                row[key[1:]] = value
            elif key == "$":
                row["value"] = value
        rows.append(row)

    df = pd.DataFrame(rows)

    # time列を先頭に
    if "time" in df.columns:
        cols = ["time"] + [c for c in df.columns if c != "time"]
        df = df[cols]

    # value列を数値に変換
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    return df
