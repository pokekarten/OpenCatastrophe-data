# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path


WORKFLOW = Path(".github/workflows/esrm20-athens-job-config-profile.yml")


def test_publisher_refences_live_default_branch_before_durable_comment() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    publisher = text.split("  publish-profile:", 1)[1]

    assert "contents: read" in publisher
    assert "issues: write" in publisher
    assert "DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}" in publisher
    assert 'gh api "repos/$GITHUB_REPOSITORY/commits/$DEFAULT_BRANCH" --jq \'.sha\'' in publisher
    assert 'test "$LATEST_SHA" = "$EXECUTION_SHA"' in publisher
    assert "actions/checkout" not in publisher

    live_fence = publisher.index('test "$LATEST_SHA" = "$EXECUTION_SHA"')
    publish = publisher.index('gh api --method POST')
    assert live_fence < publish
