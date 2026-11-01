# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Florida original historical parcel withdrawal and current state-layer gate.

The University of Florida GeoPlan Center explicitly removed every FGDL
parcel layer, including all historical versions, on 2025-10-08 at the
State GIS Office's request. The officially referred replacement FDOR state
FeatureServer exposes a *different current 2025-labelled* tax-roll parcel
product, not any independently versioned 2017 pre-Michael snapshot.

Metadata and aggregate provider counts only; no parcel features/owners,
addresses, identifiers, imagery, or insurer records are queried or accepted.
"""

from __future__ import annotations

from typing import Any

WITHDRAWAL_DATE = "2025-10-08"
WITHDRAWAL_REFERENCE = (
    "https://www.geoplan.ufl.edu/"
    "parcel-layers-removed-from-fgdl-per-state-request/"
)
LAYER = (
    "https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/"
    "Florida_Statewide_Cadastral/FeatureServer/0"
)
SERVICE_ITEM = "efa909d6b1c841d298b0a649e7f71cf2"
SOURCE_ID = "florida.fdor.statewide-cadastral-2025"
HISTORIC = frozenset(("florida.fgdl.parcels-2017", "florida.fgdl.parcels-2018"))


class ParcelAccessError(ValueError):
    """Reject stale sources, unsafe fields or temporal substitutions."""


def canonical_aggregate_query() -> dict[str, str]:
    """One geometry-free and feature-free provider source census."""
    return {
        "where": "1=1",
        "returnCountOnly": "true",
        "returnGeometry": "false",
        "f": "json",
    }


def validate_current_state_source(
    layer_metadata: Any, count_only_reply: Any,
) -> dict[str, Any]:
    """Accept only a strict trusted *projection* of original provider metadata.

    This validation is offline, pure and not a provider authentication claim.
    Caller must separately verify live provider URL and content provenance.
    """
    expected = {"serviceItemId", "name", "type", "geometryType",
                "objectIdField", "fields"}
    if type(layer_metadata) is not dict or set(layer_metadata) != expected:
        raise ParcelAccessError("unreviewed layer metadata projection or extra feature rows")
    if layer_metadata["serviceItemId"] != SERVICE_ITEM:
        raise ParcelAccessError("unreviewed state FeatureServer identity")
    if layer_metadata["name"] not in ("CADASTRAL_DOR", "FDOR Cadastral 2025"):
        raise ParcelAccessError("unexpected FDOR layer name")
    if layer_metadata["type"] != "Feature Layer" or layer_metadata["geometryType"] != "esriGeometryPolygon":
        raise ParcelAccessError("FDOR source is not the expected parcel polygon layer")
    if layer_metadata["objectIdField"] != "OBJECTID":
        raise ParcelAccessError("unreviewed source ObjectID field")
    fields = layer_metadata["fields"]
    if (type(fields) is not list or
        len(fields) != len(set(fields)) or
        set(fields) != {"OBJECTID", "CO_NO", "ASMNT_YR", "OWN_NAME"} or
        any(type(f) is not str for f in fields)):
        raise ParcelAccessError("incomplete or unexpected source metadata field set")
    if type(count_only_reply) is not dict or set(count_only_reply) != {"count"}:
        raise ParcelAccessError("provider must return only an aggregate count")
    count = count_only_reply["count"]
    if type(count) is not int or not 1_000_000 <= count <= 30_000_000:
        raise ParcelAccessError("bounded, plausible state source count required")
    return {
        "profile": "florida_current_state_parcel_metadata_count_only_v0",
        "source_id": SOURCE_ID,
        "source_service_item": SERVICE_ITEM,
        "source_polygon_layer_metadata_validated": True,
        "provider_live_statewide_parcel_feature_count": count,
        "provider_count_is_unique_building_count": False,
        "contains_sensitive_owner_address_fields": True,
        "owner_address_fields_acquired_or_released": False,
        "historical_2017_2018_fgdl_bytes_accessible": False,
        "pre_2018_building_footprints_validated": False,
        "original_source_reuse_rights_checked": False,
        "different_2025_state_product_is_historical_2017_replacement": False,
        "model_input_admitted": False,
    }


def historical_access_gate(
    source_id: Any, *,
    request_historical_zip: Any = False,
    substitute_state_current: Any = False,
) -> dict[str, Any]:
    """Explicit withdrawal control, including for access-probe suggestions."""
    if type(source_id) is not str or source_id not in HISTORIC:
        raise ParcelAccessError("unrecognized withdrawn FGDL historical source")
    if type(request_historical_zip) is not bool or type(substitute_state_current) is not bool:
        raise ParcelAccessError("access switches must be boolean")
    if request_historical_zip:
        raise ParcelAccessError("FGDL removed historical parcel ZIPs at state request")
    if substitute_state_current:
        raise ParcelAccessError("2025 FDOR state dataset cannot replace 2017 parcel vintage")
    return {
        "source_id": source_id,
        "withdrawal_date": WITHDRAWAL_DATE,
        "withdrawal_notice": WITHDRAWAL_REFERENCE,
        "former_metadata_still_viewable": True,
        "historic_dataset_download_currently_offered_by_fgdl": False,
        "authorised_original_historical_source_file_verified": False,
        "state_referred_2025_layer_may_be_explored_for_current_context": True,
        "historical_pre_event_building_input_admitted": False,
        "model_input_admitted": False,
    }
