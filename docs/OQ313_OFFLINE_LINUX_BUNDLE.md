<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# OpenQuake 3.13 portable Linux runtime checkpoint

## Purpose

Provide a reproducible Linux/amd64 runtime checkpoint for the bounded EQ1 Kosovo
OpenQuake 3.13 `reconstructed_experiment` lane.

The workflow proves that the pinned reconstructed OpenQuake 3.13 runtime
checkpoint can be materialized, exported, and exercised through the portable
launcher. It publishes only a metadata receipt in the GitHub Actions workflow
summary. The generated rootfs itself remains runner-temporary and is **not
uploaded or distributed** because redistribution authorization for the complete
third-party rootfs aggregate has not been established.

This is engineering/reproducibility evidence, not scientific validation,
publication authority, or model-use authority.

## Exact runtime fence

The workflow freezes:

- bootstrap image:
  `openquake/engine@sha256:dcfb88b3f9feb96eddee648690253492ba252619703ff48477affdbbb3c1151c`;
- exact OpenQuake source commit:
  `16dd69ecea0c6dcaf49c22ca12edc9da3f024889`;
- expected OpenQuake source version: `3.13.0-git16dd69ecea`;
- Python 3.8;
- h5py 3.1.0;
- NumPy 1.20.0;
- pandas 1.1.5;
- psutil 5.6.7;
- pyzmq 19.0.0;
- SciPy 1.4.1;
- Shapely 1.7.1.

The bootstrap digest is not learned from the candidate run and then trusted.
It is a repository-controlled expected value derived from repeated prior
trusted-main receipts. The workflow pulls the immutable digest reference and
fails closed unless the observed repository digest equals that expected value.
The Dockerfile receives that same immutable reference through `ARG BASE_IMAGE`.

The exact PR-head/default-branch source SHA, bootstrap digest, execution image
ID, and authority flags are written to the generated `manifest.json`.

## Ephemeral runtime contents

Inside runner-temporary storage the workflow creates:

- `rootfs.tar.zst` — exported Linux root filesystem containing the pinned
  OpenQuake runtime and exact OpenCatastrophe-data source revision;
- `manifest.json` — runtime/repository/provenance receipt;
- `SHA256SUMS` — file-integrity checks;
- `offline-python.sh` — portable Linux launcher;
- `offline-probe.sh` — exact Python/OpenQuake/dependency probe;
- `README.txt` — compact local-use note.

The workflow executes `offline-probe.sh` against the exported portable path
before the job ends. It then publishes only hashes and `manifest.json` metadata
to the workflow summary. No `rootfs.tar.zst` or other rootfs payload is uploaded.
The manifest records both `rootfs_distributed=false` and
`rootfs_redistribution_authorized=false`.

The source checkout embedded in the rootfs excludes `.git`; its exact Git SHA
is carried in `manifest.json`. The exact OpenQuake source checkout retains its
`.git` metadata because OpenQuake 3.13 derives the `-git<sha>` source-version
suffix from that checkout.

## Why portable execution instead of chroot

A Docker-exported rootfs is useful as a reproducible filesystem snapshot, but
a plain `chroot` is a poor fit for restricted execution sandboxes: container
runtimes can forbid bind-mounting `/proc` or recreating device nodes. OpenQuake
and `psutil` need normal Linux process information during realistic execution.

`offline-python.sh` therefore does not require Docker or chroot once an
authorized operator has an equivalent local bundle. On Linux x86-64 it:

1. extracts `rootfs.tar.zst` once if needed;
2. invokes the rootfs glibc dynamic loader directly;
3. uses the rootfs Python 3.8 standard library and OpenQuake dependency set;
4. exposes the host `/proc` naturally to `psutil`;
5. keeps the OpenQuake source at `$ROOTFS/oq-engine` and supplies it directly
   through the rootfs-backed `PYTHONPATH`;
6. supplies rootfs-backed `git` and `oq` wrappers without host-root aliases.

The original plain-chroot prototype was rejected after testing showed that the
development sandbox could not bind `/proc`.

## Data and distribution boundary

The materialized runtime contains **no EFEHR/ESRM20 provider bytes**. Provider
inputs remain separately receipted scientific evidence with their own source,
rights, hash, and role.

The complete rootfs also contains third-party operating-system, native, Python,
and OpenQuake components. Because this PR does not establish the complete
licence/notice/source-obligation closure needed to authorize redistribution of
that aggregate, the workflow deliberately keeps the rootfs non-distributed.
This is a fail-closed rights decision, not a claim that redistribution would be
unlawful.

A future change may publish a rootfs only after that separate evidence is
complete. Until then, the durable public evidence is the exact workflow,
immutable dependency fence, hosted build/probe result, and metadata receipt.

## Local use by an authorized operator

If an authorized local environment retains or independently reconstructs the
same bundle, it can verify and probe it with:

```bash
sha256sum -c SHA256SUMS
./offline-probe.sh
```

An OpenCatastrophe Python entry point can then be invoked with:

```bash
./offline-python.sh -m <module> <arguments>
```

For example:

```bash
./offline-python.sh \
  -m scripts.run_esrm20_kosovo_residential_ebrisk_openquake313_action \
  --help
```

A full numerical run still requires the separately receipted ESRM20 staging
inputs plus the run-specific runtime/resolved-runtime receipts expected by the
bounded action. This checkpoint cannot invent or fetch those scientific inputs.

## Existing reproduction evidence

A predecessor prototype artifact was independently downloaded and exercised in
the Linux ChatGPT development environment. That earlier experiment established
that the portable-loader mechanism can reproduce Python 3.8.12, OpenQuake
`3.13.0-git16dd69ecea`, the exact pinned dependency set, host `/proc` visibility,
and the bounded Kosovo action CLI without provider/model execution.

That predecessor artifact is evidence for the mechanism only. The current
workflow intentionally tightens the bootstrap identity and no longer republishes
the rootfs.

## Authority ceiling

A successful build/probe establishes only that the exact pinned runtime can be
materialized and executed. It does not establish:

- successful Kosovo numerical execution;
- historical ESRM20 reproduction;
- benchmark agreement;
- source↔GSIM compatibility;
- scientific validity or independent validation;
- redistribution authorization for the rootfs;
- publication authorization for provider bytes;
- model-use or production authority.

Those remain separate gates in #609 / #287 and the source-specific EQ1 issues.
