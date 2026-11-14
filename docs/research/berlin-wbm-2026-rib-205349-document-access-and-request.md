<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WBM 2026 – original procurement documents: public RIB tender 205349

Research observation: **2026-11-05**, read-only, outside of the TED index.

## Official document route and current access limit

The WBM April original publication [TED 286307-2026](https://ted.europa.eu/en/notice/286307-2026) links to the **official Berliner Vergabeplattform RIB tender `205349`**, platform `2`:

[Public RIB tender details (205349)](https://www.meinauftrag.rib.de/public/DetailsByPlatformIdAndTenderId/platformId/2/tenderId/205349)

When this exact link was inspected using the connected Exa public rendered webpage retrieval on **2026-11-05**, the provider displayed the English message **“Announcement not found”** and said the desired announcement was **no longer publicly available**. This was *rendered page content*, **not a byte-for-byte pinned HTTP response**: no HTTP-body SHA, original attachment bytes, policy schedule or object addresses were obtained. The [dated observation](../../research/observations/wbm_2026_rib_205349_public_access_v0.toml) explicitly records that limitation.

The [WBM procurement site](https://www.wbm.de/unternehmen/ausschreibungen/) states that the WBM group carries out procurement using the **Land Berlin procurement platform**, and publishes a public procurement contact **vergabe@wbm.de**. The [official Berlin procurement help page](https://www.berlin.de/vergabeplattform/ueber-die-vergabeplattform/download-von-unterlagen/) says documents for current procedures may be viewed without registration; registration may be required for **editable bidder documents, updates and submission**. That **does not promise perpetual availability after tender expiry**.

The [new bounded RIB public-access checker](../../research_runners/wbm_rib_205349_public_documents_preflight_v0.py) requests only the exact, approved public HTTPS URL **without login or cookies**, with a 750k-byte limit. It classifies explicit expired notice text separately from an HTTP 404/410 and a dynamic JavaScript page whose actual contents cannot be inspected by an HTML-only client. Even if public metadata becomes visible, the checker does **not** claim downloadable attachments or the signed insurance schedule without an independent original-file download and review. [17 no-network tests](../../tests/test_wbm_rib_205349_public_documents_preflight_v0.py) and [7 research receipt guards](../../tests/test_wbm_rib_205349_public_access_observation_v0.py) prevent a plausible but false success.

**Result:** This public portal URL is a genuine route to investigate an April RIB notice, but **we have not accessed its current tender attachment inventory**. No file titles, downloadable document SHA, per-building address, insured TIV, current policy participation or insurer CAT exposure may be filled from the expired page. The 0.01 EUR nominal amount in the September TED award publication is **not an actual actuarial premium, insured sum or declared economic valuation**. Do not calibrate any CAT loss or carrier market share to it.

## Distinct official-source publication identities

The following are separately verified in our TED repo research:

| Document | Official notice ID | Indexed eForms BT-04 procedure UUID | Data role |
| --- | --- | --- | --- |
| Competition, 27 April 2026 | `286307-2026` | `7df98c35-4cae-41ff-8385-141125426a4a` | Tender requirement and published link to RIB 205349 |
| Award, 29 September 2026 | `668506-2026` | `0988b2e4-9489-4b3b-9487-cd3a2a624cf5` | Official original awarded company-contract edges and published BT-150 **50/40/10 identifier text** |

Both publications bear buyer reference **`VV 2026-0069`** and similar subject descriptions. That is a *research lead* to ask the contracting authority for the actual legal publication chain; **matching internal identifiers alone do not override different published BT-04 UUIDs**. The [official Search API study](berlin-wbm-2026-ted-bt04-procedure-lineage.md) and [indexed family scan](berlin-wbm-2026-ted-procedure-family-discovery.md) found no additional notice under either BT-04 UUID on 2026-11-05. The exact original XML re-fetch of both simultaneously has intermittently failed with HTTP 202.

The April advertised **30% minimum lead, 15% minimum follower and last-residual below-minimum exception** are evidenced for April only and cannot be asserted as the legal September award criteria until procedure linkage is independently established. The official September BT-150 *labels* read 50% HDI, 40% Helvetia, 10% R+V, but these **are not a fully reviewed signed policy schedule**. There is no source-verified allocation of the nine commercial buildings to any one insurer.

## External document discovery and permission boundaries

Public provider index pages consulted include [WBM's official procurement page](https://www.wbm.de/unternehmen/ausschreibungen/), [the Land Berlin tender-download guide](https://www.berlin.de/vergabeplattform/ueber-die-vergabeplattform/download-von-unterlagen/), and [the RIB expired public tender URL](https://www.meinauftrag.rib.de/public/DetailsByPlatformIdAndTenderId/platformId/2/tenderId/205349). Third-party summaries such as [VergabeHero](https://vergabehero.eu/ausschreibungen/industrielle-sachversicherung-fuer-neun-gewerbeobjekte--cmum5i6eq05jksrdnjweftyk6) expressly report that they do **not** possess downloaded public tender files. We **did not discover** a verified public PDF, contract annex, signed final coinsurance schedule or list of nine insured risk locations during this access check. No invented attachment links.

**Next evidence priority:** Seek a public source for the complete insurance tender document index and source revisions, and formally ask WBM to clarify the two BT-04 IDs and whether **redacted/releasable** terms or aggregated commercial risk measures can be shared. Do not bypass a portal, use bidder logins, or redistribute protected policyholder/property risk details.

## Human-review-only request draft — NOT SENT

**Recipient:** WBM Zentraler Einkauf, **vergabe@wbm.de** (publicly listed by WBM)

**Subject:** Rückfrage zu Vergabe VV 2026-0069 – Bekanntmachungsbezug und öffentlich zugängliche Unterlagen

Guten Tag,

wir recherchieren öffentlich zugängliche Informationen zur industriellen Sachversicherung für neun Gewerbeobjekte der WBM (interne Kennung `VV 2026-0069`). Hierzu finden wir die TED-Bekanntmachungen `286307-2026` vom 27. April und `668506-2026` vom 29. September 2026. Beide nennen dieselbe interne Kennung, aber unterschiedliche globale eForms-Verfahrenskennungen (BT-04).

Können Sie uns bitte mitteilen, ob beide Bekanntmachungen zum selben Vergabeverfahren gehören und ob es eine amtliche Berichtigung bzw. eine weitere Verknüpfungsbekanntmachung gibt? Der in der April-Bekanntmachung angegebene RIB-Link zum Verfahren `205349` wird uns derzeit als nicht mehr öffentlich verfügbar angezeigt. Gibt es einen weiterhin öffentlich zugänglichen Dokumentenindex oder freigegebene Vergabeunterlagen (z. B. Leistungsbeschreibung und Mindestversicherungsbedingungen)?

Für eine wissenschaftliche Risikomodellierung interessieren uns zudem **nur soweit freigegeben oder anonymisiert erhältlich** die tatsächlich vereinbarten Konsortialanteile bzw. eine allgemein zugängliche Vertragsübersicht und gegebenenfalls **aggregierte** Angaben zu den gewerblichen Gebäudearten, Regionen und Versicherungswertgrößen. Schutzbedürftige Adressen, interne Sicherheitsunterlagen, personenbezogene Angaben oder vertrauliche Angebotsunterlagen benötigen wir nicht.

Vielen Dank für Ihren Hinweis auf die zuständige Auskunftsstelle oder eine öffentliche Fundstelle.

Mit freundlichen Grüßen

*Absender vor Versand ergänzen.*

---

**Status:** Draft only. This research project has not sent this message, obtained private documents, or received confirmation from WBM.
