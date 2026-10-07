#!/bin/sh
set -eu

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo=$(CDPATH= cd -- "$here/../.." && pwd)
out_root=${1:-${SKILLRY_STORAGE_OUTPUT_DIR:-"$here/build"}}
out="$out_root/Skillry Storage.app"
sdk=$(xcrun --sdk macosx --show-sdk-path)
arch=$(uname -m)

if [ -e "$out" ]; then
    printf '%s\n' "Output already exists: $out" >&2
    exit 1
fi
mkdir -p "$out/Contents/MacOS" "$out/Contents/Resources/engine"
cp "$here/Info.plist" "$out/Contents/Info.plist"
build_version=$(date -u +%Y%m%d%H%M%S)
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $build_version" "$out/Contents/Info.plist"
cp "$repo/tools/storage.py" "$out/Contents/Resources/engine/storage.py"
cp -R "$repo/tools/storage" "$out/Contents/Resources/engine/storage"

xcrun swiftc -O -parse-as-library -target "$arch-apple-macosx13.0" -sdk "$sdk" \
    "$here"/Sources/*.swift -framework AppKit -framework Security -framework ServiceManagement \
    -o "$out/Contents/MacOS/SkillryStorage"
codesign --force --sign - "$out"
printf '%s\n' "$out"
