<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source reviews

This directory contains **accepted, durable source-specific review evidence** that supports committed manifests/admissions.

Live candidates, research plans and speculative source evaluations belong in GitHub Issues when Issues are enabled. While the repository issue tracker is disabled, keep speculative candidate inventories out of this durable tree and open a Pull Request only once a source has enough authoritative public evidence for a bounded review/admission. This keeps the public tree from presenting planned work as accepted capability.

## Admission trigger

The accepted registry is **capability-driven, not a source landscape**. A scientifically strong, well-licensed or generally useful dataset is not admitted merely because it exists.

Add a durable source review and manifest only when the source has a named current role that existing accepted sources cannot provide, such as a required model-consumer component, a bounded interoperability dependency, or a predeclared scientific validation input with explicit comparison semantics. Keep each admission PR to one coherent source family/use case. Candidate benchmarks, baseline geography and possible future validation counterparts stay out of the accepted tree until that concrete role exists; preserve useful research in public Issues when enabled or in a closed/deferred PR record otherwise.

Current accepted reviews:

- `dwd-extreme-wind-v24.03.md` — supports the metadata-only DWD extreme-wind admission.
- `copernicus-c3s-european-windstorm-reanalysis-v1.0.md` — supports the metadata-only C3S Enhanced Windstorm Service admission.
- `efehr-esrm20-european-exposure-model-v1.0.md` — supports the metadata-only EFEHR ESRM20 European Exposure Model admission.
- `efehr-eshm20.md` — supports the metadata-only EFEHR ESHM20 earthquake-hazard admission.
- `efehr-esrm20-vulnerability-v1.1.md` — supports the metadata-only EFEHR ESRM20 European Building Vulnerability Database v1.1 admission.
- `microsoft-globalml-building-footprints.md` — supports the metadata-only Microsoft Global ML Building Footprints exposure-geometry admission.
- `copernicus-cems-glofas-historical.md` — supports the metadata-only CEMS GloFAS historical hydrology admission.
- `storm-ibtracs-present-climate-v4.md` — supports the metadata-only STORM v4 synthetic tropical-cyclone event-catalogue admission.
- `eiopa-catastrophe-data-hub-2023.md` — supports separate metadata-only EIOPA insured-exposure and historical incurred-loss admissions; raw/derived workbook redistribution remains blocked pending exact-file rights review.
- `google-open-buildings-v3.md` — supports the metadata-only Google Open Buildings v3 exposure-geometry admission under the selected CC BY 4.0 reuse path.

A source review never broadens the machine-readable manifest scope by itself.
