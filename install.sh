#!/usr/bin/env bash
# EnvKit installer (macOS) — https://github.com/Env-Kit/envkit-releases
#
# EnvKit is a desktop app (Electron), so this drops EnvKit.app into /Applications
# rather than installing a CLI. It downloads the latest signed release, strips the
# Gatekeeper quarantine (EnvKit is signed but not yet notarized), and opens it.
#
# Usage:
#   Install / update:   curl -fsSL https://raw.githubusercontent.com/Env-Kit/envkit-releases/main/install.sh | bash
#         or:           wget -qO- <same-url> | bash
#   Uninstall:          curl -fsSL <same-url> | bash -s -- --uninstall
#
# Publish: this file lives in the PUBLIC Env-Kit/envkit-releases repo so the raw
# URL above resolves. The private source copy is envkit/install.sh.

set -euo pipefail

# ── Constants ────────────────────────────────────────────────────────────────
REPO="${ENVKIT_REPO:-Env-Kit/envkit-releases}"
APP="EnvKit.app"
APPS_DIR="${ENVKIT_APPS_DIR:-/Applications}"
APP_PATH="${APPS_DIR}/${APP}"
DATA_DIR="$HOME/Library/Application Support/EnvKit"
LOG_DIR="$HOME/Library/Logs/EnvKit"

# ── Colors ───────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
  RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'
  CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
else
  RED=''; YELLOW=''; GREEN=''; CYAN=''; BOLD=''; RESET=''
fi

info()    { echo -e "  ${CYAN}-->${RESET} $*"; }
success() { echo -e "  ${GREEN}✓${RESET}  $*"; }
warn()    { echo -e "  ${YELLOW}!${RESET}  $*"; }
error()   { echo -e "  ${RED}✗${RESET}  $*" >&2; }
die()     { error "$*"; exit 1; }
header()  { echo -e "\n${BOLD}$*${RESET}"; }
ask()     { echo -en "  ${BOLD}?${RESET}  $* [y/N] "; read -r _ans </dev/tty 2>/dev/null || true; [[ "${_ans:-}" =~ ^[Yy]$ ]]; }

# ── Platform detection (macOS / Apple Silicon only) ──────────────────────────
require_macos_arm64() {
  [ "$(uname -s)" = "Darwin" ] || die "EnvKit's installer is for macOS. On Windows, download the .exe from https://github.com/${REPO}/releases/latest"
  case "$(uname -m)" in
    arm64) : ;;
    x86_64)
      # Could still be an M-series under Rosetta — check the hardware.
      if [ "$(sysctl -n hw.optional.arm64 2>/dev/null || echo 0)" = "1" ]; then
        warn "Running under Rosetta; installing the native arm64 build."
      else
        die "EnvKit no longer supports Intel Macs — Apple Silicon (M-series) is required."
      fi
      ;;
    *) die "Unsupported architecture: $(uname -m)" ;;
  esac
}

# ── Download tool ────────────────────────────────────────────────────────────
_dl() {
  if command -v curl &>/dev/null; then echo curl
  elif command -v wget &>/dev/null; then echo wget
  else die "Neither curl nor wget found."; fi
}

fetch() {
  local url="$1" dest="$2"
  case "$(_dl)" in
    curl) curl -fSL --progress-bar "$url" -o "$dest" ;;
    wget) wget -q --show-progress "$url" -O "$dest" ;;
  esac
}

# ── Latest version via the releases/latest redirect (no API key, not rate-limited) ──
latest_version() {
  local url="https://github.com/${REPO}/releases/latest" location
  case "$(_dl)" in
    curl) location="$(curl -fsSLI --stderr /dev/null -H 'User-Agent: envkit-installer' "$url" | grep -i '^location:' | tail -1)" ;;
    wget) location="$(wget -qS --spider --header 'User-Agent: envkit-installer' "$url" 2>&1 | grep -i 'location:' | tail -1)" ;;
  esac
  echo "$location" | sed -E 's|.*/releases/tag/v?([^[:space:]]+).*|\1|' | tr -d '\r'
}

# ── Newest macOS arm64 asset, even when /releases/latest is a Windows-only build ──
# We cut Windows and macOS releases independently — a Windows-only release becomes
# /releases/latest with NO mac zip, so resolving the download from there 404s for
# Mac users. Instead, ask the API for the releases list (newest first) and take the
# first EnvKit-<ver>-arm64.zip we see. Mirrors the app's prepareFeedForPlatform().
# Drafts are hidden from the unauthenticated API; prereleases (betas) are included.
latest_mac_zip_url() {
  local api="https://api.github.com/repos/${REPO}/releases?per_page=30" json
  case "$(_dl)" in
    curl) json="$(curl -fsSL -H 'User-Agent: envkit-installer' -H 'Accept: application/vnd.github+json' "$api" 2>/dev/null || true)" ;;
    wget) json="$(wget -qO- --header 'User-Agent: envkit-installer' --header 'Accept: application/vnd.github+json' "$api" 2>/dev/null || true)" ;;
  esac
  [ -n "$json" ] || return 0
  echo "$json" \
    | grep -oE '"browser_download_url"[[:space:]]*:[[:space:]]*"[^"]*EnvKit-[^"]*-arm64\.zip"' \
    | sed -E 's/.*"(https[^"]+)"$/\1/' \
    | head -n1 | tr -d '\r'
}

installed_version() {
  local plist="${APP_PATH}/Contents/Info.plist"
  [ -f "$plist" ] || { echo ""; return; }
  /usr/bin/defaults read "${APP_PATH}/Contents/Info" CFBundleShortVersionString 2>/dev/null || echo ""
}

