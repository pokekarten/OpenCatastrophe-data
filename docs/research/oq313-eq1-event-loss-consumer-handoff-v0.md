<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# OQ3.13 EQ1 event-loss handoff to future CAT model consumers (v0)

## Executable result, not a model admission

New offline entrypoint: [project_oq313_event_loss_handoff_v0.py](../../scripts/project_oq313_event_loss_handoff_v0.py).

It converts an **already available full canonical** reconstructed Kosovo OpenQuake
3.13 risk_by_event receipt into an event-level JSONL ledger plus a SHA-256
manifest, without modifying or rerunning the hazard/risk engine. The source
validator is the existing
profile_oq313_risk_by_event_receipt._load_validated_receipt, which in turn
uses the reviewed EQ1 numerical receipt contract. This code does not create
provider data or make a historical reproduction claim.

The export is loss-only in the exact currently established scope:
thresholded_ground_up_structural_replacement_cost_loss in EUR.
Each JSONL line has only:

- event_id: source calculation event ID, not globally unique;
- rup_id: OpenQuake rupture identifier;
- rlz_id: OpenQuake logic-tree realization identifier;
- loss_f32_be_hex: exact canonical IEEE754 binary32 source loss bits;
- variance_f32_be_hex: exact canonical IEEE754 binary32 variance bits.

The sidecar manifest fixes full source-receipt SHA-256/byte identity,
source/engine commit, quantity/selection and exported JSONL SHA-256/size/rows.
The composite row key is **(source_receipt_sha256, event_id)**. This prevents
a consumer from incorrectly joining bare event IDs across independent
catalogues/calculations. JSONL is a private, project-specific transport
contract and **not** an Oasis ODR/ELT/PLT implementation.

## Independently rechecked real computation evidence

