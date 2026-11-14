-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0

-- Research-only evidence ledger for original-provider GETs proven by first-party
-- trusted-main GitHub Actions runner execution. This is explicitly DIFFERENT
-- from research.source_api_smoke_receipt_v0, whose NOT strict_runner constraint
-- is intentionally preserved. No raw provider bytes or CAT model admission.
CREATE TABLE IF NOT EXISTS research.source_strict_original_probe_receipt_v1 (
  receipt_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_id text NOT NULL CHECK (source_id ~ '^[A-Za-z0-9][A-Za-z0-9._-]*$'),
  original_source_url text NOT NULL CHECK (original_source_url ~ '^https://[^[:space:]]+$'),
  original_http_status integer NOT NULL CHECK (original_http_status = 206),
  original_request_range text NOT NULL CHECK (original_request_range ~ '^bytes=[0-9]+-[0-9]+$'),
  original_content_range text NOT NULL CHECK (original_content_range ~ '^bytes [0-9]+-[0-9]+/[0-9]+$'),
  original_response_bytes integer NOT NULL CHECK (original_response_bytes BETWEEN 1 AND 1048576),
  original_request_sha256 text NOT NULL CHECK (original_request_sha256 ~ '^[a-f0-9]{64}$'),
  original_response_sha256 text NOT NULL CHECK (original_response_sha256 ~ '^[a-f0-9]{64}$'),
  contract_sha256 text NOT NULL CHECK (contract_sha256 ~ '^[a-f0-9]{64}$'),
  runner_code_sha256 text NOT NULL CHECK (runner_code_sha256 ~ '^[a-f0-9]{64}$'),
  provider_observed_at timestamptz NOT NULL,
  github_repo text NOT NULL DEFAULT 'pokekarten/OpenCatastrophe-data'
    CHECK (github_repo = 'pokekarten/OpenCatastrophe-data'),
  github_run_id bigint NOT NULL CHECK (github_run_id > 0),
  github_job_id bigint NOT NULL CHECK (github_job_id > 0),
  github_run_url text NOT NULL
    CHECK (github_run_url = 'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/' || github_run_id::text),
  github_head_sha text NOT NULL CHECK (github_head_sha ~ '^[a-f0-9]{40}$'),
  github_event text NOT NULL CHECK (github_event = 'push'),
  github_ref text NOT NULL CHECK (github_ref = 'refs/heads/main'),
  observed_csv_columns smallint CHECK (observed_csv_columns BETWEEN 1 AND 1000),
  observed_complete_event_rows integer CHECK (observed_complete_event_rows >= 0),
  source_rights_label text NOT NULL,
  original_provider_body_persisted boolean NOT NULL DEFAULT false
    CHECK (original_provider_body_persisted = false),
  full_source_sha256_verified boolean NOT NULL DEFAULT false
    CHECK (full_source_sha256_verified = false),
  insurer_model_input_approved boolean NOT NULL DEFAULT false
    CHECK (insurer_model_input_approved = false),
  receipt_note text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT source_strict_original_probe_receipt_v1_run_identity_unique
    UNIQUE (source_id, github_run_id, github_job_id, original_request_sha256)
);
