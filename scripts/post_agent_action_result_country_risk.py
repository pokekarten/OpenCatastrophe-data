# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Publish Agent Action results through the country-risk-aware validator layer."""

from __future__ import annotations

try:
    from scripts import post_agent_action_result as _legacy
    from scripts import validate_agent_action_result_country_risk as _result
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import post_agent_action_result as _legacy
    import validate_agent_action_result_country_risk as _result

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

# post_result() and main() resolve this module-global validator at call time.
_legacy.validate_result = _result.validate_result
validate_result = _result.validate_result


def main(argv: list[str] | None = None) -> int:
    return _legacy.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
