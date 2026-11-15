-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Exact scoped offline/read-only science check for previously staged OpenFEMA
-- NFIP Residential Penetration Rates v1, Neon source_sample_v0 #41, 2026-11-12.
-- NOT a provider API probe, original response re-download, independent NSI
-- denominator validation, house-level policy, flood risk probability or CAT
-- model admission. Requires Neon PostgreSQL 17 pg_input_is_valid.
-- Only pass/fail case IDs are returned. No raw provider bytes or private data.
WITH source AS (
 SELECT sample_json AS j FROM research.source_sample_v0
 WHERE sample_id = 41
   AND source_id = 'fema.openfema.nfip-residential-penetration-rates.v1'
   AND source_url = 'https://www.fema.gov/api/open/v1/NfipResidentialPenetrationRates?$top=2'
   AND provider_response_sha256 = '90b88c623e37a41f49d218b037fb32bbc9e258fa07d7eb53132be7da290a1a6e'
   AND sample_sha256 = encode(sha256(convert_to(sample_json::text,'UTF8')),'hex')
   AND research_only AND NOT model_input_approved
),
observed AS (
 SELECT 'observed_row_' || ord::text AS case_id, true AS expected_valid, item AS j
 FROM source CROSS JOIN LATERAL jsonb_array_elements(
   CASE WHEN jsonb_typeof(j->'provider_rows')='array' THEN j->'provider_rows'
        ELSE '[]'::jsonb END
 ) WITH ORDINALITY AS e(item,ord)
),
first_row AS (SELECT j FROM observed WHERE case_id='observed_row_1'),
cases AS (
 SELECT case_id,expected_valid,j FROM observed
 UNION ALL SELECT 'negative_bad_fips',false,jsonb_set(j,'{fipsCode}','"999"'::jsonb) FROM first_row
 UNION ALL SELECT 'negative_zero_denominator',false,jsonb_set(j,'{totalResStructures}','0'::jsonb) FROM first_row
 UNION ALL SELECT 'negative_wrong_rate',false,jsonb_set(j,'{resPenetrationRate}','0.8'::jsonb) FROM first_row
 UNION ALL SELECT 'negative_negative_contracts',false,jsonb_set(j,'{resContractsInForce}','-1'::jsonb) FROM first_row
 UNION ALL SELECT 'negative_malformed_count',false,jsonb_set(j,'{resContractsInForce}','"bad"'::jsonb) FROM first_row
 UNION ALL SELECT 'negative_invalid_asof_utc',false,jsonb_set(j,'{asOfDate}','"2026-02-31T00:00:00Z"'::jsonb) FROM first_row
 UNION ALL SELECT 'negative_changed_date',false,jsonb_set(j,'{asOfDate}','"2026-08-04T00:00:00.000Z"'::jsonb) FROM first_row
 UNION ALL SELECT 'negative_missing_sfha',false,jsonb_set(j,'{totalResStructuresSfha}','null'::jsonb) FROM first_row
 UNION ALL SELECT 'synthetic_above_100_percent_ratio_not_clipped',true,
   jsonb_set(jsonb_set(jsonb_set(j,'{totalResStructures}','100'::jsonb),
              '{resContractsInForce}','115'::jsonb),
              '{resPenetrationRate}','1.15'::jsonb) FROM first_row
),
typed AS (
 SELECT case_id,expected_valid,j,
   CASE WHEN jsonb_typeof(j->'resContractsInForce')='number' THEN (j->>'resContractsInForce')::numeric END AS n,
   CASE WHEN jsonb_typeof(j->'totalResStructures')='number' THEN (j->>'totalResStructures')::numeric END AS d,
   CASE WHEN jsonb_typeof(j->'resPenetrationRate')='number' THEN (j->>'resPenetrationRate')::numeric END AS rate,
   CASE WHEN jsonb_typeof(j->'resContractsInForceSfha')='number' THEN (j->>'resContractsInForceSfha')::numeric END AS sn,
   CASE WHEN jsonb_typeof(j->'totalResStructuresSfha')='number' THEN (j->>'totalResStructuresSfha')::numeric END AS sd,
   CASE WHEN jsonb_typeof(j->'resPenetrationRateSfha')='number' THEN (j->>'resPenetrationRateSfha')::numeric END AS srate
 FROM cases
),
evaluated AS (
 SELECT case_id,expected_valid,
   COALESCE(
      (j->>'state')='Alabama' AND (j->>'county') IN ('Autauga','Baldwin')
      AND (j->>'fipsCode') ~ '^[0-9]{5}$'
      AND (j->>'asOfDate')='2026-08-03T00:00:00.000Z'
      AND pg_input_is_valid(coalesce(j->>'asOfDate',''), 'timestamptz')
      AND n>=0 AND n=trunc(n) AND d>0 AND d=trunc(d)
      AND sn>=0 AND sn=trunc(sn) AND sd>0 AND sd=trunc(sd)
      AND rate>=0 AND srate>=0
      AND abs(rate - n/d) <= 0.00005
      AND abs(srate - sn/sd) <= 0.00005
   ,false) AS actual_valid
 FROM typed
)
SELECT case_id,expected_valid,actual_valid,
       expected_valid=actual_valid AS pass
FROM evaluated
UNION ALL
SELECT 'missing_or_mutated_source_receipt',true,false,false
WHERE NOT EXISTS (SELECT 1 FROM source)
UNION ALL
SELECT 'unexpected_original_row_count',true,false,false
WHERE (SELECT count(*) FROM observed) <> 2
ORDER BY case_id;
