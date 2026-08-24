#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

BUNDLE_DIR="${OC_OQ313_BUNDLE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
ROOTFS="${OC_OQ313_ROOTFS:-$BUNDLE_DIR/rootfs}"
EXPECTED_OQ_COMMIT="16dd69ecea0c6dcaf49c22ca12edc9da3f024889"

if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
  echo "offline OQ3.13 runtime requires Linux x86_64" >&2
  exit 2
fi

if [[ ! -d "$ROOTFS" ]]; then
  test -f "$BUNDLE_DIR/rootfs.tar.zst" || {
    echo "rootfs.tar.zst is missing from the offline bundle" >&2
    exit 2
  }
  mkdir -p "$ROOTFS"
  zstd -dc "$BUNDLE_DIR/rootfs.tar.zst" | tar -x -C "$ROOTFS"
fi

LOADER="$ROOTFS/lib/x86_64-linux-gnu/ld-2.31.so"
PYTHON="$ROOTFS/usr/local/bin/python3.8"
LIBS="$ROOTFS/usr/local/lib:$ROOTFS/lib/x86_64-linux-gnu:$ROOTFS/usr/lib/x86_64-linux-gnu"
SITE="$ROOTFS/opt/openquake/lib/python3.8/site-packages"

for required in \
  "$LOADER" \
  "$PYTHON" \
  "$SITE" \
  "$ROOTFS/usr/bin/git" \
  "$ROOTFS/opt/openquake/bin/oq" \
  "$ROOTFS/oq-engine/openquake" \
  "$ROOTFS/opencatastrophe-data/scripts"; do
  test -e "$required" || {
    echo "missing offline runtime path: $required" >&2
    exit 2
  }
done

HOME_DIR="$BUNDLE_DIR/.offline-home"
BIN_DIR="$BUNDLE_DIR/.offline-bin"
mkdir -p "$HOME_DIR" "$BIN_DIR"

cat > "$BIN_DIR/git" <<EOF
#!/usr/bin/env bash
exec "$LOADER" --library-path "$LIBS" "$ROOTFS/usr/bin/git" "\$@"
EOF

cat > "$BIN_DIR/oq" <<EOF
#!/usr/bin/env bash
exec /usr/bin/env \
  HOME="$HOME_DIR" \
  PATH="$BIN_DIR:/usr/bin:/bin" \
  PYTHONHOME="$ROOTFS/usr/local" \
  PYTHONPATH="/oq-engine:$SITE" \
  OQ_DISTRIBUTE=no \
  OPENBLAS_NUM_THREADS=1 \
  "$LOADER" --library-path "$LIBS" \
  "$PYTHON" "$ROOTFS/opt/openquake/bin/oq" "\$@"
EOF
chmod +x "$BIN_DIR/git" "$BIN_DIR/oq"

HOME="$HOME_DIR" "$BIN_DIR/git" config --global --unset-all safe.directory \
  >/dev/null 2>&1 || true
HOME="$HOME_DIR" "$BIN_DIR/git" config --global --add safe.directory \
  "$ROOTFS/oq-engine"

observed_commit="$(
  HOME="$HOME_DIR" "$BIN_DIR/git" -C "$ROOTFS/oq-engine" rev-parse HEAD
)"
if [[ "$observed_commit" != "$EXPECTED_OQ_COMMIT" ]]; then
  echo "offline OpenQuake source commit drifted: $observed_commit" >&2
  exit 2
fi

alias_created=false
if [[ -L /oq-engine ]]; then
  current_target="$(readlink -f /oq-engine)"
  expected_target="$(readlink -f "$ROOTFS/oq-engine")"
  if [[ "$current_target" != "$expected_target" ]]; then
    echo "/oq-engine points at a different runtime" >&2
    exit 2
  fi
elif [[ -e /oq-engine ]]; then
  echo "/oq-engine already exists and is not this offline runtime" >&2
  exit 2
else
  if ln -s "$ROOTFS/oq-engine" /oq-engine 2>/dev/null; then
    alias_created=true
  else
    echo "cannot create /oq-engine source alias; bounded offline execution requires root permission on this host" >&2
    exit 2
  fi
fi

cleanup() {
  if [[ "$alias_created" == true ]]; then
    rm -f /oq-engine
  fi
}
trap cleanup EXIT INT TERM

HOME="$HOME_DIR" "$BIN_DIR/git" config --global --add safe.directory /oq-engine

set +e
/usr/bin/env \
  HOME="$HOME_DIR" \
  PATH="$BIN_DIR:/usr/bin:/bin" \
  PYTHONHOME="$ROOTFS/usr/local" \
  PYTHONPATH="$ROOTFS/opencatastrophe-data:/oq-engine:$SITE" \
  OQ_DISTRIBUTE=no \
  OPENBLAS_NUM_THREADS=1 \
  "$LOADER" --library-path "$LIBS" "$PYTHON" "$@"
status=$?
set -e
exit "$status"

