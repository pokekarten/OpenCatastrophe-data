# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Conservative NRW 2022 HU GFK classification against official cadastral code table.

This is a *candidate* source-purpose filter, never a measured residential
insurance exposure, occupancy/roof construction, or sole evidence of a
Hauptgebäude. Unknown codes fail closed instead of being guessed.
"""
from __future__ import annotations

import re

OFFICIAL_NRW_REFERENCE = "https://recht.nrw.de/system/files/VA/16644-28824-mbl32-2anlage3.pdf"
OFFICIAL_NRW_HU_SOURCE_FORMAT = "https://www.bezreg-koeln.nrw.de/system/files/media/document/file/geobasis_lk_hist_dfb_hu_2020.pdf"
OFFICIAL_NRW_ALKIS_2021 = "https://recht.nrw.de/system/files/VA/19858-35606-mbl31-3anlage.pdf"
SOURCE_VINTAGE = "NRW historic HU source DFB v2.6 (2019) and official cadastral GFK table"
# The 2017 official 'Anlage 3 zu den Jahresberichten der Katasterbehörden'
# identifies the listed functions as buildings with residential component.
# Its H/N distinction has an explicit *address/numbering precondition*.
# It does NOT state that every physical polygon with these functions has a
# 2022-Zensus residential-unit match, nor that the 2022 ALKIS codebook is unchanged.
RESIDENTIAL_CANDIDATES = {
    "1000": "Wohngebaeude",
    "1010": "Wohnhaus",
    "1100": "Gemischt_genutztes_Gebaeude_mit_Wohnen",
    "1110": "Wohngebaeude_mit_Gemeinbedarf",
    "1120": "Wohngebaeude_mit_Handel_und_Dienstleistungen",
    "1121": "Wohn_und_Verwaltungsgebaeude",
    "1122": "Wohn_und_Buerogebaeude",
    "1123": "Wohn_und_Geschaeftsgebaeude",
    "1130": "Wohngebaeude_mit_Gewerbe_und_Industrie",
    "1131": "Wohn_und_Betriebsgebaeude",
    "1220": "Land_und_forstwirtschaftliches_Wohn_und_Betriebsgebaeude",
    "1221": "Bauernhaus",
    "1222": "Wohn_und_Wirtschaftsgebaeude",
    "1223": "Forsthaus",
}
# These official building functions may contain residents but represent
# special/institutional occupancy, not admitted as standard home insurance.
SPECIAL_OCCUPANCY_QUARANTINE = {
    "1020": "Wohnheim",
    "1021": "Kinderheim",
    "1022": "Seniorenheim",
    "1023": "Schwesternwohnheim",
    "1024": "Studenten_Schuelerwohnheim",
    "1025": "Schullandheim",
}
# Selected independently identified non-residential/building-part examples
# for strict negative tests. This is NOT an exhaustive code registry.
KNOWN_INELIGIBLE_EXAMPLES = {
    "2000": "Gebaeude_fuer_Wirtschaft_oder_Gewerbe",
    "2460": "Gebaeude_zum_Parken",
    "2461": "Parkhaus",
    "2462": "Parkdeck",
    "2463": "Garage",
    "2522": "Umspannwerk",
    "2523": "Umformer",
    "2720": "Land_und_forstwirtschaftliches_Betriebsgebaeude",
    "2723": "Schuppen",
    "2724": "Stall",
    "2740": "Treibhaus_Gewaechshaus",
    "3000": "Gebaeude_fuer_oeffentliche_Zwecke",
    "3021": "Allgemein_bildende_Schule",
    "1313": "Gartenhaus",
}

def classify_gfk(raw: str) -> tuple[str, str | None]:
    """Conservative raw 4-digit HU building-function code category."""
    if not isinstance(raw, str):
        return "malformed", None
    value=raw.strip()
    # Official historical HU DFB version 2.6, source example 31001_1222:
    # AX_Gebaeude ALKIS object type + four-digit building-function suffix.
    # The bare suffix is insufficient to prove a HU building object.
    match=re.fullmatch(r"(3[0-9]{4})_([0-9]{4})",value)
    if match is None:
        return "malformed", None
    if match.group(1)!="31001":
        return "non_building_object_quarantine", None
    value=match.group(2)
    if value in RESIDENTIAL_CANDIDATES:
        return "residential_function_candidate_only", RESIDENTIAL_CANDIDATES[value]
    if value in SPECIAL_OCCUPANCY_QUARANTINE:
        return "special_occupancy_quarantine", SPECIAL_OCCUPANCY_QUARANTINE[value]
    if value in KNOWN_INELIGIBLE_EXAMPLES:
        return "known_nonresidential_example", KNOWN_INELIGIBLE_EXAMPLES[value]
    return "unmapped_quarantine", None


def audit_gfk_counts(observed_counts: dict[str,int]) -> dict:
    if not isinstance(observed_counts,dict):
        raise ValueError("GFK distribution must be counted from original source")
    category={}
    code_count={}
    for raw,count in observed_counts.items():
        if type(count) is not int or count<0:
            raise ValueError("invalid source GFK frequency")
        label,_=classify_gfk(raw)
        category[label]=category.get(label,0)+count
        code_count[raw]=count
    return {
        "source_gfk_distribution":dict(sorted(code_count.items())),
        "source_gfk_categories":dict(sorted(category.items())),
        "official_reference_url":OFFICIAL_NRW_REFERENCE,
        "official_hu_source_format_url":OFFICIAL_NRW_HU_SOURCE_FORMAT,
        "official_2021_alkis_building_function_codebook":OFFICIAL_NRW_ALKIS_2021,
        "special_residential_occupancy_quarantined":True,
        "source_gfk_requires_AX_Gebaeude_31001_prefix":True,
        "mapped_code_count":len(RESIDENTIAL_CANDIDATES),
        "function_classes_not_verified_as_actual_residential_insurance_sites":True,
        "actual_RV_insurer_building_identity_known":False,
        "source_2022_HU_vs_2022_Zensus_occupancy_reconciled":False,
        "source_2022_HU_vs_2017_GFK_code_vintage_fully_reconciled":False,
    }
