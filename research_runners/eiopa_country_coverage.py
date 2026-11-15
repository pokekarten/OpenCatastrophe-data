# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Describe country overlap, never infer matched insured populations."""
MAPPING = {'AT':'Austria','BE':'Belgium','CH':'Switzerland','CZ':'Czechia',
           'DE':'Germany','DK':'Denmark','FR':'France','IE':'Ireland',
           'IT':'Italy','LU':'Luxembourg','NO':'Norway','PL':'Poland',
           'SE':'Sweden','UK':'United Kingdom'}


def compare(exposure_rows, loss_rows):
    countries = {}
    seen = set()
    for row in exposure_rows:
        if row.get('Peril') != 'Windstorm':
            continue
        key = (row['As of date'],row['Country'],row['NUTS'])
        if key in seen:
            raise ValueError('Duplicate regional exposure')
        seen.add(key)
        countries.setdefault(row['Country'],set()).add(str(row['NUTS']))
    results=[]
    for code in sorted({r['Country'] for r in loss_rows if r.get('Category')=='Storm'}):
        country=MAPPING.get(code)
        regions=countries.get(country,set())
        results.append({'loss_country_label':code,'mapped_exposure_country':country,
                        'exposure_rows':len(regions),
                        'coverage_status':'country_overlap_only' if regions else 'no_matching_country',
                        'denominator_match_verified':False,
                        'loss_ratio_computable':False})
    return results
