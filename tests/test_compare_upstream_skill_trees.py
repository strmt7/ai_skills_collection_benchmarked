import copy
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import compare_upstream_skill_trees as target
import pytest
import verify_upstream_skill_inventory as verifier

A, B, C, D, E = (x * 40 for x in "abcde")


def tree(sha, items, *, truncated=False):
    return {"sha": sha, "truncated": truncated, "tree": items}


def entry(path, sha, kind="blob", mode="100644"):
    return {"path": path, "sha": sha, "type": kind, "mode": mode}


def test_complete_trees_compare_entrypoint_resources_and_modes():
    responses = {
        f"repos/o/r/git/trees/{A}?recursive=1": tree(
            A, [entry("skills/a/SKILL.md", C), entry("skills/a/helper.py", D)]
        ),
        f"repos/o/r/git/trees/{B}?recursive=1": tree(
            B,
            [
                entry("skills/a/SKILL.md", C),
                entry("skills/a/helper.py", D, mode="100755"),
                entry("skills/a/new.txt", E),
            ],
        ),
    }
    first, second = (target.Snapshot("o/r", sha, responses.__getitem__) for sha in (A, B))
    result = target.compare_skill({"id": "a", "source_path": "skills/a/SKILL.md"}, first, second)
    assert result["entrypoint"] == "unchanged"
    assert result["directory_changed"] is True
    assert [change["path"] for change in result["changed_paths"]] == [
        "helper.py",
        "new.txt",
    ]
    assert (result["pinned_file_count"], result["observed_file_count"]) == (2, 3)


def test_removed_entrypoint_requires_complete_tree():
    responses = {
        f"repos/o/r/git/trees/{A}?recursive=1": tree(A, [entry("a/SKILL.md", C)]),
        f"repos/o/r/git/trees/{B}?recursive=1": tree(B, []),
    }
    first, second = (target.Snapshot("o/r", sha, responses.__getitem__) for sha in (A, B))
    assert (
        target.compare_skill({"id": "a", "source_path": "a/SKILL.md"}, first, second)["entrypoint"]
        == "missing_at_recorded_path"
    )
    with pytest.raises(ValueError, match="Pinned entrypoint absent"):
        target.compare_skill({"id": "missing", "source_path": "missing/SKILL.md"}, first, second)


def test_same_named_paths_are_candidates_not_confirmed_relocations():
    responses = {
        f"repos/o/r/git/trees/{A}?recursive=1": tree(A, [entry("old/a/SKILL.md", C), entry("old/a/guide.md", D)]),
        f"repos/o/r/git/trees/{B}?recursive=1": tree(
            B,
            [
                entry("new/a/SKILL.md", E),
                entry("new/a/guide.md", D),
                entry("else/a/SKILL.md", C),
            ],
        ),
    }
    first, second = (target.Snapshot("o/r", sha, responses.__getitem__) for sha in (A, B))
    item = target.compare_skill({"id": "a", "source_path": "old/a/SKILL.md"}, first, second)
    assert item["entrypoint"] == "missing_at_recorded_path"
    candidates = item["same_named_candidates"]
    assert [row["source_path"] for row in candidates] == [
        "else/a/SKILL.md",
        "new/a/SKILL.md",
    ]
    assert [row["entrypoint_identical"] for row in candidates] == [True, False]
    assert [row["path"] for row in candidates[1]["changed_paths"]] == ["SKILL.md"]


def test_truncated_root_and_subtree_use_complete_nonrecursive_walk():
    responses = {
        f"repos/o/r/git/trees/{A}?recursive=1": tree(A, [], truncated=True),
        f"repos/o/r/git/trees/{A}": tree(A, [entry("skills", B, "tree", "040000")]),
        f"repos/o/r/git/trees/{B}": tree(B, [entry("a", C, "tree", "040000")]),
        f"repos/o/r/git/trees/{C}?recursive=1": tree(C, [], truncated=True),
        f"repos/o/r/git/trees/{C}": tree(C, [entry("SKILL.md", D), entry("ref", E, "tree", "040000")]),
        f"repos/o/r/git/trees/{E}": tree(E, [entry("guide.md", A)]),
    }
    snapshot = target.Snapshot("o/r", A, responses.__getitem__)
    assert snapshot.complete is False
    assert snapshot.same_named_entrypoints(target.PurePosixPath("skills/a/SKILL.md")) is None
    assert snapshot.directory("skills/a") == {
        "SKILL.md": ("blob", "100644", D),
        "ref/guide.md": ("blob", "100644", A),
    }
    assert snapshot.directory("skills/no-such-skill") == {}


