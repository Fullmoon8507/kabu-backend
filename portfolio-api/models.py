from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey, Boolean, text
from database import Base


class Stock(Base):
    """銘柄マスタテーブル"""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    ticker_code = Column(String, unique=True, index=True, nullable=False)
    company_name = Column(String, nullable=False)
    sector = Column(String, nullable=True)
    # 上場中なら true。JPX最新リストから消えた銘柄は false に論理削除する
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    # 手動登録された銘柄なら true。シードの上場廃止処理で上書きされない
    is_manual = Column(Boolean, nullable=False, server_default=text("false"))


class Holding(Base):
    """保有株（取引履歴）テーブル"""
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True)
    ticker_code = Column(String, ForeignKey("stocks.ticker_code"), nullable=False)
    purchase_date = Column(Date, nullable=True)
    purchase_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    note = Column(Text, nullable=True)
