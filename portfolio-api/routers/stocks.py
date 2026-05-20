import os
from typing import List, Optional

import requests as req
import xlrd
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

import models
import schemas
from database import get_db

router = APIRouter(prefix="/stocks", tags=["銘柄マスタ"])

_JPX_URL = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"


@router.get("/", response_model=List[schemas.StockResponse])
def get_stocks(include_delisted: bool = False, db: Session = Depends(get_db)):
    """登録済み銘柄の一覧を返す。既定では上場中（is_active）のみ。

    include_delisted=true で上場廃止銘柄も含めた全件を返す。
    """
    query = db.query(models.Stock)
    if not include_delisted:
        query = query.filter(models.Stock.is_active.is_(True))
    return query.all()


@router.post("/seed")
def seed_stocks(
    x_admin_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """東証上場銘柄を JPX から取得して stocks テーブルに一括登録する"""
    seed_token = os.getenv("SEED_TOKEN")
    if seed_token and x_admin_token != seed_token:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = req.get(_JPX_URL, timeout=30)
        response.raise_for_status()
    except req.RequestException as e:
        raise HTTPException(status_code=502, detail=f"JPX からのダウンロードに失敗しました: {e}")

    wb = xlrd.open_workbook(file_contents=response.content)
    ws = wb.sheet_by_index(0)

    header_row = None
    headers: list[str] = []
    for i in range(min(5, ws.nrows)):
        vals = [str(ws.cell_value(i, c)) for c in range(ws.ncols)]
        if "コード" in vals:
            header_row = i
            headers = vals
            break

    if header_row is None:
        raise HTTPException(status_code=502, detail="Excel のヘッダー行が見つかりませんでした")

    def find_col(keyword: str) -> Optional[int]:
        for i, h in enumerate(headers):
            if keyword in h:
                return i
        return None

    idx_code = find_col("コード")
    idx_name = find_col("銘柄名")
    idx_market = find_col("市場")
    idx_sector = find_col("33業種区分")

    missing = [name for name, idx in [("コード", idx_code), ("銘柄名", idx_name), ("市場", idx_market)] if idx is None]
    if missing:
        raise HTTPException(status_code=502, detail=f"必須列が見つかりません: {missing}")

    stock_list = []
    for row_idx in range(header_row + 1, ws.nrows):
        code_val = ws.cell_value(row_idx, idx_code)
        if not code_val:
            continue
        market = str(ws.cell_value(row_idx, idx_market) or "")
        if "内国株式" not in market:
            continue
        code_str = str(code_val).strip()
        if code_str.endswith(".0"):
            code_str = code_str[:-2]
        code = code_str.zfill(4) if code_str.isdigit() else code_str
        company_name = str(ws.cell_value(row_idx, idx_name) or "").strip()
        if not company_name:
            continue
        sector = None
        if idx_sector is not None:
            sector_val = ws.cell_value(row_idx, idx_sector)
            if sector_val:
                sector = str(sector_val).strip() or None
        stock_list.append({
            "ticker_code": f"{code}.T",
            "company_name": company_name,
            "sector": sector,
        })

    # 同一 ticker_code が重複すると ON CONFLICT DO UPDATE が失敗するため一意化する
    # （後勝ち。最新リスト由来なので実害はない）
    deduped = {s["ticker_code"]: s for s in stock_list}
    stock_list = list(deduped.values())
    current_codes = set(deduped.keys())

    if not stock_list:
        return {"inserted": 0, "updated": 0, "delisted": 0, "total": 0}

    # 取り込み前の既存 ticker_code を取得し、新規/更新の件数を正確に算出する
    existing_codes = {
        code
        for (code,) in db.query(models.Stock.ticker_code).filter(
            models.Stock.ticker_code.in_(current_codes)
        )
    }
    inserted = len(current_codes - existing_codes)
    updated = len(current_codes & existing_codes)

    # 既存銘柄は社名・セクターを最新化し、廃止扱いだった銘柄は is_active を復帰させる
    stmt = pg_insert(models.Stock).values(stock_list)
    stmt = stmt.on_conflict_do_update(
        index_elements=["ticker_code"],
        set_={
            "company_name": stmt.excluded.company_name,
            "sector": stmt.excluded.sector,
            "is_active": True,
        },
    )
    db.execute(stmt)

    # 最新リストに無い銘柄は上場廃止とみなし論理削除する（物理削除しないので holdings の参照は保持）
    delisted = (
        db.query(models.Stock)
        .filter(
            models.Stock.is_active.is_(True),
            models.Stock.ticker_code.notin_(current_codes),
        )
        .update({"is_active": False}, synchronize_session=False)
    )

    db.commit()

    return {
        "inserted": inserted,
        "updated": updated,
        "delisted": delisted,
        "total": len(stock_list),
    }


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