def test_truncated_nonrecursive_tree_never_becomes_a_deletion():
    responses = {
        f"repos/o/r/git/trees/{A}?recursive=1": tree(A, [], truncated=True),
        f"repos/o/r/git/trees/{A}": tree(A, [], truncated=True),
    }
    snapshot = target.Snapshot("o/r", A, responses.__getitem__)
    with pytest.raises(ValueError, match="Nonrecursive.*truncated"):
        snapshot.directory("skills/a")


@pytest.mark.parametrize(
    "change",
    [
        "wrong_sha",
        "missing_flag",
        "duplicate",
        "absolute",
        "wrong_mode",
        "nested_nonrecursive",
    ],
)
def test_invalid_tree_responses_are_rejected(change):
    value = tree(A, [entry("one", C)])
    if change == "wrong_sha":
        value["sha"] = B
    elif change == "missing_flag":
        del value["truncated"]
    elif change == "duplicate":
        value["tree"].append(copy.deepcopy(value["tree"][0]))
    elif change == "absolute":
        value["tree"][0]["path"] = "/absolute"
    elif change == "wrong_mode":
        value["tree"][0]["mode"] = "040000"
    else:
        value["tree"][0]["path"] = "nested/file"
    with pytest.raises(ValueError):
        target.parse_tree(value, A, recursive=False)


def test_repository_summary_uses_pinned_and_resolved_default_heads():
    responses = {
        "repos/o/r": {"full_name": "o/r", "default_branch": "main"},
        "repos/o/r/commits/main": {"sha": B},
        "repos/o/r/releases/latest": {
            "tag_name": "v1",
            "draft": False,
            "prerelease": False,
        },
        "repos/o/r/commits/v1": {"sha": A},
        f"repos/o/r/git/commits/{A}": {"sha": A, "tree": {"sha": C}},
        f"repos/o/r/git/commits/{B}": {"sha": B, "tree": {"sha": D}},
        f"repos/o/r/git/trees/{C}?recursive=1": tree(C, [entry("a/SKILL.md", A)]),
        f"repos/o/r/git/trees/{D}?recursive=1": tree(D, [entry("a/SKILL.md", B)]),
    }
    result = target.inspect(
        "o/r",
        {"commit_sha": A},
        [{"id": "a", "source_path": "a/SKILL.md"}],
        responses.__getitem__,
    )
    assert result["pinned_commit"] == A and result["observed_head"] == B
    assert result["entrypoints_changed"] == result["directories_changed"] == 1
    assert result["latest_release"]["tag"] == "v1"
    assert result["latest_release"]["entrypoints_changed"] == 0

    def unavailable(endpoint, status):
        if endpoint == "repos/o/r/releases/latest":
            raise target.GitHubApiError(endpoint, "test", status)
        return responses[endpoint]

    no_release = target.inspect(
        "o/r",
        {"commit_sha": A},
        [{"id": "a", "source_path": "a/SKILL.md"}],
        lambda endpoint: unavailable(endpoint, 404),
    )
    assert no_release["latest_release"] is None
    with pytest.raises(target.GitHubApiError):
        target.inspect(
            "o/r",
            {"commit_sha": A},
            [{"id": "a", "source_path": "a/SKILL.md"}],
            lambda endpoint: unavailable(endpoint, 403),
        )


def test_invalid_selection_is_recorded_without_network(tmp_path):
    lock, selection = tmp_path / "lock.json", tmp_path / "selection.json"
    lock.write_text(
        json.dumps({"sources": [{"repo": "o/r", "skills": [{"id": "a"}]}]}),
        encoding="utf-8",
    )
    selection.write_text(json.dumps({"o/r": ["missing"]}), encoding="utf-8")
    output = tmp_path / "capture"
    code = target.main(
        [
            "--source-lock",
            str(lock),
            "--selection",
            str(selection),
            "--output",
            str(output),
            "--observed-at-utc",
            "2026-11-01T21:15:00Z",
        ]
    )
    assert code == 1
    data = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert data["results"][0]["status"] == "error" and data["captures"] == []


