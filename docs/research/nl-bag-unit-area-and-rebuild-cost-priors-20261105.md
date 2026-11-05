<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Netherlands BAG usable area and rebuilding-value priors: source-gated research

**Date:** 2026-11-05  
**Status:** Discovery and synthetic-only QA. No source admitted, no provider unit/address records imported, no TIV or insured portfolio calculated.  
**Upstream geometry research:** merged PR #1319, `docs/research/cadastral-land-register-exposure-source-gates-20261104.md`.  
**New candidate registry:** `landscape/sources-nl-rebuild-cost-priors-20261105.json` (3 research-only records), with matched generated Markdown.

## Motivation and entity granularity

The previous BGT→BAG link proved original official **building identity** in small research windows, and projected parcel polygons can cover full footprint geometry when the parcel query includes the entire building envelope. None of that yields usable floor area, external building volume or insured value.

Official existing register candidate `nl.kadaster.bag` in `landscape/sources-european-building-registers.json` is **not a new independent source**. The [BAG `verblijfsobject` OGC collection](https://api.pdok.nl/kadaster/bag/ogc/v2/collections/verblijfsobject?f=html) and its [official schema](https://api.pdok.nl/kadaster/bag/ogc/v2/collections/verblijfsobject/schema?f=html) expose:

- `oppervlakte`: unit usable surface area in **m²** (integer), not a building's footprint m², building gross floor area m² or building envelope volume m³.
- `pand`: an array of referenced building identities. One unit may be in **one or more** buildings; one building may contain many units. Relationship cardinality must be conserved, not forced to 1:1.
- `status`, `gebruiksdoel` and technical IDs, with address/house-number/postcode and other potentially identifying fields. **Do not acquire or store addresses, inhabitants, personal names or consumer-policy information** in CAT exposure discovery.
- BAG `pand` status `Pand in gebruik` and the unit's in-use status belong to different lifecycle entities; demolition/non-realisation and historic records must be excluded or retained as uncertain. A 'current' HTTP response timestamp does not prove the same underlying source-effective date.

**Research-only chain:** `BGT Bebouwing identificatie_bag_pnd → BAG pand identity → BAG verblijfsobject[].pand → eligible unit oppervlakte m²`. Note that `verblijfsobject` may span several `pand`, which cannot be automatically split without independent spatial/effective-date evidence. `identificatie` is an ID, not an address or ownership claim.

## Three new cost/pricing candidate metadata records

| Evidence | Exact original reference | Latest evidenced data | Valid role / hard limitation |
| --- | --- | --- | --- |
| CBS new-housing **input** construction-cost index | https://www.cbs.nl/nl-nl/cijfers/detail/85728NED | September 2026 provisional total `129.5`, base 2021=100; page changed 2026-10-30 | Dimensionless cost inflation/time ratio, not base rebuilding € per m² or per m³ |
| CBS new-housing **output** construction-price index | https://www.cbs.nl/nl-nl/cijfers/detail/85772NED | 2026 Q2 provisional `133.4`, base 2021=100; page changed 2026-09-30 | Alternative output-price trend (new housing incl. contractor overhead/margin, excludes land), **not** independent physical building valuation |
| AnsvarIdéa / Turien & Co **Herbouwwaardemeter 2026** | https://ansvar-idea.nl/media/0t1e1ifn/herbouwwaardemeter-2026-1.pdf | 2026-01 method valid through 2027-01-31 per PDF; 2025 Verbond base indexed with CBS data | Licensed-rights-unknown private insurer/adviser **€/m³** typology method for ordinary homes only; no bulk rate publication or CAT admission |

### Critical statistical/actuarial guardrails

1. **Building footprint ≠ unit usable floor area ≠ building gross area ≠ external m³ volume.** BAG unit area may omit common/ancillary areas. Do not treat total m² of flats as cubic volume or claim it equals insurable building area.
2. **Cost index ≠ price level.** Ratios may uplift an independently licensed comparable base cost across time *only when the series, component, dates, VAT and index-vintage definitions match*. A `2021=100` index with no price baseline cannot generate a € rebuilding value.
3. **Avoid double escalation.** The 2026 private insurer meter explicitly says its 2025 Verbond predecessor was already indexed with CBS figures. Applying the same 2025→2026 CBS uplift again to its 2026 rate would double-count inflation.
4. **Source independence:** CBS input and output indices are correlated construction-cost signals. They are useful for sensitivity, not two independent observations to multiply/average indiscriminately.
5. **Restricted typology:** The private 2026 PDF excludes unusual monumental, historic, very large, exceptional luxury housing. Do not apply to old canal buildings, industrial buildings or other nonstandard classes; specialist construction-cost data are needed.
6. **Tax/land value excluded.** A sale price, WOZ value, parcel value, legal Grundbuch title and rebuilding cost are different economic quantities. Land is not a building reconstruction claim.
7. **Rights review first.** CBS catalogue and original API rights/attribution must be reviewed per asset. The private insurer document is publicly viewable but does not license commercial copying, CAT calibration or redistribution of its pricing matrix. Only metadata/analytical discussion goes into Git.
8. **Insurer assignment last.** Neither BGT/BAG/CBS/insurer guide reveals which individual property is actually insured. Company-specific portfolio allocation, penetrations, deductibles and peril cover remain separate probabilistic model inputs requiring calibration and uncertainty.

## Implemented safe QA for many-to-many BAG unit-to-building links

`scripts/audit_bag_unit_area_multiplicity_v0.py` and `tests/test_audit_bag_unit_area_multiplicity_v0.py` use **fully invented normalised IDs and unit areas only**. Strict allowed fields are `as_of_date`, `buildings` (`pand_id`, `active`), `units` (`unit_id`, `area_m2`, `pand_ids[]`, `status`), plus a fixed schema label. The code does not fetch the real BAG API, ingest addresses or calculate €/m³ rates. Unexpected personal/address fields, duplicate identifiers, malformed areas and invalid statuses fail closed.

An explicitly illustrative synthetic example has 7 unit rows, 6 active unit rows, **340 m²** total active usable area counted once, and **170 m²** with unique links to an active building. The 170 m² difference remains unresolved due to cross-building units, unknown building reference, inactive building, or no link. This is an *attribution-conservation check*, not a measurement of Dutch housing or actual insurance exposures.

```sh
python -m unittest tests.test_audit_bag_unit_area_multiplicity_v0 -v
python scripts/audit_bag_unit_area_multiplicity_v0.py --input /private/synthetic-bag-units.json
python scripts/render_public_views.py --check
python scripts/check_all.py
```

**Do not merge or claim implemented empirical usable-area evaluation until CI passes.** Before requesting any real BAG `verblijfsobject` feature bytes, validate a provider-side field/projection filter that excludes all addresses and personal fields, record source rights, inspect one bounded non-personal response schema, and verify unit→pand links without publishing source IDs. Next: independently sourced residential volume and real replacement-cost baseline after a rights-review and expert-built benchmark, not by inventing rates.
