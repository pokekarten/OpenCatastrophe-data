# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Find and byte-verify official station-sheet PDFs for complete Ciara gust series.

Never print the eight-digit station identifiers, individual gust series,
station geometries or source PDF bytes. Original hours and source hashes are
rechecked first. PDF existence is not historical instrument/siting attestation,
scientific calibration or source admission.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import re
import sys
from urllib.parse import urlsplit

from research_runners.meteofrance_hourly_gust_v0 import Blocked, _read_url, sha256
from research_runners.meteofrance_north_hourly_catalogue_v0 import (
    audit_catalogue, CATALOGUE_URL, MAX_CATALOGUE_BYTES,
)
from research_runners import meteofrance_four_north_original_v0 as fr
from research_runners.meteofrance_ciara2020_four_original_window_v0 import event_envelope

CATALOGUE_URL_STATIONS = "https://www.data.gouv.fr/api/1/datasets/fiches-dinformations-sur-les-stations/"
CATALOGUE_URL_COMPLEMENTARY = "https://www.data.gouv.fr/api/1/datasets/fiches-dinformations-sur-les-stations-complementaires/"
PDF_PREFIX = "https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/INFOS_POSTES/"
COMP_PREFIX = "https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/INFOS_POSTES_COMP/"
CATALOGUE_LIMIT = 40 * 1024 * 1024
MAX_RESOURCES = 25_000
MAX_PDF_BYTES = 5 * 1024 * 1024
WINDOW_START = "2020020900"
WINDOW_END = "2020021200"
REQUIRED_HOURS = 72
ALLOWED_DEPARTMENTS = ("02", "62", "76", "80")


def complete_quality_station_ids(original: bytes) -> set[str]:
    """Original source must have been fully validated by event_envelope first."""
    hours: dict[str, set[str]] = {}
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(original)) as archive:
            bounded = fr.LimitedInflation(archive, fr.MAX_INFLATED)
            with io.TextIOWrapper(io.BufferedReader(bounded), encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream, delimiter=";")
                if reader.fieldnames is None or any(x not in reader.fieldnames for x in fr.FIELDS):
                    raise Blocked("original station-hour source schema changed")
                for row in reader:
                    timestamp = row["AAAAMMJJHH"].strip()
                    if not WINDOW_START <= timestamp < WINDOW_END:
                        continue
                    if (row["FXI3S"].strip()
                            and row["QFXI3S"].strip() in ("0", "1")
                            and row["STATUS_FXI3S"].strip() in ("0", "1")):
                        hours.setdefault(row["NUM_POSTE"].strip(), set()).add(timestamp)
    except (OSError, EOFError, UnicodeError, csv.Error) as exc:
        raise Blocked("original source station-hour inspection failed") from exc
    return {station for station, stamps in hours.items() if len(stamps) == REQUIRED_HOURS}


def _station_resource(raw: object, station: str, department: str, *, prefix: str = PDF_PREFIX) -> dict:
    if not isinstance(raw, dict):
        raise Blocked("station catalogue resource malformed")
    uid = raw.get("id")
    title = raw.get("title")
    url = raw.get("url")
    size = raw.get("filesize")
    if not isinstance(uid, str) or not re.fullmatch(
        r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}", uid
    ):
        raise Blocked("station PDF resource UUID malformed")
    expected_title = "Departement_" + department + "_station_" + station + "_commune_"
    if not isinstance(title, str) or not title.startswith(expected_title) or len(title) <= len(expected_title):
        raise Blocked("station PDF catalogue title/source identity differs")
    if type(size) is not int or not 1024 <= size <= MAX_PDF_BYTES:
        raise Blocked("station PDF original byte count unavailable or exceeds bound")
    if prefix not in (PDF_PREFIX, COMP_PREFIX) or not isinstance(url, str) or not url.startswith(prefix):
        raise Blocked("station PDF original publisher URL not approved")
    parts = urlsplit(url)
    expected_path = prefix + department + "/" + station + "_" + department + "_"
    if (parts.scheme != "https" or parts.hostname != "meteofrance.s3.sbg.io.cloud.ovh.net"
            or parts.username or parts.password or parts.port or parts.query or parts.fragment
            or not url.startswith(expected_path) or not url.lower().endswith(".pdf")
            or "/../" in url or "/./" in url):
        raise Blocked("station PDF path/host/department not a fixed official asset")
    return {"url": url, "resource_id": uid.lower(), "bytes": size}


