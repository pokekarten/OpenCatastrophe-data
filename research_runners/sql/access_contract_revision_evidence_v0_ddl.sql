-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- RESEARCH-ONLY DDL. DO NOT RUN ON THE NEON DEFAULT BRANCH.
-- Intended single isolated Neon branch: br-steep-lab-baeo8bmc.
-- Version identity is the *Git blob* (not an auto-updated source_record row).
-- Populating this table never grants external API access or CAT model use.
CREATE TABLE research.access_contract_revision_evidence_v0 (
    access_id text NOT NULL,
    git_blob_sha text NOT NULL,
    git_commit_sha text NOT NULL,
    repo text NOT NULL,
    git_path text NOT NULL,
    review_status text NOT NULL,
    rights_status text NOT NULL,
    probe_mode text NOT NULL,
    contract_metadata jsonb NOT NULL,
    evidence_role text NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT now(),
    authorized_for_production boolean NOT NULL DEFAULT false,
    provider_bytes_admitted boolean NOT NULL DEFAULT false,
    model_input_approved boolean NOT NULL DEFAULT false,
    CONSTRAINT access_contract_revision_evidence_v0_pkey
       PRIMARY KEY (access_id, git_blob_sha),
    CONSTRAINT access_contract_revision_evidence_v0_git_sha
       CHECK (git_blob_sha ~ '^[0-9a-f]{40}$'
              AND git_commit_sha ~ '^[0-9a-f]{40}$'),
    CONSTRAINT access_contract_revision_evidence_v0_repo
       CHECK (repo = 'pokekarten/OpenCatastrophe-data'
              AND git_path = 'access/' || access_id || '.json'),
    CONSTRAINT access_contract_revision_evidence_v0_roles
       CHECK (evidence_role IN ('historical_observed','proposed_unapproved')),
    CONSTRAINT access_contract_revision_evidence_v0_contract_shape
       CHECK (jsonb_typeof(contract_metadata) = 'object'
              AND contract_metadata->>'access_id' = access_id
              AND contract_metadata->>'status' = review_status
              AND contract_metadata->'rights_and_policy'->>'dataset_rights_status'
                    = rights_status
              AND contract_metadata->'probe_contract'->>'mode' = probe_mode),
    CONSTRAINT access_contract_revision_evidence_v0_never_grants
       CHECK (authorized_for_production = false
              AND provider_bytes_admitted = false
              AND model_input_approved = false)
);

CREATE OR REPLACE FUNCTION research.reject_access_contract_revision_mutation_v0()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'access revision evidence is append-only; corrections need a separate reviewed lineage table';
END;
$$;

CREATE TRIGGER access_contract_revision_no_update_or_delete_v0
BEFORE UPDATE OR DELETE ON research.access_contract_revision_evidence_v0
FOR EACH ROW EXECUTE FUNCTION research.reject_access_contract_revision_mutation_v0();

-- The above DDL is for an isolated branch only. Historical baseline receipts
-- and proposed revisions are inserted separately with pinned source bytes.
-- The production registry.source_record is NEVER altered by this research DDL.
