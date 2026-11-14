-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ ONLY: insurance-risk-core/insurance, validation-schema-20261031 only.
-- NAIC exact overlap is a research identifier intersection, not ownership,
-- legal identity certification, insurer-ZIP allocation or admitted CAT TIV.
WITH florida AS (
    SELECT DISTINCT naic_code
      FROM exposure.fl_oir_mir_company_statewide_original_v1
), nc_overlap AS (
    SELECT naic_5digit,
           bool_or(corporate_ownership_verified) AS corporate_ownership_verified,
           bool_or(company_zip_exposure_observed) AS company_zip_exposure_observed,
           bool_or(insurer_cat_tiv_admissible) AS insurer_cat_tiv_admissible,
           bool_or(florida_report_is_full) AS florida_report_is_full
      FROM research.fl_nc_legal_naic_overlap_research_v1
     GROUP BY naic_5digit
), counts AS (
    SELECT (SELECT count(*) FROM florida) AS florida_naic_codes,
           (SELECT count(*) FROM nc_overlap) AS overlapping_naic_codes,
           (SELECT count(*) FROM florida f JOIN nc_overlap n
                    ON f.naic_code=n.naic_5digit) AS exact_matched_naic_codes,
           (SELECT count(*) FROM florida f LEFT JOIN nc_overlap n
                    ON f.naic_code=n.naic_5digit WHERE n.naic_5digit IS NULL)
               AS unmatched_florida_naic_codes,
           (SELECT count(*) FROM nc_overlap n LEFT JOIN florida f
                    ON f.naic_code=n.naic_5digit WHERE f.naic_code IS NULL)
               AS overlap_codes_not_in_florida,
           (SELECT count(*) FROM nc_overlap
                    WHERE corporate_ownership_verified) AS parent_verified_codes,
           (SELECT count(*) FROM nc_overlap
                    WHERE company_zip_exposure_observed) AS company_zip_codes,
           (SELECT count(*) FROM nc_overlap
                    WHERE insurer_cat_tiv_admissible) AS cat_tiv_admitted_codes,
           (SELECT count(*) FROM nc_overlap
                    WHERE florida_report_is_full) AS full_filer_universe_claims,
           (SELECT count(*) FROM exposure.fl_oir_mir_company_statewide_original_v1
                    WHERE commercial_rights_reviewed) AS florida_rights_reviewed_rows,
           (SELECT count(*) FROM exposure.fl_oir_mir_company_statewide_original_v1
                    WHERE original_xlsx_sha256 !~ '^[0-9a-f]{64}$'
                       OR original_xlsx_sha256 IS NULL) AS florida_original_hash_missing_rows
)
SELECT 'validation_naic_exact_overlap'::text AS evidence_scope,
       current_database() AS database_name,
       (current_database()='insurance') AS expected_database,
       florida_naic_codes, overlapping_naic_codes,
       exact_matched_naic_codes, unmatched_florida_naic_codes,
       overlap_codes_not_in_florida, parent_verified_codes,
       company_zip_codes,cat_tiv_admitted_codes,full_filer_universe_claims,
       florida_rights_reviewed_rows,florida_original_hash_missing_rows,
       CASE WHEN florida_naic_codes>0
            THEN round(exact_matched_naic_codes::numeric*100/florida_naic_codes,2)
            ELSE NULL END AS naic_overlap_percent_research_only,
       false::boolean AS admitted_legal_parent_mapping,
       false::boolean AS actual_carrier_zip_exposure,
       false::boolean AS model_input_approved,
       CASE
         WHEN current_database()<>'insurance' THEN 'BLOCKED_WRONG_DATABASE'
         WHEN florida_naic_codes=0 OR overlapping_naic_codes=0
           THEN 'BLOCKED_EMPTY_NAIC_COHORT'
         WHEN overlap_codes_not_in_florida>0
           THEN 'BLOCKED_CROSSWALK_SCOPE_MISMATCH'
         WHEN florida_original_hash_missing_rows>0
           THEN 'BLOCKED_ORIGINAL_FLORIDA_SOURCE_PROVENANCE'
         WHEN florida_rights_reviewed_rows=0
           THEN 'BLOCKED_RIGHTS_REVIEW'
         WHEN parent_verified_codes=0
           THEN 'BLOCKED_CORPORATE_PARENT_EVIDENCE'
         WHEN company_zip_codes=0
           THEN 'BLOCKED_CARRIER_ZIP_EVIDENCE'
         WHEN cat_tiv_admitted_codes=0
           THEN 'BLOCKED_INSURED_TIV_EVIDENCE'
         ELSE 'BLOCKED_INDEPENDENT_LEGAL_AND_SCIENTIFIC_REVIEW'
       END AS first_gate
  FROM counts;
