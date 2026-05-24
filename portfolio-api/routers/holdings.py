from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/holdings", tags=["保有株"])


@router.get("/", response_model=List[schemas.HoldingWithCompany])
def get_holdings(
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """保有株（取引履歴）の一覧を銘柄名付きで返す"""
    rows = (
        db.query(models.Holding, models.Stock.company_name)
        .join(models.Stock, models.Holding.ticker_code == models.Stock.ticker_code)
        .all()
    )
    return [
        {
            "id": h.id,
            "ticker_code": h.ticker_code,
            "company_name": name,
            "purchase_date": h.purchase_date,
            "purchase_price": h.purchase_price,
            "quantity": h.quantity,
            "note": h.note,
        }
        for h, name in rows
    ]


@router.post("/", response_model=schemas.HoldingResponse, status_code=201)
def create_holding(
    holding: schemas.HoldingCreate,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """新しい取引（購入）を登録する。ticker_code が stocks に存在しない場合は 404 を返す"""
    stock = db.query(models.Stock).filter(
        models.Stock.ticker_code == holding.ticker_code
    ).first()
    if not stock:
        raise HTTPException(
            status_code=404,
            detail=f"ticker_code '{holding.ticker_code}' は銘柄マスタに登録されていません"
        )

    db_holding = models.Holding(**holding.model_dump())
    db.add(db_holding)
    db.commit()
    db.refresh(db_holding)
    return db_holding


@router.put("/{holding_id}", response_model=schemas.HoldingResponse)
def update_holding(
    holding_id: int,
    holding_update: schemas.HoldingUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """指定 ID の取引を修正する。存在しない場合は 404 を返す"""
    db_holding = db.query(models.Holding).filter(
        models.Holding.id == holding_id
    ).first()
    if not db_holding:
        raise HTTPException(status_code=404, detail="取引が見つかりません")

    if holding_update.ticker_code is not None:
        stock = db.query(models.Stock).filter(
            models.Stock.ticker_code == holding_update.ticker_code
        ).first()
        if not stock:
            raise HTTPException(
                status_code=404,
                detail=f"ticker_code '{holding_update.ticker_code}' は銘柄マスタに登録されていません"
            )

    update_data = holding_update.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(db_holding, key, value)

    db.commit()
    db.refresh(db_holding)
    return db_holding


@router.delete("/{holding_id}", status_code=204)
def delete_holding(
    holding_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """指定 ID の取引を削除する。存在しない場合は 404 を返す"""
    db_holding = db.query(models.Holding).filter(
        models.Holding.id == holding_id
    ).first()
    if not db_holding:
        raise HTTPException(status_code=404, detail="取引が見つかりません")

    db.delete(db_holding)
    db.commit()
