<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin 2024/2026 insurance procurements: independent official TED XML source preflight

**Status (2026-11-05): two original official TED XML HTTP byte receipts observed and their exact SHA-256/byte counts now pinned for independent re-fetch; NOT a CAT model source admission.** This supplements [the prior Gewobag ADO and WBM property-segment research](berlin-gewobag-ado-wbm-2026-commercial-contract-segments.md), where the source claims were grounded in a 2024 issuer report and secondary public notice mirrors. The strongest available next verification is the exact primary EU TED source body, not a second portal copy.

## Publisher's original unambiguous download interface

The [TED European Publications Office developer guidance](https://ted.europa.eu/en/simap/developers-corner-for-reusers) and [original-XML download docs](https://docs.ted.europa.eu/ODS/latest/reuse/download-direct.html) explicitly document the direct URL scheme `https://ted.europa.eu/en/notice/{publication-number}/xml`.

| Official original XML | Issuer buyer + published subject to check | Known secondary evidence already researched | Not proven |
| --- | --- | --- | --- |
| [TED 558592-2024 XML](https://ted.europa.eu/en/notice/558592-2024/xml) | Gewobag, **Gebäudeversicherung**, issued 2024-09-13 | [Public notice](https://de.openprocurements.com/tender/2024-gebaudeversicherung-mkn/) with 2024 procurement 221-24, ADO side-contract vs existing Gewobag main property contract | An awardee, 2026 renewal, exact contract legal obligor, insurer split, site-level TIV, 2024 official XML SHA |
| [TED 668506-2026 XML](https://ted.europa.eu/en/notice/668506-2026/xml) | WBM, **Industrielle Sachversicherung für neun reine Gewerbeobjekte**, award notice 2026-09-29 | [Secondary award rendering](https://auftragsatlas.de/ausschreibung/industrielle-sachversicherung-fuer-reine-gewerbeobjekte-1172391) names HDI Global, Helvetia and R+V for nine purely commercial objects | Original eForms field-based awardee classification, actual three-way shares, exact object allocation, insurance premium/limit/TIV, XML SHA |

The two original publications are different: **2024 competition/tender is not a winner**; **2026 contract award** is for commercial property, not WBM's 2025 main residential company stock. An indexed *EUR 0* published award value is not a premium or an insured sum. The original eForms schema must be interpreted by explicit roles; mere occurrence of a legal company name anywhere in XML is **not enough** to assert it is an awarded underwriter.

## Offline and original source checks

```bash
python -m unittest discover -s tests -p 'test_ted_berlin_insurance_original_xml_preflight_v0.py' -v
python -m research_runners.ted_berlin_insurance_original_xml_preflight_v0
```

The [read-only runner](../../research_runners/ted_berlin_insurance_original_xml_preflight_v0.py) follows a strict *two-notice allowlist*, exact official HTTPS domain and path after redirects, bounded response bytes, XML-only parsing with DTD/ENTITY refusal, expected buyer/product text markers, and an ephemeral SHA-256 of the exact original HTTP body. **No raw source XML is written to the repository or echoed**; only size, hash, document root and bounded PASS/fail metadata are printed. Code semantics explicitly reject insurer contract, insured site location and TIV assertions from this source preflight.

There are two separate verification levels:

- **First independent retrieval:** if the official endpoint returns complete expected XML, output includes observed original `sha256` and byte count; the flags `original_sha256_immutable_pin_verified=false` and `original_byte_count_immutable_pin_verified=false` remain **false**. That is **source discovery**, not pinned immutable provenance. Source publication number in body is disclosed as observed true/false rather than invented.
- **Next controlled pin:** independently review the exact original eForms source, its publication ID, XML schema/awardee element roles and rights; only then set the two fixed expected SHA/byte counts, re-fetch original bytes and require exact SHA/size and semantic matches in a second run. Cross-validate the buyer, awardee roles, lot and dates from original elements, then add a versioned typed observation. Do not assume a secondary index's winner list is verified by presence of names alone.

The [dedicated GitHub Action](../../.github/workflows/berlin-insurance-ted-original-xml-preflight.yml) executes synthetic negative tests before attempting a live public publisher fetch. **PR network failures do not falsely become source verification:** the live step is explicitly non-blocking for PR builds because of external-source availability; manually dispatched runs are strict. CI green therefore means the source parser/tests work, not necessarily that TED served a valid original notice. This is separate from normal repository CI.

**Source rights:** TED is public for reuse via its documented interfaces, subject to current fair use and licence terms; the tool does not store or redistribute original data bytes or individual insured customer/asset identifiers. One publication notices cannot be converted into actual insurance exposure, reinsurance programme or insurer market share on their own.

## Live GitHub Action source availability findings, 2026-11-05

The first original publisher HTTPS attempts from GitHub Actions **did not retrieve original XML**. Both the individual `/en/notice/{number}/xml` path and original daily archive `/packages/notice/daily/{yyyy+issue}` returned **HTTP 202 Accepted**, not the requested body. The first two offline synthetic verification suites (18 + 14 tests) passed; because the live steps were explicitly nonblocking in pull requests, green workflow status by itself is **not original source acquisition**. The subsequent direct original XML retrieval on the same PR **succeeded**, as recorded separately below. The older source register in #1359 remains truthful about checks performed during *that earlier* run.

The [official TED Search API](https://docs.ted.europa.eu/api/latest/search.html) supplies an independent third publisher path: unauthenticated `POST https://api.ted.europa.eu/v3/notices/search` with `query: publication-number = 668506-2026`, bounded fields and source-only exact match. The [read-only Search API preflight](../../research_runners/ted_berlin_insurance_search_api_preflight_v0.py) and offline tests independently check exact publication number, buyer and subject and emit only source JSON receipt SHA and size. **Even successful Search API responses establish original publisher metadata, not an original eForms XML body or who carries each insured risk.** A source API response is not accepted if it returns HTTP 202, a malformed/duplicate JSON field, multiple matches or mismatching buyer/title.

The [separate official daily ZIP alternative](../../research_runners/ted_berlin_insurance_daily_xml_preflight_v0.py) only selects one matching XML member from OJ S **181/2024** and **188/2026**, checks publisher archive hashes and exact extracted XML, and refuses ZIP bombs, duplicate notice members or corrupted archives. It does not unzip a bulk source archive to disk. The source may remain inaccessible from GitHub's network even though public EU documentation describes it. Do not modify this result to imply full original provider verification while access returns 202.

A new future publisher download attempt should be independently verified as a **complete HTTP 200 response** with exact extracted original bytes and notice-number/format semantics. If all EU official paths remain blocked, retain the source as **research-only** and do not ingest secondary mirrored notices as if they were primary, even if the secondary metadata is useful for research.

## First exact source retrieval succeeded after initial HTTP 202 (2026-11-05)

The official XML acquisition step in [GitHub Actions run 42025930149](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42025930149) eventually returned **both complete publisher eForms XML documents** with exact notice-number literal, expected buyer/title and XML document root. The evidence was printed as *metadata receipts only* (no original XML bytes stored or printed):

| Notice | XML root | Exact original bytes | SHA-256 of complete official HTTP source body |
| --- | --- | ---: | --- |
| 558592-2024 | `ContractNotice` | 39,733 | `51698e01c01caa9a0c58d41baf161d73a585d3b30f3b3dba12d95a3859b56b2f` |
| 668506-2026 | `ContractAwardNotice` | 21,837 | `7650720183d0c26430e0433858bf2e8b854ea68bb93fbf679e96ee696ee8fc78` |

These exact observed values have now been reviewed for notice identity and entered into the source preflight's **fixed SHA-256 and byte-count pins**. Subsequent successful GitHub Action fetches must match them **exactly**, not just return HTTP 200. The direct source checks still **do not establish** exact eForms role-level winner/consortium allocations, insured building sites, 2026 Gewobag contract continuity, premiums, insured value or loss.

The first metadata run's *separate* Search API synthetic test job exposed three fixtures shorter than the input boundary; those fixtures were corrected without lowering the response-size limit. Preserve distinct outcomes: initial 202 blocked; later original XML body acquired; pinned re-fetch check pending until successful exact-head run.

## Bounded official HTTP 202 polling (2026-11-05)

For both original TED notices, repeated exact official `/en/notice/{number}/xml` requests sometimes returned **HTTP 202 Accepted** instead of XML, despite one successful exact-original HTTP 200 and first SHA/size capture. The [public TED download documentation](https://docs.ted.europa.eu/ODS/latest/reuse/download-direct.html) establishes the direct URL scheme but does not guarantee immediate 200 availability or document an issuer-specific waiting schedule. **HTTP 202 does not count as original XML.** The dedicated [source fetcher](../../research_runners/ted_berlin_insurance_original_xml_preflight_v0.py) now retries *only* a 202 response, at most four total exact-URL attempts (three additional retries) and at most 5 seconds of default pacing per notice (or a capped 0–2-second numeric `Retry-After`). Other HTTP results, redirect to a different URL/domain, addition of a query string, oversized/truncated downloads, malformed XML, wrong subject/buyer, or a mismatched original SHA/byte count still **block immediately**. All requests are strictly the previously approved official TED HTTPS notice paths; no mirrors, guessed endpoints, arbitrary redirect targets, new source numbers or public publisher data bytes are admitted.

The 19 extra [no-network retry regressions](../../tests/test_ted_berlin_insurance_original_http202_retry_v0.py) cover 202→200, four consecutive 202s, 206/404 terminal refusal, unexpected redirect, bounded header delays, fake HTML/partial/oversized response, original SHA mismatch, invalid retry budget, independent original notice identity, and protection against interpreting the 202 body as XML. No retry result changes the source-science classification: original award-role extraction is only evidence when its own runner actually fetches a complete 200 XML that *matches the previously pinned exact original SHA and byte count*, and then passes the role/lot/contract graph checks. A synthetic test or workflow green state is never proof of those live conditions.

**Next validation:** inspect the updated GitHub Actions run's actual original-XML and [WBM contract-award role](berlin-wbm-2026-ted-eforms-winner-role-v0.md) steps separately. Do not infer a fresh awarded-party proof from offline tests or the advisory/continue-on-error live steps.

## Correcting the official Search API fallback from validation to retrieval (2026-11-05)

A follow-up review of [European Publications Office Search API documentation](https://docs.ted.europa.eu/ODS/latest/reuse/search-api.html) and its [official reusers workshop examples](https://op.europa.eu/en/web/ted-reusers-workshops/questions_and_answers_2023_12_14) identified a separate preflight bug: the historical reader sent `checkQuerySyntax: true`, instructing the API to **validate query syntax without searching**. Its empty `notices` list was therefore not a credible absence of the named notice. This flag has been corrected to `false`, with `onlyLatestVersions: false` explicitly selected, while keeping **exact publication-number filtering, first page, maximum two result rows, restricted metadata fields and scope ALL**. A response explicitly marked as a syntax-only validation (`totalNoticeCount=null`) or timed out is now refused as research evidence; one exact matching published notice and buyer/title are still required.

The official **Search API response is structured secondary metadata delivered by the primary EU publisher**, not a complete original eForms XML file. Even when its exact notice metadata is successfully fetched, it does **not** satisfy the separately pinned direct XML SHA/byte proof, the WBM contract→winning tender role chain, individual risk values, coinsurance shares or model exposure admission. The Search API response is not written to GitHub; the bounded metadata receipt includes only the source JSON SHA and byte size. The 17 offline Search API tests now include distinct validation-only and timeout fail-closed cases.

**Follow-up:** assess the actual successful/failed Search API call in the exact-head GitHub Actions logs. A green nonblocking workflow alone is not positive provider-source evidence.

## Successful official TED Search API exact-publication receipts (2026-11-05)

The corrected `checkQuerySyntax: false` query succeeded on [GitHub Actions run 42036609295](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42036609295) for **both exact official TED publication numbers**, returning one buyer/title-matching publisher metadata record each. These are original structured TED publisher API responses, **not the original eForms XML bytes**:

| Notice | Original API JSON response bytes | SHA-256 of complete API JSON response | Scope |
| --- | ---: | --- | --- |
| `558592-2024` (Gewobag property insurance tender) | 6,832 | `766921588c53b468fe9ea9e55125a77e2c90625e095befae081db592ddee922f` | One exact publication and matching Gewobag buyer/title |
| `668506-2026` (WBM nine-commercial-object award) | 7,127 | `cdb17ef87ecc977e76b4bf5ba0141cc90cb698cbb4024157d7591561d6db7473` | One exact publication and matching WBM buyer/title |

The API JSON response may change across index refreshes, so the JSON SHA values are **dated audit receipts**, not asserted immutable publisher-file pins or a proof of unchanging metadata. In the same run the direct original XML and the WBM structural eForms winner-role extraction still returned `HTTP 202 Accepted` after exhausting four strictly bounded attempts per request; the official daily archive also returned HTTP 202. Thus **official publication metadata is confirmed, but the live original XML role graph and actual insurer contract-participation shares remain unconfirmed**. This difference is enforced in the code and in the displayed receipt flags.

## Later exact original XML replay succeeded (2026-11-05)

The earlier HTTP 202 availability limitation was **intermittent, not permanent**. On [Actions run 42091432185](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42091432185), the original publisher successfully returned *both* complete source XML files and their immutable source checks passed again: Gewobag 558592-2024, 39,733 bytes, SHA-256 `51698e01c01caa9a0c58d41baf161d73a585d3b30f3b3dba12d95a3859b56b2f`; WBM 668506-2026, 21,837 bytes, SHA-256 `7650720183d0c26430e0433858bf2e8b854ea68bb93fbf679e96ee696ee8fc78`. The corrected WBM original source winner/contract parser was also successful, confirming **three distinct settled contracts / winning organizations in the same technical lot**, recorded in [the official graph receipt](../../research/observations/ted_wbm_2026_original_eforms_award_graph_receipt_v0.toml).

The old error observations (HTTP 202) remain historically correct; this later successful run is separately dated to avoid accidentally calling the publisher consistently available. Original XML still contains **no verified per-carrier co-insurance shares, risk sites, insured TIV or operative signed policy schedule**. The official daily ZIP alternative returned HTTP 404 in this run and is not an evidence source.
