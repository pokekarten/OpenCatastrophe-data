# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""2020-true DWD station location/height + original Ciara 2020 ERA5 peaks.

Reuses the original immutable 3 DWD 2020 FX911 source and 96h Google
ARCO ERA5 10fg matrix provenance, plus the separately source-attested
2020 historic DWD geography, device and UTC FX parameter metadata.
It NEVER alters the former current-station-position comparison receipt.
Historical sensor measurements vs model-grid 96h event peak differences
remain purely descriptive, not hourly error, bias, insurer damage or GUL.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import math
import sys
from pathlib import Path
import tomllib

import ciara2020_dwd_hourly_fx_original_station_observations_v0 as dwd
import ciara2020_dwd_historical_feb2020_station_attestation_v0 as historic
import ciara2020_dwd_original_to_era5_station_peak_comparison_v0 as prior
import ciara2020_google_arco_real_96h_nrw_area_v0 as era5

SCHEMA="CIARA2020_DWD_FX911_2020_HISTORIC_STATION_SITES_TO_ERA5_UTC_PEAK_V1"
DATE_START=datetime(2020,2,8,0,tzinfo=timezone.utc)
DATE_END=datetime(2020,2,11,23,tzinfo=timezone.utc)
# Official ECMWF documents HRES ERA5 max since postprocessing in the
# hour ending the valid UTC forecast timestamp. The DWD original 2020
# FX911 parameter states "hoechste Windspitze der letzten Stunde"
# and Zusatz-Info "in UTC". This is NOMINAL hour-ending compatibility,
# not proof of identical sensor/model sampling or a matched 96h series.
ERA5_HRES_TIME_DOC="https://confluence.ecmwf.int/pages/viewpage.action?pageId=155343959"
ORIGINAL_DWD_HISTORIC_RECEIPT=historic.ORIGINAL_RESEARCH
EXPECTED=("02667","15200","00603")

class HistoricSiteGridBlocked(ValueError):
    """Original source or historic 2020 station-to-grid scientific NO-GO."""


def _peak_utc_hour(source_text: str) -> tuple[str,str,str]:
    if not isinstance(source_text,str) or len(source_text)!=10 or not source_text.isdigit():
        raise HistoricSiteGridBlocked("original DWD 2020 hour label invalid")
    try:
        hour=datetime.strptime(source_text,"%Y%m%d%H").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise HistoricSiteGridBlocked("original DWD 2020 hour label invalid") from exc
    if not DATE_START<=hour<=DATE_END:
        raise HistoricSiteGridBlocked("original DWD FX911 gust hour outside accepted Ciara event study window")
    return (hour.isoformat().replace("+00:00","Z"),
            (hour-timedelta(hours=1)).isoformat().replace("+00:00","Z"),
            hour.isoformat().replace("+00:00","Z"))


