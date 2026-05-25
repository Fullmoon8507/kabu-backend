import requests
import pandas as pd
import yfinance as yf

_YF_SESSION = requests.Session()
_YF_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
})


def _normalize_ticker(ticker: str) -> str:
    """4桁の数字のみの場合、日本株として .T を自動補完する"""
    t = ticker.strip()
    if t.isdigit() and len(t) == 4:
        return f"{t}.T"
    return t


def run_ma_backtest(
    ticker: str,
    start_date: str,
    end_date: str,
    short_ma: int,
    long_ma: int,
) -> dict:
    ticker = _normalize_ticker(ticker)
    df_full = yf.download(
        ticker, start=start_date, end=end_date,
        auto_adjust=True, progress=False, session=_YF_SESSION,
    )

    if df_full.empty:
        raise ValueError(f"'{ticker}' のデータが取得できませんでした。ティッカーや期間を確認してください。")

    if isinstance(df_full.columns, pd.MultiIndex):
        df_full.columns = df_full.columns.get_level_values(0)

    df_full = df_full[["Close"]].copy()
    df_full["short_ma"] = df_full["Close"].rolling(short_ma).mean()
    df_full["long_ma"] = df_full["Close"].rolling(long_ma).mean()

    # チャート用データ（全期間・NaN は None に変換）
    chart_dates = [d.strftime("%Y-%m-%d") for d in df_full.index]
    chart_prices = [round(float(v), 2) for v in df_full["Close"]]
    chart_short_ma = [None if pd.isna(v) else round(float(v), 2) for v in df_full["short_ma"]]
    chart_long_ma = [None if pd.isna(v) else round(float(v), 2) for v in df_full["long_ma"]]

    # シミュレーションは NaN 除去後のデータで実行
    df = df_full.dropna()

    if df.empty:
        raise ValueError(
            f"MA計算後にデータが空です。期間を長くするか、MA期間（現在: 短期={short_ma}, 長期={long_ma}）を小さくしてください。"
        )

    initial_cash = 1_000_000
    cash = float(initial_cash)
    shares = 0
    trade_count = 0
    trades: list[dict] = []

    prev_short = df["short_ma"].iloc[0]
    prev_long = df["long_ma"].iloc[0]

    for date, row in df.iloc[1:].iterrows():
        curr_short = float(row["short_ma"])
        curr_long = float(row["long_ma"])
        price = float(row["Close"])

        # ゴールデンクロス: 未保有時に買い
        if prev_short <= prev_long and curr_short > curr_long and shares == 0:
            shares = int(cash / price)
            if shares > 0:
                cash -= shares * price
                trades.append({"date": date.strftime("%Y-%m-%d"), "type": "buy", "price": price})

        # デッドクロス: 保有中に売り
        elif prev_short >= prev_long and curr_short < curr_long and shares > 0:
            cash += shares * price
            shares = 0
            trade_count += 1
            trades.append({"date": date.strftime("%Y-%m-%d"), "type": "sell", "price": price})

        prev_short = curr_short
        prev_long = curr_long

    final_value = cash + shares * float(df["Close"].iloc[-1])
    total_return_pct = (final_value - initial_cash) / initial_cash * 100

    return {
        "total_return_pct": round(total_return_pct, 2),
        "trade_count": trade_count,
        "chart": {
            "dates": chart_dates,
            "prices": chart_prices,
            "short_ma": chart_short_ma,
            "long_ma": chart_long_ma,
            "trades": trades,
        },
    }
