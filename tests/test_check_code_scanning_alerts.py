from urllib.parse import parse_qs, urlencode, urlsplit

import check_code_scanning_alerts as gate
import pytest

SHA = "a" * 40
REPO = "example/repo"


class Snapshot:
    def __init__(self, count=0, chunk=100):
        self.count = count
        self.chunk = chunk
        self.heads = 0
        self.inventory_calls = 0

    def __call__(self, url):
        if url == "repos/" + REPO:
            return {"id": 123, "full_name": REPO, "default_branch": "main"}, None
        if url.endswith("/branches/main"):
            self.heads += 1
            return {"commit": {"sha": SHA}}, None
        if "/analyses?" in url:
            return [
                {"id": i + 1, "tool": {"name": "CodeQL"}, "category": c, "commit_sha": SHA, "error": ""}
                for i, c in enumerate(sorted(gate.CATEGORIES))
            ], None
        self.inventory_calls += 1
        q = parse_qs(urlsplit(url).query)
        page = int(q.get("page", ["1"])[0])
        start = (page - 1) * self.chunk
        rows = [{"number": n + 1, "state": "open"} for n in range(start, min(start + self.chunk, self.count))]
        next_url = None
        if start + self.chunk < self.count:
            q["page"] = [str(page + 1)]
            next_url = "https://api.github.com/repositories/123/code-scanning/alerts?" + urlencode(
                {k: v[0] for k, v in q.items()}
            )
        return rows, next_url


@pytest.mark.parametrize("count", [0, 1, 2, 3, 100, 101, 201])
def test_threshold(count):
    result = gate.check(Snapshot(count), REPO, SHA)
    assert result["open_alerts"] == count and result["passed"] is (count <= 2)


def test_nonfull_page_with_next_is_followed():
    result = gate.check(Snapshot(3, chunk=1), REPO, SHA)
    assert result["open_alerts"] == 3 and not result["passed"]


@pytest.mark.parametrize("kind", ["host", "path", "filter", "duplicate", "fragment", "cycle"])
def test_untrusted_or_repeated_next_links_fail(kind):
    snapshot = Snapshot(3, chunk=1)

    def fetch(url):
        data, link = snapshot(url)
        if link and kind == "host":
            link = link.replace("api.github.com", "evil.invalid")
        elif link and kind == "path":
            link = link.replace("/123/", "/999/")
        elif link and kind == "filter":
            link += "&severity=high"
        elif link and kind == "duplicate":
            link += "&state=closed"
        elif link and kind == "fragment":
            link += "#fragment"
        elif link and kind == "cycle":
            q = "ref=refs%2Fheads%2Fmain&state=open&per_page=100&page=2"
            link = "https://api.github.com/repositories/123/code-scanning/alerts?" + q
        return data, link

    with pytest.raises(gate.GateError):
        gate.check(fetch, REPO, SHA)


def test_duplicates_fail():
    snapshot = Snapshot(101)

    def fetch(url):
        data, link = snapshot(url)
        if "/alerts?" in url and "page=2" in url:
            data[0]["number"] = 1
        return data, link

    with pytest.raises(gate.GateError, match="Duplicate"):
        gate.check(fetch, REPO, SHA)


def test_changed_head_fails():
    snapshot = Snapshot()

    def fetch(url):
        data, link = snapshot(url)
        if url.endswith("/branches/main") and snapshot.heads == 2:
            data["commit"]["sha"] = "b" * 40
        return data, link

    with pytest.raises(gate.GateError):
        gate.check(fetch, REPO, SHA)


def test_changed_inventory_fails():
    snapshot = Snapshot(1)

    def fetch(url):
        data, link = snapshot(url)
        if "/alerts?" in url and snapshot.inventory_calls == 2:
            data = []
        return data, link

    with pytest.raises(gate.GateError, match="inventory changed"):
        gate.check(fetch, REPO, SHA)


@pytest.mark.parametrize("kind", ["stale", "missing", "failed", "malformed"])
def test_bad_analysis_fails(kind):
    snapshot = Snapshot()

    def fetch(url):
        data, link = snapshot(url)
        if "/analyses?" in url:
            if kind == "stale":
                data[0]["commit_sha"] = "b" * 40
            elif kind == "missing":
                data.pop()
            elif kind == "failed":
                data[0]["error"] = "failed"
            else:
                data[0]["id"] = None
        return data, link

    with pytest.raises(gate.GateError):
        gate.check(fetch, REPO, SHA)


def test_workflow_runs_gate_after_scans_with_read_only_permissions():
    from pathlib import Path

    import yaml

    path = Path(__file__).resolve().parents[1] / ".github/workflows/codeql.yml"
    job = yaml.safe_load(path.read_text(encoding="utf-8"))["jobs"]["alert-budget"]
    assert job["needs"] == "analyze"
    assert job["permissions"] == {"contents": "read", "security-events": "read"}
    assert job.get("continue-on-error", False) is False
    assert job["steps"][0]["with"]["persist-credentials"] is False
    assert (
        job["steps"][-1]["run"]
        == 'python tools/check_code_scanning_alerts.py --repository "$GITHUB_REPOSITORY" --commit "$GITHUB_SHA"'
    )
    assert job["steps"][-1]["env"]["GH_TOKEN"] == "${{ github.token }}"
