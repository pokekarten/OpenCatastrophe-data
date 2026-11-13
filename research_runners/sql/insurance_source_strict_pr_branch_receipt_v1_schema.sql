-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- REVIEW-REQUIRED, ADDITIVE DDL. DO NOT apply to production Neon without
-- explicit approval and a tested schema migration. Existing strict-main
-- receipt ledgers remain unchanged. Source provider bytes never stored.
--
-- This table specifically records actual original-source responses from
-- one-shot PUBLIC pull-request BRANCH GitHub Actions runs. Those commits
-- have passed source-specific checks but are NOT first-party trusted main.
-- No science/licence/CAT-model admission is implied by HTTP success.
CREATE TABLE IF NOT EXISTS research.source_strict_pr_branch_receipt_v1 (
  receipt_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_id text NOT NULL CHECK (source_id ~ '^[A-Za-z0-9][A-Za-z0-9._-]*$'),
  exact_source_url text NOT NULL CHECK (exact_source_url ~ '^https://[^[:space:]]+$'),
  source_operation text NOT NULL CHECK (source_operation IN (
    'corrected_2021_2k_prefix',
    'rtsw_mag_1m_json',
    'definitive_kp_day_json'
  )),
  original_http_status integer NOT NULL CHECK (original_http_status IN (200,206)),
  original_request_range text,
  original_content_range text,
  original_response_bytes integer NOT NULL CHECK (original_response_bytes BETWEEN 1 AND 4194304),
  original_request_sha256 text NOT NULL CHECK (original_request_sha256 ~ '^[a-f0-9]{64}$'),
  original_response_sha256 text NOT NULL CHECK (original_response_sha256 ~ '^[a-f0-9]{64}$'),
  runner_code_sha256 text NOT NULL CHECK (runner_code_sha256 ~ '^[a-f0-9]{64}$'),
  access_contract_sha256 text CHECK (access_contract_sha256 ~ '^[a-f0-9]{64}$'),
  offline_validator_sha256 text CHECK (offline_validator_sha256 ~ '^[a-f0-9]{64}$'),
  provider_observed_at timestamptz NOT NULL,
  github_repo text NOT NULL DEFAULT 'pokekarten/OpenCatastrophe-data'
    CHECK (github_repo = 'pokekarten/OpenCatastrophe-data'),
  github_run_id bigint NOT NULL CHECK (github_run_id > 0),
  github_job_id bigint NOT NULL CHECK (github_job_id > 0),
  github_run_url text NOT NULL
    CHECK (github_run_url =
      'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/' ||
      github_run_id::text),
  github_head_sha text NOT NULL CHECK (github_head_sha ~ '^[a-f0-9]{40}$'),
  github_event text NOT NULL CHECK (github_event = 'push'),
  github_ref text NOT NULL CHECK (
    github_ref ~ '^refs/heads/research/[A-Za-z0-9._/-]+$'
    AND github_ref <> 'refs/heads/main'
  ),
  verified_public_pr_branch_run boolean NOT NULL CHECK (verified_public_pr_branch_run = true),
  first_party_trusted_main_run boolean NOT NULL DEFAULT false
    CHECK (first_party_trusted_main_run = false),
  original_bytes_persisted boolean NOT NULL DEFAULT false
    CHECK (original_bytes_persisted = false),
  full_source_sha256_verified boolean NOT NULL DEFAULT false
    CHECK (full_source_sha256_verified = false),
  physical_science_validated boolean NOT NULL DEFAULT false
    CHECK (physical_science_validated = false),
  insurer_model_input_approved boolean NOT NULL DEFAULT false
    CHECK (insurer_model_input_approved = false),
  source_rights_scope text NOT NULL CHECK (length(trim(source_rights_scope)) >= 15),
  evidence_note text NOT NULL CHECK (length(trim(evidence_note)) >= 50),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT source_strict_pr_branch_receipt_v1_http_scope_ck CHECK (
    (
      original_http_status = 206
      AND source_operation = 'corrected_2021_2k_prefix'
      AND original_request_range IS NOT NULL
      AND original_content_range IS NOT NULL
      AND original_request_range = 'bytes=0-2047'
      AND original_content_range = 'bytes 0-2047/820143312'
      AND original_response_bytes = 2048
    ) OR (
      original_http_status = 200
      AND source_operation IN ('rtsw_mag_1m_json','definitive_kp_day_json')
      AND original_request_range IS NULL
      AND original_content_range IS NULL
      AND original_response_bytes BETWEEN 1 AND 4194304
    )
  ),
  CONSTRAINT source_strict_pr_branch_receipt_v1_source_scope_ck CHECK (
    (source_id = 'dwd.radklim.rw.v2017.002' AND source_operation = 'corrected_2021_2k_prefix')
    OR (source_id = 'noaa.swpc.real-time-solar-wind' AND source_operation = 'rtsw_mag_1m_json')
    OR (source_id = 'gfz.geomagnetic-kp' AND source_operation = 'definitive_kp_day_json')
  ),
  -- Bind every claimed original body hash to the fixed, previously
  -- reviewed provider endpoint. No caller-selected host or query.
  CONSTRAINT source_strict_pr_branch_receipt_v1_exact_endpoint_ck CHECK (
    (source_id = 'dwd.radklim.rw.v2017.002'
     AND exact_source_url = 'https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/radolan/reproc/2017_002/netCDF/supplement/RW2017.002_2021_netcdf_supplement.tar.gz')
    OR (source_id = 'noaa.swpc.real-time-solar-wind'
     AND exact_source_url = 'https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json')
    OR (source_id = 'gfz.geomagnetic-kp'
     AND exact_source_url = 'https://kp.gfz.de/app/json/?start=2024-01-01T00:00:00Z&end=2024-01-01T23:59:59Z&index=Kp&status=def')
  ),
  CONSTRAINT source_strict_pr_branch_receipt_v1_validated_code_ck CHECK (
    access_contract_sha256 IS NOT NULL OR offline_validator_sha256 IS NOT NULL
  ),
  CONSTRAINT source_strict_pr_branch_receipt_v1_run_unique
    UNIQUE (source_id,github_run_id,github_job_id,original_request_sha256)
);
