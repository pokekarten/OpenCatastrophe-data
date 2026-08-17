# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Adapt the reviewed ESHM20 OpenQuake-3.14 GSIM runtime gate to exact ESRM20 bytes.

The module reuses the existing acquisition, GSIM request parser, OpenQuake
source verification, alias/registry/constructor and reconstructed runtime recipe.
Immutable ESRM20 identities are applied only inside a temporary execution
context and are restored afterwards so the existing ESHM20 path is untouched.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
from pathlib import Path
from typing import Any, Iterator, Mapping

from scripts import acquire_eshm20_gsim_resource_profile as _gmm
from scripts import profile_eshm20_gsim_identities as _profiler
from scripts import run_eshm20_gsim_reference_runtime as _runtime
from scripts import validate_eshm20_gsim_openquake_runtime as _gate

SCHEMA_VERSION = "oc-esrm20-gsim-reference-runtime-result-v1"
REQUEST_SCHEMA_VERSION = "oc-esrm20-gsim-reference-runtime-request-v1"
REQUEST_MARKER = "<!-- oc-eq1-esrm20-gsim-reference-runtime-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-gsim-reference-runtime-result-v1 -->"
SOURCE_ISSUE = 493
HANDOFF_ISSUE = 281
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
REPOSITORY_PATH = "Hazard/gmpe_logic_tree_5br_slope_geology.xml"
EXPECTED_BYTE_COUNT = 34_018
EXPECTED_SHA256 = "f3efd16d56189c7804824d94b20ed75d6ceefc879144d8bd697c1f1b9b47cf17b4"