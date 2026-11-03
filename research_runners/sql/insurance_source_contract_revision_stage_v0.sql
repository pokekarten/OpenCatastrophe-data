-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Stage ONLY after review in insurance-risk-core / insurance.
-- Non-destructive, append-only registry-version research. It does NOT
-- acquire third-party data or grant source/model admission.
-- Live isolated Neon test: 2026-11-02, 115 revisions/114 source keys,
-- 0 raw/model approvals. DO NOT use on tcgp2p-core.
-- GitHub tree pinned: 45f637f8d381480c794fefba6c14605ae969a098.
-- WorldCover blob pinned: 2884e2f50b495eee3b399f55c08d43cfa100b602.
-- Keep snapshot checks and both inserts atomic: a failed evidence guard
-- must not leave half-staged rows on a database with autocommit enabled.
BEGIN;
-- Fail closed if the historical registry has drifted from the
-- exact 114-row snapshot independently reviewed for this staging step.
DO $snapshot_guard$
BEGIN
  IF (SELECT count(*) FROM registry.source_record) <> 114
     -- Deterministic exact metadata snapshot from the live 114-row registry.
     -- Built-in PostgreSQL SHA-256: no pgcrypto extension or secret required.
     OR (
       SELECT encode(sha256(convert_to(
         string_agg(jsonb_build_object(
           'source_key', source_key,
           'git_commit_sha', git_commit_sha,
           'git_blob_sha', git_blob_sha,
           'git_path', git_path,
           'raw_metadata', raw_metadata,
           'review_status', review_status
         )::text, E'\n' ORDER BY source_key), 'UTF8')), 'hex')
       FROM registry.source_record
     ) IS DISTINCT FROM
       'dce4e12c3aa9385c4a5b6805b1ad13682e2f7f91969eb1b7ed302c14c78fa822'
     OR EXISTS (
       SELECT 1 FROM registry.source_record
       WHERE git_blob_sha !~ '^[0-9a-f]{40}$'
          OR git_commit_sha !~ '^[0-9a-f]{40}$'
     )
     OR NOT EXISTS (
       SELECT 1 FROM registry.source_record
       WHERE source_key='access:esa.worldcover.2021.v200'
         AND git_blob_sha='830fff1705d6b29d8c88dc423a27c7254608ca50'
         AND review_status='documented_only'
     )
  THEN
    RAISE EXCEPTION 'Pinned source-registry snapshot drift: refuse staging';
  END IF;
END;
$snapshot_guard$;
CREATE TABLE IF NOT EXISTS registry.source_contract_revision_v0 (
 source_key text NOT NULL REFERENCES registry.source_record(source_key),
 git_commit_sha text NOT NULL CHECK (git_commit_sha ~ '^[0-9a-f]{40}$'),
 git_blob_sha text NOT NULL CHECK (git_blob_sha ~ '^[0-9a-f]{40}$'),
 git_path text NOT NULL,
 contract_record jsonb NOT NULL,
 contract_status text NOT NULL,
 raw_import_allowed boolean NOT NULL DEFAULT false CHECK (raw_import_allowed IS FALSE),
 model_input_approved boolean NOT NULL DEFAULT false CHECK (model_input_approved IS FALSE),
 receipt_kind text NOT NULL,
 recorded_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(source_key,git_blob_sha)
);

-- CREATE TABLE IF NOT EXISTS must not silently accept an existing,
-- permissive table with missing rights constraints or duplicate version keys.
-- Inspect actual PostgreSQL constraints (not merely current rows).
DO $schema_guard$
BEGIN
  IF (
    SELECT count(*)
    FROM pg_catalog.pg_constraint c
    JOIN (
      VALUES
        ('source_contract_revision_v0_raw_import_allowed_check', 'c',
         'CHECK ((raw_import_allowed IS FALSE))'),
        ('source_contract_revision_v0_model_input_approved_check', 'c',
         'CHECK ((model_input_approved IS FALSE))'),
        ('source_contract_revision_v0_pkey', 'p',
         'PRIMARY KEY (source_key, git_blob_sha)'),
        ('source_contract_revision_v0_source_key_fkey', 'f',
         'FOREIGN KEY (source_key) REFERENCES registry.source_record(source_key)')
    ) AS expected(name, kind, definition)
      ON c.conname=expected.name
     AND c.contype=expected.kind
     AND c.convalidated IS TRUE
     AND pg_catalog.pg_get_constraintdef(c.oid)=expected.definition
    WHERE c.conrelid='registry.source_contract_revision_v0'::regclass
  ) <> 4 OR (
    SELECT count(*)
    FROM pg_catalog.pg_attribute a
    WHERE a.attrelid='registry.source_contract_revision_v0'::regclass
      AND a.attname IN ('raw_import_allowed','model_input_approved')
      AND a.attnotnull IS TRUE
      AND a.attisdropped IS FALSE
  ) <> 2 THEN
    RAISE EXCEPTION 'Source revision table lacks reviewed non-admission constraints';
  END IF;
