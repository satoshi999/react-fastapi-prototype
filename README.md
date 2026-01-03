# react-fastapi-prototype

## 概要

**react-fastapi-prototype** は、「開発初期に即アプリを立ち上げ、ロジックに集中するための最小構成テンプレート」です。

React（Vite）+ FastAPI + MySQL を Docker Compose で統合し、**入口（外部公開）を1つに集約**して動かします。

## Quickstart

```bash
cp .env.example .env
docker compose --profile dev up
# open http://localhost:5173
```

---
## このテンプレートの特徴（思想）

### ポイント

- **最短で動く**：`docker compose --profile dev up` ですぐ立ち上がる
- **単一ポート構成**：Caddyが `/api` をFastAPIに、それ以外をReactに振り分け
  > 本テンプレでいう「単一ポート」とは、アプリケーションとして外部に公開する入口を1つに集約する、という意味です。
  > devは `localhost:5173`、prodは 80/443 を Caddy が受けます。
- **開発/本番をprofileで切り分け**
  - `dev`：ViteのHMR（5173）で即時開発（`/api` も同じ `localhost:5173` 配下）
  - `prod`：HTTPS + 独自ドメイン + 静的配信（ビルド済み）
- **HTTPS/独自ドメイン対応を最速で導入**：Let's Encryptによる自動証明書発行
- **Todoアプリ付き**：起動直後に動作確認可能

### あえてしていないこと

- マイグレーション（Alembic 等）未搭載
- パフォーマンス最適化（キャッシュ、マルチステージビルド）未実装
- 長期運用を想定したCI/CD構成や環境分離は最小限

> **目的は「最初のロジックを書き始めるまでの障壁を極限まで減らすこと」。**  
> プロトタイプ段階では「動くこと」を最優先。  
> 長期開発や本番運用では、このテンプレを基盤に自由に拡張してください。

---

## 前提条件

* Docker / Docker Compose が利用できること
* `prod` で運用する場合は **80/443 が外部から到達可能**であること（Firewall / Security Group 等）

---

## 起動手順

### 開発（dev）

```bash
cp .env.example .env
# .env の MySQL は必要に応じて変更
docker compose --profile dev up
```

※ 開発時は ホストの 5173 は Caddy（入口） が待ち受け、Vite は コンテナ内部で動作します（外部公開しません）。

* 入口（Frontend / API 共通）：[http://localhost:5173](http://localhost:5173)
  * Frontend：`/`
  * API：`/api/...`

---

### 本番（prod）

```bash
# .env に SITE_DOMAIN / ACME_EMAIL を設定
docker compose --profile prod up
```

※ prod は「変更が確実に反映されること」を優先し、`--profile prod up` 実行時に Frontend を毎回 build します。

* 入口（Frontend / API 共通）：`https://<SITE_DOMAIN>`

  * Frontend：`/`
  * API：`/api/...`
* `http://<SITE_DOMAIN>` は `https://<SITE_DOMAIN>` に自動リダイレクト

---

## 構成概要

```
├── Caddyfile                 # dev用
├── Caddyfile.prod            # prod用
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── app/main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── vite.config.ts
│   └── package.json
└── db/
    └── init/001_schema.sql
```

---

## ポート構成

### 開発（dev）

| 役割       | Service          | ホスト公開 | コンテナ内 | 備考             |
| -------- | ---------------- | ----: | ----: | -------------- |
| 入口       | proxy-dev（Caddy） |  5173 |  5173 | 入口を1つに集約       |
| Frontend | frontend（Vite）   |     - |  5173 | HMR 用（外部公開しない） |
| API      | backend（FastAPI） |     - |  8000 | 内部のみ           |
| DB       | db（MySQL）        |     - |  3306 | 内部のみ           |

### 本番（prod）

| 役割    | Service           |  ホスト公開 |  コンテナ内 | 備考             |
| ----- | ----------------- | -----: | -----: | -------------- |
| 入口    | proxy-prod（Caddy） | 80/443 | 80/443 | 入口を1つに集約       |
| build | frontend-build    |      - |      - | dist 生成（ビルド専用） |
| API   | backend（FastAPI）  |      - |   8000 | 内部のみ           |
| DB    | db（MySQL）         |      - |   3306 | 内部のみ           |

---

## 主要ファイル

### `.env` の設定（本番項目は prod のみ参照）

```bash
# ---- MySQL（共通） ----
DB_HOST=db
DB_USER=app
DB_PASSWORD=app_pw
DB_ROOT_PASSWORD=password
DB_NAME=appdb

# ---- 本番のみ使用 ----
SITE_DOMAIN=example.com           # または 13.112.109.54.nip.io
ACME_EMAIL=admin@example.com      # Let's Encrypt 通知用
```

* MySQL項目は dev/prod 共通で必須です。cp .env.example .env 後に必要に応じて変更してください。

### Caddyfile（dev）

```caddy
:5173 {
  handle /api/* {
    reverse_proxy backend:8000
  }
  handle {
    reverse_proxy frontend:5173
  }
}
```

### Caddyfile（prod）

```caddy
{
  email {$ACME_EMAIL}
  acme_ca https://acme-v02.api.letsencrypt.org/directory
}

http://{$SITE_DOMAIN} {
  redir https://{$SITE_DOMAIN}{uri}
}

https://{$SITE_DOMAIN} {
  @api path /api/*
  handle @api {
    reverse_proxy backend:8000
  }
  handle {
    root * /srv
    try_files {path} /index.html
    file_server
  }

  encode zstd gzip
  header {
    Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    X-Content-Type-Options "nosniff"
    X-Frame-Options "DENY"
    Referrer-Policy "strict-origin-when-cross-origin"
  }
}
```

---

## React からの API アクセス

```ts
// 現在のオリジンをそのまま利用
const API_BASE = `${window.location.origin}/api`
```

これにより、**開発／本番で環境変数の切り替え不要**で API 通信が行えます。

---

## このテンプレートが向いている人

* 個人・小規模で PoC／試作を即形にしたい
* 開発・本番を profile 一つで明示的に切り替えたい
* チームに配布する共通テンプレを整備したい

---

## License

MIT License
