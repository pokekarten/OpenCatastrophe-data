-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Research-only profile of Texas TDI ZIP x policy-type stock.
-- Apply to insurance-risk-core validation-schema-20261031 only.
-- This source does not identify the legal insurer for each ZIP and
-- cannot establish insured TIV, catastrophe losses or owned portfolios.
CREATE OR REPLACE VIEW research.tx_market_policy_stock_quality_v0 AS
WITH profile AS (
    SELECT
        source_key,
        source_effective_date,
        count(*) AS source_rows,
        count(DISTINCT zip_text) AS zip5_count,
        count(DISTINCT policy_type) AS policy_type_count,
        count(DISTINCT (zip_text, policy_type)) AS distinct_zip_policy_type_pairs,
        count(*) FILTER (
            WHERE quality_status = 'RESEARCH_MARKET_ONLY'
              AND reported_policy_count_signed >= 0
        ) AS nonnegative_research_rows,
        sum(reported_policy_count_signed) FILTER (
            WHERE quality_status = 'RESEARCH_MARKET_ONLY'
              AND reported_policy_count_signed >= 0
        ) AS reported_nonnegative_policy_count_sum,
        count(*) FILTER (WHERE quality_status = 'QUARANTINED_NEGATIVE') AS quarantined_rows,
        sum(reported_policy_count_signed) FILTER (
            WHERE quality_status = 'QUARANTINED_NEGATIVE'
        ) AS quarantined_signed_count_sum,
        count(*) FILTER (
            WHERE zip_text IS NULL OR zip_text !~ '^[0-9]{5}$'
              OR policy_type IS NULL OR policy_type NOT BETWEEN 1 AND 6
              OR reported_policy_count_signed IS NULL
              OR source_row_ordinal IS NULL
              OR source_git_blob_sha IS NULL
        ) AS malformed_rows,
        count(*) FILTER (
            WHERE (reported_policy_count_signed < 0 AND quality_status <> 'QUARANTINED_NEGATIVE')
               OR (reported_policy_count_signed >= 0 AND quality_status = 'QUARANTINED_NEGATIVE')
               OR quality_status NOT IN ('RESEARCH_MARKET_ONLY','QUARANTINED_NEGATIVE')
        ) AS quarantine_status_mismatches,
        count(*) FILTER (WHERE original_http_sha256 IS NOT NULL) AS rows_with_provider_original_hash,
        count(*) FILTER (WHERE legal_insurer_id_observed) AS rows_with_legal_carrier,
        count(*) FILTER (WHERE actual_insured_tiv IS NOT NULL) AS rows_with_actual_insured_tiv
    FROM exposure.market_policy_stock_research_v0
    GROUP BY source_key, source_effective_date
)
SELECT
    p.*,
    'market_zip5_by_policy_type_not_company_specific'::text AS observational_grain,
    false::boolean AS model_input_approved,
    CASE
        WHEN p.malformed_rows > 0
          OR p.quarantine_status_mismatches > 0
          OR p.distinct_zip_policy_type_pairs <> p.source_rows - p.quarantined_rows
                 + p.quarantined_rows THEN 'BLOCKED_SOURCE_INTEGRITY'
        WHEN p.rows_with_provider_original_hash <> p.source_rows THEN 'BLOCKED_ORIGINAL_SOURCE_PROVENANCE'
        WHEN p.rows_with_legal_carrier <> p.source_rows THEN 'BLOCKED_NO_CARRIER_ZIP_IDENTITY'
        WHEN p.rows_with_actual_insured_tiv <> p.source_rows THEN 'BLOCKED_NO_INSURED_TIV'
        ELSE 'BLOCKED_EXPOSURE_AND_LICENSE_REVIEW'
    END AS next_evidence_gate
FROM profile p;