def research_historical_site_grid_crosswalk(
    measured_dwd: dict, original_era5: dict, historical: dict,
) -> dict:
    """Conserve the old accepted source results, correct 2020 site support."""
    # The old receipt must NOT be rewritten: it accurately captures what
    # the originally published current station master list said and the
    # verified exact original DWD ZIP + ERA5 matrix source evidence.
    old=prior.combine_original_2020_station_and_grid_peaks(measured_dwd,original_era5)
    prior.verify_first_original_station_era5_comparison_receipt(old)

    with ORIGINAL_DWD_HISTORIC_RECEIPT.open("rb") as f:
        pinned=tomllib.load(f)
    if (historical.get("schema")!=historic.SCHEMA
        or historical.get("station_count")!=3
        or historical.get("DWD_original_site_geography_Feb2020_verified") is not True
        or historical.get("DWD_original_sensor_height_type_Feb2020_verified") is not True
        or historical.get("DWD_original_FX911_hour_reference_declared_UTC") is not True
        or historical.get("DWD_FX911_and_ERA5_10fg_exact_gust_aggregation_same") is not False
        or historical.get("ERA5_station_matched_hour_bias_or_RMSE_approved") is not False
        or historical.get("insurer_real_2020_loss_vulnerability_GUL_IL_RI_OEP_AEP_admitted") is not False
        or pinned.get("schema")!=historic.SCHEMA
        or pinned.get("source_original_DWD_FX911_UTC_reference_hour_label_attested") is not True
        or pinned.get("ERA5_10fg_time_support_aggregation_equal_to_DWD_FX911_verified") is not False):
        raise HistoricSiteGridBlocked("historical site and UTC source evidence not admitted")
    original_station_records=historical.get("stations",[])
    frozen_station_records=pinned.get("stations",[])
    if (len(original_station_records)!=3 or len(frozen_station_records)!=3
        or [s.get("station_id") for s in original_station_records]!=list(EXPECTED)
        or [s.get("station_id") for s in frozen_station_records]!=list(EXPECTED)):
        raise HistoricSiteGridBlocked("expected exactly three original 2020 DWD station histories")

    required_pairs={
        "original_DWD_station_latitude_as_of_Feb2020":"feb2020_latitude",
        "original_DWD_station_longitude_as_of_Feb2020":"feb2020_longitude",
        "original_DWD_station_elevation_m_as_of_Feb2020":"feb2020_station_elevation_m",
        "original_FX911_anemometer_height_above_ground_m_as_of_Feb2020":
            "feb2020_wind_anemometer_height_above_ground_m",
        "original_FX911_instrument_type_as_of_Feb2020":"feb2020_instrument_type",
        "original_FX911_procedure_as_of_Feb2020":"feb2020_measurement_procedure",
        "nearest_2020_ERA5_grid_lat":"2020_original_era5_comparison_grid_lat",
        "nearest_2020_ERA5_grid_lon":"2020_original_era5_comparison_grid_lon",
        "historical_station_to_ERA5_grid_centre_km":"nearest_original_era5_grid_distance_km",
        "DWD_original_zip_sha256":"original_zip_sha256",
        "original_geo_interval_from":"feb2020_geo_valid_from",
        "original_instrument_interval_from":"feb2020_device_valid_from",
        "original_parameter_interval_from":"feb2020_parameter_valid_from",
    }
    old_stations=old["station_to_original_ERA5_peak_only"]
    results=[]
    cells=set()
    for i,(live_station,source_station,previous) in enumerate(
        zip(original_station_records,frozen_station_records,old_stations)):
        if (live_station["station_id"]!=EXPECTED[i]
            or previous["original_dwd_station_id"]!=EXPECTED[i]
            or any(live_station.get(k)!=source_station.get(v)
                   for k,v in required_pairs.items())
            or live_station.get("original_DWD_FX911_hour_label_declared_UTC") is not True
            or live_station.get("original_DWD_FX911_gust_highest_during_previous_hour") is not True
            or live_station.get("DWD_FX911_exact_same_postprocess_window_as_ERA5_10fg_verified") is not False
            or source_station.get("feb2020_hour_reference")!="in UTC"
            or source_station.get("feb2020_gust_reference")!="hoechste Windspitze der letzten Stunde"):
            raise HistoricSiteGridBlocked("DWD February 2020 source-attested metadata differs from its nine-SHA receipt")
        members=live_station.get("historical_member_sha256")
        if (not isinstance(members,dict) or set(members)!={"geographie","geraete","parameter"}
            or any(members[k]!=source_station[
                {"geographie":"geo","geraete":"device","parameter":"parameter"}[k]+"_member_sha256"
            ] for k in members)):
            raise HistoricSiteGridBlocked("original February 2020 DWD source member SHA changed")
        lat=live_station["original_DWD_station_latitude_as_of_Feb2020"]
        lon=live_station["original_DWD_station_longitude_as_of_Feb2020"]
        row,col,separation=prior.station_to_grid(lat,lon)
        gr_lat,gr_lon=era5.LATITUDE[row],era5.LONGITUDE[col]
        if (gr_lat!=source_station["2020_original_era5_comparison_grid_lat"]
            or gr_lon!=source_station["2020_original_era5_comparison_grid_lon"]
            or separation!=source_station["nearest_original_era5_grid_distance_km"]
            or gr_lat!=previous["nearest_era5_grid_lat"]
            or gr_lon!=previous["nearest_era5_grid_lon"]):
            raise HistoricSiteGridBlocked("source 2020 site changes ERA5 spatial node without independent evidence")
        utc_hour,interval_begin,interval_end=_peak_utc_hour(
            previous["dwd_peak_hour_label_unharmonized"])
        cells.add((row,col))
        results.append({
            "DWD_station_id":EXPECTED[i],
            "DWD_station_name":source_station["name"],
            "DWD_original_zip_sha256":source_station["original_zip_sha256"],
            "DWD_2020_source_geography_sha256":source_station["geo_member_sha256"],
            "DWD_2020_source_device_sha256":source_station["device_member_sha256"],
            "DWD_2020_source_parameter_sha256":source_station["parameter_member_sha256"],
            "actual_2020_DWD_station_latitude":lat,
            "actual_2020_DWD_station_longitude":lon,
            "actual_2020_station_elevation_m":live_station["original_DWD_station_elevation_m_as_of_Feb2020"],
            "actual_2020_wind_anemometer_height_m":live_station[
                "original_FX911_anemometer_height_above_ground_m_as_of_Feb2020"],
            "actual_2020_wind_anemometer_type":live_station["original_FX911_instrument_type_as_of_Feb2020"],
            "original_DWD_measured_2020_96h_peak_mps":previous[
                "dwd_measured_original_2020_96h_peak_FX911_mps"],
            "DWD_reported_peak_hour_label_in_UTC":utc_hour,
            "DWD_peak_gust_previous_hour_start_UTC":interval_begin,
            "DWD_peak_gust_previous_hour_end_UTC":interval_end,
            "Google_ERA5_reanalysis_grid_centre_lat":gr_lat,
            "Google_ERA5_reanalysis_grid_centre_lon":gr_lon,
            "2020_historic_sensor_to_model_grid_distance_km":separation,
            "Google_ERA5_2020_96h_event_peak_mps":previous[
                "google_era5_modelled_original_2020_96h_peak_10fg_mps"],
            "descriptive_event_peak_ERA5_minus_DWD_mps_NOT_BIAS":previous[
                "descriptive_peak_difference_era5_minus_dwd_mps_not_bias_or_skill"],
            "prior_current_station_site_to_grid_distance_km":previous[
                "distance_publisher_current_station_to_era5_grid_km"],
            "same_UTC_hour_gust_pair_read_or_matched":False,
            "ERA5_vs_DWD_hourly_RMSE_bias_skill_approved":False,
        })
    if len(cells)!=2 or results[0]["Google_ERA5_reanalysis_grid_centre_lat"]!=results[2]["Google_ERA5_reanalysis_grid_centre_lat"]:
        raise HistoricSiteGridBlocked("three 2020 historical DWD stations do not map to original two independent ERA5 nodes")
    if (results[2]["actual_2020_DWD_station_latitude"]==pinned["stations"][2]["after_event_publisher_station_lat"]
        or results[2]["actual_2020_wind_anemometer_height_m"]==
            pinned["stations"][2]["after_event_publisher_sensor_height_m"]):
        raise HistoricSiteGridBlocked("post-Ciara October 2020 Königswinter relocation improperly reused")
    return {
        "schema":SCHEMA,
        "status":"RESEARCH_ORIGINAL_2020_HISTORIC_DWD_SITE_PLUS_UTC_NOMINAL_HOUR_TO_ERA5_EVENT_PEAK_ONLY",
        "actual_source_verified_2020_DWD_station_count":len(results),
        "actual_source_verified_2020_ERA5_unique_grid_cells":len(cells),
        "original_DWD_2020_observed_hourly_FX911_count":288,
        "original_Google_ERA5_2020_decoded_96h_160node_sha256":
            prior.ERA5_DECODED_96H_160_SHA,
        "original_source_historical_site_member_SHAs_checked":9,
        "DWD_original_2020_hourly_gust_definition":"highest wind gust in previous hour",
        "DWD_original_2020_hour_label_timezone":"UTC",
        "ERA5_HRES_10fg_hour_ending_validity_documentation":ERA5_HRES_TIME_DOC,
        "nominal_UTC_hour_ending_support_for_DWD_and_ERA5_documented":True,
        "DWD_original_observed_at_station_ERA5_modelled_at_0p25degree_cell":True,
        "2020_station_site_and_instrument_verified":True,
        "2020_station_source_rights":"DWD CDC CC BY 4.0, DWD attribution",
        "ERA5_original_source_rights":"Copernicus Licence, C3S and Google Research attribution",
        "historically_correct_stations":results,
        "same_UTC_hour_wind_pairs_retrieved":False,
        "same_hour_gust_sampling_methods_ERA5_DWD_physically_equivalent":False,
        "independent_ERA5_station_gridpoint_skill_RMSE_bias_approved":False,
        "observed_RV_insured_2020_site_or_claims":False,
        "German_wind_damage_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted":False,
        "annual_stochastic_EP_or_SCR_admitted":False,
    }


