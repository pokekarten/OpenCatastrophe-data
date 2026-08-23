# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed wrapper that preserves a durable terminal on ledger-read failure."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from scripts import acquire_efehr_esrm20_athens_sibling_receipts as worker

_LEDGER_FAILURE_MESSAGE = "cannot read complete Athens sibling result ledger"


def prepare_action_result(
    body: object,
    *,
    expected_issue: int,
    execution_sha: str,
    repository: str,
    token: str,
) -> dict[str, Any]:
    """Run the fixed worker and terminalize only its pre-provider ledger failure."""
    try:
        return worker.prepare_result(
            body,
            expected_issue=expected_issue,
            execution_sha=execution_sha,
            repository=repository,
            token=token,
        )
    except worker.AthensSiblingReceiptError as exc:
        if str(exc) != _LEDGER_FAILURE_MESSAGE:
            raise
        blocked = {
            **worker._base_result(execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": "ledger_incomplete",
            "receipts": None,
            "provider_file_bytes_read": None,
        }
        return worker.validate_result(blocked)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--token-env", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    body = os.environ.get(args.comment_body_env)
    token = os.environ.get(args.token_env, "")
    if body is None:
        raise worker.AthensSiblingReceiptError(
            "Athens sibling request comment environment variable is absent"
        )
    result = prepare_action_result(
        body,
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
        repository=args.repository,
        token=token,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
