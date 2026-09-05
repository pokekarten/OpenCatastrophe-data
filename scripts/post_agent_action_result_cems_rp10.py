# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Publish Agent Action results through the CEMS-RP10-aware validator layer."""

from __future__ import annotations

try:
    from scripts import post_agent_action_result as _publisher
    from scripts import validate_agent_action_result_cems_rp10 as _result
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import post_agent_action_result as _publisher
    import validate_agent_action_result_cems_rp10 as _result

for _name in dir(_publisher):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_publisher, _name)

_publisher.validate_result = _result.validate_result
validate_result = _result.validate_result


def main(argv: list[str] | None = None) -> int:
    return _publisher.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
