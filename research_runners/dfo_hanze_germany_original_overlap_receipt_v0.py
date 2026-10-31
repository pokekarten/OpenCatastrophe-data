# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Frozen aggregate-only real-source research receipt; not model data admission."""
import json

ORIGINAL_OVERLAP_RECEIPT = json.loads(r'''{
  "schema_version": "dfo-hanze-original-provider-overlap-receipt-v0",
  "observed_at": "2026-10-31",
  "reproducer_workflow": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41240799150",
  "reproducer_commit": "418f776739cb17ebc733deaff02f44a6230963e2",
  "method": "DFO event country text exactly 'Germany' and date range overlap with HANZE country_code DE; UN M49 country mapping evidence; no geographic footprint or cause confirmation",
  "country_mapping_evidence": "https://unstats.un.org/unsd/methodology/m49/overview/",
  "sources": {
    "dfo": {
      "release": "v0.9.0",
      "record": "https://zenodo.org/records/19288171",
      "bytes": 428865,
      "publisher_md5": "8fe3cd72474abe8d4d83641e2d33266f",
      "sha256": "9ebcb24b96e06f826a2a18f37e51788f7e8410575258e58f0c4c6310cece7924",
      "observed_events": 5503,
      "observed_start": "1985-01-01",
      "observed_end": "2024-01-09",
      "records_beyond_publisher_declared_end_year_2023": 4
    },
    "hanze": {
      "release": "v3.0.2-beta",
      "record": "https://zenodo.org/records/23670886",
      "bytes": 699910,
      "publisher_md5": "0e49c409d7cc9b1d42196d9c7cf677a1",
      "sha256": "44dc1861cf620d9e64085dc66159488237ca45df760d64042d921cd8b807ba66",
      "observed_events": 2780
    }
  },
  "country_only_results": {
    "dfo_germany_labelled_events": 13,
    "dfo_events_with_no_mapping": 5490,
    "germany_dfo_events_without_hanze_interval_overlap": 4,
    "possible_same_country_and_time_pairs": 9,
    "distinct_dfo_events_in_possible_pairs": 9,
    "distinct_hanze_events_in_possible_pairs": 9
  },
  "scientific_gates": {
    "same_event_identity_confirmed": false,
    "cause_geographic_footprints_harmonized": false,
    "source_reporting_independence_proven": false,
    "economic_or_insured_losses_joined": false,
    "model_data_admitted": false
  },
  "raw_provider_rows_in_git": false,
  "interpretation": "Exploratory 9 candidate pairs only. Shared country and overlapping dates do not establish duplicate records or identical flood events. 5490 unmapped DFO rows are deliberate absence of a reviewed country crosswalk, not evidence of absent flood risk.",
  "temporal_and_cause_diagnostics": {
    "evidence_stage": "AGGREGATE_EVENT_INTERVAL_AND_CAUSE_LABEL_COMPLETENESS_ONLY",
    "reproducer_workflow": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41243868121",
    "candidate_pair_count": 9,
    "inclusive_temporal_overlap_days": {
      "1": 0,
      "2-3": 3,
      "4-7": 4,
      "8+": 2
    },
    "absolute_start_date_difference_days": {
      "0": 3,
      "1-3": 2,
      "4-7": 2,
      "8+": 2
    },
    "pairs_with_both_cause_texts": 9,
    "pairs_with_exactly_same_casefolded_cause_text": 0,
    "cause_taxonomies_harmonized": false,
    "same_event_identity_confirmed": false,
    "geography_confirmed": false,
    "insured_loss_observed": false,
    "raw_provider_rows_emitted": false
  }
}''')
