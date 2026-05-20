# 株式ポートフォリオ API

Python + FastAPI で構築した株式ポートフォリオ管理用バックエンドAPI。  
銘柄マスタ（stocks）と保有株取引履歴（holdings）をCRUDで管理します。

---

## ローカル開発環境のセットアップ

### 1. リポジトリをクローン

```bash
git clone <repository-url>
cd portfolio-api
```

### 2. 仮想環境を作成・有効化

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数を設定

```bash
cp .env.example .env
# .env を編集して DATABASE_URL を設定する
```

Supabaseを使う場合は、Supabaseダッシュボード → Settings → Database → Connection string（URI）をコピーして設定してください。

### 5. サーバーを起動

```bash
uvicorn main:app --reload
```

ブラウザで <http://localhost:8000/docs> を開くとSwagger UIが表示されます。

---

## APIエンドポイント一覧

| メソッド | パス | 説明 |
|---|---|---|
| GET | /stocks | 銘柄一覧取得 |
| POST | /stocks | 銘柄登録 |
| DELETE | /stocks/{ticker_code} | 銘柄削除 |
| GET | /holdings | 保有株一覧取得 |
| POST | /holdings | 取引登録（購入） |
| PUT | /holdings/{id} | 取引修正 |
| DELETE | /holdings/{id} | 取引削除 |

---

## Renderへのデプロイ手順

### 前提条件

- [Render](https://render.com/) アカウント
- GitHubにコードをプッシュ済み
- SupabaseなどのPostgreSQLデータベースが用意済み

### 手順

#### 1. Renderダッシュボードで新規Webサービスを作成

1. Renderにログインし、**New → Web Service** をクリック
2. GitHubリポジトリを選択し、`portfolio-api` ディレクトリを含むリポジトリを選択

#### 2. ビルド・起動設定

| 項目 | 設定値 |
|---|---|
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Root Directory** | `portfolio-api`（サブディレクトリの場合） |

#### 3. 環境変数を設定

Renderダッシュボードの **Environment** タブで以下を追加:

| Key | Value |
|---|---|
| `DATABASE_URL` | `postgresql://...`（SupabaseのConnection URI） |

#### 4. デプロイ

**Create Web Service** をクリックするとビルドが始まり、数分後にデプロイが完了します。

デプロイ後、`https://<your-service-name>.onrender.com/docs` でSwagger UIを確認できます。

### 注意事項

- Renderの無料プランはサービスが一定時間アクセスされないとスリープします。最初のリクエストに数秒かかる場合があります。
- `DATABASE_URL` は必ずRenderの環境変数に設定してください。ソースコードに直接書かないでください。
- Supabase接続はSSLが必要な場合があります。接続できない場合は `DATABASE_URL` の末尾に `?sslmode=require` を追加してください。

---

## プロジェクト構成

```
portfolio-api/
├── main.py          # FastAPIアプリ本体・CORS設定・ルーター登録
├── database.py      # DB接続・セッション管理
├── models.py        # SQLAlchemyモデル（テーブル定義）
├── schemas.py       # Pydanticスキーマ（リクエスト/レスポンス）
├── routers/
│   ├── stocks.py    # 銘柄マスタAPIルーター
│   └── holdings.py  # 保有株APIルーター
├── requirements.txt
├── .env.example     # 環境変数サンプル
└── README.md
```
