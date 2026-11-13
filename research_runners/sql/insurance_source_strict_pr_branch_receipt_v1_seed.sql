-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- REVIEW-REQUIRED seed for three INDEPENDENT verified public GitHub ORIGINAL
-- provider runs on research PR branches, never on trusted main. Do not run on
-- production until the additive schema and exact Actions logs are approved.
-- Values are original response hashes and provenance only, NO provider bytes.
INSERT INTO research.source_strict_pr_branch_receipt_v1
(source_id, exact_source_url, source_operation, original_http_status,
 original_request_range, original_content_range, original_response_bytes,
 original_request_sha256, original_response_sha256, runner_code_sha256,
 access_contract_sha256, offline_validator_sha256, provider_observed_at,
 github_run_id, github_job_id, github_run_url, github_head_sha, github_event,
 github_ref, verified_public_pr_branch_run, source_rights_scope, evidence_note)
VALUES
 ('dwd.radklim.rw.v2017.002',
  'https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/radolan/reproc/2017_002/netCDF/supplement/RW2017.002_2021_netcdf_supplement.tar.gz',
  'corrected_2021_2k_prefix',206,'bytes=0-2047',
  'bytes 0-2047/820143312',2048,
  '76b410d2c64e3147bb6932df07c860455d04e097d1ec3fe179ea16a472cb28c3',
  '741c1320301be519a57818655d0380d94a6b6865adc3249f454f9c9cdf254867',
  '635be219e2faf2b2e680f5a3d0f8d0b32cb3f80ba19440f38c6bb68b9672bd71',
  NULL,
  '86cbdfaf7e764d29be08d0c3b01b110726b10c480bdb21dbda782bbf62674a4b',
  '2026-11-13T19:04:19.824499+00:00',
  43488656039,132103695178,
  'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43488656039',
  '01ab7b83d1765fb6bbe590ad772880c65d5e43c9','push',
  'refs/heads/research/dwd-radklim-2021-corrected-native-header-proof-20261113',
  true,
  'DWD CDC CC BY 4.0 research scope; correction-specific 2021 supplement, attribution required',
  'Verified exact HTTP206 original compressed 2048-byte prefix with two TAR checksums and NetCDF4 signature; complete monthly NetCDF, source archive, meteorology and model inputs NOT verified. Public PR-branch run; not main.'),
 ('noaa.swpc.real-time-solar-wind',
  'https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json',
  'rtsw_mag_1m_json',200,NULL,NULL,1719377,
  '9c8cff6ed4aa0ba97edb2a8d179728c5696e446c25437fbf9dfc758d20ac31d2',
  'bc35b0a375b85efe559f132cfae46d8c79b7e8f19400299ae223d067f6091159',
  '80b80b5b214c471eb43ae3d303e95748afb7be624dea351f663a057f52333281',
  '28a80ab81521d4b4a3b5332cfd0d38343b7b41bdb9168cc8833c8aa0320292ca',
  NULL,
  '2026-11-13T19:09:57.147645+00:00',
  43489514680,132106651956,
  'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43489514680',
  '4a579279e240c9429e6e66360194446c7c6e48b9','push',
  'refs/heads/research/noaa-swpc-rtsw-2026-shape-gate-20261113',
  true,
  'NOAA NWS public government service with appropriate-use/nonendorsement caveats; no third-party sensor reuse assumption',
  'Direct original HTTP200 1719377-byte rolling JSON, 2026 multi-spacecraft fields and SHA verified; no fixed source history, sensor science verification, response republication or model admission. Public PR-branch run; not main.'),
 ('gfz.geomagnetic-kp',
  'https://kp.gfz.de/app/json/?start=2024-01-01T00:00:00Z&end=2024-01-01T23:59:59Z&index=Kp&status=def',
  'definitive_kp_day_json',200,NULL,NULL,361,
  'f766594d3b83d42a9a16ef247c7119f1a435a2ea00d5c004876e4cfab3cd7dfd',
  'f03506f678672a99c4c5a2c1d251740bd484b064853db18177b9b5ba4ad27d0a',
  '423e21bda179d5664a74f3c3bbe2a5e6d955aa4386305545d292a627b191affa',
  '1c57d8e1147c511e14af0d9468b4a55fc80c5000c3c441b30660679673f1c02d',
  NULL,
  '2026-11-13T19:19:54.407282+00:00',
  43491158483,132112397671,
  'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43491158483',
  '17da6a4a3250bc63e7c363a47f74213472196eeb','push',
  'refs/heads/research/noaa-swpc-rtsw-2026-shape-gate-20261113',
  true,
  'GFZ definitive Kp original dataset CC BY 4.0; attribution and source-product scope required',
  'Direct original HTTP200 361-byte definitive 2024-01-01 Kp JSON, eight three-hourly definitive bins and SHA verified; no independent physical science verification, extended event history or model admission. Public PR-branch run; not main.')
ON CONFLICT (source_id,github_run_id,github_job_id,original_request_sha256)
DO NOTHING;
