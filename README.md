# react-fastapi-prototype

## 概要

**react-fastapi-prototype**は、「開発初期に即アプリを立ち上げ、ロジックに集中するための最小構成テンプレート」です。

React (Vite) + FastAPI + MySQLを**Docker Compose**で統合し、
Caddyによるリバースプロキシで**単一ポート運用**を実現します。

---

## このテンプレートの思想

### ポイント

* **最短で動く**：`docker compose up --profile dev`ですぐ立ち上がる
* **単一ポート構成**：Caddyが `/api`をFastAPIに、それ以外をReactに振り分け
* **開発/本番をprofileで切り分け**

  * `dev`：ViteのHMR（5173）を使いながら即時開発
  * `prod`：HTTPS + 独自ドメイン + 静的配信（ビルド済み）
* **HTTPS/独自ドメイン対応を最速で導入**：Let's Encryptによる自動証明書発行
* **Todo アプリ付き**：起動直後に動作確認可能

### あえてしていないこと

* マイグレーション（Alembic 等）未搭載
* パフォーマンス最適化（キャッシュ、マルチステージビルド）未実装
* 長期運用を想定したCI/CD構成や環境分離は最小限

> **目的は「最初のロジックを書き始めるまでの障壁を極限まで減らすこと」。**
>
> プロトタイプ段階では「動くこと」を最優先。
> 長期開発や本番運用では、このテンプレを基盤に自由に拡張してください。

---

## プロファイル運用

| profile  | 用途        | 特徴                             | 公開ポート               |
| -------- | --------- | ------------------------------ | ------------------- |
| **dev**  | 開発・HMRあり  | Vite dev server (5173) をそのまま利用 | 5173 |
| **prod** | 本番・サービス公開 | HTTPS + 独自ドメイン + 静的配信          | 80 / 443            |

---

## 開発（profile=dev）

開発時はホットリロード（HMR）を有効にし、
**Caddyが`/api`をFastAPIに、それ以外をViteに転送**します。

### 起動手順

```bash
docker compose --profile dev up
```

### アクセス

* React(Vite)：[http://localhost:5173](http://localhost:5173)
* FastAPI：Caddy経由で`/api`パスにアクセス

---

## 本番（profile=prod）

本番では、Viteをビルドして静的配信します。
Caddyが**Let's Encrypt で自動的に証明書を発行し、HTTPS/独自ドメインで配信**します。

### .envの設定(ドメインとLet's Encrypt通知メールは本番のみ参照)

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

### 起動コマンド

```bash
docker compose --profile prod up
```

### アクセス

* HTTPS：`https://<SITE_DOMAIN>`
* 自動リダイレクト：`http://<SITE_DOMAIN>` → `https://<SITE_DOMAIN>`

---

## 構成概要

```
├── Caddyfile                 # dev用
├── Caddyfile.prod            # prod用（HTTPS対応）
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

## ポート構成とプロキシ挙動

| コンポーネント                | ポート    | 用途                  |
| ---------------------- | ------ | ------------------- |
| **frontend(Vite)**    | 5173   | 開発時のみHMR用         |
| **backend(FastAPI)**  | 8000   | APIサーバ             |
| **db(MySQL)**         | 3306   | DB                  |
| **proxy-dev(Caddy)**  | 5173   | 開発時：単一ポートに見せるリバプロ   |
| **proxy-prod(Caddy)** | 80/443 | 本番：HTTPS + 独自ドメイン配信 |

---

## 主要ファイル

### 開発用Caddyfile

```caddy
:5173 {
  handle /api* {
    reverse_proxy backend:8000
  }
  handle {
    reverse_proxy frontend:5173
  }
}
```

### 本番用Caddyfile.prod

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

## 使い分けのまとめ

| 環境     | コマンド                               | ポート    | HTTPS | 備考                     |
| ------ | ---------------------------------- | ------ | ----- | ---------------------- |
| **開発** | `docker compose --profile dev up`  | 5173   | ×     | HMR有効。|
| **本番** | `docker compose --profile prod up` | 80/443 | ○     | HTTPS + 独自ドメイン配信       |

---

## ReactからのAPIアクセス

```ts
// 現在のオリジンをそのまま利用
const API_BASE = `${window.location.origin}/api`
```

これにより、
**開発／本番で環境変数の切り替え不要**でAPI通信が行えます。

---

## このテンプレートが向いている人

* 個人・小規模でPoC／試作を即形にしたい
* HTTPS／独自ドメインを早期に組み込みたい
* チームに配布する共通テンプレを整備したい
* 開発・本番をprofile一つで明示的に切り替えたい

---

## License

MIT License
