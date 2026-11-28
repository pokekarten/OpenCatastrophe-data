<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# European wind: observed impact and independent hazard validation preflight

Research date: 2026-11-05. Companion to CLIMK original Kyrill damage preview PR #1361 and NextGen conditional two-state/dependence tests PR #280. **No source dataset downloaded, licensed bulk extract accepted, observed impact fitted, country insured portfolio inferred or annual AEP/OEP produced here.** This is a source-access and *semantic* preflight.

## Why a single real footprint is insufficient

The source-pinned CLIMK-WINDS v2 ERA5 storm index 0 represents historical KYRILL with modelled maximum gust, NOT observed insurer or building losses. Both invented synthetic site markers are in the same ERA5 grid cell, so one source event cannot estimate correlation between spatially separated buildings or annual event frequency. Its 50 selected extreme winter storms are a selected set, not a representative independent annual event process.

The literature cross-comparison [*Windstorm losses in Europe – What to gain from damage datasets* (2024)](https://doi.org/10.1016/j.wace.2024.100661) studies 94 storm events across 21 European countries, October 1999–March 2022: only 11 storms appear in all five impact sources, and about 60% appear in only one. Study data are **available on request**; **not an openly licensed ingestible training CSV on this evidence**. It explicitly warns against treating one modelled/reported loss dataset as loss ground truth. Use source intersections and held-out cross-source ranking/uncertainty, not single-benchmark target fitting.

## Source matrix: what each can and cannot identify

| Candidate | Primary link | Observational role | Access / rights gate | What it CANNOT identify |
|---|---|---|---|---|
| DWD CDC historical hourly wind station data | https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/wind/historical/ | Station-measured hourly wind conditions and station metadata; potential independent **physical** validation and Kyrill timing checks in Germany | Directory publicly browsable; download terms/individual variables, station continuity and licence require exact review; public directory is not source admission | Not insurer building losses, not conditional damage correlation; hourly mean wind should not be equated to ERA5 storm maximum gust or 3-second gust without variable/time-height semantics |
| ESWD (ESSL) | https://www.essl.org/cms/european-severe-weather-database/ and https://eswd.eu/en/signup | Quality-controlled *reported* severe-convective event/damage observations; event identity and geographically localized reports may support independent **event impact occurrence** checks, with reporting bias | Public use under user agreement; general commercial use not allowed; public account at most 25 reports at a time, no public CSV/bulk export; seek authorized license for larger/professional access; **do not automate scraping** | Not a complete all-winter extra-tropical cyclone exposure census or insured damage ratio; missing reports are not non-events |
| EM-DAT public disaster records | https://doc.emdat.be/docs/data-accessibility/ | Event/country-level reported disaster impacts, possible high-level cross-source event and country validation | Free registration for **non-commercial** use, commercial annual subscription; do not mirror without permitted use | Not asset-level physical damage, wind field, company losses, building correlations or exact insurer policy terms |
| EEA economic climate-extreme losses | https://www.eea.europa.eu/en/datahub/datahubitem-view/77389680-ecd2-4f56-926f-8106061a5570 | Country/period macro-economic climate-hazard loss context; 1980–2024 dataset, March 2026 publication | Published EU/EEA download; verify exact XLSX provenance, reuse licence, inflation/revaluation and peril mappings before ingestion | Not original/retained insurer losses or damage state per asset; annual country totals cannot calibrate building-level storm vulnerability correlation |
| 2024 academic cross-source paper | https://doi.org/10.1016/j.wace.2024.100661 | Methodological audit of inter-dataset event matches and loss-range disagreement | Paper open access, underlying data **on request**; independent rights for each embedded data provider | Does not supply a ready-to-use observed asset-level damage sample; cannot import referenced insurer losses without rights |

## Next implementable science gates (no fictional observations)

1. **Hazard holdout, physically measured**: select at least two spatially distinct DWD stations with original station-history and suitable measured gust fields, and obtain a time-appropriate wind footprint. Verify 2007 observation completeness, height/time statistic, UTC/local conventions, outages, geographic spacing, reanalysis interpolation and stationary vs moved instruments. DWD hourly mean wind cannot silently be substituted for a 3-second or instantaneous maximum gust.
2. **Loss holdout at the right economic basis**: obtain rights-cleared event-level storm impact or insured claim data with explicit country/peril, covered asset classes, EUR year/currency and exposure denominator. EM-DAT and EEA aggregate context may test event/rank/season patterns only; ESWD reports test observed occurrence and geographic impact patterns, not zero-report observations.
3. **Separate datasets and error layers**: distinct train/validation events, split spatial blocks to avoid leakage, source/provider crosswalks, damage ratio denominators, event-ID matching uncertainty, event detection bias and independent observation uncertainty. Never identify case-by-case latent insured losses from annual aggregate reports.
4. **Fit joint damage only after independent damage labels**: estimate marginal building vulnerability by taxonomy/height/gust, then spatial conditional dependence at multiple source grid cells and events. At least two spatially distinct measured sites and many events are necessary; one KYRILL grid value at two fictional sites identifies no correlation parameter. The 0..1 Bernoulli parameter in NextGen PR #280 is still an authored sensitivity.
5. **Frequency and annual CAT separated**: source representative annually complete physical events, explicitly including zero-event years, with choice of annual sampling measure; C3S regional event-intersection counts must not be double-counted as globally independent storms. Only then integrate a separately calibrated severity/dependence law through unchanged policy / Inward / Retro into annual Gross/Net AAL, AEP and OEP.

## Status and rights

All sources above are **candidates only**. Original data bytes and explicit licence decisions are absent here; none may be called independently validated historical building-level insurer losses. Public URL is not permission for automated redistribution. No downloads, accounts, dataset registration, DB mutations, model parameter or current CI requirements have been changed by this document. Keep PR #1361 Draft and use separate provenance receipts for each future source.
