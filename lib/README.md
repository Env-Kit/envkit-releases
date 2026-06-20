# EnvKit service binaries (`lib/`)

EnvKit mirrors the bundled service archives on **this** repo so installs don't
depend on flaky/slow upstreams (MariaDB archive, dev.mysql.com, fastdl, …).

> **Why aren't the `.zip` files committed here?** GitHub rejects any file over
> **100 MB** on `git push` — and several archives are much larger (MongoDB 620 MB,
> PostgreSQL 311 MB, MySQL 8 243 MB). So the binaries are hosted as **release
> assets** on the [`services`](https://github.com/Env-Kit/envkit-releases/releases/tag/services)
> release, and this folder is the committed **index** of them.

## Download all services

```bash
node lib/download-all.mjs            # → ./services-cache/, sha256-verified
```

The app downloads from these same URLs (mirror first, upstream fallback).

## Contents

| Service | Version | File | Size |
|---|---|---|---|
| nginx | 1.26.2 | `nginx-1.26.2.zip` | 2 MB |
| Apache | 2.4.68 | `apache-2.4.68.zip` | 13 MB |
| PHP | 8.5.6 | `php-8.5.6.zip` | 34 MB |
| MariaDB | 10.11.10 | `mysql-10.11.10.zip` | 86 MB |
| MySQL | 8.0.40 | `mysql-8.0.40.zip` | 232 MB |
| PostgreSQL | 17.2 | `postgres-17.2.zip` | 297 MB |
| MongoDB | 7.0.14 | `mongodb-7.0.14.zip` | 592 MB |
| Redis | 5.0.14.1 | `redis-5.0.14.1.zip` | 12 MB |
| Node.js | 26.2.0 | `nodejs-26.2.0.zip` | 37 MB |
| Mailpit | 1.21.8 | `mailpit-1.21.8.zip` | 8 MB |
| phpMyAdmin | 5.2.3 | `phpmyadmin-5.2.3.zip` | 16 MB |

Base URL: `https://github.com/Env-Kit/envkit-releases/releases/download/services/<file>`

Machine-readable index + checksums: [`services.json`](./services.json).

To add or refresh versions, run `scripts/mirror-services.mjs` in the private app
repo (it uploads to the `services` release and regenerates the manifest).
