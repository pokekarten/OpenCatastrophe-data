# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from scripts import validate_agent_action_request_country_risk as request_validator
from scripts import validate_agent_action_result_country_risk as result_validator


def test_country_risk_request_actions_are_globally_result_classified() -> None:
    missing = request_validator.ALLOWED_ACTIONS - result_validator.ALLOWED_ACTIONS
    assert not missing, f"request actions missing from result classification: {sorted(missing)}"