def test_invalid_timestamp_returns_json_without_creating_capture(tmp_path, capsys):
    output = tmp_path / "capture"
    code = target.main(
        [
            "--source-lock",
            str(tmp_path / "unused-lock"),
            "--selection",
            str(tmp_path / "unused-selection"),
            "--output",
            str(output),
            "--observed-at-utc",
            "2026-11-01T21:15:00",
        ]
    )
    assert code == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False
    assert not output.exists()


def test_verifier_reports_missing_capture_without_writing_receipt(tmp_path, capsys):
    output = tmp_path / "receipt.json"
    code = verifier.main(
        [
            "--capture",
            str(tmp_path / "missing"),
            "--selection",
            str(tmp_path / "missing-selection"),
            "--source-lock",
            str(tmp_path / "missing-lock"),
            "--output",
            str(output),
        ]
    )
    assert code == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False
    assert not output.exists()


def test_replay_validates_native_streams_and_never_calls_network(tmp_path, monkeypatch):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    captured = target.Capture(source)
    captured.record("repos/o/r", b'{"full_name":"o/r"}', b"", 0)
    with pytest.raises(target.GitHubApiError):
        captured.record("repos/o/r/releases/latest", b'{"status":"404"}', b"HTTP 404", 1)
    replay = target.ReplayCapture(destination, source, {"captures": captured.receipts})
    monkeypatch.setattr(
        target.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("unexpected network call"),
    )
    assert replay("repos/o/r") == {"full_name": "o/r"}
    with pytest.raises(target.GitHubApiError) as exc:
        replay("repos/o/r/releases/latest")
    assert exc.value.status == 404
    (source / "0000.stdout").write_bytes(b"changed")
    again = target.ReplayCapture(destination, source, {"captures": captured.receipts})
    with pytest.raises(ValueError, match="digest differs"):
        again("repos/o/r")


def test_timeout_keeps_partial_streams_and_replays_as_timeout(tmp_path, monkeypatch):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()

    def timeout(*args, **kwargs):
        raise target.subprocess.TimeoutExpired("gh", 90, output=b"partial", stderr=b"diagnostic")

    monkeypatch.setattr(target.subprocess, "run", timeout)
    captured = target.Capture(source)
    with pytest.raises(TimeoutError):
        captured("repos/o/r")
    assert captured.receipts[0]["exit_code"] is None
    assert (source / "0000.stdout").read_bytes() == b"partial"
    replay = target.ReplayCapture(destination, source, {"captures": captured.receipts})
    with pytest.raises(TimeoutError):
        replay("repos/o/r")
    assert (destination / "0000.stderr").read_bytes() == b"diagnostic"


def test_independent_verifier_reconciles_and_rejects_changed_evidence(tmp_path):
    lock = tmp_path / "lock.json"
    selection = tmp_path / "selection.json"
    skill = {"id": "a", "source_path": "a/SKILL.md"}
    lock.write_text(json.dumps({"sources": [{"repo": "o/r", "commit_sha": A, "skills": [skill]}]}), encoding="utf-8")
    selection.write_text(json.dumps({"o/r": ["a"]}), encoding="utf-8")
    seed, output = tmp_path / "seed", tmp_path / "capture"
    seed.mkdir()
    output.mkdir()
    capture = target.Capture(seed)
    responses = {
        "repos/o/r": {"full_name": "o/r", "default_branch": "main"},
        "repos/o/r/commits/main": {"sha": B},
        f"repos/o/r/git/commits/{A}": {"sha": A, "tree": {"sha": C}},
        f"repos/o/r/git/commits/{B}": {"sha": B, "tree": {"sha": D}},
        f"repos/o/r/git/trees/{C}?recursive=1": tree(C, [entry("a/SKILL.md", A)]),
        f"repos/o/r/git/trees/{D}?recursive=1": tree(D, [entry("a/SKILL.md", B)]),
    }
    for endpoint, payload in responses.items():
        capture.record(endpoint, json.dumps(payload).encode(), b"", 0)
    with pytest.raises(target.GitHubApiError):
        capture.record("repos/o/r/releases/latest", b'{"status":"404"}', b"HTTP 404", 1)
    replay = target.ReplayCapture(output, seed, {"captures": capture.receipts})
    result = target.inspect("o/r", {"commit_sha": A}, [skill], replay)
    summary: dict[str, Any] = {
        "selection_sha256": hashlib.sha256(selection.read_bytes()).hexdigest(),
        "source_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
        "results": [{"status": "complete", **result}],
        "captures": replay.receipts,
    }
    summary_path = output / "summary.json"
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    assert verifier.verify(output, selection, lock)["skill_tree_comparisons"] == 1
    summary["results"][0]["entrypoints_changed"] = 0
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises(ValueError, match="Aggregate counts"):
        verifier.verify(output, selection, lock)
    summary["results"][0]["entrypoints_changed"] = 1
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    (output / "0000.stdout").write_bytes(b"changed")
    with pytest.raises(ValueError, match="digest mismatch"):
        verifier.verify(output, selection, lock)


