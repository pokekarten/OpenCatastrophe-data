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
OQ_SOURCE="$ROOTFS/oq-engine"
OC_SOURCE="$ROOTFS/opencatastrophe-data"

for required in \
  "$LOADER" \
  "$PYTHON" \
  "$SITE" \
  "$ROOTFS/usr/bin/git" \
  "$ROOTFS/opt/openquake/bin/oq" \
  "$OQ_SOURCE/openquake" \
  "$OC_SOURCE/scripts"; do
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
  PYTHONPATH="$OQ_SOURCE:$SITE" \
  OQ_DISTRIBUTE=no \
  OPENBLAS_NUM_THREADS=1 \
  "$LOADER" --library-path "$LIBS" \
  "$PYTHON" "$ROOTFS/opt/openquake/bin/oq" "\$@"
EOF
chmod +x "$BIN_DIR/git" "$BIN_DIR/oq"

HOME="$HOME_DIR" "$BIN_DIR/git" config --global --unset-all safe.directory \
  >/dev/null 2>&1 || true
HOME="$HOME_DIR" "$BIN_DIR/git" config --global --add safe.directory \
  "$OQ_SOURCE"

observed_commit="$(
  HOME="$HOME_DIR" "$BIN_DIR/git" -C "$OQ_SOURCE" rev-parse HEAD
)"
if [[ "$observed_commit" != "$EXPECTED_OQ_COMMIT" ]]; then
  echo "offline OpenQuake source commit drifted: $observed_commit" >&2
  exit 2
fi

set +e
/usr/bin/env \
  HOME="$HOME_DIR" \
  PATH="$BIN_DIR:/usr/bin:/bin" \
  PYTHONHOME="$ROOTFS/usr/local" \
  PYTHONPATH="$OC_SOURCE:$OQ_SOURCE:$SITE" \
  OC_OQ313_ROOTFS="$ROOTFS" \
  OQ_DISTRIBUTE=no \
  OPENBLAS_NUM_THREADS=1 \
  "$LOADER" --library-path "$LIBS" "$PYTHON" "$@"
status=$?
set -e
exit "$status"
