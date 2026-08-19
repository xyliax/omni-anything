#!/usr/bin/env bash
# Build a pinned project runtime profile without modifying third_party sources.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PROFILE="cuda13_vllm023"
PROFILE_DIR="$ROOT/infra/env/profiles/$PROFILE"
VENV="$ROOT/.venv-vllm023"
PYTHON="${PYTHON:-python3.12}"
GO_BIN="${GO_BIN:-go}"
GO_VERSION_REQUIRED="1.22.5"
GO_SHA256="904b924d435eaea086515bc63235b192ea441bd8c9b198c507e85009e6e4c7f0"
DOWNLOAD_MODELS=0
SKIP_GATEWAY=0

usage() {
  cat <<'EOF'
Usage: bash infra/env/setup.sh [options]

Options:
  --profile NAME    runtime profile (currently: cuda13_vllm023)
  --venv PATH       virtual environment path (default: .venv-vllm023)
  --python COMMAND  Python 3.12 executable (default: python3.12)
  --go COMMAND      Go >=1.22.5 executable (default: go)
  --download-models download model revisions locked by implemented experiments
  --skip-gateway    skip the Go gateway build
  -h, --help        show this help
EOF
}

while (( $# )); do
  case "$1" in
    --profile) PROFILE="$2"; PROFILE_DIR="$ROOT/infra/env/profiles/$2"; shift 2 ;;
    --venv) VENV="$(realpath -m "$2")"; shift 2 ;;
    --python) PYTHON="$2"; shift 2 ;;
    --go) GO_BIN="$2"; shift 2 ;;
    --download-models) DOWNLOAD_MODELS=1; shift ;;
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

command -v "$PYTHON" >/dev/null || { echo "Python 3.12 not found: $PYTHON" >&2; exit 1; }
"$PYTHON" - <<'PY'
import sys
if sys.version_info[:2] != (3, 12):
    raise SystemExit(f"Python 3.12 is required, found {sys.version.split()[0]}")
PY
command -v nvidia-smi >/dev/null || { echo "nvidia-smi is required" >&2; exit 1; }
[[ "$(uname -s)-$(uname -m)" == "Linux-x86_64" ]] || {
  echo "the pinned vLLM wheel is validated only on Linux x86_64" >&2
  exit 1
}
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
      curl --fail --location --retry 3 --output "$ARCHIVE" \
        "https://dl.google.com/go/go$GO_VERSION_REQUIRED.linux-amd64.tar.gz"
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
  "$PYTHON" -m venv "$VENV"
fi
"$VENV/bin/python" -m pip install --upgrade "pip==26.1.0"
"$VENV/bin/python" -m pip install --require-hashes --only-binary=:all: \
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
  (cd "$ROOT" && "$VENV/bin/python" - <<'PY'
from experiments.shared import model
from huggingface_hub import snapshot_download
path = snapshot_download(repo_id=model.ID, revision=model.REVISION)
print(f"model snapshot: {path}")
PY
  )
fi

"$VENV/bin/python" -m pip freeze > "$VENV/omni-anything-resolved.txt"
python3 "$ROOT/infra/env/verify.py" --worker-python "$VENV/bin/python"

cat <<EOF

Environment ready.
Profile: $PROFILE
Worker Python: $VENV/bin/python
Resolved lock: $VENV/omni-anything-resolved.txt

Plan a run:
  python -m experiments.baseline --trace
EOF
if (( ! DOWNLOAD_MODELS )); then
  echo "Download pinned experiment models before GPU runs: bash infra/env/setup.sh --download-models"
fi
