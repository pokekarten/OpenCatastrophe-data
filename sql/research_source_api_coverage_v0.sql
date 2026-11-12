-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Reproducible private Neon SQL for original-source API smoke coverage.
-- All external data is fetched and checked elsewhere. This schema stores
-- receipts only: no provider payloads, credentials, personal data, original
-- claim/policy values, or CAT-model admission.
--
-- Applied to the separate private insurance-risk-core database (2026-11-12).
-- The full registry includes landscape candidates AND admitted manifests.
-- Passing a JSON smoke or an existing manifest is not scientific admission.

CREATE TABLE IF NOT EXISTS research.source_api_smoke_receipt_v0 (
    receipt_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id text NOT NULL,
    endpoint_url text NOT NULL CHECK (endpoint_url ~ '^https://'),
    checked_at timestamptz NOT NULL DEFAULT now(),
    observation_kind text NOT NULL DEFAULT 'live_bounded_metadata_smoke'
        CHECK (observation_kind = 'live_bounded_metadata_smoke'),
    response_bytes integer CHECK (response_bytes >= 0 AND response_bytes <= 4194304),
    http_read_status text NOT NULL
        CHECK (http_read_status IN ('succeeded', 'unverified')),
    json_shape_status text NOT NULL
        CHECK (json_shape_status IN ('pass', 'inconclusive')),
    note text NOT NULL,
    strict_repository_runner_executed boolean NOT NULL DEFAULT false
        CHECK (NOT strict_repository_runner_executed),
    provider_bytes_persisted boolean NOT NULL DEFAULT false
        CHECK (NOT provider_bytes_persisted),
    model_input_approved boolean NOT NULL DEFAULT false
        CHECK (NOT model_input_approved)
);

-- First, research candidate-only coverage (692 as at initial audit).
-- Read-only projection; absence of a probe is not an API outage.
CREATE OR REPLACE VIEW research.source_api_coverage_v0 AS
WITH normalized_receipts AS (
    SELECT r.*,
        CASE WHEN r.source_id = 'wsv.pegelonline.rest-v2.dresden'
        THEN 'wsv.pegelonline.elbe-dresden-discharge.2020-2023'
        ELSE r.source_id END AS candidate_id
    FROM research.source_api_smoke_receipt_v0 r
), numbered AS (
    SELECT n.*,
        row_number() OVER (
            PARTITION BY n.candidate_id ORDER BY n.checked_at DESC, n.receipt_id DESC
        ) AS most_recent_rank,
        count(*) OVER (PARTITION BY n.candidate_id) AS observations_for_candidate
    FROM normalized_receipts n
)
SELECT c.source_id, c.source_name, c.commercial_reuse_verdict, c.admission_status,
    coalesce(n.observations_for_candidate, 0)::int AS bounded_original_request_receipts,
    coalesce(n.http_read_status, 'not_tested') AS latest_http_read,
    coalesce(n.json_shape_status, 'not_tested') AS latest_json_shape,
    n.endpoint_url AS last_exact_endpoint,
    n.checked_at AS last_checked_at,
    CASE
       WHEN n.receipt_id IS NULL THEN 'needs_rights_review_and_bounded_provider_probe'
       WHEN n.json_shape_status = 'inconclusive' THEN 'recheck_with_trusted_original_runner'
       ELSE 'needs_strict_repository_probe_and_scientific_source_validation'
    END AS next_gate,
    false AS model_input_admitted_by_receipts
FROM research.source_candidate_review_v0 c
LEFT JOIN numbered n ON c.source_id = n.candidate_id AND n.most_recent_rank = 1;

-- Full 692 + 15 registered-source records, including the WSV admitted-manifest
-- source whose fixed Dresden probe has a distinct access-contract ID.
CREATE OR REPLACE VIEW research.all_source_api_coverage_v0 AS
WITH normalized AS (
    SELECT r.*,
       CASE WHEN r.source_id = 'wsv.pegelonline.rest-v2.dresden'
       THEN 'wsv.pegelonline.elbe-dresden-discharge.2020-2023'
       ELSE r.source_id END AS registry_source_id
    FROM research.source_api_smoke_receipt_v0 r
), ranked AS (
    SELECT n.*,
       row_number() OVER (
           PARTITION BY n.registry_source_id ORDER BY n.checked_at DESC,n.receipt_id DESC
       ) rn,
       count(*) OVER (PARTITION BY n.registry_source_id) AS total_probes
    FROM normalized n
)
SELECT i.record_type, i.source_id, i.source_name,
    i.commercial_reuse_verdict, i.admission_status,
    coalesce(r.total_probes,0)::int AS bounded_original_requests,
    coalesce(r.http_read_status,'not_tested') AS last_http_read,
    coalesce(r.json_shape_status,'not_tested') AS last_json_shape,
    r.endpoint_url AS last_exact_endpoint,
    r.checked_at AS last_probe_at_utc,
    CASE
      WHEN r.receipt_id IS NULL THEN 'needs_exact_access_and_rights_preflight'
      WHEN r.json_shape_status = 'inconclusive' THEN 'retest_trusted_strict_original_probe'
      ELSE 'needs_scientific_and_commercial_specific_admission_gate'
    END AS next_gate,
    false AS model_input_admitted_by_api_probe
FROM research.all_source_inventory_v0 i
LEFT JOIN ranked r ON i.source_id = r.registry_source_id AND r.rn = 1;

-- Read-only coverage query:
-- SELECT record_type, count(*) AS source_records,
-- count(*) FILTER (WHERE last_json_shape = 'pass') AS parseable_bounded_read,
-- count(*) FILTER (WHERE last_json_shape = 'inconclusive') AS unclear,
-- count(*) FILTER (WHERE last_json_shape = 'not_tested') AS no_actual_api_smoke
-- FROM research.all_source_api_coverage_v0 GROUP BY 1;
