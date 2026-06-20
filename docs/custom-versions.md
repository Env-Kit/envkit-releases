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
| **Node.js** | ➜ via **nvm** | `22.11.0` | Settings → Node / nvm |
| **PHP** | ⤵ pick from list | — | windows.php.net (build-specific names) |
| **PostgreSQL** | ⤵ pick from list | — | EnterpriseDB (build-suffix in URL) |
| **Apache** | ⤵ pick from list | — | ApacheLounge (date-stamped builds) |
| **Python** | auto-detected | — | system interpreter on PATH |

### Why a few aren't free-form

PHP, PostgreSQL, and Apache name their Windows archives with extra build
metadata that can't be derived from the version number alone (PHP's
`-nts-Win32-vs17-x64`, PostgreSQL's `-1` build suffix, Apache's date + VS tag).
For those, use the dropdown and click **Refresh catalog** to pull the latest
list. **Node.js** is managed through nvm in **Settings → Node**, where you can
install any version.

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
