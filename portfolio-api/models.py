from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey
from database import Base


class Stock(Base):
    """銘柄マスタテーブル"""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    # ティッカーコード（例: 7203.T）。ユニーク制約あり
    ticker_code = Column(String, unique=True, index=True, nullable=False)
    company_name = Column(String, nullable=False)
    # セクター（任意項目）
    sector = Column(String, nullable=True)


class Holding(Base):
    """保有株（取引履歴）テーブル"""
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True)
    # stocksテーブルのticker_codeを参照する外部キー
    ticker_code = Column(String, ForeignKey("stocks.ticker_code"), nullable=False)
    purchase_date = Column(Date, nullable=False)
    # 購入単価（1株あたりの価格）
    purchase_price = Column(Float, nullable=False)
    # 購入株数
    quantity = Column(Integer, nullable=False)
    # 任意メモ
    note = Column(Text, nullable=True)
