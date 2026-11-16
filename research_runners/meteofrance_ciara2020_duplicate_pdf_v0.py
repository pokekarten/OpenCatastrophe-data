# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Compare all exact publisher PDF source bytes behind one ambiguous Ciara station.

Original station IDs, coordinates, PDF URLs, and PDF content stay in ephemeral
memory. A byte comparison does NOT certify the historical instrument/site.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from research_runners.meteofrance_hourly_gust_v0 import Blocked, _read_url, sha256
from research_runners.meteofrance_four_north_original_v0 import (
    MAX_COMPRESSED, asset_url, check_identity
)
from research_runners.meteofrance_north_hourly_catalogue_v0 import (
    CATALOGUE_URL, MAX_CATALOGUE_BYTES, audit_catalogue
)
from research_runners.meteofrance_ciara2020_four_original_window_v0 import event_envelope
from research_runners.meteofrance_ciara2020_station_pdf_proof_v0 import (
    CATALOGUE_LIMIT, CATALOGUE_URL_STATIONS, MAX_PDF_BYTES,
    _station_resource, complete_quality_station_ids, resolve_station_sheets,
    verify_pdf_bytes
)

DEP = "76"
MAX_CANDIDATES = 6


def _unique_pairs(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise Blocked("duplicate official JSON key")
        result[k] = v
    return result


def compare_pdf_candidates(original: bytes, catalogue: bytes, *,
                           fetch_pdf=_read_url, min_resources: int = 10000) -> dict:
    event = event_envelope(DEP, original)
    eligible = complete_quality_station_ids(original)
    if len(eligible) != event["quality_checked_full_72_hour_stations"]:
        raise Blocked("station-hour cohort differs from Ciara original receipt")
    _unique, catalog_sha, missing, ambiguous = resolve_station_sheets(
        catalogue, eligible, DEP, min_resources=min_resources,
        allow_unmatched=True, report_ambiguous=True
    )
    if missing or len(ambiguous) != 1:
        raise Blocked("expected one precisely ambiguous original station PDF identity")
    station = next(iter(ambiguous))
    if not 0 < len(catalogue) <= CATALOGUE_LIMIT:
        raise Blocked("catalogue size outside accepted bound")
    try:
        root = json.loads(catalogue.decode("utf-8"), object_pairs_hook=_unique_pairs)
    except (UnicodeError, ValueError) as exc:
        raise Blocked("malformed original PDF catalogue") from exc
    resources = root.get("resources")
    if type(resources) is not list or not min_resources <= len(resources) <= 25000:
        raise Blocked("unexpected station PDF catalogue resource count")
    title_prefix = "Departement_" + DEP + "_station_" + station + "_commune_"
    matches = [x for x in resources if
               type(x) is dict and isinstance(x.get("title"), str)
               and x["title"].startswith(title_prefix)]
    if not 2 <= len(matches) <= MAX_CANDIDATES:
        raise Blocked("ambiguous station PDF candidate count out of bound")
    entries = sorted((_station_resource(x, station, DEP) for x in matches),
                     key=lambda x: x["resource_id"])
    if len({e["resource_id"] for e in entries}) != len(entries):
        raise Blocked("duplicate official resource UUID for station")
    total = 0
    hashes = []
    urls = set()
    bound = [station]
    for entry in entries:
        if total + entry["bytes"] > MAX_CANDIDATES * MAX_PDF_BYTES:
            raise Blocked("PDF candidate byte budget exceeded")
        data = fetch_pdf(entry["url"], MAX_PDF_BYTES)
        digest = verify_pdf_bytes(data, entry)
        hashes.append(digest)
        urls.add(entry["url"])
        bound.append(entry["resource_id"] + ":" + digest)
        total += len(data)
    return {
        "profile": "ciara2020-station-ambiguous-original-pdf-byte-proof-v0",
        "department": DEP,
        "source_hourly_original_sha256": event["original_gzip_sha256"],
        "official_station_catalogue_sha256": catalog_sha,
        "ambiguous_station_count": 1,
        "candidate_pdf_resource_count": len(entries),
        "unique_pdf_url_count": len(urls),
        "unique_pdf_sha256_count": len(set(hashes)),
        "all_original_pdfs_byte_identical": len(set(hashes)) == 1,
        "total_original_pdf_bytes_checked": total,
        "station_bound_pdf_cohort_digest": sha256("\n".join(bound).encode("utf-8")),
        "individual_station_ids_or_original_urls_published": False,
        "pdf_original_bytes_published": False,
        "February_2020_station_site_and_instrument_verified": False,
        "unique_historical_pdf_version_admitted": False,
        "era5_hourly_gust_equivalence_proven": False,
        "source_admitted": False,
        "annual_ep_authorized": False,
        "hazard_skill_or_loss_calibration_authorized": False,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true", required=True)
    p.parse_args(argv)
    try:
        overview = audit_catalogue(_read_url(CATALOGUE_URL, MAX_CATALOGUE_BYTES))
        check_identity(overview, DEP)
        original = _read_url(asset_url(DEP), MAX_COMPRESSED)
        pdf_catalogue = _read_url(CATALOGUE_URL_STATIONS, CATALOGUE_LIMIT)
        print(json.dumps(compare_pdf_candidates(original, pdf_catalogue),
                         indent=2, sort_keys=True))
        return 0
    except Blocked as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    except (ValueError, OSError) as exc:
        # urllib diagnostics could carry individual original PDF URLs.
        print("BLOCKED: " + type(exc).__name__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
