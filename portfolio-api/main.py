from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
from database import engine
from routers import stocks, holdings

# データベース接続時に全テーブルを自動作成する
models.Base.metadata.create_all(bind=engine)

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
