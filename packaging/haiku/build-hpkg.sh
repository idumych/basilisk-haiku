#!/bin/sh
# Build basilisk-<version>-<revision>-x86_64.hpkg from a packaged objdir.
#
#   ./mach package          # stages $OBJDIR/dist/basilisk
#   packaging/haiku/build-hpkg.sh [OBJDIR] [OUTDIR] [REVISION]
#
# Installs to apps/Basilisk with a Deskbar menu link and bin/basilisk.
# Run on Haiku (needs package, mimeset). Unofficial community port.
set -e

here=$(cd "$(dirname "$0")" && pwd)
objdir=${1:-${MOZ_OBJDIR:-obj}}
outdir=${2:-.}
revision=${3:-1}
appdir="$objdir/dist/basilisk"

if [ ! -x "$appdir/basilisk" ]; then
	echo "build-hpkg.sh: $appdir/basilisk not found; run ./mach package first" >&2
	exit 1
fi

# Version from application.ini; hpkg versions may not contain '-'.
version=$(sed -n 's/^Version=//p' "$appdir/application.ini" | head -n 1 | tr '-' '_')
[ -n "$version" ] || { echo "build-hpkg.sh: no Version in application.ini" >&2; exit 1; }

stage=$(mktemp -d "${TMPDIR:-/tmp}/basilisk-hpkg.XXXXXX")
trap 'rm -rf "$stage"' EXIT

mkdir -p "$stage/apps/Basilisk" "$stage/bin" \
	"$stage/data/deskbar/menu/Applications"
cp -a "$appdir/." "$stage/apps/Basilisk/"
ln -s ../../../../apps/Basilisk/basilisk \
	"$stage/data/deskbar/menu/Applications/Basilisk"
ln -s ../apps/Basilisk/basilisk "$stage/bin/basilisk"

# Make sure Tracker sees the app signature/icon attached at link time.
mimeset -f "$stage/apps/Basilisk/basilisk" "$stage/apps/Basilisk/basilisk-bin" \
	2>/dev/null || true

sed -e "s/@VERSION@/$version/g" -e "s/@REVISION@/$revision/g" \
	"$here/PackageInfo.in" > "$stage/.PackageInfo"

mkdir -p "$outdir"
out="$outdir/basilisk-$version-$revision-x86_64.hpkg"
rm -f "$out"
package create -C "$stage" -i "$stage/.PackageInfo" "$out"
echo "$out"
