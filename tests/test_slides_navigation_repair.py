"""Check the recorded component controls and maintained slide-template provenance."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELATIVE = Path("by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-slides")
OVERLAY = ROOT / "included/repaired/skills" / RELATIVE
MIRROR = ROOT / "included/skills" / RELATIVE
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/slides-navigation-v1"
SOURCE = "fd5b051a37365fc6059c75bb388ec6f64daf1bd9ae938b287b6d762dc83c0c35"
CANDIDATE = "090d3bb90fb22b97fdf6352e463bf7d61802fb1352592e40453c65312643384d"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def test_overlay_preserves_upstream_and_binds_all_artifacts() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    assert manifest["model_performance_claim"] is False
    assert manifest["original_template_sha256"] == SOURCE
    assert manifest["repaired_template_sha256"] == CANDIDATE
    for source, saved in [
        ("SKILL.md", "original.SKILL.md"),
        ("references/create.md", "original.create.md"),
        ("references/html-template.md", "original.html-template.md"),
    ]:
        assert normalized(MIRROR / source) == normalized(OVERLAY / "provenance" / saved)
    for reference in ["copywriting-formulas.md", "layout-patterns.md", "slide-strategies.md"]:
        assert normalized(MIRROR / "references" / reference) == normalized(OVERLAY / "references" / reference)
    for base, key, ignored in [(OVERLAY, "overlay_sha256", {"repair.json"}), (EVIDENCE, "evidence_sha256", set())]:
        actual = {
            p.relative_to(base).as_posix(): digest(p)
            for p in base.rglob("*")
            if p.is_file() and p.relative_to(base).as_posix() not in ignored
        }
        assert actual == manifest[key]
    assert digest(OVERLAY / "references/html-template.md") == CANDIDATE


def test_recorded_browser_matrix_reports_the_observed_controls() -> None:
    qualification = json.loads((EVIDENCE / "qualification.json").read_text(encoding="utf-8"))
    assert qualification["receipt_count"] == 72
    assert qualification["full_accessibility_audit"] is False
    assert qualification["agent_performance_tested"] is False
    assert qualification["pnpm_lock_sha256"] == digest(EVIDENCE / "dependencies/pnpm-lock.yaml")
    assert qualification["reproduction_sha256"] == digest(EVIDENCE / "reproduce.py")
    dependency = json.loads((EVIDENCE / "dependencies/package.json").read_bytes())
    assert qualification["playwright_version"] == dependency["devDependencies"]["playwright"]
    assert qualification["chart_js_version"] == dependency["devDependencies"]["chart.js"]
    assert dependency["engines"]["pnpm"] == qualification["pnpm_version"]
    platforms = {"windows": ["chromium", "webkit"], "linux": ["chromium", "firefox"]}
    runtimes = ("24.22.3", "26.13.1")
    expected_runs = {(system, node) for system in platforms for node in runtimes}
    runs = qualification["runs"]
    assert len(runs) == 4
    assert {(row["platform"], row["node"]) for row in runs} == expected_runs
    valid_names = set()
    for row in runs:
        expected = {}
        for engine in platforms[row["platform"]]:
            expected.update({f"{name}-{engine}": engine for name in ("labels", "motion")})
            layouts = {
                "navigation": ("desktop", "narrow"),
                "chart": ("desktop", "narrow", "landscape"),
                "overflow": ("narrow", "landscape"),
            }
            for check, sizes in layouts.items():
                expected.update({f"{check}-{engine}-{layout}": engine for layout in sizes})
        assert set(row["cases"]) == set(expected)
        for name, engine in expected.items():
            evidence = row["cases"][name]
            filename = f"{row['platform']}-node-{row['node']}-{name}.json"
            assert evidence["file"] == filename
            valid_names.add(filename)
            path = EVIDENCE / "results" / filename
            assert evidence["sha256"] == digest(path)
            item = json.loads(path.read_bytes())
            assert item["browser_engine"] == engine
            assert item["platform"] == ("win32" if row["platform"] == "windows" else "linux")
            assert item.get("node_version", item.get("node")) == f"v{row['node']}"
            assert item.get("candidate_sha256", item.get("source_sha256")) == CANDIDATE
            assert item["agent_performance_tested"] is False
            if name.startswith("navigation-"):
                assert item["original"]["previous_space"] == 3
                assert item["repaired"]["previous_space"] == 1
            elif name.startswith("chart-"):
                assert item["chart"]["version"] == qualification["chart_js_version"]
                assert item["chart"]["values"] == [5, 12, 28, 45]
                assert item["chart"]["max_pixel_error"] < 0.5
            elif name.startswith("overflow-"):
                assert not item["original"]["keyboard_scrolled"]
                assert item["repaired"]["keyboard_scrolled"] and item["repaired"]["wheel_scrolled"]
                assert item["repaired"]["end"]["last_bottom"] <= item["repaired"]["end"]["nav_top"]
            elif name.startswith("labels-"):
                assert item["repaired"]["named_region_count"] == 1
                assert item["original"]["custom"] == item["repaired"]["custom"]
            else:
                assert item["results"]["original"]["reduce"]["fade"]["animation"] == "fadeUp"
                assert item["results"]["repaired"]["reduce"]["fade"]["animation"] == "none"
                assert item["results"]["repaired"]["reduce"]["fade"]["opacity"] == "1"
    assert {p.name for p in (EVIDENCE / "results").glob("*.json")} == valid_names
