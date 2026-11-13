-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0

-- Exact successful original first-party PDOK collection metadata receipt.
-- GitHub Action: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43489886311
-- Direct main job 132108208702, push commit 526303e78974ed234610bf0a65fac4786512da13.
-- Actual source raw byte digest 99a64145c7b198bbe2e2a78f248c24845e212210d482e805cb581d6aaa61ca79, 3730 original bytes.
-- No provider source JSON retained and no 2025 archival-source assertion.
INSERT INTO research.source_strict_metadata_probe_receipt_v1
  (source_id, access_id, exact_source_url, http_method, response_http_status, response_mime, original_response_bytes, request_sha256, original_response_sha256, source_access_contract_sha256, original_runner_code_sha256, provider_observed_at, github_run_id, github_job_id, github_run_url, github_head_sha, github_event, github_ref, original_source_identity_validated, response_json_schema_validated, original_response_body_persisted, original_feature_rows_acquired, raw_source_assets_admitted, model_input_approved, science_or_version_admission_verified, source_provenance_note)
VALUES
  ('nl.rvo.brp-gewaspercelen.2025',
   'nl.rvo.brp-gewaspercelen.2025.ogc-collection',
   'https://api.pdok.nl/rvo/gewaspercelen/ogc/v1/collections/brpgewas?f=json',
   'GET',
   200,
   'application/json',
   3730,
   'f50ae18fd344ff4c201dd3e1db6fd75f321bb302e4f84fda642d6a1750696eb2',
   '99a64145c7b198bbe2e2a78f248c24845e212210d482e805cb581d6aaa61ca79',
   '7164465a21b3cfb7e0dae2b77e89e31fcfd034297a156c7781083e53717ad396',
   'be00542bed9b6b5a2e41773a32421b41aba0d5b3b8ade4ca8d293c133eb10d66',
   '2026-11-13T19:12:32.658210+00:00',
   43489886311,
   132108208702,
   'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43489886311',
   '526303e78974ed234610bf0a65fac4786512da13',
   'push',
   'refs/heads/main',
   true,
   true,
   false,
   0,
   false,
   false,
   false,
   'Original fixed public PDOK BRP collection metadata-only anonymous GET. Exact brpgewas identity, CRS84 + EPSG:28992 and Netherlands bbox verified. No items/crop features, historical 2025 frozen archive, source raw body, insured exposure, event hazards or model inputs. First-party main GitHub Action succeeded with exact original response SHA.')
ON CONFLICT (source_id, github_run_id, github_job_id, request_sha256)
DO NOTHING;
