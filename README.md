<div align="center">

<img src="brand/envkit-light.svg" alt="EnvKit logo" width="92" />

<img src="brand/envkit-bannner.png" alt="EnvKit — Your local stack, one place." width="880" />

# EnvKit — local development environment for Windows

**Your local stack, one place.** A free Laragon / XAMPP / Herd alternative.

EnvKit is a Windows desktop app that runs your entire local web-development stack — nginx **or**
Apache, multiple PHP versions, MySQL/MariaDB, PostgreSQL, Redis, MongoDB, Mailpit, Node.js,
Python, phpMyAdmin, trusted `.test` HTTPS, and PATH sync — from one modern tray app. Build
Laravel, WordPress, PHP, and Node/React/Next.js sites locally with one-click services and
trusted local SSL. It can even be **driven by an AI assistant** (Claude Code / Desktop, Cursor,
Windsurf, VS Code, Zed, OpenCode, Gemini CLI) through a built-in MCP server.

[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0d9488)](#requirements)
[![Price](https://img.shields.io/badge/price-Free-2563eb)](#install)
[![Download](https://img.shields.io/badge/download-latest%20release-2dd4aa)](https://github.com/Env-Kit/envkit-releases/releases/latest)

</div>

---

> **This repository is the public home for EnvKit releases & documentation.** Grab the
> installer from the [**Releases**](https://github.com/Env-Kit/envkit-releases/releases/latest)
> page. The application source is maintained privately.

## Install

Download the latest **`EnvKit-Setup-x.y.z.exe`** from the
[releases page](https://github.com/Env-Kit/envkit-releases/releases/latest) and run it.

EnvKit **auto-updates**: once installed, it checks GitHub for new releases and installs them
silently in place (Settings → Updates lets you check/download manually). On first launch a
short **onboarding wizard** asks your source — **Load from Laragon** (a guided detect →
import flow, including databases) or **Start fresh** (pick your stack and install the
runtimes it needs).

Upgrading from a previous version? Your data directory, certificates, and settings are
**migrated automatically** on first launch — nothing to do.

## Requirements

- Windows 10 / 11

## Screenshots

**Dashboard**

<img src="art/dashboard.png" alt="EnvKit dashboard" width="920" />

**Sites**

<img src="art/sites.png" alt="EnvKit sites" width="920" />

**Services**

<img src="art/services.png" alt="EnvKit services" width="920" />

**Tools**

<img src="art/tools.png" alt="EnvKit tools" width="920" />

**AI (MCP)**

<img src="art/ai.png" alt="EnvKit AI / MCP" width="920" />

**Settings**

<img src="art/settings.png" alt="EnvKit settings" width="920" />

## Highlights

- **nginx _or_ Apache**, switchable in Settings — PHP via FastCGI on both.
- **Trusted `.test` HTTPS** for every site via an auto-installed local CA.
- **Multiple PHP versions** with **per-site isolation** and **Xdebug on-demand**.
- **Bundled databases & tools** — MySQL/MariaDB, PostgreSQL, Redis, **MongoDB**, **Mailpit**,
  Node.js, **Python**, phpMyAdmin, plus Composer/Git/gh/nvm/ngrok/Cmder installers.
- **Node / React / Next.js dev sites** reverse-proxied at `.test` HTTPS with **hot-reload**.
- **Laravel Reverb (WebSockets)** — one-click install, supervise, and proxy per site.
- **Import from Laragon** — projects **and** databases (incl. MySQL → MariaDB transfer).
- **Diagnose & self-heal services** — find port conflicts / stale PIDs / bad configs and
  repair them.
- **AI control via MCP** — let Claude Code/Desktop, Cursor, Windsurf, VS Code, Zed, OpenCode,
  or Gemini CLI operate your stack: add/remove sites, manage MySQL databases, start/stop and
  diagnose services.
- **Clean PATH, your way** — sync to the **user** or **system (Machine)** PATH, with stale
  entries pruned and **competing stacks (Laragon/XAMPP/WAMP/MAMP/Herd…) auto-removed** so
  nothing shadows EnvKit's `php`/`mysql`/`nginx`.
- **Light/dark, fully translated (EN + AR, RTL)** native UI in the tray.
- **Free to use** (proprietary — not open source) with **silent auto-update**.

## How EnvKit compares

A best-effort snapshot (mid-2026) against other popular local PHP stacks.

| Feature | **EnvKit** | Laravel Herd | Laragon | AppServ | XAMPP |
|---|:---:|:---:|:---:|:---:|:---:|
| Platform | Windows | macOS, Windows | Windows | Windows | Win / macOS / Linux |
| Price / license | Free · proprietary | Free + paid Pro | Free | Free | Free |
| Web server | nginx **+** Apache | nginx | Apache + nginx | Apache | Apache |
| Multiple PHP versions | ✅ | ✅ | ✅ | ❌ | ❌ |
| Per-site PHP isolation | ✅ | ✅ | 🟡 | ❌ | ❌ |
| Auto `.test` domains | ✅ | ✅ | ✅ | ❌ | ❌ |
| Trusted local HTTPS | ✅ | ✅ | ✅ | ❌ | 🟡 manual |
| MySQL / MariaDB | ✅ | 💲 Pro | ✅ | ✅ | ✅ |
| PostgreSQL | ✅ | 💲 Pro | 🟡 | ❌ | ❌ |
| Redis | ✅ | 💲 Pro | 🟡 | ❌ | ❌ |
| MongoDB | ✅ | ❌ | 🟡 | ❌ | ❌ |
| DB web admin UIs (Postgres/Mongo) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Mail catcher (Mailpit) | ✅ | 💲 Pro | ❌ | ❌ | 🟡 Mercury |
| Node.js | ✅ | 🟡 | ✅ | ❌ | ❌ |
| Node/React/Next.js dev sites | ✅ | 🟡 | 🟡 | ❌ | ❌ |
| Laravel Reverb (WebSockets) | ✅ | 🟡 | ❌ | ❌ | ❌ |
| nvm + per-project `.nvmrc` | ✅ | ❌ | ❌ | ❌ | ❌ |
| Python | ✅ | ❌ | 🟡 | ❌ | ❌ |
| Composer / Laravel scaffolding | ✅ | ✅ | ✅ | ❌ | ❌ |
| Light / dark UI | ✅ | ✅ | 🟡 | ❌ | ❌ |
| Multi-language UI (+ RTL) | ✅ | ❌ | 🟡 | ❌ | ❌ |
| Import from Laragon (projects **+ databases**) | ✅ | ❌ | — | ❌ | ❌ |
| AI control via MCP | ✅ | ❌ | ❌ | ❌ | ❌ |
| Diagnose & self-heal services | ✅ | ❌ | ❌ | ❌ | ❌ |
| Auto-update | ✅ | ✅ | 🟡 | ❌ | ❌ |

<sub>✅ built-in · 🟡 partial / via add-on · ❌ not available · 💲 paid tier</sub>

## AI access (MCP)

EnvKit ships an MCP server so AI assistants can operate your local stack.

1. Open **Settings → AI** and toggle **Enable MCP server**.
2. Click **Set up AI clients** — EnvKit registers itself **globally** with Claude Code /
   Desktop, Cursor, Windsurf, VS Code, Zed, OpenCode, and Gemini CLI, and installs an
   `envkit` skill. (Or copy the shown URL config into your client's `mcpServers` yourself.)
3. **Restart your AI client**, then ask things like *"start redis"*, *"diagnose why mysql
   won't start, then repair it"*, or *"list my Laravel sites"*.

The endpoint is local-only (`http://127.0.0.1:<port>/mcp`), bearer-token authenticated, off
by default, and only works while EnvKit is running.

## Reporting issues

Found a bug or have a feature request?
[Open an issue](https://github.com/Env-Kit/envkit/issues). Please include your Windows
version, EnvKit version, and steps to reproduce.

## Team

EnvKit is built and maintained by:

- **Kirlos Osama** — [@ker00sama-dev](https://github.com/ker00sama-dev)
- **Youssef Yasser** — [@7aWy11](https://github.com/7aWy11)
- **Ziad Talaat** — [@zsnakeee](https://github.com/zsnakeee)

## License

**EnvKit is free to use**, but it is **not open source**. All rights reserved.

<div align="center">

<sub>EnvKit · <a href="https://github.com/Env-Kit">Env-Kit</a></sub>

</div>
