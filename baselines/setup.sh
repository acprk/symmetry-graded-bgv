#!/usr/bin/env bash
# Clone the three baselines at the exact commits measured in the paper.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$HERE/_upstream"
mkdir -p "$OUT"

clone_at() {
  local url="$1" dir="$2" commit="$3"
  if [ -d "$OUT/$dir/.git" ]; then
    echo "[skip] $dir already present"
    return
  fi
  echo "[clone] $url @ $commit -> $dir"
  git clone --quiet "$url" "$OUT/$dir"
  git -C "$OUT/$dir" checkout --quiet "$commit"
}

clone_at https://github.com/msh086/BGV-Boot-for-Large-p.git \
         BGV-Boot-for-Large-p 83b54d534ef36776c912ca49247d1e3157509299

clone_at https://github.com/Nobody673/artifact-helib.git \
         artifact-helib e8b9cab0908e994a8f2d7b9b2c3dda02bf135c32

clone_at https://github.com/KULeuven-COSIC/Bootstrapping_Polyfunctions.git \
         Bootstrapping_Polyfunctions fc27e5461815499c1d6366a1d73ec7e39087b2cd

clone_at https://github.com/homenc/HElib.git \
         HElib-vanilla 3e337a66a91a92d49de6a9505340826b0eb71081

echo
echo "Done. Each baseline has its own build instructions in _upstream/<name>/README.md."
echo "For Zhao et al. (artifact-helib), apply one of patches/GN*.patch to HElib-vanilla"
echo "before building -- see README.md in this directory."
