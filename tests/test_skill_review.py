from __future__ import annotations

import json
from html.parser import HTMLParser

import build_skill_review as review
import pytest

from tests.helpers import ROOT


def test_bundled_offline_helper_matches_the_qualified_maintained_tool():
    bundled = ROOT / "included/improved/skills/skill-authoring-current/scripts/build_skill_review.py"
    assert bundled.read_bytes() == (ROOT / "tools/build_skill_review.py").read_bytes()


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.sections = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == "section":
            self.sections.append(dict(attrs))


def test_output_markup_cannot_create_active_elements_or_change_identifiers(tmp_path):
    malicious = '</script><img src=x onerror="alert(1)"><script>'
    run = {"id": 'owned" data-extra="changed', "prompt": malicious, "output_text": malicious}
    file = tmp_path / "runs.json"
    file.write_text(json.dumps([run]), encoding="utf-8")
    loaded = review.read_runs(file)
    result = review.render(loaded)
    elements = Elements()
    elements.feed(result)
    assert elements.tags.count("script") == 1
    assert "img" not in elements.tags
    assert elements.sections == [{"data-run-id": run["id"]}]
    assert malicious not in result
    assert review.render(loaded) == result


@pytest.mark.parametrize(
    "runs",
    [
        [],
        {},
        [None],
        [{"id": "x"}],
        [{"id": "x", "prompt": {}, "output_text": ""}],
        [{"id": " ", "prompt": "", "output_text": ""}],
        [{"id": "x", "prompt": "", "output_text": ""}] * 2,
        [{"id": "x", "prompt": "x" * 65537, "output_text": ""}],
    ],
)
def test_malformed_or_ambiguous_runs_rejected(tmp_path, runs):
    file = tmp_path / "runs.json"
    file.write_text(json.dumps(runs), encoding="utf-8")
    with pytest.raises(ValueError):
        review.read_runs(file)


def test_duplicate_json_fields_rejected(tmp_path):
    file = tmp_path / "runs.json"
    file.write_text('[{"id":"x","id":"y","prompt":"","output_text":""}]', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        review.read_runs(file)


def test_oversized_input_rejected_without_loading_the_rest(tmp_path):
    file = tmp_path / "runs.json"
    file.write_bytes(b" " * (review.MAX_INPUT_BYTES + 1))
    with pytest.raises(ValueError, match="2 MiB"):
        review.read_runs(file)


def test_existing_output_preserved_and_new_output_is_utf8(tmp_path):
    source, target = tmp_path / "runs.json", tmp_path / "review.html"
    source.write_text(json.dumps([{"id": "owned", "prompt": "Grüße", "output_text": ""}]), encoding="utf-8")
    target.write_text("existing", encoding="utf-8")
    with pytest.raises(FileExistsError):
        review.main(["--input", str(source), "--output", str(target)])
    assert target.read_text() == "existing"
    new = tmp_path / "new.html"
    assert review.main(["--input", str(source), "--output", str(new)]) == 0
    assert "Grüße" in new.read_text(encoding="utf-8")
    assert review.main(["--input", str(source), "--output", str(new), "--check"]) == 0
    new.write_text("changed", encoding="utf-8")
    assert review.main(["--input", str(source), "--output", str(new), "--check"]) == 1
    assert new.read_text() == "changed"
    assert review.main(["--input", str(source), "--output", str(tmp_path / "missing"), "--check"]) == 1
