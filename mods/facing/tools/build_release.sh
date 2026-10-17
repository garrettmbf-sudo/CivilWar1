#!/usr/bin/env bash
# Build, test and package the Facing mod as a release zip in ${DIST:-/workspace/dist}.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
dist="${DIST:-/workspace/dist}"
cd "$here"
[ -f .hos-libs/Assembly-CSharp.dll ] || ./tools/fetch_libs.sh
dotnet build -c Release HexOfSteelFacing.csproj
dotnet test tests/FacingMath.Tests/FacingMath.Tests.csproj
ver=$(python3 -c "import json;print(json.load(open('ModPackage/Manifest.json'))['modVersion'])")
stage="$(mktemp -d)/Facing"
mkdir -p "$stage/Libraries"
cp ModPackage/Manifest.json ModPackage/FacingConfig.json "$stage/"
[ -f ModPackage/Thumbnail.jpg ] && cp ModPackage/Thumbnail.jpg "$stage/"
cp INSTALL.md TESTING.md "$stage/"
cp output/HexOfSteelFacing.dll "$stage/Libraries/"
mkdir -p "$dist"
zip="$dist/HexOfSteelFacing-$ver.zip"
rm -f "$zip"
python3 -c "import shutil,sys; shutil.make_archive(sys.argv[1][:-4], 'zip', sys.argv[2], 'Facing')" "$zip" "$(dirname "$stage")"
sha256sum "$zip" "$stage/Libraries/HexOfSteelFacing.dll" | tee "$dist/HexOfSteelFacing-$ver.sha256"
echo "built $zip"
