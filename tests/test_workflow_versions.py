from __future__ import annotations

import audit_workflow_versions as audit
import pytest


def release(tag, **flags):
    return {
        "tag_name": tag,
        "published_at": "2026-09-24T10:27:53Z",
        "html_url": "https://github.com/example/tool",
        **flags,
    }


def test_release_selection_ignores_bundle_tags_and_unstable_releases():
    values = [
        release("codeql-bundle-v2.27.1"),
        release("v3.38.2"),
        release("v4.38.2"),
        release("v5.0.0", prerelease=True),
        release("v6.0.0", draft=True),
    ]
    assert audit.latest_stable(values)["tag_name"] == "v4.38.2"


def test_no_stable_release_is_explicit_failure():
    with pytest.raises(ValueError, match="no published stable"):
        audit.latest_stable([release("v2.0.0-rc1")])


def test_action_commit_must_be_immutable():
    result = audit.inspect_action("example/tool", lambda _: [release("v1.2.3")], lambda _: {"sha": "main"})
    assert result["status"] == "error"


def test_inventory_includes_subactions_and_content_drift(tmp_path):
    directory = tmp_path / ".github/workflows"
    directory.mkdir(parents=True)
    workflow = directory / "check.yml"
    workflow.write_text(
        "jobs:\n  check:\n    steps:\n      - uses: 'github/codeql-action/init@abcdef'\n      - uses: actions/checkout@v7.0.1 # release\n",
        encoding="utf-8",
    )
    before = audit.inventory(tmp_path)
    assert before["uses"][0]["subpath"] == "/init"
    assert before["uses"][1]["ref"] == "v7.0.1"
    workflow.write_text(workflow.read_text() + "# changed\n", encoding="utf-8")
    assert audit.inventory(tmp_path)["workflow_sha256"] != before["workflow_sha256"]


def test_outdated_or_mutable_pins_fail_latest_verification():
    inputs = {"uses": [{"workflow": "check.yml", "repo": "example/tool", "subpath": "/init", "ref": "v1.0.0"}]}
    actions = [{"repo": "example/tool", "status": "resolved", "commit_sha": "a" * 40, "stable_tag": "v2.0.0"}]
    assert "differs from latest stable" in audit.pin_errors(inputs, actions)[0]
    inputs["uses"][0]["ref"] = "a" * 40
    assert audit.pin_errors(inputs, actions) == []


@pytest.mark.parametrize(
    "actions",
    [
        [],
        [{"repo": "other/tool"}],
        [{"repo": "example/tool", "status": "resolved", "commit_sha": "main"}],
        [{"repo": "example/tool"}, {"repo": "example/tool"}],
        None,
    ],
)
def test_incomplete_or_invalid_observations_cannot_pass(actions):
    with pytest.raises(ValueError):
        audit.pin_errors({"uses": [{"repo": "example/tool"}]}, actions)


@pytest.mark.parametrize("reference", ["./local-action", "docker://image:latest", 17, "${{ inputs.action }}"])
def test_unreviewed_action_reference_is_explicit_failure(tmp_path, reference):
    import yaml

    directory = tmp_path / ".github/workflows"
    directory.mkdir(parents=True)
    (directory / "check.yml").write_text(
        yaml.safe_dump({"jobs": {"check": {"steps": [{"uses": reference}]}}}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="requires explicit version review"):
        audit.inventory(tmp_path)