The canonical github-actions[bot] result on
[EQ1 issue #609](https://github.com/pokekarten/OpenCatastrophe-data/issues/609)
for execution SHA d1160e641c5a4bb6a7c9d9bae1b5d276ca667314 declares:

- native OpenQuake process exit_code=0, reconstructed experiment;
- canonical numerical receipt **220,619 event-loss rows**;
- full canonical receipt **24,217,988 bytes**, SHA-256
  f2cb7180dc1dc76d38ea92b08e28732cc1b114d702767b5a500eedc35fe5b9ac;
- full_receipt_published=false, provider bytes/datastore not persisted;
- scientific validation, historical reproduction, model-use and publication
  rights **false**.

**Important:** the published hash/commitment is *not* the original
24MB receipt. The new export cannot reconstruct loss numbers from a digest.
For this exact execution, acquire the **existing full source receipt from its
authorized local datastore/recovery environment**, or rerun through a
separately reviewed execution lane and pin the new output identity. Do not
guess or invent event losses from the public commitment.

## Local usage (when the actual full receipt is present)

Run in a reviewed checkout of OpenCatastrophe-data with Python:

~~~bash
python scripts/project_oq313_event_loss_handoff_v0.py \
  /secure/local/receipt.json \
  --expected-receipt-sha256 f2cb7180dc1dc76d38ea92b08e28732cc1b114d702767b5a500eedc35fe5b9ac \
  --jsonl-out /secure/local/events.jsonl \
  --manifest-out /secure/local/events.manifest.json
~~~

The SHA argument is **only** correct if the input is exactly the 24MB
canonical receipt above. A different reviewed run must provide its own
authenticated receipt SHA-256. The command fails closed on absent, modified,
wrong-schema, over-budget or symlink input, existing output paths, and
invalid numerical semantics. It writes two new local private files with no
overwrite and no provider data printed on stdout. Do not commit the outputs.

For a newly authorized owner-local OpenQuake calc_*.hdf5:
project_existing_oq313_datastore.py --full-receipt-out ... is the
**existing** sanctioned recovery path, subject to its own provenance,
data-rights and resource constraints. This handoff is downstream of that
validated receipt, not a substitute for it.

## Validation and remaining pipeline work

Synthetic unit tests create a canonical sample receipt through the existing
project_oq313_risk_by_event_receipt builder. They test exact f32 preservation,
event order, hash pins, invalid policy/numeric fields, local new-only files,
rollback and authority flags. Only synthetic inputs are committed.

This module deliberately does **not** infer occurrence rates, exposure
allocation, annual/loss sampling, insurer policy values, excess layers,
reinstatements, peril correlation, secondary uncertainty or reinsurance.
The manifest always declares:

- event_rates_available=false, annualization_authorized=false;
- insured_loss_calculated=false, financial_terms_applied=false;
- model_input_approved=false, public_redistribution_authorized=false;
- oasis_odr_conformant=false, nextgen_import_verified=false.

The next real integration gate is to join **independently authorized**
event occurrence/frequency, physical intensity, exposure, vulnerability
and financial terms with exact version compatibility, then implement and
test an explicit consumer importer. This source-only event-loss adapter does
not itself establish those prerequisites.

No writes to CAT Neon production or validation branch were performed.

## Independent consumer-side validation (same PR)

New offline program:
[`validate_oq313_event_loss_handoff_v0.py`](../../scripts/validate_oq313_event_loss_handoff_v0.py).

Before accepting the loss-only JSONL in any downstream component, the
consumer must supply **two independent, previously pinned commitments**:
the handoff manifest SHA-256 and the original source receipt SHA-256.
The validator checks canonical bytes, strict schema and typed source fields,
exact OQ3.13 engine and original numerical-quantity semantics, all
non-admission flags, file-byte and row hashes, exact float32 validity,
strictly increasing unique event IDs and row completeness. The composite
row identity is (source receipt digest, event ID) and cannot be inferred
from the bare event ID.

Run on reviewed local artifacts only:

~~~bash
python scripts/validate_oq313_event_loss_handoff_v0.py \
  --jsonl /secure/local/events.jsonl \
  --manifest /secure/local/events.manifest.json \
  --expected-manifest-sha256 <independently-authenticated-manifest-sha256> \
  --expected-source-receipt-sha256 <independently-authenticated-receipt-sha256> \
  --source-receipt /secure/local/receipt.json
~~~

The optional `--source-receipt` **materially strengthens** the check: it
revalidates the complete original OpenQuake numerical receipt and recreates
the canonical export to require a **byte-for-byte identical** JSONL and
manifest. The output flag `canonical_source_rows_reconciled` is true only
in this mode. Without that full source, a malicious actor could forge a
self-consistent pair of source claims/JSONL/manifest if the claimed pins
were never authenticated outside the transfer; therefore the verifier
explicitly reports no origin authentication in *either* mode.

The validator writes **nothing** and never promotes event records to insurer
portfolio loss, annualized AAL/AEP/OEP or Oasis/NextGen. Synthetic negative
tests cover independently pinned manifest tampering, wrong source identity,
loss/variance corruption, duplicate/reordered events, policy/authority
spoofing, canonicalization drift, symlink inputs and fabricated-but-self-
consistent losses. The latter are rejected **only when** the full source
receipt is supplied, as required by the actual trust boundary.

## Reproducible 220,619-row scale proof

The new `tests/test_oq313_event_loss_handoff_scale_v0.py` is an
end-to-end **fully synthetic** stress regression deliberately sized to
**220,619 rows**, matching the cardinality disclosed by the earlier Kosovo
OpenQuake terminal without requiring or fabricating its missing original bytes.

It constructs a canonical synthetic source receipt with constant invented
1-EUR structural binary32 losses and zero variances, projects loss-only JSONL
with the original source receipt digest, verifies the entire manifest and
per-row preservation, then makes the independent consumer validate every row
first without and then *with* the full original **synthetic** receipt. This
also challenges the 64-MiB source and 96-MiB JSONL budgets, execution cost,
consumer row ordering and two-SHA transport binding at realistic row count.

This proves only that the adapter can process a synthetic sample at the
historical receipt's **row count**, not that the original 220,619 Kosovo
loss values are available, reproduced or admitted. It does not prove
NextGen can calculate annual/treaty losses. NextGen's already existing
OpenQuake 3.23 loss tables require independent source **physical events,
realization weights and a complete world/year catalogue**. The EQ1 3.13
loss-only source has none of those and must not be used as though it did.
