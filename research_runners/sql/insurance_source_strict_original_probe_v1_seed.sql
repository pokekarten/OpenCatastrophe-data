-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0

-- Two ACTUAL original-provider 4096-byte Range responses, from immutable
-- GitHub Actions run 43480623017 (job 132075848823) on trusted main
-- commit cf22ff485271d4d681a9b87f766440c2986bd13e. Confirmed job success,
-- source IDs, byte size/CSV schema and hashes in GitHub first-party logs.
-- Idempotent; no response bodies or secret material.
INSERT INTO research.source_strict_original_probe_receipt_v1
(source_id, original_source_url, original_http_status, original_request_range, original_content_range, original_response_bytes, original_request_sha256, original_response_sha256, contract_sha256, runner_code_sha256, provider_observed_at, github_repo, github_run_id, github_job_id, github_run_url, github_head_sha, github_event, github_ref, observed_csv_columns, observed_complete_event_rows, source_rights_label, receipt_note)
VALUES
  ('dwd.catrare.w3-eta.v2026.01',
    'https://opendata.dwd.de/climate_environment/CDC/event_catalogues/germany/precipitation/CatRaRE_v2026.01/data/CatRaRE_2001_2025_W3_Eta_v2026_01.csv',
    206,
    'bytes=0-4095',
    'bytes 0-4095/12410601',
    4096,
    'cdafab234e55ec4e5800180faad0c3e5876c367c76b3f13942a6bf2573ce841c',
    'a3e02cb676b855390c0a9b69f41352c7c3dff74c7c25e2578727e8397f9d9b12',
    '819de3fd2a30096915f36b9adb6538cb37fad78cfc2b21507aecae6b3c848d52',
    'd5ffbe69e3f790da41be11e7b64b4032a23f0a4a35c3330e8e7fdaf6220dd878',
    '2026-11-13T18:14:13.418748+00:00',
    'pokekarten/OpenCatastrophe-data',
    43480623017,
    132075848823,
    'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43480623017',
    'cf22ff485271d4d681a9b87f766440c2986bd13e',
    'push',
    'refs/heads/main',
    67,
    3,
    'DWD CDC CC BY 4.0; exact product/source release; attribution required',
    'Trusted main original-provider range on GitHub Actions; exact HTTP 206/Content-Range, 4096 original bytes, fixed CSV version/67 columns/first 3 rows, previous prefix SHA pin validated. Original provider bytes not persisted; no full CSV hash, EventZone geometry, scientific independence or model admission.'),
  ('dwd.catrare.t5-eta.v2026.01',
    'https://opendata.dwd.de/climate_environment/CDC/event_catalogues/germany/precipitation/CatRaRE_v2026.01/data/CatRaRE_2001_2025_T5_Eta_v2026_01.csv',
    206,
    'bytes=0-4095',
    'bytes 0-4095/17208653',
    4096,
    'e838175fe38591cc5abf2e196fd53e2f8a21e3482170e21553825e625c907815',
    '5dc4b6f0dac14f0a442103b78c16f647556bd870898aabff6d9f62aa4534f542',
    '2d342e8db510692bcc6ad7a11881fc41a3992d9738a4a64f2baa16169ba02fa4',
    'd5ffbe69e3f790da41be11e7b64b4032a23f0a4a35c3330e8e7fdaf6220dd878',
    '2026-11-13T18:14:14.096842+00:00',
    'pokekarten/OpenCatastrophe-data',
    43480623017,
    132075848823,
    'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43480623017',
    'cf22ff485271d4d681a9b87f766440c2986bd13e',
    'push',
    'refs/heads/main',
    67,
    3,
    'DWD CDC CC BY 4.0; exact product/source release; attribution required',
    'Trusted main original-provider range on GitHub Actions; exact HTTP 206/Content-Range, 4096 original bytes, fixed CSV version/67 columns/first 3 rows, previous prefix SHA pin validated. Original provider bytes not persisted; no full CSV hash, EventZone geometry, scientific independence or model admission.')
ON CONFLICT (source_id, github_run_id, github_job_id, original_request_sha256)
DO NOTHING;
