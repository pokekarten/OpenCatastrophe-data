# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded official NRW 2022 historical Hausumringe listing receipt ONLY.

No 859 MB ZIP, source geometry, provider actual feature row or insurance-site
data is fetched. The listing does not authenticate ZIP SHA-256 or geocodes.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
import json
import re
import sys

URL="https://www.opengeodata.nrw.de/produkte/geobasis/lk/hist/hist_hu_shp/"
ZIP_NAME="2022_hu_EPSG4647_Shape.zip"
ZIP_URL=URL+ZIP_NAME
MAX_HTML=128*1024
SOURCE_PUBLISHER="Geobasis NRW"
SOURCE_CRS="EPSG:4647"


class ListingBlocked(ValueError):
    pass


class _ListingLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs=[]
        self.body=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            self.hrefs.append(dict(attrs).get("href",""))
    def handle_data(self,data):
        self.body.append(data)


def validate_official_index(source:bytes)->dict:
    if not isinstance(source,bytes) or not 100<=len(source)<=MAX_HTML:
        raise ListingBlocked("publisher HTML size outside strict bound")
    try:
        txt=source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ListingBlocked("publisher listing is not UTF-8") from exc
    p=_ListingLinks()
    p.feed(txt)
    plain=" ".join(p.body)
    if (ZIP_NAME not in plain
        or "Historische Hausumringe" not in plain
        or "Datenlizenz Deutschland - Zero - Version 2.0" not in plain
        or not re.search(r"\bEPSG[\s:]+4647\b",plain)
        or not re.search(r"\b859[.,]3\s*MB\b",plain)):
        raise ListingBlocked("historical 2022 exact source year, size, CRS or publisher license not verified")
    links=[]
    for href in p.hrefs:
        target=urljoin(URL,href)
        parts=urlsplit(target)
        if parts.scheme!="https" or parts.netloc!="www.opengeodata.nrw.de" or parts.query or parts.fragment:
            continue
        if target==ZIP_URL:
            links.append(target)
    if len(links)!=1:
        raise ListingBlocked("cannot pin unique original provider ZIP link")
    return {
        "schema":"RVA_NRW_HISTORICAL_HU_2022_ORIGINAL_INDEX_METADATA_RECEIPT_V0",
        "publisher":SOURCE_PUBLISHER,
        "original_index_url":URL,
        "original_index_full_bytes":len(source),
        "original_index_full_sha256":hashlib.sha256(source).hexdigest(),
        "original_publisher_zip_url":ZIP_URL,
        "original_publisher_zip_name":ZIP_NAME,
        "source_year":"2022",
        "listing_original_zip_reported_size":"859.3 MB",
        "original_zip_full_bytes_acquired":False,
        "original_zip_sha256_verified":False,
        "original_zip_zipfile_members_inspected":False,
        "original_geo_shape_geometry_imported":False,
        "original_source_spatial_reference_declared":SOURCE_CRS,
        "source_spatial_reference_transformed_to_EPSG4326":False,
        "listing_license_label":"Datenlizenz Deutschland - Zero - Version 2.0",
        "exact_zip_object_license_independently_reviewed":False,
        "2022_house_outlines_mean_2022_census_residential_buildings":False,
        "2022_house_outlines_are_RV_insured_risk_sites":False,
        "original_source_approved_for_German_Oasis_GUL":False,
        "comparison_requires_year_end_vs_2022_05_15_vintage_reconciliation":True,
    }


def fetch_index(*,urlopen_=urlopen):
    req=Request(URL,headers={"User-Agent":"OpenCatastrophe-source-metadata-research/0.1",
                             "Accept":"text/html"},method="GET")
    with urlopen_(req,timeout=20) as response:
        if getattr(response,"status",None)!=200 or response.geturl()!=URL:
            raise ListingBlocked("publisher GET status or final URL changed")
        length=response.headers.get("Content-Length")
        if length is not None and (not length.isascii() or not length.isdecimal() or int(length)>MAX_HTML):
            raise ListingBlocked("untrusted listing exceeds maximum")
        content_type=response.headers.get("Content-Type","").split(";")[0].lower()
        if content_type not in ("text/html","application/xhtml+xml"):
            raise ListingBlocked("publisher content type changed")
        body=response.read(MAX_HTML+1)
    return validate_official_index(body)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live",action="store_true",help="opt-in one bounded official listing GET only; never ZIP")
    p=parser.parse_args()
    if not p.live:
        parser.exit(2,"BLOCKED: opt-in --live required for original publisher listing\n")
    print(json.dumps(fetch_index(),sort_keys=True,indent=2))
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except (OSError,ListingBlocked) as exc:
        print(f"NRW_HU_2022_LISTING_BLOCKED: {exc}",file=sys.stderr)
        sys.exit(2)
