# Installing a custom service version

EnvKit ships a curated version list per service, but you can install **any
released version** of several services without waiting for it to appear in the
dropdown.

## How to do it (in the app)

1. Open **Services** → click the service (e.g. **MySQL**).
2. In **Install versions**, find the **Custom version** field.
3. Type the version number (e.g. `8.0.39`) and click **Install version**.

EnvKit builds the download URL from the version, fetches it from **EnvKit's
GitHub mirror** first and falls back to the official upstream, extracts it, and
registers it side-by-side with any other installed versions. Switch between
installed versions any time from the same dropdown.

> Tip: the version dropdown also has a **Custom version** hint right under it
> showing an example for that service.

## Which services support a typed custom version

| Service | Custom version? | Example | Where it comes from |
|---|---|---|---|
| **MariaDB** (mysql) | ✅ | `10.11.10`, `11.4.4` | archive.mariadb.org |
| **MySQL** (mysql) | ✅ | `8.0.40`, `8.4.3` | dev.mysql.com |
| **nginx** | ✅ | `1.27.3` | nginx.org |
| **MongoDB** | ✅ | `7.0.14` | fastdl.mongodb.org |
| **Redis** | ✅ | `5.0.14.1` | github.com/tporadowski/redis |
| **Mailpit** | ✅ | `1.21.8` | github.com/axllent/mailpit |
| **phpMyAdmin** | ✅ | `5.2.3` | files.phpmyadmin.net |
| **PHP** | ✅ | `8.4.21`, `8.3.14` | windows.php.net |
| **Node.js** | ➜ via **nvm** | `22.11.0` | Settings → Node / nvm |
| **PostgreSQL** | ⤵ list or manual | — | EnterpriseDB (build-suffix in URL) |
| **Apache** | ⤵ pick from list | — | ApacheLounge (date-stamped builds) |
| **Python** | auto-detected | — | system interpreter on PATH |

PHP works too: the field tries `php-<v>-nts-Win32-vs17-x64.zip` for 8.4+ (vs16 for
8.0–8.3) and falls back to php.net's `/releases/archives/` for superseded patches.

### Why a couple aren't free-form

PostgreSQL and Apache name their Windows archives with build metadata that can't
be derived from the version number alone (PostgreSQL's `-1` build suffix, Apache's
date + VS tag). For those, use the dropdown + **Refresh catalog**, or the **manual
method** below. **Node.js** is managed through nvm in **Settings → Node**.

## Method 2 — add any version manually (Laragon-style)

Works for **every** service, including PostgreSQL and Apache. Bring your own build
from anywhere:

1. Download a Windows build of the service (e.g. PHP from windows.php.net,
   MySQL from dev.mysql.com, PostgreSQL from EnterpriseDB) and **extract** it.
2. Move the extracted folder into EnvKit's services directory — **one folder per
   version**, the folder name *is* the version:
   ```
   <DataDir>\services\<service>\<version>\
   ```
   e.g. `C:\ProgramData\envkit\services\php\8.4.21\` (with `php.exe` inside), or
   `…\services\mysql\8.4.3\` (with `bin\mysqld.exe`).
3. Open **Services → <service>** — the version now shows in the dropdown. Select it
   and click **Switch to <version>**.

EnvKit only counts a folder that contains the service's real binary (it checks for
`php.exe`, `mysqld.exe`, …), so junk folders are ignored. The exact path to drop
into is shown as a hint right under the version dropdown in the app.

## Notes

- **Side-by-side installs.** Each version installs into its own folder; nothing is
  overwritten. For databases, each version keeps its own data dir — switching
  engines (MariaDB ⇄ MySQL) is safe.
- **Mirror + fallback.** Custom versions download from EnvKit's
  [`services`](https://github.com/Env-Kit/envkit-releases/releases/tag/services)
  mirror when available, otherwise from the upstream above. A bad/typo'd version
  fails fast with a clear "not a valid archive" message.
- **Version format.** Digits and dots only (e.g. `8.0.40`); a leading `v` is
  stripped automatically.
