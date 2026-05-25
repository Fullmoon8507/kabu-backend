import pandas as pd
import yfinance as yf


def run_ma_backtest(
    ticker: str,
    start_date: str,
    end_date: str,
    short_ma: int,
    long_ma: int,
) -> dict:
    df = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)

    if df.empty:
        raise ValueError(f"'{ticker}' のデータが取得できませんでした。ティッカーや期間を確認してください。")

    # yfinance が MultiIndex で返す場合に平坦化
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[["Close"]].copy()
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

        # ゴールデンクロス: 未保有時に買い
        if prev_short <= prev_long and curr_short > curr_long and shares == 0:
            shares = int(cash / price)
            if shares > 0:
                cash -= shares * price

        # デッドクロス: 保有中に売り
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
