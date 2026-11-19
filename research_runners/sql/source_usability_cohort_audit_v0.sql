-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Research-only, SELECT-only, aggregate-only current-state audit.
-- Run against Neon insurance-risk-core, database insurance, main branch.
-- This verifies stored structural invariants, NOT original-provider truth,
-- dataset rights, scientific validity, or model admission.
WITH research_checks AS (
 SELECT 'USGS ComCat origins'::text AS source_family,
 count(*)::bigint AS records,
 count(DISTINCT usgs_event_id)::bigint AS distinct_analytical_keys,
 count(*) FILTER (WHERE usgs_event_id IS NULL OR origin_time_utc IS NULL OR magnitude IS NULL OR latitude NOT BETWEEN -90 AND 90 OR longitude NOT BETWEEN -180 AND 180)::bigint AS malformed_records,
 count(*) FILTER (WHERE COALESCE(raw_response_sha256,'') !~ '^[0-9a-f]{64}$')::bigint AS original_sha256_missing,
 count(*) FILTER (WHERE model_admitted IS TRUE)::bigint AS approved_model_rows
 FROM research.usgs_comcat_origin_observation_v0
 UNION ALL
 SELECT 'Hubeau Seine 2016 daily Q',
 count(*), count(DISTINCT (code_station,observed_date)),
 count(*) FILTER (WHERE code_station IS NULL OR observed_date IS NULL OR original_daily_flow_lps IS NULL OR normalized_daily_flow_m3s IS NULL OR normalized_daily_flow_m3s < 0 OR ABS(original_daily_flow_lps / 1000 - normalized_daily_flow_m3s) > 0.00001),
 count(*) FILTER (WHERE COALESCE(original_response_sha256,'') !~ '^[0-9a-f]{64}$'),
 count(*) FILTER (WHERE model_input_admitted IS TRUE)
 FROM research.hubeau_seine_47day_daily_q_research_v0
 UNION ALL
 SELECT 'Worldwide insurer directory',
 count(*), count(DISTINCT (country_slug,lower(btrim(display_name)))),
 count(*) FILTER (WHERE country_slug IS NULL OR btrim(country_slug)='' OR display_name IS NULL OR btrim(display_name)=''),
 count(*) FILTER (WHERE COALESCE(raw_provider_sha256,'') !~ '^[0-9a-f]{64}$'),
 count(*) FILTER (WHERE model_input_approved IS TRUE)
 FROM research.insurer_directory_candidate_v0
 UNION ALL
 SELECT 'Ponthierry research buildings',
 count(*), count(DISTINCT rnb_id),
 count(*) FILTER (WHERE rnb_id IS NULL OR rnb_geom IS NULL OR ign_geom_3d IS NULL),
 count(*) FILTER (WHERE COALESCE(rnb_response_sha256,'') !~ '^[0-9a-f]{64}$' OR COALESCE(ign_response_sha256,'') !~ '^[0-9a-f]{64}$'),
 count(*) FILTER (WHERE cat_model_admitted IS TRUE)
 FROM research.fr_ponthierry_rnb_ign_building_v0
 UNION ALL
 SELECT 'Hydrometric observations',
 count(*), count(DISTINCT (station_uuid,observed_at,parameter)),
 count(*) FILTER (WHERE station_uuid IS NULL OR observed_at IS NULL OR measured_value IS NULL OR parameter IS NULL OR unit IS NULL),
 count(*) FILTER (WHERE COALESCE(response_sha256,'') !~ '^[0-9a-f]{64}$'),
 count(*) FILTER (WHERE hazard_input_admitted IS TRUE)
 FROM research.hydrometric_observation_v0
)
SELECT source_family, records, distinct_analytical_keys, malformed_records,
       (records-distinct_analytical_keys)::bigint AS repeated_analytical_keys,
       original_sha256_missing, approved_model_rows,
       CASE WHEN records=0 THEN 'NO_RESEARCH_ROWS'
            WHEN malformed_records>0 THEN 'STRUCTURAL_QA_NEEDED'
            WHEN records<>distinct_analytical_keys THEN 'IDENTITY_RESOLUTION_NEEDED'
            WHEN original_sha256_missing>0 THEN 'ORIGINAL_PROVENANCE_NOT_PINNED'
            WHEN approved_model_rows<records THEN 'MODEL_ADMISSION_NOT_ESTABLISHED'
            ELSE 'REVIEW_RIGHTS_AND_SCIENTIFIC_FITNESS'
       END AS diagnostic
FROM research_checks
ORDER BY source_family;
