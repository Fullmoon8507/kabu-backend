from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from services.backtest_engine import run_ma_backtest

router = APIRouter(prefix="/api/backtest", tags=["バックテスト"])


class BacktestRequest(BaseModel):
    ticker: str
    start_date: str
    end_date: str
    short_ma: int = 25
    long_ma: int = 75


class TradePoint(BaseModel):
    date: str
    type: str
    price: float


class ChartData(BaseModel):
    dates: list[str]
    prices: list[float]
    short_ma: list[float | None]
    long_ma: list[float | None]
    trades: list[TradePoint]


class BacktestResponse(BaseModel):
    total_return_pct: float
    trade_count: int
    chart: ChartData


@router.post("/run", response_model=BacktestResponse)
def run_backtest(
    req: BacktestRequest,
    _: str = Depends(get_current_user),
):
    """MAクロス戦略のバックテストを実行する"""
    try:
        result = run_ma_backtest(
            req.ticker,
            req.start_date,
            req.end_date,
            req.short_ma,
            req.long_ma,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"データ取得エラー: {str(e)}")
