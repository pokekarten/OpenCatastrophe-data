<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Loing 2016: original water-depth evidence paths and synthetic interval-comparison runtime

**Research snapshot: 2026-11-04.** No event geospatial original bytes have been acquired or stored here. No real hazard calibration, insurer TIV, exposure, source approval or source-rights upgrade.

## A new building-depth research method exists upstream

An [official French government/Cerema Applisat Loing 2016 research case](https://www.applisat.fr/cas-utilisation/eau/determiner-hauteur-eau-bati-crue-du-loing-2016) describes a **building-proximity inundation-height method** from the exact May/June 2016 Loing flood. It used **Landsat optical + Radarsat-2 radar images**, classified visible flooded extent, and combined radar-inferred submerged/exposed buildings with a 3D **MNE / digital elevation surface**. The output divided buildings into **seven estimated surrounding-water-height categories, from less than 0.5 m to more than 3 m**. These are **remote-sensing-derived estimates**, neither original independently surveyed building losses nor insured claims, and not necessarily event-maximum depths.

The publicly reviewed page illustrates the output and links a **method summary PDF**, but **does not offer a verified machine-readable original building/polygon/depth dataset or source-specific commercial redistribution licence**. The exact **seven legend bin cutoffs are not established** by that page, so **do not create a guessed seven-to-four-depth-class crosswalk**. The underlying **Radarsat-2** image/data rights cannot be inferred from the public Applisat case page; a derived layer may have its own restrictions. The MNE source/vertical datum, acquisition instant, exact building footprint and calibration lineage must be verified separately.

This is distinct from the previously reviewed [DDT Loiret final 2021 reconstructed AZI depth atlas](loing2016-high-water-mark-ngf1969-azi-20261104.md): **four** published depth intervals (`0–0.5`, `0.5–1`, `1–2`, `>2` m), 1-m working grid and 500-m² polygon deletion, and possibly **overlapping flood marks, imagery or DEM**. An independent satellite-based method does not guarantee the produced samples are statistically or causally independent of the DDT model; upstream overlap must be assessed.

## A route to the original event GIS, not an open download claim

The official [2016 SPC Seine-Moyenne–Yonne–Loing retrospective](https://www.drieat.ile-de-france.developpement-durable.gouv.fr/IMG/pdf/rex4m_spc_smyl_mai_juin_2016_vf.pdf) explicitly planned production of **2016 Loing/Ouanne ZIP and ZICH polygons** and deposit into **VIGInond**. Later official [Loing Aval PPRI methodology](https://www.loiret.gouv.fr/contenu/telechargement/54071/372051/file/Annexe%203_20211116.pdf) explains that DRIEE/Cerema indeed delivered working geospatial data to DDT and that the DDT revised water surfaces and geometry. This establishes a historically described *producer-to-custodian chain*, **not** a currently located, externally downloadable, licensed original parcel-depth GIS ZIP.

Camptocamp's [SCHAPI QGIS-plugin technical case study](https://camptocamp.com/en/news-events/qgis-plugin-for-schapi) identifies three complementary tools:
- **CartoZI**: builds candidate flooded-zone geospatial layers with QGIS and GRASS-based algorithms;
- **VIGInond Format**: converts vector products into national **ZIP**, **ZICH**, **LIC** isocote line and **COM** commune schemas;
- **VIGInond INVITE**: browses and displays layers from the national VIGInond catalogue in QGIS.

These are useful *architecture pointers* for a reproducible open-source preprocessing chain; **this review has not identified a pinned open-weight model, a verified freely distributable source repository/release, or public guest access to the original Loing 2016 VIGInond ZIP/ZICH assets**. The [official DRIEAT VIGInond introduction](https://www.drieat.ile-de-france.developpement-durable.gouv.fr/atlas-phpc-a3582.html) describes national access for **crisis managers**. No authenticated access, bulk scrape, or provider original vector download was attempted. Do not substitute the later [open-licence Loing Aval PPRI regulatory WFS](https://www.data.gouv.fr/datasets/zone-dalea-du-ppri-de-la-vallee-du-loing-aval-departement-du-loiret) for that missing **observed-event reconstruction**.

**Actionable original-source request to DDT45/DRIEAT/SCHAPI or Cerema:** identify exactly the 2017 `68` high-water marks selected for reconstruction (per-record IDs), 2021 additions and corrections (including all auxiliary undocumented check points), the **original final 2021 2016-event** ZICH/LIC/ZIP or raster/gauge-independent water-surface datasets, original projection, vertical datum, source period and shapefile/GPKG details, checksum and download channel, provider terms for scientific/commercial reuse and redistribution, and the exact Cerema seven-bin output/imagery/DEM source and rights. Record written provider permission **before acquisition** where required. The public source docs alone cannot grant an open model release.

## Executed capability: synthetic depth-versus-provider interval diagnostic

A new [offline script](../../research_runners/loing2016_synthetic_depth_interval_compare_v0.py) exercises the **correct** computation for comparing a deterministic predicted flood depth with one of the **four 2021 DDT map depth classes**, by importing the [canonical validated class contract](../../research_runners/loing2016_azi_depth_class_semantics_v0.py) rather than inventing duplicate categorical truth. A predicted 1.6 m within `1–2` has **zero distance outside the provider's stated interval**, rather than an invented error to a fake 1.5-m point target. Predicted 2.4 m for class `1–2` lies **0.4 m above the class boundary**. The `>2` class has **no finite upper limit**; a predicted 4 m is not a 2.0-m error. An exact class boundary is labelled **endpoint inclusion unresolved**.

The script reports **synthetic-only distances outside the classified intervals** in metres. This is **not a probabilistic likelihood or independent holdout model-skill score**, and should **not** be minimized against the same flood marks or model inputs used to construct the published atlas. It does not certify spatial footprint, exclude underrepresented small flooded parcels, infer a water-depth midpoint or mark nonmapped areas as dry. The input permits only explicitly labelled synthetic cell IDs (`SYN_...`), finite nonnegative decimal predictions and the exact source 2021 edition; all external original bytes, GIS coordinates, real addresses and insurer/model admission claims are outside the allowed input contract.

A self-contained synthetic example (no external data) can be placed in a local JSON file:

```json
{
  "experiment": "SYNTHETIC_ONLY_NO_OBSERVED_PROVIDER_BYTES",
  "atlas_version": "DDT45_LOING_AVAL_AZI_2021",
  "event_id": "LOING_MAY_JUNE_2016",
  "synthetic_rows": [
    {"synthetic_cell_id": "SYN_A", "depth_class": "0.5-1", "predicted_depth_m": "0.700"},
    {"synthetic_cell_id": "SYN_B", "depth_class": "1-2", "predicted_depth_m": "2.400"},
    {"synthetic_cell_id": "SYN_C", "depth_class": ">2", "predicted_depth_m": "4.000"}
  ]
}
```

Run:

```sh
python research_runners/loing2016_synthetic_depth_interval_compare_v0.py --synthetic-json /local/example.json
python -m unittest discover -s tests -p 'test_loing2016_synthetic_depth_interval_compare_v0.py' -v
python scripts/check_all.py
```

The diagnostic would give **one out-of-interval synthetic cell**, **0.4 m total class-boundary distance**. Every science/rights/real-hazard/insured-loss gate remains false regardless of synthetically favourable agreement. **13** separate synthetic regression tests cover all four intervals, below/inside/above logic, open-top and uncertain endpoints, fake real source assertions, type and duplicate failures, numerical limits, and source-edition drift. Exact PR-head GitHub CI is still required.

## Next original-model readiness gates

**First actual local flood hazard pilot** should only proceed after obtaining official 2016 water-surface/DEM artefacts, 2017/2021 lineage and a valid redistribution licence. Then perform the physically meaningful equation *water-surface elevation (NGF69) minus terrain elevation (NGF69)* over the same time/support, with DEM accuracy and horizontal alignment explicitly checked. Quantify differences to independent 2016 field marks (not those used for reconstruction); report additional independent observational coverage including event imagery and no-data. Only then connect hazard to **2016-vintage buildings, valuation, vulnerability and insurance conditions** in the risk engine. Keep Gross/Net OEP/AEP curves out of scope until the event hazard and licensed exposure inputs are independently validated.