def test_recorded_inventory_retains_selected_skills_and_reconciled_counts():
    root = Path(__file__).resolve().parents[1]
    evidence = root / "artifacts/research/2026-11-01/upstream-inventory-v1"
    summary_bytes = (evidence / "summary.json").read_bytes()
    summary = json.loads(summary_bytes)
    selection_bytes = (evidence / "selection.json").read_bytes()
    selection = json.loads(selection_bytes)
    verification = json.loads((evidence / "verification.json").read_text(encoding="utf-8"))
    assert summary["selection_sha256"] == hashlib.sha256(selection_bytes).hexdigest()
    assert len(summary["source_lock_sha256"]) == 64
    assert verification["ok"] is True and verification["summary_sha256"] == hashlib.sha256(summary_bytes).hexdigest()
    assert verification["skill_tree_comparisons"] == 468 and verification["candidate_directories_checked"] == 258
    assert {item["repo"] for item in summary["results"]} == set(selection)
    assert sum(len(ids) for ids in selection.values()) == 334
    for item in summary["results"]:
        assert item["status"] == "complete"
        assert {row["skill_id"] for row in item["skills"]} == set(selection[item["repo"]])
        for observed in [item, *([item["latest_release"]] if item["latest_release"] else [])]:
            rows = observed["skills"]
            assert observed["entrypoints_changed"] == sum(row["entrypoint"] == "changed" for row in rows)
            assert observed["entrypoints_missing_at_recorded_path"] == sum(
                row["entrypoint"] == "missing_at_recorded_path" for row in rows
            )
            assert observed["directories_changed"] == sum(row["directory_changed"] for row in rows)


def test_recorded_karpathy_baseline_matches_historical_protocol():
    root = Path(__file__).resolve().parents[1]
    evidence = root / "artifacts/research/2026-11-01/upstream-inventory-v1/karpathy-baseline.json"
    observation = json.loads(evidence.read_text(encoding="utf-8"))
    protocol = json.loads(
        (root / "benchmarks/agent-effectiveness/development/protocol-v2.json").read_text(encoding="utf-8")
    )
    assert observation["head_matches_pin"] is True
    assert observation["observed_head"] == observation["pinned_commit"]
    assert observation["historical_protocol_bytes_match"] is True
    assert observation["skill_sha256"] == protocol["conditions"]["karpathy"]["skills"][0]["sha256"]


