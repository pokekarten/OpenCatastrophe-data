# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Explicit, local-only original CDS EWS annual-summary acquisition candidate.

Research intake, NOT scientific/data-rights admission, insurer loss, or CAT.
The authenticated CDS download requires a user-controlled CDS API token and
manual acceptance of the dataset licence. Never put either in Git or logs.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import tempfile
from zipfile import BadZipFile, ZipFile

from research_runners.c3s_wind_annual_summary_v0 import (
    AnnualSummaryError, parse_annual_csv,
)

DATASET = "sis-european-wind-storm-reanalysis"
RECEIPT_VERSION = "oc-c3s-ews-original-annual-summary-acquisition-v0"
MAX_CSV_BYTES = 250_000_000
MAX_PACKAGE_BYTES = 280_000_000
ALGORITHMS = ("hodges", "tempestextremes")


class AcquisitionError(ValueError):
    """Source/data-rights boundary was not satisfied."""


def official_request(algorithms=ALGORITHMS):
    """The exact three selectors applicable to the *annual summary* branch.

    Derived from ECMWF's original catalogue form and its conditional constraints
    as inspected 2026-11-05; the non-summary month, event and grid widgets are
    deliberately omitted. No invented per-year request parameters.
    """
    if (type(algorithms) not in (tuple, list) or not algorithms or
            len(algorithms) > 2 or len(set(algorithms)) != len(algorithms) or
            any(type(a) is not str or a not in ALGORITHMS for a in algorithms)):
        raise AcquisitionError("unsupported or duplicate official tracking algorithm")
    return {
        "product": "windstorm_summary_indicator",
        "variable": ["all"],
        "tracking_algorithm": list(algorithms),
    }


