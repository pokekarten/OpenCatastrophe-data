-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- ESA WorldCover 2021 v200: one previously verified Map COG block 185,
-- tile N48E009. Read-only Neon research sample #30 plus header sample #7.
-- No source-network GET, raw pixels, original-file promotion or model admission.
-- Official PUM v2.0: Map is uint8; tiled internally 1024x1024; eleven
-- classes 10,20,30,40,50,60,70,80,90,95,100 (zero permitted as nodata).
-- Source: https://esa-worldcover.org/en/data-access
-- https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/docs/WorldCover_PUM_V2.0.pdf
-- A PASS only establishes stored aggregate/lineage consistency, not truth
-- of the underlying land-cover pixels, exposure, hazard, loss or fitness.
WITH source AS (
  SELECT s.sample_json j, s.provider_response_sha256 original_range_sha,
         h.provider_response_sha256 header_range_sha,
         s.sample_kind, h.sample_kind header_kind
  FROM research.source_sample_v0 s
  JOIN research.source_sample_v0 h
    ON h.sample_id=7 AND h.source_id='esa.worldcover.2021.v200'
  WHERE s.sample_id=30 AND s.source_id='esa.worldcover.2021.v200'
),
cases AS (
  SELECT 'stored_original_block185' case_id, true expected_valid, j FROM source
  UNION ALL SELECT 'negative_invalid_class_110',false,
   jsonb_set(jsonb_set(j,'{observed_class_counts,10}','433360'::jsonb),'{observed_class_counts,110}','1'::jsonb) FROM source
  UNION ALL SELECT 'negative_count_negative',false,jsonb_set(j,'{observed_class_counts,50}','-1'::jsonb) FROM source
  UNION ALL SELECT 'negative_fractional_count',false,jsonb_set(j,'{observed_class_counts,50}','29214.5'::jsonb) FROM source
  UNION ALL SELECT 'negative_string_count',false,jsonb_set(j,'{observed_class_counts,50}','"29214"'::jsonb) FROM source
  UNION ALL SELECT 'negative_count_total_off_by_one',false,jsonb_set(j,'{observed_class_counts,50}','29215'::jsonb) FROM source
  UNION ALL SELECT 'negative_missing_histogram',false,jsonb_set(j,'{observed_class_counts}','null'::jsonb) FROM source
  UNION ALL SELECT 'negative_block_index_changed',false,jsonb_set(j,'{block_index}','186'::jsonb) FROM source
  UNION ALL SELECT 'negative_tile_changed',false,jsonb_set(j,'{tile_id}','"N00E000"'::jsonb) FROM source
  UNION ALL SELECT 'negative_wrong_header_hash',false,jsonb_set(j,'{original_tiff_header_sha256}',to_jsonb(repeat('0',64))) FROM source
  UNION ALL SELECT 'negative_wrong_table_hash',false,jsonb_set(j,'{original_tiff_tables_sha256}',to_jsonb(repeat('0',64))) FROM source
  UNION ALL SELECT 'negative_wrong_original_block_hash',false,jsonb_set(j,'{compressed_original_sha256}',to_jsonb(repeat('0',64))) FROM source
  UNION ALL SELECT 'negative_wrong_original_range',false,jsonb_set(j,'{compressed_original_range}','[43278196,43334636]'::jsonb) FROM source
  UNION ALL SELECT 'negative_wrong_original_bytes',false,jsonb_set(j,'{compressed_original_bytes}','56441'::jsonb) FROM source
  UNION ALL SELECT 'negative_wrong_decoded_pixel_count',false,jsonb_set(j,'{decoded_original_pixel_count}','1048575'::jsonb) FROM source
  UNION ALL SELECT 'negative_bad_decoded_pixel_sha',false,jsonb_set(j,'{decoded_original_pixels_sha256}','"not-a-sha256"'::jsonb) FROM source
  UNION ALL SELECT 'negative_publication_flag',false,jsonb_set(j,'{raw_raster_pixels_persisted}','true'::jsonb) FROM source
  UNION ALL SELECT 'negative_model_admission_flag',false,jsonb_set(j,'{model_input_approved}','true'::jsonb) FROM source
  UNION ALL SELECT 'negative_full_tiff_claim',false,jsonb_set(j,'{full_original_tiff_verified}','true'::jsonb) FROM source
  UNION ALL SELECT 'negative_version_changed',false,jsonb_set(j,'{product_version}','"2020 v100"'::jsonb) FROM source
),
hist AS (
  SELECT c.case_id,
         count(k.key) class_keys,
         coalesce(bool_and(
           k.key=ANY(ARRAY['0','10','20','30','40','50','60','70','80','90','95','100'])
           AND jsonb_typeof(k.value)='number'
           AND k.value::text ~ '^[0-9]{1,7}$'
         ),false) valid_entries,
         sum(CASE WHEN jsonb_typeof(k.value)='number'
                   AND k.value::text ~ '^[0-9]{1,7}$'
                  THEN (k.value::text)::bigint ELSE 0 END) AS total_counts
  FROM cases c
  LEFT JOIN LATERAL jsonb_each(
     CASE WHEN jsonb_typeof(c.j->'observed_class_counts')='object'
          THEN c.j->'observed_class_counts' ELSE '{}'::jsonb END
  ) k ON true
  GROUP BY c.case_id
),
checked AS (
 SELECT c.case_id,c.expected_valid,
 coalesce(
   hist.class_keys BETWEEN 1 AND 12
   AND hist.valid_entries
   AND hist.total_counts=1048576
   AND (c.j->>'source_id')='esa.worldcover.2021.v200'
   AND (c.j->>'product_version')='2021 v200'
   AND (c.j->>'tile_id')='N48E009'
   AND (c.j->'block_index')='185'::jsonb
   AND (c.j->'compressed_original_bytes')='56442'::jsonb
   AND (c.j->'compressed_original_range')='[43278196,43334637]'::jsonb
   AND (c.j->>'compressed_original_sha256')=s.original_range_sha
   AND (c.j->>'original_tiff_header_sha256')=s.header_range_sha
   AND (c.j->>'original_tiff_tables_sha256')='7de08710b64cad350b81da83a81fcfc0c74f5285e20e28b0a3e42d19151885ba'
   AND (c.j->'decoded_original_pixel_count')='1048576'::jsonb
   AND (c.j->>'decoded_original_pixels_sha256') ~ '^[a-f0-9]{64}$'
   AND (c.j->'model_input_approved')='false'::jsonb
   AND (c.j->'full_original_tiff_verified')='false'::jsonb
   AND (c.j->'raw_raster_pixels_persisted')='false'::jsonb
   AND (c.j->'building_exposure_or_insured_tiv_validated')='false'::jsonb
   AND s.sample_kind='observed_values' AND s.header_kind='public_metadata'
 ,false) actual_valid
 FROM cases c JOIN hist USING(case_id) CROSS JOIN source s
)
SELECT case_id, expected_valid, actual_valid, expected_valid=actual_valid AS pass
FROM checked
UNION ALL
SELECT 'missing_required_source_samples',true,false,false WHERE NOT EXISTS(SELECT 1 FROM source)
ORDER BY case_id;