def test_recorded_nonsecurity_batch_has_bound_source_and_reconciled_results():
    root = Path(__file__).resolve().parents[1]
    evidence = root / "artifacts/research/2026-11-02/nonsecurity-upstream-v1"
    manifest = json.loads((evidence / "manifest.json").read_bytes())
    actual_files = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in evidence.iterdir()
        if path.is_file() and path.name != "manifest.json"
    }
    assert manifest["files_sha256"] == actual_files
    original = gzip.decompress((evidence / "source-lock.json.gz").read_bytes())
    alias = gzip.decompress((evidence / "alias-source-lock.json.gz").read_bytes())
    assert hashlib.sha256(original).hexdigest() == manifest["source_lock_sha256"]
    source = json.loads(original)
    derived = json.loads(alias)
    redirects = json.loads((evidence / "redirect-observations.json").read_bytes())
    mapping = {item["original"]: item["canonical"] for item in redirects}
    for item in source["sources"]:
        if item["repo"] in mapping:
            item["repo"] = mapping[item["repo"]]
            item["origin_url"] = "https://github.com/" + item["repo"] + ".git"
    assert source == derived
    selection = json.loads((evidence / "selection.json").read_bytes())
    original_subset = json.loads((evidence / "complete-selection.json").read_bytes())
    alias_subset = json.loads((evidence / "alias-selection.json").read_bytes())
    unavailable = json.loads((evidence / "unavailable.json").read_bytes())
    unavailable_names = {item["repo"] for item in unavailable}
    assert set(selection) == set(original_subset) | set(mapping) | unavailable_names
    assert all(alias_subset[new] == selection[old] for old, new in mapping.items())
    assert all(original_subset[repo] == selection[repo] for repo in original_subset)
    assert len(selection) == manifest["selected_repositories"] == 15
    assert sum(map(len, selection.values())) == manifest["selected_skills"] == 49
    assert len(unavailable_names) == manifest["unavailable_repositories"] == 2
    assert all(item["http_status"] == 404 for item in unavailable)
    for item, stem in zip(unavailable, ("video", "music"), strict=True):
        stdout = (evidence / f"{stem}-404.stdout").read_bytes()
        stderr = (evidence / f"{stem}-404.stderr").read_bytes()
        assert hashlib.sha256(stdout).hexdigest() == item["stdout_sha256"]
        assert hashlib.sha256(stderr).hexdigest() == item["stderr_sha256"]
        assert b"HTTP 404" in stderr
    for name, source_bytes, selection_bytes, verification_name in (
        ("complete-summary.json", original, (evidence / "complete-selection.json").read_bytes(), "verification.json"),
        ("alias-summary.json", alias, (evidence / "alias-selection.json").read_bytes(), "alias-verification.json"),
    ):
        summary_bytes = (evidence / name).read_bytes()
        summary = json.loads(summary_bytes)
        verification = json.loads((evidence / verification_name).read_bytes())
        assert summary["source_lock_sha256"] == hashlib.sha256(source_bytes).hexdigest()
        assert summary["selection_sha256"] == hashlib.sha256(selection_bytes).hexdigest()
        assert verification["ok"] and verification["summary_sha256"] == hashlib.sha256(summary_bytes).hexdigest()
        expected = json.loads(selection_bytes)
        pins = {item["repo"]: item["commit_sha"] for item in json.loads(source_bytes)["sources"]}
        assert {item["repo"] for item in summary["results"]} == set(expected)
        for item in summary["results"]:
            assert item["status"] == "complete" and item["pinned_commit"] == pins[item["repo"]]
            assert {row["skill_id"] for row in item["skills"]} == set(expected[item["repo"]])
    summary = json.loads((evidence / "complete-summary.json").read_bytes())
    browser = next(item for item in summary["results"] if item["repo"] == "browser-act/skills")
    moved = [row for row in browser["skills"] if row["entrypoint"] == "missing_at_recorded_path"]
    assert len(moved) == manifest["browser_missing_recorded_paths"] == 31
    assert all(
        len(row["same_named_candidates"]) == 1
        and row["same_named_candidates"][0]["entrypoint_identical"]
        and not row["same_named_candidates"][0]["changed_paths"]
        for row in moved
    )
    for observation, stem in zip(redirects, ("comfyui-workflow-skill", "create-infographics"), strict=True):
        headers = json.loads((evidence / f"{stem}-301-headers.json").read_bytes())
        metadata = json.loads((evidence / f"{stem}-canonical-metadata.json").read_bytes())
        target = json.loads((evidence / f"{stem}-redirect-target.json").read_bytes())
        commit = json.loads((evidence / f"{stem}-pinned-commit.json").read_bytes())
        assert observation["redirect_status"] == 301 and headers["Location"] == observation["redirect_location"]
        assert metadata["id"] == target["id"] == observation["repository_id"]
        assert metadata["full_name"] == target["full_name"] == observation["canonical"]
        original_pins = {item["repo"]: item["commit_sha"] for item in json.loads(original)["sources"]}
        assert commit["sha"] == observation["pinned_commit"] == original_pins[observation["original"]]


