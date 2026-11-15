# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Check reported ALL versus components without authorizing portfolio joins."""
from decimal import Decimal


def reconcile(rows):
    groups = {}
    for row in rows:
        key = (row['Event ID'], row['Country'])
        lob = row['LoB']
        value = Decimal(str(row['Insured loss (EUR)']))
        if not value.is_finite() or value < 0:
            raise ValueError('Invalid insured loss')
        group = groups.setdefault(key, {})
        if lob in group:
            raise ValueError('Duplicate event/country/LoB')
        if lob not in {'ALL', 'RES', 'COM', 'RES+COM'}:
            raise ValueError('Unknown LoB')
        group[lob] = value
    result = []
    for (event, country), group in sorted(groups.items(), key=lambda item: tuple(str(v) for v in item[0])):
        if 'RES+COM' in group and ({'RES','COM'} & group.keys()):
            raise ValueError('Overlapping component representations')
        components = sum((v for k,v in group.items() if k != 'ALL'), Decimal(0))
        comparable = 'ALL' in group and len(group)>1
        delta = group['ALL'] - components if comparable else None
        result.append({'event_id':event,'country':country,'event_identity_complete':bool(event and country),'lob_labels':sorted(group),
                       'all_equals_components_within_cent':abs(delta)<=Decimal('0.01') if delta is not None else None,
                       'all_minus_components_eur':str(delta) if delta is not None else None,
                       'aggregation_rule':'ALL is an alternative total; never add it to component rows',
                       'denominator_match_verified':False})
    return result
