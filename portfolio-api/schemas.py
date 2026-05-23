from datetime import date
from typing import Optional
from pydantic import BaseModel


# ─────────────────────────────────────────
# 銘柄マスタ（stocks）スキーマ
# ─────────────────────────────────────────

class StockBase(BaseModel):
    ticker_code: str
    company_name: str
    sector: Optional[str] = None


class StockCreate(StockBase):
    """POST /stocks のリクエストボディ"""
    pass


class StockResponse(StockBase):
    """GET /stocks のレスポンス"""
    id: int
    is_active: bool
    is_manual: bool

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# 保有株（holdings）スキーマ
# ─────────────────────────────────────────

class HoldingBase(BaseModel):
    ticker_code: str
    purchase_date: date
    purchase_price: float
    quantity: int
    note: Optional[str] = None


class HoldingCreate(HoldingBase):
    """POST /holdings のリクエストボディ"""
    pass


class HoldingUpdate(BaseModel):
    """PUT /holdings/{id} のリクエストボディ（全項目任意）"""
    ticker_code: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_price: Optional[float] = None
    quantity: Optional[int] = None
    note: Optional[str] = None


class HoldingResponse(HoldingBase):
    """GET /holdings のレスポンス"""
    id: int

    class Config:
        from_attributes = True
