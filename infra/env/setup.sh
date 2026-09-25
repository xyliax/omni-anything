#!/usr/bin/env bash
# Build a pinned project runtime profile without modifying third_party sources.
set -Eeuo pipefail
export LC_ALL=C.UTF-8

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PROFILE="cuda13_vllm023"
PROFILE_DIR="$ROOT/infra/env/profiles/$PROFILE"
VENV="$ROOT/.venv-vllm023"
PYTHON="${PYTHON:-python3.12}"
PYTHON_EXPLICIT=0
GO_BIN="${GO_BIN:-go}"
GO_VERSION_REQUIRED="1.22.5"
GO_SHA256="904b924d435eaea086515bc63235b192ea441bd8c9b198c507e85009e6e4c7f0"
DOWNLOAD_MODELS=0
MODEL_PRESET="qwen25_omni"
SKIP_GATEWAY=0
GPU=0

usage() {
  cat <<'EOF'
Usage: bash infra/env/setup.sh [options]

Options:
  --profile NAME    runtime profile (currently: cuda13_vllm023)
  --venv PATH       virtual environment path (default: .venv-vllm023)
  --python COMMAND  Python 3.12 executable (auto-bootstrap if default is absent)
  --go COMMAND      Go >=1.22.5 executable (default: go)
  --download-models download model revisions locked by implemented experiments
  --model-preset NAME qwen25_omni, minicpm_o45, or all (default: qwen25_omni)
  --gpu INDEX       GPU checked after installation (default: 0)
  --skip-gateway    skip the Go gateway build
  -h, --help        show this help
EOF
}

while (( $# )); do
  case "$1" in
    --profile) PROFILE="$2"; PROFILE_DIR="$ROOT/infra/env/profiles/$2"; shift 2 ;;
    --venv) VENV="$(realpath -m "$2")"; shift 2 ;;
    --python) PYTHON="$2"; PYTHON_EXPLICIT=1; shift 2 ;;
    --go) GO_BIN="$2"; shift 2 ;;
    --download-models) DOWNLOAD_MODELS=1; shift ;;
    --model-preset) MODEL_PRESET="$2"; shift 2 ;;
    --gpu) GPU="$2"; shift 2 ;;
    --skip-gateway) SKIP_GATEWAY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ "$PROFILE" != "cuda13_vllm023" || ! -d "$PROFILE_DIR" ]]; then
  echo "unsupported environment profile: $PROFILE" >&2
  echo "available profiles: cuda13_vllm023" >&2
  exit 2
fi

case "$MODEL_PRESET" in
  qwen25_omni|minicpm_o45|all) ;;
  *) echo "unknown model preset: $MODEL_PRESET" >&2; exit 2 ;;
esac
[[ "$GPU" =~ ^[0-9]+$ ]] || { echo "--gpu requires a nonnegative index" >&2; exit 2; }
[[ "$(uname -s)-$(uname -m)" == "Linux-x86_64" ]] || {
  echo "the pinned wheel profile requires Linux x86_64" >&2; exit 1;
}
for prerequisite in nvidia-smi patch cc c++; do
  command -v "$prerequisite" >/dev/null || {
    echo "Missing $prerequisite. On Ubuntu: sudo apt-get install build-essential patch curl ca-certificates" >&2
    exit 1
  }
done
nvidia-smi --id="$GPU" --query-gpu=name,driver_version --format=csv,noheader

# Use a local, verified uv binary only to supply missing Python; never alter
# system Python or ask its resolver to replace our hashed runtime lock.
if [[ -x "$VENV/bin/python" && "$PYTHON_EXPLICIT" == 0 ]]; then
  PYTHON="$VENV/bin/python"
elif ! command -v "$PYTHON" >/dev/null; then
  if (( PYTHON_EXPLICIT )); then
    echo "Python 3.12 not found: $PYTHON" >&2; exit 1
  fi
  UV_VERSION=0.8.15
  UV_SHA256=be9878e9d08ebcb621a683aba52e7fb8bbf92b2532e0d759026ffcc067673042
  UV_DIR="$ROOT/.tools/uv-$UV_VERSION"
  UV_ARCHIVE="$ROOT/.tools/uv-$UV_VERSION.tar.gz"
  mkdir -p "$UV_DIR"
  if [[ ! -x "$UV_DIR/uv" ]]; then
    command -v curl >/dev/null || { echo "curl is required to bootstrap Python" >&2; exit 1; }
    curl --fail --location --retry 3 --output "$UV_ARCHIVE.part" \
      "https://github.com/astral-sh/uv/releases/download/$UV_VERSION/uv-x86_64-unknown-linux-gnu.tar.gz"
    echo "$UV_SHA256  $UV_ARCHIVE.part" | sha256sum --check --status
    mv "$UV_ARCHIVE.part" "$UV_ARCHIVE"
    tar -xzf "$UV_ARCHIVE" --strip-components=1 -C "$UV_DIR"
  fi
  export UV_PYTHON_INSTALL_DIR="$ROOT/.tools/python"
  "$UV_DIR/uv" python install 3.12.11
  PYTHON="$("$UV_DIR/uv" python find --managed-python 3.12.11)"
fi
"$PYTHON" - <<'PY'
import sys
if sys.version_info[:2] != (3, 12):
    raise SystemExit(f"Python 3.12 is required, found {sys.version.split()[0]}")