FIRST_VERIFIED_2020_SITE_ERA5_ORIGINAL_PEAKS = (
    Path(__file__).resolve().parents[1] /
    "research/observations/ciara2020_dwd2020_historic_sites_to_two_era5_utc_peaks_v1.toml"
)


def verify_first_historical_site_original_live_receipt(result: dict) -> None:
    """Pin the actual first independent live 2020 DWD/ERA5 corrected sites."""
    with FIRST_VERIFIED_2020_SITE_ERA5_ORIGINAL_PEAKS.open("rb") as fd:
        source=tomllib.load(fd)
    if (source.get("schema")!=SCHEMA
        or source.get("first_genuine_2020_historic_site_and_ERA5_live_github_run")!=43608886802
        or source.get("first_genuine_2020_historic_site_and_ERA5_live_github_job")!=132489320449
        or source.get("original_source_era5_decoded_96h_160node_sha256")!=prior.ERA5_DECODED_96H_160_SHA
        or result.get("original_Google_ERA5_2020_decoded_96h_160node_sha256")!=prior.ERA5_DECODED_96H_160_SHA
        or source.get("original_dwd_archives_source_count")!=3
        or source.get("original_historical_geo_device_param_metadata_sha_count")!=9
        or source.get("original_2020_DWD_hourly_FX911_observations")!=288
        or source.get("unique_original_ERA5_grid_cells_for_three_sites")!=2
        or source.get("DWD_original_FX911_previous_hour_UTC_declared") is not True
        or source.get("ERA5_HRES_10fg_previous_hour_ending_validity_documented") is not True
        or source.get("source_2020_historical_site_sensor_verified") is not True
        or source.get("same_hour_station_vs_ERA5_gust_pairs_extracted") is not False
        or source.get("matched_hour_ERA5_station_model_bias_or_RMSE_approved") is not False
        or source.get("german_building_wind_vulnerability_or_loss_function_calibrated") is not False
        or source.get("real_2020_RV_policy_site_exposure_or_claims_observed") is not False
        or source.get("native_GUL_IL_RI_OEP_AEP_or_SCR_admitted") is not False
        or result.get("same_UTC_hour_wind_pairs_retrieved") is not False
        or result.get("independent_ERA5_station_gridpoint_skill_RMSE_bias_approved") is not False
        or result.get("German_wind_damage_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted") is not False):
        raise HistoricSiteGridBlocked("actual first live source 2020 historic-site receipt or model NO-GO drift")
    actual=result.get("historically_correct_stations",[])
    accepted=source.get("stations",[])
    if len(actual)!=3 or len(accepted)!=3:
        raise HistoricSiteGridBlocked("historical 2020 original 3 DWD source sites changed")
    pairs={
        "id":"DWD_station_id",
        "original_dwd_zip_sha256":"DWD_original_zip_sha256",
        "historic_2020_lat":"actual_2020_DWD_station_latitude",
        "historic_2020_lon":"actual_2020_DWD_station_longitude",
        "historic_2020_ground_elevation_m":"actual_2020_station_elevation_m",
        "historic_2020_anemometer_height_m":"actual_2020_wind_anemometer_height_m",
        "ERA5_original_node_lat":"Google_ERA5_reanalysis_grid_centre_lat",
        "ERA5_original_node_lon":"Google_ERA5_reanalysis_grid_centre_lon",
        "historic_2020_to_original_ERA5_node_km":"2020_historic_sensor_to_model_grid_distance_km",
        "old_current_site_to_original_ERA5_node_km":"prior_current_station_site_to_grid_distance_km",
        "DWD_original_2020_event_max_FX911_mps":"original_DWD_measured_2020_96h_peak_mps",
        "Google_original_2020_ERA5_event_max_10fg_mps":"Google_ERA5_2020_96h_event_peak_mps",
        "descriptive_peak_diff_mps_NOT_BIAS":"descriptive_event_peak_ERA5_minus_DWD_mps_NOT_BIAS",
        "DWD_original_FX911_peak_hour_UTC":"DWD_reported_peak_hour_label_in_UTC",
        "DWD_original_FX911_peak_previous_hour_start_UTC":"DWD_peak_gust_previous_hour_start_UTC",
    }
    for a,b in zip(accepted,actual):
        if (any(a.get(k)!=b.get(v) for k,v in pairs.items())
            or b.get("same_UTC_hour_gust_pair_read_or_matched") is not False
            or b.get("ERA5_vs_DWD_hourly_RMSE_bias_skill_approved") is not False):
            raise HistoricSiteGridBlocked("true original February 2020 sites, UTC periods or ERA5 source peaks drift")


