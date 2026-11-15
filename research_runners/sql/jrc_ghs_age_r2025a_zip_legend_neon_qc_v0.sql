-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
-- GHS-AGE R2025A / V1-0, 1km 10-year classes: read-only original-range
-- cross-receipt science preflight. Uses prior Neon research receipts #38,
-- #51 and #59. These are partial ZIP-byte observations, not full ZIP SHA or
-- raster pixels. No external request, raw upload, table mutation or admission.
-- Run once on the authorized insurance-risk-core research database.
-- Expected: "observed_original_metadata" and all synthetic controls have
-- control_pass=true. Only observed_original_metadata may have gate_pass=true.
WITH receipts AS (
  SELECT
    (SELECT sample_json FROM research.source_sample_v0 WHERE sample_id=51
      AND source_id='ec-jrc.ghsl.ghs-age.r2025a') AS legend,
    (SELECT sample_json FROM research.source_sample_v0 WHERE sample_id=59
      AND source_id='ec-jrc.ghsl.ghs-age.r2025a') AS archive,
    (SELECT count(*)=3 AND coalesce(bool_and(
        source_id='ec-jrc.ghsl.ghs-age.r2025a'
        AND research_only=true
        AND model_input_approved=false
        AND source_byte_persistence_authorized=false
        AND provider_license LIKE 'CC BY 4.0%'
        AND provider_response_sha256 ~ '^[0-9a-f]{64}$'
    ),false) FROM research.source_sample_v0 WHERE sample_id IN (38,51,59))
      AS research_receipts_bounded
),
cases(id, expected_pass) AS (
 VALUES ('observed_original_metadata',true),
        ('synthetic_missing_legend',false),
        ('synthetic_wrong_release',false),
        ('synthetic_wrong_csv_crc',false),
        ('synthetic_missing_age_class',false),
        ('synthetic_wrong_epoch',false),
        ('synthetic_member_overlap',false),
        ('synthetic_bad_eocd',false),
        ('synthetic_false_raster_claim',false),
        ('synthetic_false_admission',false)
),
variants AS (
 SELECT c.id, c.expected_pass, r.research_receipts_bounded,
  CASE c.id
    WHEN 'synthetic_missing_legend' THEN NULL::jsonb
    WHEN 'synthetic_wrong_release' THEN jsonb_set(r.legend,'{ghsl_version}','"R2024A V1-0"')
    WHEN 'synthetic_wrong_csv_crc' THEN jsonb_set(r.legend,'{zip_member_crc32}','"00000000"')
    WHEN 'synthetic_missing_age_class' THEN r.legend #- '{gridcode_legend,5}'
    WHEN 'synthetic_wrong_epoch' THEN jsonb_set(r.legend,'{gridcode_legend,2,epoch_num}','1981')
    WHEN 'synthetic_false_raster_claim' THEN jsonb_set(r.legend,'{no_geo_raster_pixels_downloaded}','false')
    WHEN 'synthetic_false_admission' THEN jsonb_set(r.legend,'{model_input_approved}','true')
    ELSE r.legend END AS legend,
  CASE c.id
    WHEN 'synthetic_member_overlap' THEN jsonb_set(r.archive,'{zip_members,2,local_header_offset}','200')
    WHEN 'synthetic_bad_eocd' THEN jsonb_set(r.archive,'{zip_central_directory_offset}','18662000')
    ELSE r.archive END AS archive
 FROM cases c CROSS JOIN receipts r
),
age_rows AS (
 SELECT v.id, a.ord, a.value AS age FROM variants v
 CROSS JOIN LATERAL jsonb_array_elements(
   CASE WHEN jsonb_typeof(v.legend->'gridcode_legend')='array'
        THEN v.legend->'gridcode_legend' ELSE '[]'::jsonb END
 ) WITH ORDINALITY AS a(value,ord)
),
age_gate AS (
 SELECT id, count(*) AS nclasses,
  coalesce(bool_and(
   jsonb_typeof(age->'gridcode')='number'
   AND jsonb_typeof(age->'epoch_num')='number'
   AND (age->>'gridcode')::int=ord-1
   AND (age->>'epoch_num')::int=(ARRAY[0,1980,1990,2000,2010,2020])[ord]
   AND age->>'epoch_txt'=(ARRAY[
      'not built-up','< 1980','1980 - 1990','1990 - 2000',
      '2000 - 2010','2010 - 2020'
   ])[ord]
   AND jsonb_typeof(age->'display_rgb')='array'
   AND jsonb_array_length(age->'display_rgb')=3
  ),false) AS scientific_legend_ok
 FROM age_rows GROUP BY id
),
zip_rows AS (
 SELECT v.id, v.archive, a.ord, a.value->>'name' AS name,
  (a.value->>'local_header_offset')::bigint AS byte_offset,
  (a.value->>'compressed_size_bytes')::bigint AS compressed_bytes,
  (a.value->>'uncompressed_size_bytes')::bigint AS uncompressed_bytes,
  a.value->>'member_crc32_hex' AS crc32,
  (a.value->>'compression_method')::int AS compression_method,
  lead((a.value->>'local_header_offset')::bigint)
    OVER (PARTITION BY v.id ORDER BY a.ord) AS next_offset
 FROM variants v
 CROSS JOIN LATERAL jsonb_array_elements(
   CASE WHEN jsonb_typeof(v.archive->'zip_members')='array'
      THEN v.archive->'zip_members' ELSE '[]'::jsonb END
 ) WITH ORDINALITY AS a(value,ord)
),
zip_gate AS (
 SELECT id, count(*) AS nmembers,
   count(DISTINCT name) AS distinct_members,
   coalesce(bool_and(
     byte_offset>=0 AND compressed_bytes>0 AND uncompressed_bytes>0
     AND compression_method=8
     AND crc32 ~ '^[0-9a-f]{8}$'
     AND byte_offset+compressed_bytes <
       coalesce(next_offset,(archive->>'zip_central_directory_offset')::bigint)
   ),false) AS safe_member_layout,
   coalesce(bool_or(
     name='GHS_AGE_1980102020_GLOBE_R2025A_54009_1000_V1_0.csv'
     AND byte_offset=139 AND compressed_bytes=145
     AND uncompressed_bytes=209 AND crc32='abea4f34'
   ),false) AS exact_csv_member,
   coalesce(bool_or(
     name='GHS_AGE_1980102020_GLOBE_R2025A_54009_1000_V1_0.tif'
     AND compressed_bytes=11015723 AND uncompressed_bytes=14381462
   ),false) AS declared_raster_member_exists
 FROM zip_rows GROUP BY id
),
gates AS (
 SELECT v.id,v.expected_pass,
  v.research_receipts_bounded
  AND v.legend IS NOT NULL AND v.archive IS NOT NULL
  AND v.legend->>'source_id'='ec-jrc.ghsl.ghs-age.r2025a'
  AND v.archive->>'source_id'='ec-jrc.ghsl.ghs-age.r2025a'
  AND v.legend->>'ghsl_version'='R2025A V1-0'
  AND v.legend->>'original_resolution_m'='1000'
  AND v.legend->>'source_range'='bytes=139-588'
  AND v.legend->>'source_range_sha_scope'='ONLY source ZIP byte range, NOT complete ZIP archive'
  AND v.legend->'member_header'='["gridcode","epoch_num","epoch_txt","R","G","B"]'::jsonb
  AND v.legend->>'zip_member_crc32'='abea4f34'
  AND v.legend->>'zip_member_uncompressed_bytes'='209'
  AND v.legend->>'zip_member_compression_method'='deflate'
  AND v.legend->>'no_geo_raster_pixels_downloaded'='true'
  AND v.legend->>'model_input_approved'='false'
  AND v.archive->>'model_input_approved'='false'
  AND v.archive->>'source_file_contents_persisted'='false'
  AND v.archive->>'no_scientific_raster_or_policy_values_collected'='true'
  AND v.archive->>'zip_member_count'='7'
  AND v.archive->>'zip_central_directory_offset'='18662393'
  AND v.archive->>'zip_central_directory_size_bytes'='905'
  AND v.archive->>'zip_eocd_implied_archive_bytes'='18663320'
  AND v.archive->>'zip_eocd_not_whole_archive_sha'='true'
  AND v.archive->>'source_response_sha_scope'='last 32768 original ZIP bytes only, not full ZIP SHA'
  AND v.legend->>'original_zip_url'=v.archive->>'source_zip_url'
  AND coalesce(a.nclasses=6 AND a.scientific_legend_ok,false)
  AND coalesce(z.nmembers=7 AND z.distinct_members=7
        AND z.safe_member_layout AND z.exact_csv_member
        AND z.declared_raster_member_exists,false)
  AS gate_pass
 FROM variants v
 LEFT JOIN age_gate a USING(id)
 LEFT JOIN zip_gate z USING(id)
)
SELECT id,expected_pass,coalesce(gate_pass,false) AS gate_pass,
       coalesce(gate_pass,false)=expected_pass AS control_pass
FROM gates ORDER BY id;
