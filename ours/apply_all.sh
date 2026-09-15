#!/usr/bin/env bash
# Reconstructs the exact HElib tree this artifact measures, from vanilla HElib,
# in two layers (see README.md for what each layer is and why it is separate).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$HERE/HElib-patched}"

if [ -d "$OUT" ]; then
  echo "refusing to overwrite existing directory: $OUT" >&2
  exit 1
fi

echo "[1/4] cloning vanilla HElib at the pinned commit..."
git clone --quiet https://github.com/homenc/HElib.git "$OUT"
git -C "$OUT" checkout --quiet 3e337a66a91a92d49de6a9505340826b0eb71081

echo "[2/4] applying layer 1 (aux-radix bootstrapping infrastructure)..."
git -C "$OUT" apply "$HERE/patches/layer1_infrastructure.patch"

echo "[3/4] applying layer 2 (this paper's order-4/order-6/composed evaluator)..."
patch -p0 "$OUT/src/extractDigits.cpp" < "$HERE/patches/layer2_order456_composed_extractDigits.patch"
patch -p0 "$OUT/src/recryption.cpp"    < "$HERE/patches/layer2_explicit_aux_recryption.patch"

echo "[4/4] verifying byte-for-byte against the shipped reference source..."
diff -q "$OUT/src/extractDigits.cpp" "$HERE/src/extractDigits.cpp" \
  && echo "    extractDigits.cpp: OK, matches ours/src/extractDigits.cpp exactly"
diff -q "$OUT/src/recryption.cpp" "$HERE/src/recryption.cpp" \
  && echo "    recryption.cpp: OK, matches ours/src/recryption.cpp exactly"

echo
echo "Done. Build $OUT as you would build HElib (see its INSTALL.md), then build"
echo "fatboot-driver/ against it -- see README.md."