# ── Install / update ─────────────────────────────────────────────────────────
cmd_install() {
  header "Installing EnvKit"
  require_macos_arm64

  # Prefer the newest release that actually ships a mac arm64 zip (Windows-only
  # releases don't), and derive the version from that asset. Fall back to the
  # /releases/latest tag only if the API is unreachable (rate-limited/offline).
  local url asset version
  url="$(latest_mac_zip_url)"
  if [ -n "$url" ]; then
    asset="${url##*/}"                                              # EnvKit-<ver>-arm64.zip
    version="$(echo "$asset" | sed -E 's/^EnvKit-(.+)-arm64\.zip$/\1/')"
  else
    warn "Couldn't query the releases API; falling back to /releases/latest."
    version="$(latest_version)"
    [ -n "$version" ] || die "Could not resolve a macOS release. Check https://github.com/${REPO}/releases"
    asset="EnvKit-${version}-arm64.zip"
    url="https://github.com/${REPO}/releases/download/v${version}/${asset}"
  fi

  local current; current="$(installed_version)"
  if [ -n "$current" ] && [ "$current" = "$version" ]; then
    success "EnvKit v${version} is already installed and up to date."
    if ask "Reinstall anyway?"; then : ; else exit 0; fi
  fi

  # electron-builder emits EnvKit-<ver>-arm64.zip (what the auto-updater uses); the
  # zip extracts straight to EnvKit.app with no hdiutil mounting.
  local tmp; tmp="$(mktemp -d)"
  # Double-quoted so $tmp expands NOW (while still in scope) into a literal
  # path baked into the trap command — a single-quoted trap defers the lookup
  # to EXIT time, by which point this function (and its `local tmp`) has
  # already returned, so $tmp is unset under `set -u` ("unbound variable").
  trap "rm -rf '$tmp'" EXIT

  info "Downloading ${asset} ..."
  fetch "$url" "${tmp}/${asset}" || die "Download failed: ${url}"

  info "Extracting ..."
  # ditto preserves the app bundle + code signature better than unzip.
  ditto -x -k "${tmp}/${asset}" "${tmp}/extracted" 2>/dev/null || unzip -q "${tmp}/${asset}" -d "${tmp}/extracted"
  [ -d "${tmp}/extracted/${APP}" ] || die "Archive did not contain ${APP}"

  if [ -d "$APP_PATH" ]; then
    info "Removing the previous ${APP} ..."
    rm -rf "$APP_PATH" 2>/dev/null || sudo rm -rf "$APP_PATH"
  fi

  info "Installing to ${APPS_DIR} ..."
  if ! ditto "${tmp}/extracted/${APP}" "$APP_PATH" 2>/dev/null; then
    sudo ditto "${tmp}/extracted/${APP}" "$APP_PATH"
  fi

  # Signed but not notarized → clear the quarantine so Gatekeeper doesn't block
  # first launch (otherwise the user must right-click → Open).
  xattr -dr com.apple.quarantine "$APP_PATH" 2>/dev/null || true

  success "Installed EnvKit v${version} → ${APP_PATH}"
  info "Launching ..."
  open "$APP_PATH" || true
  echo ""
  echo -e "  ${CYAN}★${RESET}  A GitHub star helps others find EnvKit: https://github.com/${REPO}"
}

# ── Uninstall ────────────────────────────────────────────────────────────────
cmd_uninstall() {
  header "Uninstalling EnvKit"

  osascript -e 'quit app "EnvKit"' 2>/dev/null || true

  if [ -d "$APP_PATH" ]; then
    rm -rf "$APP_PATH" 2>/dev/null || sudo rm -rf "$APP_PATH"
    success "Removed ${APP_PATH}"
  else
    info "No app at ${APP_PATH}"
  fi

  warn "EnvKit's privileged helper, the /etc/resolver/test entry, and /etc/hosts lines"
  warn "are set up with admin rights — remove them from inside the app (Settings) BEFORE"
  warn "deleting it, or clean up manually. This script does not touch them (needs sudo)."

  if ask "Also remove EnvKit data + logs? (${DATA_DIR})"; then
    rm -rf "$DATA_DIR" "$LOG_DIR" 2>/dev/null || true
    # Some early builds used a lowercased dir.
    rm -rf "$HOME/Library/Application Support/envkit" "$HOME/Library/Logs/envkit" 2>/dev/null || true
    success "Removed data and logs"
  else
    info "Data kept at ${DATA_DIR}"
  fi

  success "EnvKit uninstalled"
}

# ── Entry point ──────────────────────────────────────────────────────────────
main() {
  echo -e "${BOLD}"
  echo "  EnvKit — local web-dev stack for macOS"
  echo -e "${RESET}  https://github.com/${REPO}\n"

  case "${1:-install}" in
    --update|-u|update)    cmd_install ;;
    --uninstall|uninstall) cmd_uninstall ;;
    --install|install|"")  cmd_install ;;
    --help|-h)
      echo "Usage: install.sh [--update | --uninstall]"
      echo "  (no args)     Install or update EnvKit (latest arm64 release)"
      echo "  --update      Same as install — fetch the latest"
      echo "  --uninstall   Remove EnvKit (asks about data)"
      ;;
    *) die "Unknown option: $1 (try --help)" ;;
  esac
}

# Run main when executed or piped to bash, not when sourced.
set +u
_src="${BASH_SOURCE[0]:-}"
set -u
if [[ -z "$_src" || "$_src" == "$0" ]]; then
  main "$@"
fi
unset _src
