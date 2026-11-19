-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- FEMA OpenFEMA DisasterDeclarationsSummaries v2, exact existing private
-- Neon research sample #42 (original provider response SHA below).
-- Two administrative county designation rows for EM-3654-HI are one
-- FEMA DECLARATION, not two independent physical tropical-storm events.
-- Read-only. No new FEMA GET, model admission, insurer underwriting, PII or
-- publication of raw external rows.
-- Official dataset: https://www.fema.gov/openfema-dataset-disaster-declarations-summaries-v2
-- Terms: https://www.fema.gov/about/openfema/terms-conditions
WITH sample AS (
 SELECT sample_json j,provider_response_sha256 original_sha,
        sample_kind,research_only,model_input_approved
 FROM research.source_sample_v0
 WHERE source_id='fema.openfema.disaster-declarations-summaries.v2'
   AND sample_id=42
), rows AS (
 SELECT s.*,rec.elem,rec.ord::int n
 FROM sample s CROSS JOIN LATERAL jsonb_array_elements(
   CASE WHEN jsonb_typeof(s.j->'provider_rows')='array'
     THEN s.j->'provider_rows' ELSE '[]'::jsonb END
 ) WITH ORDINALITY rec(elem,ord)
), cases AS (
 SELECT n,'stored_area_row' test,true expected,j,elem,original_sha,
        sample_kind,research_only,model_input_approved FROM rows
 UNION ALL SELECT n,'wrong_declaration_id',false,j,jsonb_set(elem,'{femaDeclarationString}','"DR-3654-HI"'),original_sha,sample_kind,research_only,model_input_approved FROM rows
 UNION ALL SELECT n,'wrong_state',false,j,jsonb_set(elem,'{state}','"NY"'),original_sha,sample_kind,research_only,model_input_approved FROM rows
 UNION ALL SELECT n,'negative_disaster_no',false,j,jsonb_set(elem,'{disasterNumber}','-1'),original_sha,sample_kind,research_only,model_input_approved FROM rows
 UNION ALL SELECT n,'bad_type',false,j,jsonb_set(elem,'{declarationType}','"XXX"'),original_sha,sample_kind,research_only,model_input_approved FROM rows
 UNION ALL SELECT n,'blank_area',false,j,jsonb_set(elem,'{designatedArea}','""'),original_sha,sample_kind,research_only,model_input_approved FROM rows
 UNION ALL SELECT n,'bad_county_code',false,j,jsonb_set(elem,'{fipsCountyCode}','"1"'),original_sha,sample_kind,research_only,model_input_approved FROM rows
 UNION ALL SELECT n,'bad_fiscal_year',false,j,jsonb_set(elem,'{fyDeclared}','2020'),original_sha,sample_kind,research_only,model_input_approved FROM rows
 UNION ALL SELECT n,'invalid_declaration_date',false,j,jsonb_set(elem,'{declarationDate}','"bad"'),original_sha,sample_kind,research_only,model_input_approved FROM rows
 UNION ALL SELECT n,'refresh_before_declaration',false,j,jsonb_set(elem,'{lastRefresh}','"2026-01-01T00:00:00.000Z"'),original_sha,sample_kind,research_only,model_input_approved FROM rows
 UNION ALL SELECT n,'missing_incident_type',false,j,jsonb_set(elem,'{incidentType}','null'::jsonb),original_sha,sample_kind,research_only,model_input_approved FROM rows
 UNION ALL SELECT n,'false_cat_model_admission',false,jsonb_set(j,'{model_input_approved}','true'),elem,original_sha,sample_kind,research_only,model_input_approved FROM rows
), typed AS (
 SELECT cases.*,
 CASE WHEN jsonb_typeof(elem->'disasterNumber')='number'
  AND elem->>'disasterNumber'~'^[0-9]{1,6}$'
  THEN (elem->>'disasterNumber')::int END disaster_no,
 CASE WHEN jsonb_typeof(elem->'fyDeclared')='number'
  AND elem->>'fyDeclared'~'^[0-9]{4}$'
  THEN (elem->>'fyDeclared')::int END fy,
 CASE WHEN elem->>'declarationDate'~
    '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}([.][0-9]{1,3})?Z$'
  AND pg_input_is_valid(coalesce(elem->>'declarationDate',''),'timestamptz')
  THEN (elem->>'declarationDate')::timestamptz END declared_at,
 CASE WHEN elem->>'lastRefresh'~
    '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}([.][0-9]{1,3})?Z$'
  AND pg_input_is_valid(coalesce(elem->>'lastRefresh',''),'timestamptz')
  THEN (elem->>'lastRefresh')::timestamptz END refreshed_at
 FROM cases
), checks AS (
 SELECT n,test,expected,coalesce(
 sample_kind='observed_values' AND research_only AND NOT model_input_approved
 AND original_sha='ac55a377dd407f46778319b323622ed9f56a0130e8171833adfb333396eefab2'
 AND j->>'source_id'='fema.openfema.disaster-declarations-summaries.v2'
 AND j->>'original_entity'='DisasterDeclarationsSummaries'
 AND j->>'request_query'='$top=2'
 AND j->'original_response_row_count'='2'::jsonb
 AND j->'original_raw_provider_body_saved'='false'::jsonb
 AND j->'model_input_approved'='false'::jsonb
 AND j->>'data_usage_limit' LIKE 'Research or reporting only%'
 AND disaster_no BETWEEN 1 AND 999999 AND fy=2026
 AND elem->>'state'='HI' AND elem->>'declarationType'='EM'
 AND elem->>'femaDeclarationString'=concat(elem->>'declarationType','-',disaster_no,'-',elem->>'state')
 AND length(coalesce(elem->>'designatedArea',''))>0
 AND elem->>'fipsCountyCode'~'^[0-9]{3}$'
 AND elem->>'incidentType'='Tropical Storm'
 AND declared_at IS NOT NULL AND refreshed_at>=declared_at
 AND declared_at>='2026-01-01T00:00:00Z'::timestamptz
 AND declared_at<'2027-01-01T00:00:00Z'::timestamptz,false) valid
 FROM typed
), group_check AS (
 SELECT count(*)=2 AND count(DISTINCT elem->>'fipsCountyCode')=2
 AND count(DISTINCT elem->>'femaDeclarationString')=1
 AND count(DISTINCT elem->>'disasterNumber')=1
 AND count(DISTINCT elem->>'designatedArea')=2 AS one_declaration_two_areas
 FROM rows
)
SELECT n,test,expected,valid,expected=valid AS pass FROM checks
UNION ALL
SELECT NULL::int,'one_declaration_two_areas_not_two_events',
 true,coalesce((SELECT one_declaration_two_areas FROM group_check),false),
 coalesce((SELECT one_declaration_two_areas FROM group_check),false)
ORDER BY n NULLS FIRST,test;
