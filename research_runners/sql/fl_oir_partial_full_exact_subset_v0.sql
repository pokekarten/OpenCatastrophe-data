-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Florida OIR original 442-row full report versus 282-row legacy preview.
-- READ ONLY. Execute only on insurance-risk-core validation-schema-20261031.
-- 282 preview rows are a subset, NEVER an additional 282 insured records.
-- Same company/LOB counts do not prove ZIP exposures, filing completeness,
-- original partial XLSX bytes, claims, insurer TIV, rights or CAT suitability.
WITH full_rows AS (
  SELECT report_as_of,naic_code,reported_policy_type,reported_company_name,
         reported_policies_in_force,original_xlsx_sha256,
         complete_published_workbook,all_regulatory_filers_included,
         cat_loss_calibration_admissible,commercial_rights_reviewed
  FROM exposure.fl_oir_mir_company_statewide_original_v1
), preview AS (
  SELECT report_as_of,naic_code,reported_policy_type,company_name_as_reported,
         reported_policies_in_force,original_xlsx_sha256,
         workbook_is_complete,source_reuse_rights_approved,
         carrier_specific_cat_tiv_admissible
  FROM exposure.fl_oir_statewide_company_policy_research_v0
), paired AS (
  SELECT p.*,f.naic_code AS matched_full_key,
         f.reported_company_name AS full_name,
         f.reported_policies_in_force AS full_policies,
         f.original_xlsx_sha256 AS full_sha
  FROM preview p LEFT JOIN full_rows f USING(report_as_of,naic_code,reported_policy_type)
), checks AS (
  SELECT 'full_exact_442_rows'::text check_id,
         ((SELECT count(*) FROM full_rows)=442) passed
  UNION ALL SELECT 'preview_exact_282_rows',
         ((SELECT count(*) FROM preview)=282)
  UNION ALL SELECT 'full_unique_company_type_period',
         ((SELECT count(*) FROM full_rows)=
          (SELECT count(DISTINCT (report_as_of,naic_code,reported_policy_type)) FROM full_rows))
  UNION ALL SELECT 'preview_unique_company_type_period',
         ((SELECT count(*) FROM preview)=
          (SELECT count(DISTINCT (report_as_of,naic_code,reported_policy_type)) FROM preview))
  UNION ALL SELECT 'every_preview_key_in_full',
         NOT EXISTS (SELECT 1 FROM paired WHERE matched_full_key IS NULL)
  UNION ALL SELECT 'all_preview_policy_counts_identical',
         NOT EXISTS (SELECT 1 FROM paired WHERE reported_policies_in_force IS DISTINCT FROM full_policies)
  UNION ALL SELECT 'all_preview_company_names_identical_casefold',
         NOT EXISTS (SELECT 1 FROM paired WHERE lower(btrim(company_name_as_reported))
                                          IS DISTINCT FROM lower(btrim(full_name)))
  UNION ALL SELECT 'same_report_date_2025_12_31',
         NOT EXISTS (SELECT 1 FROM full_rows WHERE report_as_of<>DATE '2025-12-31')
         AND NOT EXISTS (SELECT 1 FROM preview WHERE report_as_of<>DATE '2025-12-31')
  UNION ALL SELECT 'full_original_xlsx_sha_pinned',
         NOT EXISTS (SELECT 1 FROM full_rows WHERE original_xlsx_sha256
           IS DISTINCT FROM 'a4fc7d5e20daed10299b06b2b661480b7c92c2cbaecc697a26567156bf1d4d3a')
  UNION ALL SELECT 'no_premature_source_promotion',
         NOT EXISTS (SELECT 1 FROM full_rows WHERE cat_loss_calibration_admissible
            OR commercial_rights_reviewed OR all_regulatory_filers_included)
         AND NOT EXISTS (SELECT 1 FROM preview WHERE carrier_specific_cat_tiv_admissible
            OR source_reuse_rights_approved OR workbook_is_complete)
)
SELECT check_id,coalesce(passed,FALSE) AS passed,
       FALSE AS model_admission_granted,
       FALSE AS permission_to_add_282_to_442
FROM checks ORDER BY check_id;
