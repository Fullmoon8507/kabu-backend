from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db

router = APIRouter(prefix="/stocks", tags=["銘柄マスタ"])


@router.get("/", response_model=List[schemas.StockResponse])
def get_stocks(db: Session = Depends(get_db)):
    """登録済み銘柄の一覧を返す"""
    return db.query(models.Stock).all()


@router.post("/", response_model=schemas.StockResponse, status_code=201)
def create_stock(stock: schemas.StockCreate, db: Session = Depends(get_db)):
    """新しい銘柄を登録する。ticker_code が重複する場合は 409 を返す"""
    existing = db.query(models.Stock).filter(
        models.Stock.ticker_code == stock.ticker_code
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="この ticker_code は既に登録されています")

    db_stock = models.Stock(**stock.model_dump())
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock


@router.delete("/{ticker_code}", status_code=204)
def delete_stock(ticker_code: str, db: Session = Depends(get_db)):
    """指定した ticker_code の銘柄を削除する。存在しない場合は 404 を返す"""
    db_stock = db.query(models.Stock).filter(
        models.Stock.ticker_code == ticker_code
    ).first()
    if not db_stock:
        raise HTTPException(status_code=404, detail="銘柄が見つかりません")

    db.delete(db_stock)
    db.commit()