PY
if (( ! SKIP_GATEWAY )); then
  GO_VERSION=""
  if command -v "$GO_BIN" >/dev/null; then
    GO_VERSION="$($GO_BIN env GOVERSION | sed 's/^go//')"
  fi
  OLDEST_VERSION="$(printf '%s\n' "$GO_VERSION_REQUIRED" "$GO_VERSION" | sort -V | head -1)"
  if [[ -z "$GO_VERSION" || "$OLDEST_VERSION" != "$GO_VERSION_REQUIRED" ]]; then
    GO_ROOT="$ROOT/.tools/go$GO_VERSION_REQUIRED"
    ARCHIVE="$ROOT/.tools/go$GO_VERSION_REQUIRED.linux-amd64.tar.gz"
    mkdir -p "$ROOT/.tools"
    if [[ ! -f "$ARCHIVE" ]]; then
      command -v curl >/dev/null || { echo "curl is required to bootstrap Go" >&2; exit 1; }
      curl --fail --location --retry 3 --output "$ARCHIVE.part" \
        "https://dl.google.com/go/go$GO_VERSION_REQUIRED.linux-amd64.tar.gz"
      echo "$GO_SHA256  $ARCHIVE.part" | sha256sum --check --status
      mv "$ARCHIVE.part" "$ARCHIVE"
    fi
    echo "$GO_SHA256  $ARCHIVE" | sha256sum --check --status || {
      echo "Go archive checksum mismatch: $ARCHIVE" >&2
      exit 1
    }
    if [[ ! -x "$GO_ROOT/bin/go" ]]; then
      mkdir -p "$GO_ROOT"
      tar -xzf "$ARCHIVE" --strip-components=1 -C "$GO_ROOT"
    fi
    GO_BIN="$GO_ROOT/bin/go"
    GO_VERSION="$($GO_BIN env GOVERSION | sed 's/^go//')"
    echo "using repository-local Go $GO_VERSION: $GO_BIN"
  fi
fi

if [[ ! -x "$VENV/bin/python" ]]; then
  "$PYTHON" -m venv "$VENV" || {
    echo "Python lacks venv support; install python3.12-venv or use --python with a complete Python 3.12." >&2
    exit 1
  }
fi
"$VENV/bin/python" -m pip install --upgrade "pip==26.1.0"
"$VENV/bin/python" -m pip install --require-hashes --only-binary=:all: --no-deps \
  -r "$PROFILE_DIR/requirements.lock"
"$VENV/bin/python" -m pip check

SITE_PACKAGES="$($VENV/bin/python - <<'PY'
import site
print(site.getsitepackages()[0])
PY
)"
FIX_TARGET="$SITE_PACKAGES/vllm/model_executor/layers/attention/mm_encoder_attention.py"
if ! grep -q "METRONOME FIX 1" "$FIX_TARGET"; then
  patch --batch --forward -d "$SITE_PACKAGES" -p1 \
    < "$PROFILE_DIR/patches/vllm-0.23-fix1.patch"
fi

CU13="$SITE_PACKAGES/nvidia/cu13"
if [[ -d "$CU13" ]]; then
  [[ -e "$CU13/lib64" ]] || ln -s lib "$CU13/lib64"
  if [[ -e "$CU13/lib/libcudart.so.13" && ! -e "$CU13/lib/libcudart.so" ]]; then
    ln -s libcudart.so.13 "$CU13/lib/libcudart.so"
  fi
else
  echo "CUDA 13 wheel layout not found at $CU13" >&2
  exit 1
fi

if (( ! SKIP_GATEWAY )); then
  mkdir -p "$ROOT/.build"
  (cd "$ROOT/third_party/metronome/gateway-go" && "$GO_BIN" build -o "$ROOT/.build/metronome-gateway" .)
  (cd "$ROOT/engines/conveyor/gateway" && "$GO_BIN" build -o "$ROOT/.build/conveyor-gateway" .)
fi

if (( DOWNLOAD_MODELS )); then
  (cd "$ROOT" && "$VENV/bin/python" - "$MODEL_PRESET" <<'PY'
import sys
from experiments.shared import model
from infra.run.probes import model_snapshot_issues
from huggingface_hub import snapshot_download
from pathlib import Path
presets = list(model.PRESETS) if sys.argv[1] == 'all' else [sys.argv[1]]
for preset in presets:
    selected = model.PRESETS[preset]
    path = snapshot_download(repo_id=selected['id'], revision=selected['revision'])
    issues = model_snapshot_issues(Path(path))
    if issues:
        raise SystemExit('\n'.join(issues))
    print(f"model snapshot: {path}")
PY
  )
fi

"$VENV/bin/python" -m pip freeze > "$VENV/omni-anything-resolved.txt"
"$VENV/bin/python" "$ROOT/infra/env/verify.py" --worker-python "$VENV/bin/python" --gpu "$GPU"

cat <<EOF

Environment ready.
Profile: $PROFILE
Worker Python: $VENV/bin/python
Resolved lock: $VENV/omni-anything-resolved.txt

Use this runtime in every shell (also handles a custom --venv):
  export OMNI_WORKER_PYTHON="$VENV/bin/python"
  source "$VENV/bin/activate"

Check real multi-session serving after downloading the selected models:
  python -m experiments.conveyor.check --gpu "$GPU" --model-preset "$MODEL_PRESET"
EOF
if (( ! DOWNLOAD_MODELS )); then
  echo "Download pinned experiment models before GPU runs: bash infra/env/setup.sh --download-models"
fi
