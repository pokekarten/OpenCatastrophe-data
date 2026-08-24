<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# OpenQuake 3.13 offline Linux runtime bundle

## Purpose

Provide a portable Linux/amd64 runtime checkpoint for the bounded EQ1 Kosovo
OpenQuake 3.13 `reconstructed_experiment` lane so runtime probing and later
model execution do not have to rebuild the old Python 3.8/OpenQuake dependency
stack from the network every time.

The bundle is an **engineering/reproducibility artifact**, not scientific
validation or model-use authority.

## Exact runtime fence

The workflow freezes the same runtime identities already used by the trusted
Kosovo runner:

- bootstrap image: `openquake/engine:3.13.0`;
- exact OpenQuake source commit:
  `16dd69ecea0c6dcaf49c22ca12edc9da3f024889`;
- expected OpenQuake version: `3.13.0-git16dd69ecea`;
- Python: 3.8;
- expected dependency versions:
  - h5py 3.1.0;
  - NumPy 1.20.0;
  - pandas 1.1.5;
  - psutil 5.6.7;
  - pyzmq 19.0.0;
  - SciPy 1.4.1;
  - Shapely 1.7.1.

The exact bootstrap image repository digest and resulting execution image ID
are recorded in `manifest.json` for every produced artifact.

## Artifact contents

The generated artifact contains:

- `rootfs.tar.zst` — exported Linux root filesystem containing the pinned
  OpenQuake runtime and the exact OpenCatastrophe-data source revision;
- `manifest.json` — runtime/repository/provenance receipt;
- `SHA256SUMS` — local file-integrity checks;
- `offline-probe.sh` — minimal root/chroot probe for Linux hosts;
- `README.txt` — compact usage note.

The source checkout embedded in the rootfs excludes `.git`; its exact Git SHA
is carried in `manifest.json`.

## Deliberate data boundary

The bundle contains **no EFEHR/ESRM20 provider bytes**. This preserves the
current external-data boundary and avoids turning an engineering runtime cache
into a provider-data mirror.

For a real offline model run, separately receipted provider inputs must be
mounted or copied into the extracted rootfs. Those bytes retain their own
source, rights, hash, and scientific-role evidence. A later exact-scope data
bundle can be handled separately if rights/publication policy allows it.

## Offline use

Requirements on the host:

- Linux x86-64;
- root privileges or another mechanism capable of entering the rootfs;
- `zstd`, `tar`, and `chroot` for the supplied helper.

After downloading and extracting the GitHub Actions artifact:

```bash
sha256sum -c SHA256SUMS
./offline-probe.sh
```

The helper expands `rootfs.tar.zst` into `rootfs/` on first use and prints the
Python and OpenQuake versions from inside the rootfs.

The ChatGPT execution environment used during development is itself Linux
x86-64 and exposes `chroot`, so the same artifact can be materialized into the
chat workspace and probed without Docker once downloaded.

## Authority ceiling

A successful bundle build or offline probe establishes only that the pinned
runtime can be materialized and imported. It does not establish:

- successful Kosovo numerical execution;
- historical ESRM20 reproduction;
- benchmark agreement;
- scientific validity or independent validation;
- publication authorization for external provider bytes;
- model-use or production authority.

Those remain governed by the exact run/data evidence in #609 / #287 and the
source-specific component issues.
