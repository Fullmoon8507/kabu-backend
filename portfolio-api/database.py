import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# .env ファイルから環境変数を読み込む
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # import時ではなく明示的なエラーメッセージをstderrに出してから終了する
    print("ERROR: DATABASE_URL が設定されていません。Renderの環境変数を確認してください。", file=sys.stderr)
    sys.exit(1)

# PostgreSQL接続エンジンの作成
# pool_pre_ping=True: 接続が切れていた場合に自動再接続する
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# セッションファクトリ（各リクエストごとにセッションを生成する）
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 全モデルの基底クラス
Base = declarative_base()


def get_db():
    """FastAPIの依存性注入用DBセッションジェネレータ"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
