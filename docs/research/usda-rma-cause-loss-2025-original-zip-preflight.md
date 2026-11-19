<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# USDA RMA 2025 Cause of Loss: offline original ZIP and 30-field receipt

**Status:** research-only, *not* a source admission, not a live provider
acquisition and not an approved catastrophe-loss or insurance-exposure input.

## Exact official source identity

- Publisher: [US Department of Agriculture – Risk Management Agency (RMA)](https://www.rma.usda.gov/tools-reports/summary-of-business/cause-loss)
- Source release link: [colsom_2025.zip](https://pubfs-rma.fpac.usda.gov/pub/Web_Data_Files/Summary_of_Business/cause_of_loss/colsom_2025.zip)
- Field definitions: [Cause of Loss Information – Summary of Business Data, all-years layout, as of May 28, 2026](https://pubfs-rma.fpac.usda.gov/pub/Web_Data_Files/Summary_of_Business/cause_of_loss/COL_Summary_of_Business_with_Month_All_Years.pdf)
- Registered source candidate: \`usda.rma.crop-cause-of-loss-summary.2026\` in \`landscape/sources-search-followup-20261115.json\`.
- ZIP discovery and record-layout descriptions were independently reviewed on November 15, 2026. The binary link was not acquired, so **no original provider HTTP response, original ZIP SHA-256, real row count or source scientific pass is claimed**.

The publisher states that each yearly ZIP contains pipe-delimited files. The
May 2026 layout has **30 ordered fields**. The critical distinctions are:

1. **Commodity year (field 1)** is the insured crop's *harvest/policy year*; **year of loss (field 16)** is when damage occurred and may differ.
2. **Month of loss** is distinct from policy year. Do not fabricate a day/date or claim that month uniquely identifies a catastrophic event.
3. **Coverage category (field 10)** has codes A (Buyup), C (CAT coverage), E (Existing Coverage) and L (Limited). **The code C does not mean a catastrophe peril.** The actual **cause of loss** has separate code/description fields 12–13.
4. **Liability, premium, subsidy, indemnity and loss ratio** have different financial meanings. Indemnity is signed in the layout. Net quantity fields may use crop-specific units other than acreage. A ratio or amount is not independently a model-calibrated event loss.
5. **CLIP policy counts are unavailable** according to the record layout; blank policy counts must not be treated as zero or a count denominator. Some source numeric data use the layout's implied-decimal notation; the preflight does not rescale or calculate amounts from that text.
6. USDA's Summary of Business refreshes recent years; a bare **2025** label does not prove the ZIP bytes are immutable. Fix an original response timestamp and original SHA-256 for any evaluation.

## Offline ZIP inspection, no source transfer

After a rights-reviewed independent authorised acquisition, save the
**exact original bytes** outside public Git under the publisher filename
\`colsom_2025.zip\`. Use:

~~~sh
python -m scripts.usda_rma_cause_loss_zip_preflight_v0 \
    --zip /private/research/colsom_2025.zip

# Only if there are multiple eligible .txt/.dat members:
python -m scripts.usda_rma_cause_loss_zip_preflight_v0 \
    --zip /private/research/colsom_2025.zip --member exact/member.txt

python -m unittest tests.test_usda_rma_cause_loss_zip_preflight_v0 -v
~~~

The checker never opens the network, unpacks to disk, imports records, produces
individual farm/insured/company data, or writes to Neon. It checks a bounded
ZIP against traversal/symlink/encryption/duplicate-member/zip-bomb controls,
selects one exact flat file, parses bounded UTF-8 pipe-delimited rows,
requires the 2025 commodity year, all 30 official positions, numeric
state/county/crop/plan/cause codes, valid month and loss year, valid
coverage code, and guarded numeric formats. Output contains **only**
original-*local* ZIP and decompressed-member SHA-256/size and aggregated row,
state, cause, month, missing-policy-count and negative-indemnity-row counts.

A local SHA-256 **is not original HTTP provenance**; record the final provider
URL, trusted response receipt with UTC timestamp, true original bytes and
versioned terms separately before claiming source identity. The parser's
initial shape restrictions may need evidence-driven adjustment after
legitimate original data inspection; never weaken checks just to force a pass.

## Admission and modelling next steps

Before using this as a global crop CAT model validation/calibration dataset:

- Review the exact provider access/automation and dataset commercial/
  redistribution rights. Do not infer all source rights from government
  publication alone.
- Verify native cause-code dictionary and stage/coverage crosswalk, units,
  policy-count population, subsidy and negative indemnity meanings.
- Freeze interpretation of county FIPS (leading zeros), crop year versus
  loss year, multi-county exposure, missing fields and data-revision vintage.
- Independently link observed county/crop/month losses to hazard **windows**
  and explain which co-occurring losses can or cannot be assigned to one event.
- Confirm insured crop programme loss is not general property insurance,
  enterprise exposure, an insured sum for each address or an ELT.

**No Neon write, model admission, publication of raw data or unknown-source
commercial reuse is authorized by this proof.**
