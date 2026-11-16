-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0

-- First-party trusted-main original provider API JSON metadata GET receipts.
-- Separate from 206 Range table and intermediary smoke ledger. No original
-- body storage, raw asset admission, external source bytes or model approval.
CREATE TABLE IF NOT EXISTS research.source_strict_metadata_probe_receipt_v1 (
  receipt_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_id text NOT NULL CHECK (source_id ~ '^[A-Za-z0-9][A-Za-z0-9._-]*$'),
  access_id text NOT NULL CHECK (access_id ~ '^[A-Za-z0-9][A-Za-z0-9._-]*$'),
  exact_source_url text NOT NULL CHECK (exact_source_url ~ '^https://[^[:space:]]+$'),
  http_method text NOT NULL DEFAULT 'GET' CHECK (http_method = 'GET'),
  response_http_status integer NOT NULL CHECK (response_http_status = 200),
  response_mime text NOT NULL CHECK (response_mime = 'application/json'),
  original_response_bytes integer NOT NULL CHECK (original_response_bytes BETWEEN 1 AND 262144),
  request_sha256 text NOT NULL CHECK (request_sha256 ~ '^[a-f0-9]{64}$'),
  original_response_sha256 text NOT NULL CHECK (original_response_sha256 ~ '^[a-f0-9]{64}$'),
  source_access_contract_sha256 text NOT NULL CHECK (source_access_contract_sha256 ~ '^[a-f0-9]{64}$'),
  original_runner_code_sha256 text NOT NULL CHECK (original_runner_code_sha256 ~ '^[a-f0-9]{64}$'),
  provider_observed_at timestamptz NOT NULL,
  github_run_id bigint NOT NULL CHECK (github_run_id > 0),
  github_job_id bigint NOT NULL CHECK (github_job_id > 0),
  github_run_url text NOT NULL CHECK (
    github_run_url = 'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/' || github_run_id::text
  ),
  github_head_sha text NOT NULL CHECK (github_head_sha ~ '^[a-f0-9]{40}$'),
  github_repo text NOT NULL DEFAULT 'pokekarten/OpenCatastrophe-data'
    CHECK (github_repo = 'pokekarten/OpenCatastrophe-data'),
  github_event text NOT NULL DEFAULT 'push' CHECK (github_event = 'push'),
  github_ref text NOT NULL DEFAULT 'refs/heads/main' CHECK (github_ref = 'refs/heads/main'),
  original_source_identity_validated boolean NOT NULL CHECK (original_source_identity_validated),
  response_json_schema_validated boolean NOT NULL CHECK (response_json_schema_validated),
  original_response_body_persisted boolean NOT NULL DEFAULT false
    CHECK (original_response_body_persisted = false),
  original_feature_rows_acquired integer NOT NULL DEFAULT 0
    CHECK (original_feature_rows_acquired = 0),
  raw_source_assets_admitted boolean NOT NULL DEFAULT false
    CHECK (raw_source_assets_admitted = false),
  model_input_approved boolean NOT NULL DEFAULT false
    CHECK (model_input_approved = false),
  science_or_version_admission_verified boolean NOT NULL DEFAULT false
    CHECK (science_or_version_admission_verified = false),
  source_provenance_note text NOT NULL CHECK (length(trim(source_provenance_note)) >= 30),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT source_strict_metadata_probe_receipt_v1_unique_source_run
    UNIQUE (source_id, github_run_id, github_job_id, request_sha256)
);
