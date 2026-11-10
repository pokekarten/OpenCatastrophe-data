<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EA flood-depth original catalogue receipt and BfG/EA licence boundary (2026-11-10)

**Scope:** Original publisher **metadata only** for three England Environment Agency
flood-depth catalogues, and newly confirmed source-specific reuse constraints.
No actual flood geometries, cell/depth measurements, archive/ZIP downloads,
API feature calls, insurer/customer details or model inputs were acquired.

## Original catalogue bytes: reproducible receipt

Three **uncached** read-only original HTTP response bodies were fetched via a
third-party HTTP transport from `https://data.gov.uk/api/action/package_show?id=...`,
with final publisher-side URL
`https://ckan.publishing.service.gov.uk/api/action/package_show?id=...`.
Transport reported `application/json;charset=utf-8`. The complete response
body bytes were obtained but **not copied into Git**. SHA-256 calculation was
verified against standard empty-string and `abc` test vectors first.

The authoritative repository machine-checkable receipt table is
[`OBSERVED_ORIGINAL_METADATA_RECEIPTS`](../../scripts/preflight_ea_flood_ckan_v0.py);
it contains exact **byte counts and SHA-256 digests** for the three selectors
`river_present`, `river_climate` and `surface_present`.
The measured receipt totals are 3 original metadata responses and 20 resource
identities (8 present-day river/sea, 8 climate river/sea, 4 present-day pluvial).

| Fixed dataset | Original source identity | Provider metadata_modified | Resource IDs |
| --- | --- | --- | ---: |
| river_present | `e4698ae1-184b-4b5d-801a-90364a93e229` | `2026-10-30T14:00:39.007132` | 8 |
| river_climate | `67a734bb-2b7b-491a-aafd-3f7e52c8d7f3` | `2026-10-30T14:00:37.670274` | 8 |
| surface_present | `b0bbfacf-ccf7-4ed9-a94c-be18d91c258d` | `2026-07-06T07:10:48.657123` | 4 |

Each result had `success=true`, exact dataset identity, `private=false`,
`isopen=false`, `license_id=null`, and catalogue
`extras.licence=["Open Government Licence"]`. Do **not** reinterpret the
`isopen` field as evidence of licence grant, nor assume that an empty top-level
CKAN licence ID negates the separately published dataset licence statement.
The actual resource UUID/name/format/URL lists match the frozen source profile
in the above preflight. No provider assets were followed.

**Reproducibility:** A legitimately saved original response byte stream can be
checked offline (and only offline) with:

```sh
python scripts/preflight_ea_flood_ckan_v0.py --dataset river_present --input /private/path/ea-ckan-response.json
```

The preflight checks identity, version, licence label, exact 20 frozen resource
references, UTF-8 JSON, duplicate-key safety and raw-byte hash. Its boolean
`matches_observed_original_metadata_receipt` means **identical bytes to this
specific retrieved response**, not cryptographically authenticated publisher
identity. Any new payload or provider release must be separately reviewed;
the checker must never fetch, return, persist or execute resource URLs.