END;
$schema_guard$;
-- Preserve independently recorded, historical Neon metadata without
-- mutating source_record. Different revisions must stay distinguishable.
INSERT INTO registry.source_contract_revision_v0
 (source_key,git_commit_sha,git_blob_sha,git_path,contract_record,contract_status,receipt_kind)
 SELECT source_key,git_commit_sha,git_blob_sha,git_path,raw_metadata,review_status,'neon_historical'
 FROM registry.source_record
 WHERE git_blob_sha ~ '^[0-9a-f]{40}$' AND git_commit_sha ~ '^[0-9a-f]{40}$'
 ON CONFLICT DO NOTHING;
-- New ESA contract: a digest-linked canonical Git metadata pointer only.
-- Complete authoritative JSON remains access/esa.worldcover.2021.v200.json.
-- This is NOT a raster, source-data import or model admission.
INSERT INTO registry.source_contract_revision_v0
 (source_key,git_commit_sha,git_blob_sha,git_path,contract_record,contract_status,receipt_kind)
 VALUES ('access:esa.worldcover.2021.v200',
 '45f637f8d381480c794fefba6c14605ae969a098',
 '2884e2f50b495eee3b399f55c08d43cfa100b602',
 'access/esa.worldcover.2021.v200.json',
 '{"access_id":"esa.worldcover.2021.v200","status":"probe_ready","provider":"ESA WorldCover / VITO","source":"pinned_original_github_json","raw_data_import":"prohibited","model_admission":"prohibited","bounded_one_block_canary":true}'::jsonb,
 'probe_ready','github_pinned_review') ON CONFLICT DO NOTHING;
-- ON CONFLICT DO NOTHING may only ignore identical prior receipts. Reject
-- contradictory pre-existing rights/status/source provenance rather than
-- disguising them as a successful idempotent migration.
DO $revision_guard$
BEGIN
  IF EXISTS (
    SELECT 1 FROM registry.source_record s
    LEFT JOIN registry.source_contract_revision_v0 r
      ON r.source_key=s.source_key AND r.git_blob_sha=s.git_blob_sha
    WHERE r.source_key IS NULL
       OR r.git_commit_sha IS DISTINCT FROM s.git_commit_sha
       OR r.git_path IS DISTINCT FROM s.git_path
       OR r.contract_record IS DISTINCT FROM s.raw_metadata
       OR r.contract_status IS DISTINCT FROM s.review_status
       OR r.receipt_kind IS DISTINCT FROM 'neon_historical'
  ) OR NOT EXISTS (
    SELECT 1 FROM registry.source_contract_revision_v0
    WHERE source_key='access:esa.worldcover.2021.v200'
      AND git_commit_sha='45f637f8d381480c794fefba6c14605ae969a098'
      AND git_blob_sha='2884e2f50b495eee3b399f55c08d43cfa100b602'
      AND git_path='access/esa.worldcover.2021.v200.json'
      AND contract_record='{"access_id":"esa.worldcover.2021.v200","status":"probe_ready","provider":"ESA WorldCover / VITO","source":"pinned_original_github_json","raw_data_import":"prohibited","model_admission":"prohibited","bounded_one_block_canary":true}'::jsonb
      AND contract_status='probe_ready'
      AND receipt_kind='github_pinned_review'
      AND raw_import_allowed IS FALSE AND model_input_approved IS FALSE
  ) OR EXISTS (
    SELECT 1 FROM registry.source_contract_revision_v0
    WHERE raw_import_allowed IS DISTINCT FROM FALSE
       OR model_input_approved IS DISTINCT FROM FALSE
  ) THEN
    RAISE EXCEPTION 'Source revision evidence conflicts with pinned source records';
  END IF;
END;
$revision_guard$;
COMMIT;
-- Verification gates (read-only after staging):
-- SELECT count(*) AS revisions,count(DISTINCT source_key) AS sources,
--   count(*) FILTER (WHERE raw_import_allowed OR model_input_approved) AS unsafe
-- FROM registry.source_contract_revision_v0;
-- SELECT git_blob_sha,contract_status,receipt_kind
-- FROM registry.source_contract_revision_v0
-- WHERE source_key='access:esa.worldcover.2021.v200';
