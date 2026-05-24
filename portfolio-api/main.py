import os
import sys

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import auth
from routers import stocks, holdings

# 起動時に Alembic マイグレーションを head まで適用する（スキーマ管理は Alembic が担う）。
# Start Command に依存せず、デプロイ環境でも確実に最新スキーマへ揃える。
try:
    _alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
    command.upgrade(_alembic_cfg, "head")
except Exception as e:
    print(f"ERROR: マイグレーションに失敗しました: {e}", file=sys.stderr)
    sys.exit(1)

app = FastAPI(
    title="株式ポートフォリオ API",
    description="銘柄マスタと保有株（取引履歴）を管理するREST API",
    version="1.0.0",
)

_raw_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:4200")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(holdings.router)


@app.get("/", tags=["ヘルスチェック"])
def root():
    """APIの死活確認用エンドポイント"""
    return {"status": "ok", "message": "株式ポートフォリオ API is running"}
