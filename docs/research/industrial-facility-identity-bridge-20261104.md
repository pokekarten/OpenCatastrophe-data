<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Industrial physical-asset identity: EPA FRS × GEM research preflight (2026-11-04)

**Status: synthetic-only executable research; no source acquisition, original-byte authentication, licence admission, database write, insurer assignment or CAT model input.** Three new source candidates remain in [the discovery shard](../../landscape/sources-owner-facility-business-priors-20261104.json), not accepted manifests.

## Why a separate crosswalk is needed

- [EPA ECHO Exporter](https://echo.epa.gov/tools/data-downloads) is a US regulated-facility collection. Its [FRS dictionary](https://echo.epa.gov/tools/data-downloads/frs-download-summary) describes `REGISTRY_ID`, location fields, NAICS codes and agency-specific linked programme IDs. FRS identity does not prove insured physical buildings, ownership or replacement values.
- [GEM Global Energy Ownership Tracker](https://globalenergymonitor.org/projects/global-energy-ownership-tracker) October 2026 tracks physical project IDs and direct/ultimate entity owners. It exposes company identifiers including LEIs where available, and ownership connection sources. Its definition of an ultimate "parent" is not equivalent to an insurance group or a solvency consolidation perimeter.
- GEM **imputes some missing ownership percentages**. Those synthetic shares must not be represented as observed equity stakes, insured percentages, underwriting retentions, or treaty shares.
- **No original verified generic EPA FRS ↔ GEM asset cross-ID was found.** Shared names, industrial category or close coordinates alone do not prove a common asset.

## Executable, synthetic-only contract

The [runner](../../research_runners/industrial_frs_gem_identity_v0.py) and [14 tests](../../tests/test_industrial_frs_gem_identity_v0.py) audit caller-prepared *normalized projections*, **not native publisher data schemas**:

- FRS CSV: `frs_id,country_code,latitude,longitude`
- GEM CSV: `gem_asset_id,country_code,latitude,longitude`
- Link CSV: `frs_id,gem_asset_id,evidence_kind,evidence_url,evidence_sha256`

Callers must supply exact projection SHA-256s and explicit source snapshot dates. Each projection is capped at 1 MB / 10,000 rows. The runner does not fetch, write, export or approve any external data.

Link evidence kinds: `publisher_explicit_cross_id`, `independent_document` and `name_or_proximity_only`. Stronger assertions require a fixed HTTPS evidence URL without query parameters, credentials or fragments, plus a claimed original-evidence digest; **the script does not verify the original publisher bytes, URI content or rights**. A name/location-only link cannot qualify as an identity candidate.

Every FRS record ends in exactly one aggregate disposition: no link in selected subset, ambiguous cardinality, referenced GEM missing, unsupported name/proximity link, country contradiction, missing coordinates, distance greater than 5 km, or unique *research-only* candidate. More than 5 km is a **screen for review**, not a calibrated scientific or geographic rule; industrial sites can be large. Even unique linked records do not establish a building, parent company, LEI, insurer, policy, claim, TIV, or exposure admitted to a CAT model.

The output contains only totals, explicit source-vintage fields and SHA-256s of the supplied projections; it does not echo identifiers, company names, site coordinates, original evidence or assets.

Run on authorized local input after legal/scientific review:

```bash
python -m unittest discover -s tests -p 'test_industrial_frs_gem_identity_v0.py' -v
python research_runners/industrial_frs_gem_identity_v0.py \
  --frs-projection /approved/local/frs.csv --frs-sha256 HASH \
  --gem-projection /approved/local/gem.csv --gem-sha256 HASH \
  --links-projection /approved/local/links.csv --links-sha256 HASH \
  --frs-vintage YYYY-MM-DD --gem-vintage YYYY-MM-DD --link-vintage YYYY-MM-DD
```

Each native-to-normalized transform still needs a pinned original source version, audited column mappings, coordinate reference system and original-byte receipt. Projection hash validation is not source authenticity. No record in the subset does not mean no physical asset or no insurance exists. Multiple EPA identifiers can represent one physical site and one site can encompass multiple GEM projects: those links require typed n:m relationship modeling, not premature deduplication.

## Next falsifiable real-data test

1. Review exact GEM October 2026 download-product rights and EPA FRS selected original ZIP rights. Pin exact asset identity, file bytes, release dates and published field mappings before making small local projections; keep third-party files out of Git.
2. Check at most **5–10 real US sites** with individually documented third-party FRS↔GEM mapping evidence. Reject mere proximity, carry identity confidence and cardinality, and report genuine nonmatches/unknowns separately.
3. For GEM entities that carry **observed** LEIs, validate the IDs via existing GLEIF tools and keep GLEIF accounting consolidation distinct from GEM ownership. Separately preserve observed versus GEM-imputed stakes.
4. Only after independent asset geometry, actual vs imputed owner identity, economic asset-value priors and insurer financial constraints are approved, hand **distributions of synthetic scenarios** into NextGen. Do not reconstruct a claim that any public facility is insured by a named company.

**Execution evidence:** 14/14 new deterministic local unit tests and compilation passed in ChatGPT Linux on 2026-11-04. Repository-wide CI must be checked on the exact latest PR head. No provider original data, live site crosswalk or production database integration was executed.