Publisher CKAN URLs:
- [England river/sea present day](https://data.gov.uk/api/action/package_show?id=e4698ae1-184b-4b5d-801a-90364a93e229)
- [England river/sea climate change](https://data.gov.uk/api/action/package_show?id=67a734bb-2b7b-491a-aafd-3f7e52c8d7f3)
- [England pluvial present day](https://data.gov.uk/api/action/package_show?id=b0bbfacf-ccf7-4ed9-a94c-be18d91c258d)

## United Kingdom: positive rights evidence; actual data admission still blocked

The [National Archives Open Government Licence v3](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
permits commercial reuse and adaptations of materials expressly licensed under
it, with required attribution and exceptions for third-party rights.
Defra's [Data Services Platform licence guidance](https://environment.data.gov.uk/support/faqs/275874594/275874729)
warns that **individual product licensing and special use constraints** must
be checked separately. The three exact EA data.gov.uk product pages list OGL.
This is strong **published licence evidence**, not a blanket approval for every
asset or every linked endpoint, derived map, upstream Ordnance Survey component,
bulk download or insured-property intersection.

The [DSP Fair Use Policy](https://dsp.environment.data.gov.uk/support/faqs/275808874/1169555459)
explicitly allows apps and legitimate automated data/API use, subject to fair
use and rates subject to change. Its published indicative ceilings are
200 requests/minute for standard/system-to-system use and 10 requests/minute
for web bots. **Do not treat the published ceilings as a quota assigned to
OpenCatastrophe**, a mandate to crawl, or a source-specific automation approval;
the DSP [Terms and Conditions](https://environment.data.gov.uk/support/faqs/275811163/275811177)
and exact data product licence still apply.

**Scientific block:** all datasets describe *area-level scenario depth bands*
rather than an insured building's measured flood depth. England river/sea
present day, climate-change and pluvial products share some upstream lineage.
`Unavailable` must never become zero depth, and defended vs undefended
must not be treated as independent stochastic events. This evidence cannot
produce a calibrated occurrence event catalogue, damage ratio, OEP or AEP.

## Germany: BfG related source has materially different constraints

[MDI-DE's original BfG Überflutungstiefen record](https://nokis.mdi-de-dienste.org/trefferanzeige?docuuid=51bc5f69-c33b-4f39-a13b-348b7801f6fe)
publishes **GeoNutzV** reuse conditions, required attribution to
`WasserBLIcK/BfG & Zuständige Behörden der Länder` with date, and reports
free commercial/non-commercial use **subject to some Länder access restrictions**.
It also states national completeness is not assured, generalized data may be
unsuitable for parcel-scale assessment, nominal mapping scale is
approximately 1:25,000, and native spatial reference is EPSG:3035.

**Critical provenance distinction:** the MDI-DE record links the older-looking
`/ueberflutungstiefen/servicefeed.xml` while our candidate for the newer
third-cycle reporting product references
`/ueberflutungstiefen-2025/servicefeed.xml`.
They are **not verified to be the same exact asset, licence, vintage or layer**
and must not be conflated. The [third-cycle GovData listing](https://data.gov.de/suche/daten/uberflutungstiefen-de-hochwasserrisikomanagement-rl-3-zyklus-2022-2027)
is the relevant catalogue but a successful direct original service-feed
read/asset receipt remains missing. The combined `T_class` value includes
area-type and depth-class digits; it is not a property water depth or loss.

## Acceptance / next smallest action

1. **Done:** metadata byte-size/SHA-256 original-response receipts for the
   three EA CKAN catalogues, code-frozen and offline-checkable; official
   provider licence/fair-use conditions and BfG restrictions located.
2. **Not done:** original EA WFS/WMS/OGC capabilities/body receipt or GIS
   feature sample; review of exact linked spatial asset licences/service terms;
   exact BfG 2025 service feed and rights; flood-value/unit/CRS verification;
   source admission, asset publication or production model use.
3. **Proposed bounded next step:** select only *one* published EA 2026
   OGL-marked WFS/OGC service after source-specific legal/technical review,
   obtain one limited original capability document (no feature records),
   pin final URL and content SHA-256, then investigate a synthetic-only
   `Unavailable`/AEP/defence/CRS schema validator. Keep this PR Draft until
   genuine data admission evidence permits promotion.

## Follow-up: 3.3% defended depth scenarios (2026-11-10)

The [EA present-day 3.3% AEP depth product](https://www.data.gov.uk/dataset/2b1dc7a4-ff9f-42fd-9971-11638eabf814/rivers-and-sea-3-3-defended-flood-risk-depths-present-day)
and corresponding [climate-change 3.3% AEP depth product](https://www.data.gov.uk/dataset/9d5e56d5-7713-42a1-890f-3d0a3e895cd5/rivers-and-sea-3-3-defended-flood-risk-depths-climate-change)
were confirmed from the original publisher's CKAN catalogue metadata. They
contribute **two more fixed catalogues** and 18 separate resource UUIDs,
bringing the exact metadata snapshot coverage to **5 CKAN products / 38
resource metadata records**.

| Fixed selector | Publisher CKAN package UUID | Catalogue modified | Original JSON bytes | Exact raw SHA-256 |
| --- | --- | --- | ---: | --- |
| `river_3p3_present` | `2b1dc7a4-ff9f-42fd-9971-11638eabf814` | `2026-10-30T14:00:33.438078` | 13959 | `64d01c89e24c82e7c9384f1a8a2762ddc065890bbbff81e19e16bc4fc8a32857` |
| `river_3p3_climate` | `9d5e56d5-7713-42a1-890f-3d0a3e895cd5` | `2026-10-30T14:00:32.171469` | 15093 | `15ba47630e376659d3c22dcdcd72ac504e3ee5ff8b150b0491e5613848e3e1fa` |

Two original uncached publisher CKAN JSON response bodies were retrieved
through an external HTTP transport. Both redirected to
`https://ckan.publishing.service.gov.uk/api/action/package_show?id=...`
and carried `application/json;charset=utf-8`. As with the original three
datasets, hash equality supports *exact byte replay only* and does not
authenticate an arbitrary payload or authorize following 18 linked resources.
No response bodies or ZIP assets are committed. The separately frozen asset
identity and resource naming are in
[`scripts/preflight_ea_flood_ckan_v0.py`](../../scripts/preflight_ea_flood_ckan_v0.py).
Metadata-only access and unreviewed rights are recorded in
[`access/uk.ea.flood-depth-3p3.ckan.2026.json`](../../access/uk.ea.flood-depth-3p3.ckan.2026.json).

**Scientific scope:** 3.3% AEP (approximately 1 in 30 per year) is a
scenario-probability label, *not* annual loss frequency inferred from a
stochastic flood event catalogue. Both products are defended-only;
there is no undefended 3.3% scenario in these particular packages, and
defence failure is not modelled. The current and RCP8.5 climate scenarios
have shared national modelling lineage, not independent evidence. Depth
classes are not precise building-ground-level inundation measurements.
Unavailable national coverage remains explicitly missing. Do not use these
products to construct event counts, AEP/OEP or per-property vulnerability
parameters before asset and scientific checks.
