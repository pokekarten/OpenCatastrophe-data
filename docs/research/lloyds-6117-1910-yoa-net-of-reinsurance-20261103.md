<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original Lloyd's 6117 sidecar ordering: 2025 audited disclosures and synthetic-only v0

**Research-only / non-admission.** The published percentage is **not** an insurer asset list, policy loss, property TIV, catastrophe event, ceded external recovery schedule, or an independently executed Lloyd's contract. No original report bytes, confidential commercial data, or source credentials are committed.

## Primary dated disclosures

- [Lloyd's Syndicate 6117 audited year-end 2025 accounts](https://assets.lloyds.com/media-651c0e64-c1d0-4f97-90f7-883c69fe2ef2/d0c78619-c395-42fd-97b2-49a13bc87990/6117_Accounts_2025Q4_20260219_131838.html), authorised 18 February 2026; managing agent Ariel Re Managing Agency Limited.
- [Lloyd's Syndicate 1910 audited year-end 2025 accounts](https://assets.lloyds.com/media-651c0e64-c1d0-4f97-90f7-883c69fe2ef2/25672d32-527e-4268-bc5f-417b394bb00d/1910_Accounts_2025Q4_20260219_131624.html), host/cedent.

6117 describes a **whole-account quota share of host Syndicate 1910**, by **underwriting year of account (YoA)**: 2023 = 11.68%, 2024 = 13.28%, 2025 = 15.27%; 2026 = 4.18% announced prospectively in those 2025 accounts. The 2026 value is *not* asserted to be a finalized measured 2026 occurrence or financial-year percentage. The contract is **net of host external outward reinsurance**, not a fraction of the host's unprotected catastrophe loss. These are published statements, not a complete parameter set for risk or capital modelling.

**Important accounting distinction:** 6117 reports certain net-of-host-outwards balances under gross presentation, with acquisition costs also affecting gross premiums; its financial-year 2025 income is not identical to an underwriting-year 2025 event catalogue. Host 1910 also has other special purpose syndicate arrangements, so the amount remaining after allocating to 6117 is **unresolved**, not automatically the host's ultimate retained share.

## Executable, synthetic-only loss conservation challenge

The script takes a caller-created fictional *gross loss* and already fictional host *external recovery*. It does not calculate recoveries, use a real insured loss, replicate contractual accounting or estimate a cedent portfolio. For the audited **2025 YoA rate** only:

    host synthetic gross = 100.0000 USD
    host hypothetical external recovery = 30.0000
    host post-external amount = 70.0000
    6117 toy sidecar allocation = 70 × 0.1527 = 10.6890
    unresolved post-external allocation = 59.3110
    conservation = 30 + 10.6890 + 59.3110 = 100.0000

Call the in-memory Python function or execute the CLI with a **fully fictional** JSON scenario. Required scenario fields:
- schema_version = 0.1.0; scenario_kind = fully_synthetic_test_only
- source_basis = lloyds_6117_2025_audited_accounts_yoa_disclosure
- financial_year = 2025 (the *report vintage*) and year_of_account = 2023, 2024 or 2025
- external_reinsurance_order = host_external_reinsurance_before_sidecar
- unit = uppercase three-letter currency identifier
- events = 1 to 128 rows, each with unique SYNTH_ event_id and two canonical nonnegative decimal-string monetary fields host_gross_loss and host_external_reinsurance_recovery

The 2026 prospective ratio is explicitly **blocked** by this v0 tool. No fictional result is a validated ILS risk allocation, real treaty loss or model input.

Run offline regression:

    python -m unittest tests.test_synthetic_sidecar_yoa_allocation_v0 -v
    python scripts/check_all.py

## Gates before any private model integration

1. Freeze exact original issuer report asset bytes and confirm extraction/licence permission; preserve YoA versus financial-year and role labels.
2. Obtain contractual definition of whole-account quota share, attachments, external protection and effective dates; this simple arithmetic cannot replace execution of a full reinsurance contract.
3. Resolve **all** outward and sidecar relationships (including 6136 if materially applicable), recovery allocation, currencies, event aggregation and event chronology before interpreting the remaining share as actual retention.
4. Connect to insurance exposure/hazard/vulnerability and NextGen *only through reviewed synthetic fixture and exact-head native execution proofs*. Keep real CAT and insurer model admission blocked.
