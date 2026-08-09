---
name: reproducibility-run
description: Run or review a formal OpenCatastrophe-data validation/transformation with replayable evidence.
license: Apache-2.0
---
<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->
# Reproducibility run
Pin repository commit and all material input/config identities. Record argv-style commands, relevant runtime versions, start/end timestamps, exit status and output hashes/sizes. Do not record credentials, private paths, signed URLs or unrelated machine metadata. A technical PASS does not imply scientific fitness or redistribution permission. Run `python scripts/check_all.py` on the exact candidate and report assumptions/blockers explicitly.