def test_recorded_mixed_source_batch_binds_canonical_alias_and_selection():
    root = Path(__file__).resolve().parents[1]
    evidence = root / "artifacts/research/2026-11-02/mixed-upstream-v1"
    manifest = json.loads((evidence / "manifest.json").read_bytes())
    actual = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in evidence.iterdir()
        if p.is_file() and p.name != "manifest.json"
    }
    assert manifest["files_sha256"] == actual
    original_bytes = gzip.decompress((evidence / "source-lock.json.gz").read_bytes())
    alias_bytes = gzip.decompress((evidence / "alias-source-lock.json.gz").read_bytes())
    assert hashlib.sha256(original_bytes).hexdigest() == manifest["source_lock_sha256"]
    source, derived = json.loads(original_bytes), json.loads(alias_bytes)
    redirect = json.loads((evidence / "redirect-observation.json").read_bytes())
    pinned = next(item for item in source["sources"] if item["repo"] == redirect["original"])
    assert pinned["commit_sha"] == redirect["pinned_commit"]
    pinned["repo"] = redirect["canonical"]
    pinned["origin_url"] = "https://github.com/" + redirect["canonical"] + ".git"
    assert source == derived
    headers = json.loads((evidence / "ecc-301-headers.json").read_bytes())
    target = json.loads((evidence / "ecc-redirect-target.json").read_bytes())
    metadata = json.loads((evidence / "ecc-canonical-metadata.json").read_bytes())
    commit = json.loads((evidence / "ecc-pinned-commit.json").read_bytes())
    assert redirect["redirect_status"] == 301 and headers["Location"] == redirect["redirect_location"]
    assert target["id"] == metadata["id"] == redirect["repository_id"]
    assert target["full_name"] == metadata["full_name"] == redirect["canonical"]
    assert commit["sha"] == redirect["pinned_commit"]
    selection = json.loads((evidence / "selection.json").read_bytes())
    direct = json.loads((evidence / "complete-selection.json").read_bytes())
    alias = json.loads((evidence / "alias-selection.json").read_bytes())
    assert set(selection) == set(direct) | {redirect["original"]}
    assert all(direct[repo] == selection[repo] for repo in direct)
    assert alias == {redirect["canonical"]: selection[redirect["original"]]}
    assert len(selection) == manifest["selected_repositories"] == 5
    assert sum(map(len, selection.values())) == manifest["selected_skills"] == 82
    for name, source_bytes, selected_name, verification_name in (
        ("complete-summary.json", original_bytes, "complete-selection.json", "verification.json"),
        ("alias-summary.json", alias_bytes, "alias-selection.json", "alias-verification.json"),
    ):
        raw = (evidence / name).read_bytes()
        summary = json.loads(raw)
        expected = json.loads((evidence / selected_name).read_bytes())
        verification = json.loads((evidence / verification_name).read_bytes())
        pins = {item["repo"]: item["commit_sha"] for item in json.loads(source_bytes)["sources"]}
        assert summary["source_lock_sha256"] == hashlib.sha256(source_bytes).hexdigest()
        assert summary["selection_sha256"] == hashlib.sha256((evidence / selected_name).read_bytes()).hexdigest()
        assert verification["ok"] and verification["summary_sha256"] == hashlib.sha256(raw).hexdigest()
        assert {item["repo"] for item in summary["results"]} == set(expected)
        for item in summary["results"]:
            assert item["status"] == "complete" and item["pinned_commit"] == pins[item["repo"]]
            assert {row["skill_id"] for row in item["skills"]} == set(expected[item["repo"]])
    summary = json.loads((evidence / "complete-summary.json").read_bytes())
    varnan = next(item for item in summary["results"] if item["repo"] == "Varnan-Tech/opendirectory")
    missing = [row for row in varnan["skills"] if row["entrypoint"] == "missing_at_recorded_path"]
    assert len(missing) == manifest["varnan_missing_recorded_paths"] == 26
    assert (
        sum(bool(row["same_named_candidates"]) for row in missing)
        == manifest["varnan_with_same_named_candidates"]
        == 21
    )
    assert (
        sum(not row["same_named_candidates"] for row in missing)
        == manifest["varnan_without_same_named_candidates"]
        == 5
    )
