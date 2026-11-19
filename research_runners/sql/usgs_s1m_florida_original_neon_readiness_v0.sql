-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- USGS S1M fixed Florida original-file science gate in authorised insurance Neon.
-- Read-only research evidence. No source bytes, insurer data or model admission.
-- Absence from THIS register is not proof that no trusted original exists elsewhere.
WITH sample AS (
    SELECT
        COUNT(*)::integer AS catalogue_samples,
        COUNT(*) FILTER (
            WHERE sample_kind = 'public_metadata'
        )::integer AS metadata_samples,
        COUNT(*) FILTER (
            WHERE model_input_approved IS TRUE
        )::integer AS sample_model_admissions,
        MAX(retrieved_at) AS latest_sample_utc
    FROM research.source_sample_v0
    WHERE source_id = 'usgs.3dep.seamless-1m.s1m'
),
receipt AS (
    SELECT
        COUNT(*)::integer AS original_receipt_rows,
        COUNT(*) FILTER (
            WHERE full_source_sha256_verified IS TRUE
        )::integer AS full_file_sha_verified_rows,
        COUNT(*) FILTER (
            WHERE insurer_model_input_approved IS TRUE
        )::integer AS model_approved_receipts
    FROM research.source_strict_original_probe_receipt_v1
    WHERE source_id = 'usgs.3dep.seamless-1m.s1m'
)
SELECT
    'usgs.3dep.seamless-1m.s1m' AS source_id,
    sample.*,
    receipt.*,
    CASE
        WHEN receipt.full_file_sha_verified_rows = 0
        THEN 'BLOCKED: no independently verified complete original in checked Neon receipt register'
        ELSE 'REVIEW_REQUIRED: receipt is not GeoPackage lineage, vertical datum or CAT admission'
    END AS next_gate,
    FALSE AS model_input_admitted_by_this_query
FROM sample CROSS JOIN receipt;
