<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# OpenQuake 3.13 offline Linux runtime bundle

## Purpose

Provide a portable Linux/amd64 runtime checkpoint for the bounded EQ1 Kosovo
OpenQuake 3.13 `reconstructed_experiment` lane so runtime probing and later
model execution do not have to rebuild the old Python 3.8/OpenQuake dependency
stack from network access every time.

The bundle is an **engineering/reproducibility artifact**, not scientific
validation or model-use authority.

## Exact runtime fence

The workflow freezes the same runtime identities already used by the trusted
Kosovo runner:

- bootstrap image: `openquake/engine:3.13.0`;
- exact OpenQuake source commit:
  `16dd69ecea0c6dcaf49c22ca12edc9da3f024889`;
- expected OpenQuake source version: `3.13.0-git16dd69ecea`;
- Python: 3.8;
- expected dependency versions:
  - h5py 3.1.0;
  - NumPy 1.20.0;
  - pandas 1.1.5;
  - psutil 5.6.7;
  - pyzmq 19.0.0;
  - SciPy 1.4.1;
  - Shapely 1.7.1.

The exact PR-head/default-branch source SHA, bootstrap image repository digest,
and resulting execution image ID are recorded in `manifest.json` for every
produced artifact. Pull-request builds explicitly checkout the PR head rather
than relying on GitHub's synthetic merge SHA.

## Artifact contents

The generated artifact contains:

- `rootfs.tar.zst` — exported Linux root filesystem containing the pinned
  OpenQuake runtime and exact OpenCatastrophe-data source revision;
- `manifest.json` — runtime/repository/provenance receipt;
- `SHA256SUMS` — local file-integrity checks;
- `offline-python.sh` — portable Linux launcher for arbitrary Python/module
  entry points through the pinned rootfs runtime;
- `offline-probe.sh` — exact Python/OpenQuake/dependency probe using that
  portable launcher;
- `README.txt` — compact usage note.

The source checkout embedded in the rootfs excludes `.git`; its exact Git SHA
is carried in `manifest.json`. The exact OpenQuake source checkout retains its
`.git` metadata because OpenQuake 3.13 derives the `-git<sha>` source-version
suffix from that checkout.

## Why portable execution instead of chroot

A Docker-exported rootfs is useful as a reproducible filesystem snapshot, but
a plain `chroot` is a poor fit for restricted execution sandboxes: container
runtimes can forbid bind-mounting `/proc` or recreating device nodes. OpenQuake
and `psutil` need normal Linux process information during realistic execution.

`offline-python.sh` therefore does **not** require Docker or chroot. On Linux
x86-64 it:

1. extracts `rootfs.tar.zst` once if needed;
2. invokes the rootfs glibc dynamic loader directly;
3. uses the rootfs Python 3.8 standard library and OpenQuake dependency set;
4. exposes the host `/proc` naturally to `psutil`;
5. creates a temporary `/oq-engine` alias so the existing bounded runner's
   immutable source-overlay contract is preserved;
6. supplies rootfs-backed `git` and `oq` wrappers so a child
   `oq engine --run ...` still executes the exact historical runtime;
7. removes the temporary source alias when the command exits.

This design was selected specifically so the same bundle can execute in the
Linux ChatGPT sandbox used during development, where Docker is unavailable and
bind mounts are prohibited.

## Deliberate data boundary

The bundle contains **no EFEHR/ESRM20 provider bytes**. This preserves the
current external-data boundary and avoids turning an engineering runtime cache
into a provider-data mirror.

For a real offline model run, separately receipted provider inputs must be
supplied outside the runtime bundle and staged at the paths required by the
bounded runner. Those bytes retain their own source, rights, hash, and
scientific-role evidence. A later exact-scope data bundle can be handled
separately if rights/publication policy allows it.

## Offline use

Requirements on the host:

- Linux x86-64;
- `zstd` and `tar` for first extraction;
- permission to create the temporary `/oq-engine` source alias. The current
  bounded runner therefore normally needs root privileges in this mode.

After downloading and extracting the GitHub Actions artifact:

```bash
sha256sum -c SHA256SUMS
./offline-probe.sh
```

Run an OpenCatastrophe Python entry point through the pinned runtime with:

```bash
./offline-python.sh -m <module> <arguments>
```

For example, the Kosovo action CLI can be inspected entirely offline:

```bash
./offline-python.sh \
  -m scripts.run_esrm20_kosovo_residential_ebrisk_openquake313_action \
  --help
```

A full numerical run still requires the separately receipted ESRM20 staging
inputs plus the run-specific runtime/resolved-runtime receipts expected by the
bounded action. The runtime bundle alone intentionally cannot invent or fetch
those scientific inputs.

## Development verification

The first prototype artifact was downloaded into the Linux ChatGPT execution
environment with outbound network unavailable. Its internal SHA-256 manifest
verified successfully. The portable execution approach then reproduced:

- Python `3.8.12`;
- OpenQuake `3.13.0-git16dd69ecea` from the exact `/oq-engine` source overlay;
- h5py `3.1.0`;
- NumPy `1.20.0`;
- pandas `1.1.5`;
- psutil `5.6.7` with host `/proc` visibility;
- pyzmq `19.0.0`;
- SciPy `1.4.1`;
- Shapely `1.7.1`;
- successful import/`--help` execution of the bounded Kosovo action CLI;
- a child `oq --version` returning the same exact source version.

The original plain-chroot prototype was intentionally rejected after testing
showed that the sandbox could not bind `/proc`; this finding is why portable
loader execution is the supported path.

## Authority ceiling

A successful bundle build or offline probe establishes only that the pinned
runtime can be materialized and executed. It does not establish:

- successful Kosovo numerical execution;
- historical ESRM20 reproduction;
- benchmark agreement;
- scientific validity or independent validation;
- publication authorization for external provider bytes;
- model-use or production authority.

Those remain governed by the exact run/data evidence in #609 / #287 and the
source-specific component issues.

