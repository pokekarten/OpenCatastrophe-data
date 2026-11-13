-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Research-only CBS 83673NED: compare definitive 2025VJ06 with
-- provisional 2026VJ06 *permit project averages*, not individual
-- property inflation, an insurance replacement-cost index or CAT model.
-- One read-only SQL SELECT; all original source replies are bounded
-- intermediary-retrieved public JSON bodies with separate SHA256 proofs.
WITH expected(period, tenure, url, digest, byte_count) AS (
  VALUES
    ('2025VJ06','rental','https://opendata.cbs.nl/ODataApi/OData/83673NED/TypedDataSet?$filter=Perioden%20eq%20%272025VJ06%27%20and%20Eigendom%20eq%20%27A028867%27&$top=5','70731cf7be6e73813059c250db9f1f21ad4024f0fb7cba5075ad8af666d90a5e',1457),
    ('2025VJ06','owner','https://opendata.cbs.nl/ODataApi/OData/83673NED/TypedDataSet?$filter=Perioden%20eq%20%272025VJ06%27%20and%20Eigendom%20eq%20%27A028868%27&$top=5','7c9b9e307fd7fbf4ef8d5e9e26eaf3d9b9a991dd54a6b95c01409d22663c5908',1459),
    ('2026VJ06','rental','https://opendata.cbs.nl/ODataApi/OData/83673NED/TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028867%27&$top=5','2b224f3f6546f7c5f5905a6b226a3471c986eaf2d7cd16b7001f720ff26e9fe0',1457),
    ('2026VJ06','owner','https://opendata.cbs.nl/ODataApi/OData/83673NED/TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028868%27&$top=5','67a2647fc84a812569caf0d128d1b7f7cd8a3d8e2f427fc2ebe28ab68ed39ed3',1459)
),
expected_status(period, url, digest, byte_count, official_status) AS (
  VALUES
    ('2025VJ06','https://opendata.cbs.nl/ODataApi/OData/83673NED/Perioden?$filter=Key%20eq%20%272025VJ06%27&$top=1','626dac3ab357839e615bcf0260237651d4a3983a88a0f18f6c8e3bfc24272c4d',234,'Definitief'),
    ('2026VJ06','https://opendata.cbs.nl/ODataApi/OData/83673NED/Perioden?$filter=Key%20eq%20%272026VJ06%27&$top=1','ebe2b837bc17b3b48b14df38c2abc078ea2da4056ff37f32b77653c3a85e6fe0',251,'Voorlopig')
),
source_data AS (
  SELECT e.period,e.tenure,e.digest,s.sample_id,s.sample_json
  FROM expected e
  JOIN research.source_sample_v0 s
    ON s.source_id='nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned'
   AND s.source_url=e.url
   AND s.provider_response_sha256=e.digest
   AND s.sample_kind='observed_values'
   AND s.sample_sha256=encode(sha256(convert_to(s.sample_json::text,'UTF8')),'hex')
   AND s.research_only IS TRUE
   AND s.model_input_approved IS FALSE
   AND s.source_byte_persistence_authorized IS FALSE
   AND s.sample_json->>'original_response_sha256'=e.digest
   AND (s.sample_json->>'original_response_bytes')::int=e.byte_count
   AND COALESCE(s.sample_json->>'publisher_revision',
                s.sample_json->>'official_publisher_revision')='2026-08-20T02:00:00'
   AND COALESCE(s.sample_json->>'strict_repository_runner_executed',
                s.sample_json->>'direct_trusted_repository_runner_executed')='false'
   AND COALESCE(s.sample_json->>'period',
                s.sample_json->>'rolling_12_month_period')=e.period
   AND s.sample_json->>'publication_status'=
       CASE e.period WHEN '2025VJ06' THEN 'Definitief'
                     ELSE 'Voorlopig' END
   AND (
      (e.period='2025VJ06'
       AND s.sample_json->'crosswalk'->>'GemiddeldeBouwkostenPerM_2'='EUR per m³'
       AND s.sample_json->'crosswalk'->>'GemiddeldeBouwkostenPerM_3'='EUR per m²')
      OR
      (e.period='2026VJ06'
       AND s.sample_json->'source_native_field_crosswalk'->>'GemiddeldeBouwkostenPerM_2'='EUR per m³ (cubic metre), NOT per square metre'
       AND s.sample_json->'source_native_field_crosswalk'->>'GemiddeldeBouwkostenPerM_3'='EUR per m² (square metre), NOT per cubic metre')
   )
   AND EXISTS (
     SELECT 1 FROM research.source_api_smoke_receipt_v0 api
     WHERE api.source_id='nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned'
       AND api.endpoint_url=e.url AND api.response_bytes=e.byte_count
       AND api.strict_repository_runner_executed IS FALSE
       AND api.provider_bytes_persisted IS FALSE
       AND api.model_input_approved IS FALSE
       AND api.note LIKE '%'||e.digest||'%'
   )
),
source_status AS (
  SELECT e.period, e.official_status, s.sample_id
  FROM expected_status e
  JOIN research.source_sample_v0 s
    ON s.source_id='nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned'
   AND s.source_url=e.url AND s.provider_response_sha256=e.digest
   AND s.sample_kind='public_metadata'
   AND s.sample_sha256=encode(sha256(convert_to(s.sample_json::text,'UTF8')),'hex')
   AND s.research_only IS TRUE AND s.model_input_approved IS FALSE
   AND s.source_byte_persistence_authorized IS FALSE
   AND s.sample_json->>'original_response_sha256'=e.digest
   AND (s.sample_json->>'original_response_bytes')::int=e.byte_count
   AND COALESCE(s.sample_json->>'publisher_revision',
                s.sample_json->>'official_publication_modified')='2026-08-20T02:00:00'
   AND COALESCE(s.sample_json->>'strict_repository_runner_executed',
                s.sample_json->>'direct_trusted_repository_runner_executed')='false'
   AND CASE WHEN e.period='2025VJ06' THEN
       s.sample_json->'provider_status'->>'Status'='Definitief'
     ELSE s.sample_json->>'status'='Voorlopig' END
   AND EXISTS (
     SELECT 1 FROM research.source_api_smoke_receipt_v0 api
     WHERE api.source_id='nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned'
       AND api.endpoint_url=e.url AND api.response_bytes=e.byte_count
       AND api.strict_repository_runner_executed IS FALSE
       AND api.provider_bytes_persisted IS FALSE
       AND api.model_input_approved IS FALSE
       AND api.note LIKE '%'||e.digest||'%'
   )
),
native AS (
  SELECT
    d.period,d.tenure,d.sample_id,
    COALESCE(v.j->>'native_region_code_exact',v.j->>'native_RegionS_code') AS region_code,
    v.j->>'region_name' AS region_name,
    COALESCE(v.j->>'native_tenure_code',v.j->>'native_Eigendom_code') AS native_tenure,
    v.j->>'native_period' AS native_period,
    (COALESCE(v.j->>'average_eur_per_m2',v.j->>'average_permitted_eur_per_m2'))::numeric AS eur_m2,
    (COALESCE(v.j->>'average_eur_per_m3',v.j->>'average_permitted_eur_per_m3'))::numeric AS eur_m3,
    (COALESCE(v.j->>'avg_permitted_dwelling_thousand_eur',v.j->>'average_permitted_eur_per_dwelling_thousands'))::numeric AS cost_thousand,
    (COALESCE(v.j->>'average_volume_m3',v.j->>'mean_permitted_dwelling_volume_m3'))::numeric AS volume_m3,
    (COALESCE(v.j->>'average_floor_area_m2',v.j->>'mean_permitted_dwelling_floor_area_m2'))::numeric AS area_m2
  FROM source_data d
  CROSS JOIN LATERAL jsonb_array_elements(
     CASE WHEN d.period='2025VJ06' THEN d.sample_json->'rows'
          ELSE d.sample_json->'actual_public_aggregate_rows' END
  ) AS v(j)
),
paired AS (
  SELECT
    prev.tenure,prev.region_code,prev.region_name,
    prev.sample_id AS definitive_2025_sample,
    curr.sample_id AS provisional_2026_sample,
    prev.eur_m2 AS definitive_2025_eur_per_m2,
    curr.eur_m2 AS preliminary_2026_eur_per_m2,
    prev.eur_m3 AS definitive_2025_eur_per_m3,
    curr.eur_m3 AS preliminary_2026_eur_per_m3,
    ROUND((curr.eur_m2/NULLIF(prev.eur_m2,0)-1)*100,2) AS change_in_permitted_eur_m2_pct,
    ROUND((curr.eur_m3/NULLIF(prev.eur_m3,0)-1)*100,2) AS change_in_permitted_eur_m3_pct,
    ROUND((curr.cost_thousand/NULLIF(prev.cost_thousand,0)-1)*100,2) AS change_in_permitted_eur_per_dwelling_pct
  FROM native prev JOIN native curr
   ON prev.period='2025VJ06' AND curr.period='2026VJ06'
  AND prev.tenure=curr.tenure AND prev.region_code=curr.region_code
),
quality AS (
  SELECT
    ((SELECT COUNT(*) FROM source_data)=4)
    AND ((SELECT COUNT(*) FROM source_status)=2)
    AND
    (SELECT COUNT(*)=20 AND COUNT(DISTINCT (period,tenure,region_code))=20
       AND COUNT(*) FILTER (WHERE period='2025VJ06')=10
       AND COUNT(*) FILTER (WHERE period='2026VJ06')=10
       AND COALESCE(BOOL_AND(
          region_code ~ '^(NL01|LD0[1-4])  $'
          AND native_tenure=CASE tenure WHEN 'rental' THEN 'A028867' ELSE 'A028868' END
          AND native_period=period
          AND eur_m2>0 AND eur_m3>0 AND cost_thousand>0
          AND area_m2>0 AND volume_m3>0
          AND ABS(eur_m2*area_m2-cost_thousand*1000)<=3000
          AND ABS(eur_m3*volume_m3-cost_thousand*1000)<=3000
       ),false)
     FROM native)
    AND ((SELECT COUNT(*) FROM paired)=10)
    AS is_complete
)
SELECT
 p.tenure,p.region_code,p.region_name,p.definitive_2025_sample,
 p.provisional_2026_sample,p.definitive_2025_eur_per_m2,
 p.preliminary_2026_eur_per_m2,
 p.definitive_2025_eur_per_m3,p.preliminary_2026_eur_per_m3,
 p.change_in_permitted_eur_m2_pct,p.change_in_permitted_eur_m3_pct,
 p.change_in_permitted_eur_per_dwelling_pct,
 '2025VJ06 definitive versus 2026VJ06 provisional; pure newly permitted housing, rolling 12-month averages; not building inflation or insured TIV'::text AS interpretation,
 'RESEARCH_ONLY_VALIDATED_ORIGINAL_RECEIPTS; MODEL_NOT_ADMITTED'::text AS research_gate
FROM paired p CROSS JOIN quality q WHERE q.is_complete IS TRUE
UNION ALL
SELECT NULL::text,NULL::text,NULL::text,NULL::bigint,NULL::bigint,
       NULL::numeric,NULL::numeric,NULL::numeric,NULL::numeric,
       NULL::numeric,NULL::numeric,NULL::numeric,
       'One or more original source samples, source IDs, period statuses or hashes are missing'::text,
       'BLOCKED_INCOMPLETE_OR_UNVERIFIED_SOURCE_EVIDENCE'::text
FROM quality q WHERE q.is_complete IS NOT TRUE
ORDER BY tenure NULLS LAST,region_code NULLS LAST;
