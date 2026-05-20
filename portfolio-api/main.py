import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

import models
from database import engine
from routers import stocks, holdings

# データベース接続時に全テーブルを自動作成する
try:
    models.Base.metadata.create_all(bind=engine)
    # 既存の stocks テーブルに is_active 列が無い場合は追加する（create_all は列追加を行わないため）
    insp = inspect(engine)
    cols = [c["name"] for c in insp.get_columns("stocks")]
    if "is_active" not in cols:
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE stocks ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"
            ))
except Exception as e:
    print(f"ERROR: データベース接続に失敗しました: {e}", file=sys.stderr)
    print("DATABASE_URL が正しいか確認してください。", file=sys.stderr)
    sys.exit(1)

app = FastAPI(
    title="株式ポートフォリオ API",
    description="銘柄マスタと保有株（取引履歴）を管理するREST API",
    version="1.0.0",
)

# CORS設定: 全オリジン・全メソッド・全ヘッダーを許可する
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(stocks.router)
app.include_router(holdings.router)


@app.get("/", tags=["ヘルスチェック"])
def root():
    """APIの死活確認用エンドポイント"""
    return {"status": "ok", "message": "株式ポートフォリオ API is running"}
