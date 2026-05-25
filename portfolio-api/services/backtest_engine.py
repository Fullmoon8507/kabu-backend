import os
import pandas as pd
import requests

JQUANTS_BASE = "https://api.jquants.com/v1"


def _get_id_token() -> str:
    refresh_token = os.environ.get("JQUANTS_REFRESH_TOKEN", "")
    if not refresh_token:
        raise ValueError("JQUANTS_REFRESH_TOKEN が環境変数に設定されていません。")
    res = requests.post(
        f"{JQUANTS_BASE}/token/auth_refresh",
        params={"refreshtoken": refresh_token},
        timeout=10,
    )
    res.raise_for_status()
    return res.json()["idToken"]


def _normalize_code(ticker: str) -> str:
    """8267.T や 2928.S → 8267 / 2928 に正規化（4桁コードのみ抽出）"""
    t = ticker.strip()
    if "." in t:
        t = t.split(".")[0]
    return t


def _fetch_prices(code: str, start_date: str, end_date: str, id_token: str) -> pd.DataFrame:
    res = requests.get(
        f"{JQUANTS_BASE}/prices/daily_quotes",
        params={"code": code, "dateFrom": start_date, "dateTo": end_date},
        headers={"Authorization": f"Bearer {id_token}"},
        timeout=15,
    )
    res.raise_for_status()
    data = res.json().get("daily_quotes", [])
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    return df[["Close"]]


def run_ma_backtest(
    ticker: str,
    start_date: str,
    end_date: str,
    short_ma: int,
    long_ma: int,
) -> dict:
    code = _normalize_code(ticker)
    id_token = _get_id_token()
    df = _fetch_prices(code, start_date, end_date, id_token)

    if df.empty:
        raise ValueError(f"'{ticker}' のデータが取得できませんでした。銘柄コードや期間を確認してください。")

    df["short_ma"] = df["Close"].rolling(short_ma).mean()
    df["long_ma"] = df["Close"].rolling(long_ma).mean()
    df = df.dropna()

    if df.empty:
        raise ValueError(
            f"MA計算後にデータが空です。期間を長くするか、MA期間（現在: 短期={short_ma}, 長期={long_ma}）を小さくしてください。"
        )

    initial_cash = 1_000_000
    cash = float(initial_cash)
    shares = 0
    trade_count = 0

    prev_short = df["short_ma"].iloc[0]
    prev_long = df["long_ma"].iloc[0]

    for _, row in df.iloc[1:].iterrows():
        curr_short = float(row["short_ma"])
        curr_long = float(row["long_ma"])
        price = float(row["Close"])

        if prev_short <= prev_long and curr_short > curr_long and shares == 0:
            shares = int(cash / price)
            if shares > 0:
                cash -= shares * price

        elif prev_short >= prev_long and curr_short < curr_long and shares > 0:
            cash += shares * price
            shares = 0
            trade_count += 1

        prev_short = curr_short
        prev_long = curr_long

    final_value = cash + shares * float(df["Close"].iloc[-1])
    total_return_pct = (final_value - initial_cash) / initial_cash * 100

    return {
        "total_return_pct": round(total_return_pct, 2),
        "trade_count": trade_count,
    }
