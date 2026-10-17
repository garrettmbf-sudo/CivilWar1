#!/usr/bin/env bash
# Copies the compile-time reference DLLs from the official Harmony template into .hos-libs/ (gitignored).
# These DLLs belong to War Frogs Studio / Unity / their authors: never commit or redistribute them.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"
git clone -q --depth 1 https://github.com/acorsicanfrog/Template-Mod-Harmony "$tmp/t"
mkdir -p "$here/.hos-libs"
cp "$tmp/t/Libraries/"*.dll "$here/.hos-libs/"
( cd "$tmp/t" && git log -1 --format='template commit %H %cd' ) | tee "$here/.hos-libs/SOURCE.txt"
sha256sum "$here/.hos-libs/Assembly-CSharp.dll" | tee -a "$here/.hos-libs/SOURCE.txt"
rm -rf "$tmp"
