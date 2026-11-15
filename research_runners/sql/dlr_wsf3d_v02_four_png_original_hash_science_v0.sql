-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- DLR WSF3D v02. Four fixed 32x32 original WMS GetMap PNG previews,
-- stored in the authorised insurance research Neon database, sample #22-25.
-- Original PNG bytes are SHA256-rechecked FROM recorded base64 in Neon.
-- No new GET, provider download, raw data in Git, model or TIV admission.
-- Source: https://web.geoservice.dlr.de/web/datasets/wsf_3d (CC BY 4.0).
-- Four native 90-m layers exist as TIFF: PNG GetMap is visualisation only.
WITH expected(sample_id,layer,parameter,unit) AS (
 VALUES
 (22::bigint,'WSF3D_V02_BUILDINGAREA','building_area','m²/cell'),
 (23::bigint,'WSF3D_V02_BUILDINGVOLUME','building_volume','m³/cell'),
 (24::bigint,'WSF3D_V02_BUILDINGFRACTION','building_fraction','%'),
 (25::bigint,'WSF3D_V02_BUILDINGHEIGHT','building_height','m')
), original AS (
 SELECT e.sample_id,e.layer,e.parameter,e.unit,
        s.sample_json j,s.source_url,s.request_identity,
        s.provider_response_sha256 provider_sha,
        s.sample_kind,s.product_version
 FROM expected e JOIN research.source_sample_v0 s
 ON s.sample_id=e.sample_id AND s.source_id='dlr.wsf.3d.v02'
), cases AS (
 SELECT sample_id,'original_png' case_id,true should_validate,j,source_url,provider_sha FROM original
 UNION ALL SELECT sample_id,'bad_layer',false,jsonb_set(j,'{layer}','"WRONG_LAYER"'),source_url,provider_sha FROM original
 UNION ALL SELECT sample_id,'bad_unit',false,jsonb_set(j,'{native_unit}','"kg"'),source_url,provider_sha FROM original
 UNION ALL SELECT sample_id,'bad_bbox',false,jsonb_set(j,'{original_bbox_lonlat}','[11.52,48.1,11.6,48.19]'),source_url,provider_sha FROM original
 UNION ALL SELECT sample_id,'bad_srs',false,jsonb_set(j,'{srs}','"EPSG:3857"'),source_url,provider_sha FROM original
 UNION ALL SELECT sample_id,'bad_image_size',false,jsonb_set(j,'{image_pixel_size}','[33,32]'),source_url,provider_sha FROM original
 UNION ALL SELECT sample_id,'not_visualization_only',false,jsonb_set(j,'{visualization_only}','false'),source_url,provider_sha FROM original
 UNION ALL SELECT sample_id,'false_numeric_source_claim',false,jsonb_set(j,'{raw_numeric_raster_values}','true'),source_url,provider_sha FROM original
 UNION ALL SELECT sample_id,'false_insurance_tiv_claim',false,jsonb_set(j,'{insurance_tiv_verified}','true'),source_url,provider_sha FROM original
 UNION ALL SELECT sample_id,'false_height_claim',false,jsonb_set(j,'{building_level_height_verified}','true'),source_url,provider_sha FROM original
 UNION ALL SELECT sample_id,'bad_product',false,jsonb_set(j,'{source_product}','"different dataset"'),source_url,provider_sha FROM original
 UNION ALL SELECT sample_id,'bad_base64',false,jsonb_set(j,'{rendered_png_base64}','"not valid !!!!"'),source_url,provider_sha FROM original
 UNION ALL SELECT sample_id,'bad_png_signature',false,jsonb_set(j,'{rendered_png_base64}',to_jsonb('aV'||substring(j->>'rendered_png_base64' from 3))),source_url,provider_sha FROM original
 UNION ALL SELECT sample_id,'wrong_original_hash',false,j,source_url,repeat('0',64) FROM original
 UNION ALL SELECT sample_id,'wrong_wms_path',false,j,'https://example.org/not-dlr',provider_sha FROM original
 UNION ALL SELECT sample_id,'wrong_parameter',false,jsonb_set(j,'{parameter}','"not_native_parameter"'),source_url,provider_sha FROM original
), parsed AS (
 SELECT c.*,
 CASE WHEN length(c.j->>'rendered_png_base64') BETWEEN 100 AND 16384
        AND length(c.j->>'rendered_png_base64')%4=0
        AND (c.j->>'rendered_png_base64') ~ '^[A-Za-z0-9+/]+={0,2}$'
      THEN decode(c.j->>'rendered_png_base64','base64')
 END png
 FROM cases c
), checked AS (
 SELECT p.sample_id,p.case_id,p.should_validate,coalesce(
   (p.j->>'layer')=o.layer
   AND (p.j->>'parameter')=o.parameter
   AND (p.j->>'native_unit')=o.unit
   AND (p.j->>'source_product')='DLR WSF 3D v02'
   AND (p.j->>'srs')='EPSG:4326'
   AND (p.j->'original_bbox_lonlat')='[11.52,48.1,11.6,48.18]'::jsonb
   AND (p.j->'image_pixel_size')='[32,32]'::jsonb
   AND (p.j->'visualization_only')='true'::jsonb
   AND (p.j->'raw_numeric_raster_values')='false'::jsonb
   AND (p.j->'insurance_tiv_verified')='false'::jsonb
   AND (p.j->'building_level_height_verified')='false'::jsonb
   AND o.sample_kind='geospatial_preview'
   AND o.product_version='WSF 3D v02'
   AND p.source_url=o.request_identity
   AND p.source_url=
    'https://geoservice.dlr.de/eoc/land/wms?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS='
    ||o.layer||
    '&STYLES=&SRS=EPSG%3A4326&BBOX=11.52%2C48.10%2C11.60%2C48.18&WIDTH=32&HEIGHT=32&FORMAT=image%2Fpng&TRANSPARENT=TRUE'
   AND p.png IS NOT NULL
   AND octet_length(p.png) BETWEEN 100 AND 65536
   AND left(encode(p.png,'hex'),16)='89504e470d0a1a0a'
   AND substring(encode(p.png,'hex') from 17 for 16)='0000000d49484452'
   AND right(encode(p.png,'hex'),24)='0000000049454e44ae426082'
   AND (get_byte(p.png,16)*16777216+get_byte(p.png,17)*65536+
        get_byte(p.png,18)*256+get_byte(p.png,19))=32
   AND (get_byte(p.png,20)*16777216+get_byte(p.png,21)*65536+
        get_byte(p.png,22)*256+get_byte(p.png,23))=32
   AND encode(sha256(p.png),'hex')=p.provider_sha
   AND p.provider_sha=o.provider_sha
 ,false) actual_valid
 FROM parsed p JOIN original o ON o.sample_id=p.sample_id
)
SELECT sample_id,case_id,should_validate,actual_valid,
 should_validate=actual_valid AS pass FROM checked
UNION ALL
SELECT NULL::bigint,'exactly_four_unique_layer_samples',true,
 (SELECT count(*)=4 AND count(DISTINCT layer)=4 FROM original),
 (SELECT count(*)=4 AND count(DISTINCT layer)=4 FROM original)
ORDER BY sample_id NULLS FIRST,case_id;
