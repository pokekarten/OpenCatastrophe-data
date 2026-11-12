<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original CAL FIRE DINS CKAN source metadata vintage drift — 2026-11-12

**Evidence class:** original provider metadata body, research only; **no** individual
damage features, addresses, parcel identifiers, linked resources, or CAT model
inputs inspected or retained.

An uncached, exact read of the official
[CAL FIRE DINS CKAN package_show](https://publish.data.ca.gov/api/3/action/package_show?id=1fdaea07-4bcd-4795-aa88-cd72b98e8a03)
returned original HTTP body bytes through a connected source-fetch
interface on 2026-11-12. The SHA-256 implementation was verified against
the standard empty and abc test vectors. Original bytes were read transiently,
not checked into Git.

| Field | November independently observed original |
| --- | --- |
| Response content type | application/json;charset=utf-8 |
| Original HTTP response body size | **16,335 bytes** |
| Original HTTP response SHA-256 | `83b75ccd9fe2ce7b2f2ee95ba3170b6e87554aa943d2e55748fdc01005fbf2ce` |
| CKAN JSON application status | success=true |
| Package ID | `1fdaea07-4bcd-4795-aa88-cd72b98e8a03` |
| Slug | `cal-fire-damage-inspection-dins-data` |
| Licence label | `cc-by` |
| Access level / open | public / true |
| Current metadata_modified | **`2026-11-11T01:27:13.459792`** |
| Resource UUID/format pairs | **11 of 11 frozen IDs/formats match** |
| Followed resource URLs or provider features | 0 |
| GitHub strict Python runner live pass | **not yet verified** |
| Approved CAT model inputs | 0 |

Compare the immutable [2026-11-01 historical original source receipt]
(calfire-dins-ckan-original-metadata-receipt-20261101.md): 16,916 bytes,
SHA-256 `1998a87aff518a059162d9c4faff3ce3c2e145f007323c6a91cf3fb3617927f8`,
metadata_modified `2026-10-21T20:55:50.264159`. This older historical
receipt remains correct *for its acquisition time* and is not overwritten.

The old offline preflight keeps that October date as its default.
The trusted one-shot GitHub probe now calls the same strict structure checker
with the explicitly pinned *November* `metadata_modified` value. On future
metadata-version drift the probe must BLOCK rather than silently accepting
unknown provider changes. The original response byte digest is included in
the resulting receipt; a boolean shows exact match with this November external
source-fetch proof. This separate fetch interface does not establish that
GitHub Actions has run a live provider request, or that GitHub's no-redirect
behavior was exercised against the original source.

The provider [developer documentation](https://data.ca.gov/docs/developer-documentation)
allows public anonymous CKAN reads and documents request limits.
The [official DINS catalogue](https://publish.data.ca.gov/dataset/cal-fire-damage-inspection-dins-data)
identifies a public CC Attribution package. This narrow rights evidence
**does not** authorize unrestricted commercial ArcGIS harvesting,
public dissemination of precise individual damage or address fields,
bulk provider assets, or synthetic insurer portfolio CAT-model admission.

**Next gate:** authorize one `workflow_dispatch` on trusted `main` in
`.github/workflows/calfire-dins-ckan-metadata.yml`. Do not conflate
separate public metadata observations with a passing full GitHub runtime test.