def resolve_station_sheets(catalogue: bytes, selected: set[str], dep: str,
                           *, min_resources: int = 10_000,
                           allow_unmatched: bool = False,
                           report_ambiguous: bool = False,
                           prefix: str = PDF_PREFIX):
    if dep not in ALLOWED_DEPARTMENTS or any(
        not re.fullmatch(r"\d{8}", x) or not x.startswith(dep) for x in selected
    ):
        raise Blocked("invalid station cohort or departmental provenance")
    if len(catalogue) > CATALOGUE_LIMIT or len(catalogue) == 0:
        raise Blocked("station metadata catalogue byte cap exceeded or catalogue empty")
    try:
        payload = json.loads(catalogue.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise Blocked("station metadata catalogue not UTF-8 JSON") from exc
    if type(payload) is not dict or type(payload.get("resources")) is not list:
        raise Blocked("station catalogue resources array missing")
    resources = payload["resources"]
    if not min_resources <= len(resources) <= MAX_RESOURCES:
        raise Blocked("station catalogue resource population outside fixed bounds")
    matches: dict[str, list[dict]] = {station: [] for station in selected}
    for item in resources:
        if not isinstance(item, dict):
            raise Blocked("malformed station PDF catalogue resource")
        title = item.get("title")
        if not isinstance(title, str):
            continue
        m = re.match(r"^Departement_(\d{2})_station_(\d{8})_commune_", title)
        if m and m.group(1) == dep and m.group(2) in matches:
            matches[m.group(2)].append(item)
    selected_out: dict[str, dict] = {}
    unmatched = 0
    ambiguous: set[str] = set()
    for station in sorted(selected):
        candidates = matches[station]
        if not candidates:
            # A negative match is not proof that the station lacks a provider
            # PDF; the publisher may use another resource naming convention.
            if not allow_unmatched:
                raise Blocked("no exact PDF metadata title match for eligible station")
            unmatched += 1
            continue
        if len(candidates) != 1:
            if report_ambiguous:
                # Do not select a latest/first PDF for a duplicated identity.
                # Keep ambiguity IDs ephemeral so no station name is emitted.
                ambiguous.add(station)
                continue
            raise Blocked("ambiguous multiple PDF metadata identities for station")
        selected_out[station] = _station_resource(candidates[0], station, dep, prefix=prefix)
    if len({x["resource_id"] for x in selected_out.values()}) != len(selected_out):
        raise Blocked("station resource UUID reused for distinct original stations")
    if report_ambiguous:
        if not allow_unmatched:
            raise Blocked("ambiguous reporting requires partial cohort mode")
        return selected_out, sha256(catalogue), unmatched, ambiguous
    if allow_unmatched:
        return selected_out, sha256(catalogue), unmatched
    return selected_out, sha256(catalogue)


def verify_pdf_bytes(body: bytes, record: dict) -> str:
    if type(body) is not bytes or len(body) != record["bytes"]:
        raise Blocked("original station PDF length differs from official catalogue")
    if not body.startswith(b"%PDF-") or b"%%EOF" not in body[-1024:]:
        raise Blocked("original station source not a complete PDF signature")
    return sha256(body)


def station_pdf_proof(dep: str, original: bytes, catalogue: bytes,
                      *, supplemental_catalogue: bytes | None = None,
                      download_pdf=_read_url, min_resources: int = 10_000,
                      min_supplemental_resources: int = 500) -> dict:
    if dep not in ALLOWED_DEPARTMENTS:
        raise Blocked("department not in approved observed-station cohort")
    event = event_envelope(dep, original)
    selected = complete_quality_station_ids(original)
    if len(selected) != event["quality_checked_full_72_hour_stations"]:
        raise Blocked("selected station count inconsistent with validated Ciara event proof")
    matched, metadata_sha, unmatched, ambiguous = resolve_station_sheets(
        catalogue, selected, dep, min_resources=min_resources,
        allow_unmatched=True, report_ambiguous=True,
    )
    regular_count = len(matched)
    supplemental_sha = None
    supplemental_count = 0
    if unmatched and supplemental_catalogue is not None:
        # Distinct authoritative partner-station dataset. Use only exact
        # station identities absent from the primary publisher catalogue.
        remaining = selected.difference(matched).difference(ambiguous)
        extra, supplemental_sha, unmatched, extra_ambiguous = resolve_station_sheets(
            supplemental_catalogue, remaining, dep,
            min_resources=min_supplemental_resources,
            allow_unmatched=True, report_ambiguous=True, prefix=COMP_PREFIX,
        )
        ambiguous.update(extra_ambiguous)
        if set(extra).intersection(matched):
            raise Blocked("station sheet cohort overlaps primary and complementary")
        matched.update(extra)
        supplemental_count = len(extra)
    hashes = []
    pdf_bytes = 0
    for station in sorted(matched):
        record = matched[station]
        # Requests are exact official provider URLs with no redirect allowed.
        body = download_pdf(record["url"], MAX_PDF_BYTES)
        pdf_sha = verify_pdf_bytes(body, record)
        hashes.append(station + ":" + record["resource_id"] + ":" + pdf_sha)
        pdf_bytes += len(body)
    # Digest of secret station-ID-bound receipts, without publishing the IDs
    # or individual PDF links; reproducible by authorized reinspection.
    cohort_sha = sha256("\n".join(hashes).encode("utf-8"))
    return {
        "profile": "meteofrance-ciara2020-official-station-pdf-provenance-v0",
        "department": dep,
        "event_start_utc_inclusive": "2020-02-09T00:00:00Z",
        "event_end_utc_exclusive": "2020-02-12T00:00:00Z",
        "hourly_original_gzip_sha256": event["original_gzip_sha256"],
        "hourly_source_72h_qualified_station_count": len(selected),
        "official_station_catalogue_sha256": metadata_sha,
        "official_station_catalogue_pdf_resource_count": len(matched),
        "official_station_pdf_primary_count": regular_count,
        "official_station_pdf_complementary_count": supplemental_count,
        "complementary_station_catalogue_sha256": supplemental_sha,
        "eligible_station_pdf_unmatched_exact_title_count": unmatched,
        "eligible_station_pdf_ambiguous_multiple_resource_count": len(ambiguous),
        "eligible_station_pdf_exact_match_complete": unmatched == 0 and not ambiguous,
        "pdf_original_bytes_verified": pdf_bytes,
        "official_station_pdf_cohort_sha256": cohort_sha,
        "station_identifiers_or_locations_published": False,
        "original_pdf_bytes_or_station_rows_published": False,
        "pdf_metadata_presence_verified": bool(matched),
        "station_site_and_instrument_history_verified_for_2020": False,
        "hourly_gust_interval_equivalence_to_era5_verified": False,
        "production_hazard_calibration_authorized": False,
        "source_admitted": False,
        "annual_ep_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--department", required=True, choices=ALLOWED_DEPARTMENTS)
    parser.add_argument("--live", action="store_true", required=True)
    args = parser.parse_args(argv)
    try:
        official = audit_catalogue(_read_url(CATALOGUE_URL, MAX_CATALOGUE_BYTES))
        fr.check_identity(official, args.department)
        original = _read_url(fr.asset_url(args.department), fr.MAX_COMPRESSED)
        station_catalogue = _read_url(CATALOGUE_URL_STATIONS, CATALOGUE_LIMIT)
        supplemental_catalogue = _read_url(CATALOGUE_URL_COMPLEMENTARY, CATALOGUE_LIMIT)
        proof = station_pdf_proof(
            args.department, original, station_catalogue,
            supplemental_catalogue=supplemental_catalogue,
        )
        print(json.dumps(proof, sort_keys=True, indent=2))
        return 0
    except Blocked as exc:
        # Blocked exceptions use only fixed, non-identifying diagnostic text.
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        # urllib errors may contain the station URL: never print their details.
        print("BLOCKED: " + type(exc).__name__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
