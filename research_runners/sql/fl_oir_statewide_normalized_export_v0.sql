-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Research only. Execute on the isolated Neon validation-schema-20261031
-- branch; export the query result as UTF-8 CSV outside Git.
-- Fixed source and period deliberately prevent a mixed-time comparison.
-- The scope token is a human-declared normalized selection label, NOT
-- evidence of an official ZIP extract with matching query filters.
-- reported_exposure_including_wind_usd is the ONLY comparable wind-
-- structure exposure column; never substitute all-perils exposure or TIV.
SELECT
  report_as_of::text AS report_as_of,
  'fl_oir_mir_2025_12_statewide_company_policy_v1'::text AS scope_token,
  naic_code,
  reported_policy_type,
  reported_policies_in_force::text AS policies_in_force,
  reported_exposure_including_wind_usd::text AS wind_structure_exposure_usd
FROM exposure.fl_oir_mir_company_statewide_original_v1
WHERE source_key = 'official_fl_oir:2025_12_mir_original_full_company_policy_v1'
  AND report_as_of = DATE '2025-12-31'
ORDER BY naic_code, reported_policy_type;
