<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->
# Architecture

OpenCatastrophe-data is a public metadata-first data registry and provenance project, not a data lake.

The trust path is: authoritative source and terms -> candidate metadata -> rights/provenance review -> scientific review -> admitted manifest -> optional external acquisition -> deterministic transformation -> exact artifact identity -> consumer adapter.

Git history and source-data storage are separate security domains. Large, confidential, proprietary or rights-unclear bytes normally remain outside Git. Storage location is not identity; use stable source identifiers and content hashes when bytes are legitimately acquired.

Transformations must preserve input identity, code/config identity, semantic changes and output identity. Transformation never creates rights absent upstream.

Consumer adapters may target insurance, risk-data and geospatial standards, but native rights, privacy, provenance and scientific gates remain authoritative.