def live_original_historical_site_peak_replay() -> dict:
    measured=dwd.live_dwd_2020_original_three_stations()
    weather=era5.original_96h_grid(include_public_grid_peaks=True)
    metadata=historic.live_feb2020_attestation()
    result=research_historical_site_grid_crosswalk(measured,weather,metadata)
    verify_first_historical_site_original_live_receipt(result)
    return result


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run",action="store_true")
    mode.add_argument("--live-historic-site-peaks",action="store_true")
    args=p.parse_args()
    try:
        if args.dry_run:
            output={
                "schema":SCHEMA,
                "expected_historically_source_attested_DWD_stations":3,
                "expected_original_ERA5_distinct_grid_cells":2,
                "2020_original_DWD_ERA5_source_data_fetched":False,
                "2020_historic_sensor_site_replayed":False,
                "loss_model_approved":False,
            }
        else:
            output=live_original_historical_site_peak_replay()
        print(json.dumps(output,indent=2,sort_keys=True,ensure_ascii=True))
        return 0
    except (HistoricSiteGridBlocked,prior.DWDGridComparisonBlocked,
            dwd.OriginalDWDRejected,era5.RealGridBlocked,
            historic.HistoricalDWDNoGo,OSError,ValueError) as exc:
        p.exit(2,"CIARA2020_ORIGINAL_HISTORIC_DWD_SITE_ERA5_UTC_PEAK_NO_GO: "+str(exc)+"\n")


if __name__=="__main__":
    sys.exit(main())
