-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ ONLY. Branch-neutral insurance CAT pipeline evidence checkpoint.
-- A green integrity check on an empty table does NOT imply readiness.
-- Positive counts are STRUCTURAL evidence only, not scientific, legal,
-- commercial, insurer, catastrophe, or model-input admission decisions.
-- Always select the intended Neon project + database + branch explicitly.
WITH stages AS (
 SELECT '01_source_metadata'::text AS stage,
        (SELECT count(*) FROM registry.source_record)::bigint AS observed_rows,
        (SELECT count(*) FROM registry.source_record WHERE admissible_for_raw IS TRUE)::bigint AS structurally_qualified_rows,
        'Raw source registration is not raw source admission'::text AS qualification
 UNION ALL SELECT '02_content_artifacts',
        (SELECT count(*) FROM registry.artifact),
        (SELECT count(*) FROM registry.artifact
          WHERE content_sha256 ~ '^[0-9a-f]{64}$' AND byte_length>0
            AND storage_ref IS NOT NULL AND btrim(storage_ref)<>''
            AND source_key IN (SELECT source_key FROM registry.source_record
                               WHERE admissible_for_raw IS TRUE)),
        'SHA and source-rights flags are necessary but not sufficient for scientific admission'
 UNION ALL SELECT '03_verified_legal_organizations',
        (SELECT count(*) FROM entity.organization),
        (SELECT count(*) FROM entity.organization WHERE identity_status='verified'),
        'Verified legal identity is not proof of insured exposure or group ownership'
 UNION ALL SELECT '04_portfolios_real_vs_synthetic',
        (SELECT count(*) FROM exposure.portfolio),
        (SELECT count(*) FROM exposure.portfolio p
          JOIN entity.organization o ON o.organization_id=p.organization_id
          WHERE p.portfolio_type IS DISTINCT FROM 'synthetic'
            AND o.identity_status='verified'),
        'Non-synthetic company-linked portfolios only'
 UNION ALL SELECT '05_exposure_units_real_vs_synthetic',
        (SELECT count(*) FROM exposure.exposure_unit),
        (SELECT count(*) FROM exposure.exposure_unit u
          JOIN exposure.portfolio_version pv ON pv.portfolio_version_id=u.portfolio_version_id
          JOIN exposure.portfolio p ON p.portfolio_id=pv.portfolio_id
          JOIN entity.organization o ON o.organization_id=p.organization_id
          JOIN registry.source_record s ON s.source_key=u.source_key
          WHERE p.portfolio_type IS DISTINCT FROM 'synthetic'
            AND u.assumption_status IS DISTINCT FROM 'synthetic'
            AND o.identity_status='verified'
            AND s.admissible_for_raw IS TRUE
            AND u.insured_value>0 AND u.location IS NOT NULL
            AND ST_IsValid(u.location)),
        'Only non-synthetic, source-approved, geolocated candidate insured value'
 UNION ALL SELECT '06_hazard_event_catalogues',
        (SELECT count(*) FROM hazard.event_catalogue),
        (SELECT count(*) FROM hazard.event_catalogue
          WHERE event_count>0 AND evidence_sha256 ~ '^[0-9a-f]{64}$'
            AND source_key IN (SELECT source_key FROM registry.source_record
                               WHERE admissible_for_raw IS TRUE)),
        'Event count and SHA are necessary but not hazard-footprint proof'
 UNION ALL SELECT '07_physical_hazard_events',
        (SELECT count(*) FROM hazard.physical_event),
        (SELECT count(*) FROM hazard.physical_event e
          WHERE EXISTS (
            SELECT 1 FROM hazard.event_artifact ea
            JOIN registry.artifact a ON a.artifact_id=ea.artifact_id
            JOIN registry.source_record s ON s.source_key=a.source_key
            WHERE ea.event_id=e.event_id AND s.admissible_for_raw IS TRUE
              AND a.content_sha256 ~ '^[0-9a-f]{64}$')),
        'Needs associated source-approved artifact, still not proof of physical intensity'
 UNION ALL SELECT '08_real_reinsurance_contracts',
        (SELECT count(*) FROM insurance.contract),
        (SELECT count(*) FROM insurance.contract c
          JOIN registry.source_record s ON s.source_key=c.source_key
          WHERE c.is_synthetic IS FALSE AND c.cedent_id IS NOT NULL
            AND c.counterparty_id IS NOT NULL
            AND c.contract_type IN ('cat_xl','retro','retrocession')
            AND s.admissible_for_raw IS TRUE
            AND c.contract_terms IS NOT NULL),
        'Synthetic CAT-XL smoke contracts excluded; actual treaty terms need legal review'
 UNION ALL SELECT '09_pinned_model_versions',
        (SELECT count(*) FROM model.model_version),
        (SELECT count(*) FROM model.model_version
          WHERE source_commit_sha ~ '^[0-9a-f]{40}$'
            AND parameter_sha256 ~ '^[0-9a-f]{64}$'),
        'Pinned code and parameters are not independent model validation'
 UNION ALL SELECT '10_model_loss_artifacts',
        (SELECT count(*) FROM model.loss_artifact),
        (SELECT count(*) FROM model.loss_artifact l
          JOIN registry.artifact a ON a.artifact_id=l.artifact_id
          JOIN model.simulation_run r ON r.run_id=l.run_id
          WHERE r.run_status='completed' AND l.row_count>0
            AND a.content_sha256 ~ '^[0-9a-f]{64}$'),
        'Loss artifacts need source and financial-scientific approval beyond a SHA'
 UNION ALL SELECT '11_joint_10k_loss_runs',
        (SELECT count(*) FROM model.simulation_run),
        (SELECT count(*) FROM model.simulation_run r
          JOIN model.model_version v ON v.model_version_id=r.model_version_id
          JOIN exposure.portfolio_version pv ON pv.portfolio_version_id=r.portfolio_version_id
          JOIN exposure.portfolio p ON p.portfolio_id=pv.portfolio_id
          JOIN hazard.event_catalogue ec ON ec.catalogue_id=r.catalogue_id
          WHERE p.portfolio_type IS DISTINCT FROM 'synthetic'
            AND v.source_commit_sha ~ '^[0-9a-f]{40}$'
            AND v.parameter_sha256 ~ '^[0-9a-f]{64}$'
            AND r.run_status='completed' AND r.simulation_years>=10000
            AND r.config_sha256 ~ '^[0-9a-f]{64}$'
            AND r.shared_event_namespace IS NOT NULL
            AND btrim(r.shared_event_namespace)<>''
            AND EXISTS (
              SELECT 1 FROM model.loss_artifact l
              JOIN registry.artifact a ON a.artifact_id=l.artifact_id
              WHERE l.run_id=r.run_id AND l.row_count>0
                AND a.content_sha256 ~ '^[0-9a-f]{64}$')),
        'Completed 10k simulation is not proof of insured CAT results or retro accuracy'
)
SELECT stage,observed_rows,structurally_qualified_rows,
 CASE WHEN observed_rows=0 THEN 'MISSING_RECORDS'
      WHEN structurally_qualified_rows=0 THEN 'RESEARCH_OR_UNQUALIFIED_ONLY'
      ELSE 'STRUCTURAL_EVIDENCE_PRESENT_NOT_ADMITTED' END AS evidence_status,
 qualification,FALSE AS automatic_model_admission
FROM stages ORDER BY stage;