def inspect_provider_package(original: bytes, *, request=None) -> dict:
    """Inspect raw CDS CSV or a one-CSV ZIP without claiming publisher signatures.

    Original bytes are never rewritten. Each source hash belongs to the actual
    fetched response/member, never an independently authenticated publisher key.
    """
    if type(original) is not bytes or not 1 <= len(original) <= MAX_PACKAGE_BYTES:
        raise AcquisitionError("bounded original CDS response bytes required")
    request = official_request() if request is None else request
    if type(request) is not dict or request != official_request(request.get("tracking_algorithm", ())) :
        raise AcquisitionError("unexpected source request schema")
    package_sha = sha256(original).hexdigest()
    if original.startswith(b"PK\x03\x04"):
        try:
            with ZipFile(BytesIO(original)) as archive:
                members = archive.infolist()
                if len(members) != 1:
                    raise AcquisitionError("CDS ZIP must contain exactly one original CSV member")
                info = members[0]
                if (info.is_dir() or info.filename != Path(info.filename).name or
                        chr(92) in info.filename or ":" in info.filename or
                        not info.filename.lower().endswith(".csv") or
                        not 1 <= info.file_size <= MAX_CSV_BYTES or
                        info.flag_bits & 1 or (info.external_attr >> 16) & 0o170000 == 0o120000):
                    raise AcquisitionError("unsafe or unsupported original ZIP member")
                with archive.open(info) as source:
                    csv_bytes = source.read(MAX_CSV_BYTES + 1)
                if len(csv_bytes) != info.file_size:
                    raise AcquisitionError("bounded ZIP CSV member size mismatch")
                member = info.filename
        except (BadZipFile, OSError, RuntimeError) as exc:
            raise AcquisitionError("invalid official CDS ZIP response") from exc
        representation = "ZIP_ONE_ORIGINAL_CSV"
    else:
        if len(original) > MAX_CSV_BYTES:
            raise AcquisitionError("original CSV exceeds bounded parser capacity")
        csv_bytes = original
        member = None
        representation = "ORIGINAL_CSV"
    try:
        parsed = parse_annual_csv(csv_bytes)
    except AnnualSummaryError as exc:
        raise AcquisitionError("CDS source does not satisfy strict annual-summary CSV schema") from exc
    years = parsed["observed_years"]
    return {
        "receipt_version": RECEIPT_VERSION,
        "status": "ORIGINAL_CDS_RESPONSE_SCHEMA_CHECKED_RESEARCH_NOT_ADMITTED",
        "dataset": DATASET,
        "request": request,
        "request_sha256": sha256(json.dumps(request, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "response_representation": representation,
        "original_response_sha256": package_sha,
        "original_response_bytes": len(original),
        "original_csv_member_name": member,
        "original_csv_sha256": sha256(csv_bytes).hexdigest(),
        "original_csv_bytes": len(csv_bytes),
        "official_annual_parser_rows": parsed["observed_row_count"],
        "official_annual_parser_min_year": min(years),
        "official_annual_parser_max_year": max(years),
        "official_annual_parser_algorithms": parsed["observed_tracking_algorithm_labels"],
        "observed_nuts_levels": parsed["observed_nuts_levels"],
        "rights_admitted": False,
        "original_bytes_independently_publisher_signed": False,
        "nuts_vintage_verified": False,
        "frequency_model_calibrated": False,
        "insurer_gross_net_authorized": False,
    }


def acquire(*, output_dir: Path, client=None, algorithms=ALGORITHMS) -> dict:
    """Use an *existing user-controlled* CDS login; never retrieve in CI.

    Raw download and provenance receipt are stored strictly outside the Git
    checkout, and existing files are not overwritten.
    """
    request = official_request(algorithms)
    output_dir = Path(output_dir).resolve()
    repository_root = Path(__file__).resolve().parents[1]
    if output_dir == repository_root or repository_root in output_dir.parents:
        raise AcquisitionError("original CDS downloads and receipts must remain outside the repository")
    output_dir.mkdir(parents=True, exist_ok=True)
    package_path = output_dir / "c3s-ews-original-annual-summary-response.bin"
    receipt_path = output_dir / "c3s-ews-original-annual-summary-receipt.json"
    if (package_path.exists() or package_path.is_symlink() or
            receipt_path.exists() or receipt_path.is_symlink()):
        raise AcquisitionError("refuse overwrite of original CDS bytes or previous receipt")
    if client is None:
        try:
            import cdsapi
        except ImportError as exc:
            raise AcquisitionError("cdsapi is optional; install it in the authorized local environment") from exc
        client = cdsapi.Client(quiet=True, progress=False)
    with tempfile.TemporaryDirectory(dir=output_dir) as staging:
        temporary = Path(staging) / "response.bin"
        try:
            client.retrieve(DATASET, request, str(temporary))
        except Exception:
            # Avoid echoing URL query, credentials or account response bodies.
            raise AcquisitionError("CDS retrieval failed; check local login, licence and request selection") from None
        if not temporary.is_file() or temporary.is_symlink():
            raise AcquisitionError("CDS client did not create one regular response file")
        if not 1 <= temporary.stat().st_size <= MAX_PACKAGE_BYTES:
            raise AcquisitionError("download exceeds original-source intake size gate")
        original = temporary.read_bytes()
        receipt = inspect_provider_package(original, request=request)
        with package_path.open("xb") as out:
            out.write(original)
        with receipt_path.open("x", encoding="utf-8") as out:
            json.dump(receipt, out, sort_keys=True, indent=2, allow_nan=False)
            out.write("\n")
    return receipt


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute", action="store_true",
                   help="opt-in authenticated CDS retrieve; requires manual licence acceptance")
    p.add_argument("--out-dir", type=Path,
                   help="external local directory for original response and its research receipt")
    p.add_argument("--algorithm", action="append", choices=ALGORITHMS)
    args = p.parse_args(argv)
    algs = args.algorithm or list(ALGORITHMS)
    if not args.execute:
        if args.out_dir is not None:
            p.error("--out-dir requires explicit --execute")
        print(json.dumps({"dataset": DATASET, "request": official_request(algs),
                          "mode": "PRINT_ONLY_NO_NETWORK_NO_ADMISSION"},
                         sort_keys=True, indent=2))
        return 0
    if args.out_dir is None:
        p.error("--execute requires --out-dir outside the repository")
    result = acquire(output_dir=args.out_dir, algorithms=algs)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
