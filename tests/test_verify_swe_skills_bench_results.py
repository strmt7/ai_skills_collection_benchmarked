from __future__ import annotations

import hashlib
import json

import pytest
from verify_swe_skills_bench_results import main, parse_frame, replay_table

TABLE = "codex__example_cells.csv"
HEADER = b"skill,requirement_batch,none_pass_rate,one_pass_rate,delta_pp\n"
ROWS = (
    b"alpha,batch1,50.00,60.00,10.00\n",
    b"beta,batch1,50.00,55.00,5.00\n",
    b"gamma,batch1,60.00,55.00,-5.00\n",
    b"delta,batch1,50.00,50.00,0.00\n",
)
ARCHIVE = HEADER + b"".join(ROWS)


def declared(raw: bytes) -> dict:
    return {
        "schema_version": 1,
        "source_commit": "a" * 40,
        "skills": {
            "alpha": {"repository": "example/tools", "commit": "b" * 40},
            "beta": {"repository": "example/tools", "commit": "b" * 40},
            "gamma": {"repository": "example/other", "commit": "c" * 40},
            "delta": {"repository": None, "commit": None},
        },
        "batches": ["batch1"],
        "tables": {TABLE: hashlib.sha256(raw).hexdigest()},
    }


def test_reproduces_paired_percentages_and_removes_whole_repository_groups():
    result = replay_table(ARCHIVE, TABLE, parse_frame(declared(ARCHIVE)))
    assert result["pairs"] == 4
    assert result["none_mean_percent"] == 52.5
    assert result["one_mean_percent"] == 55.0
    assert result["published_delta_mean_pp"] == 2.5
    assert result["published_delta_direction_counts"] == {"higher": 2, "lower": 1, "tied": 1}
    assert result["declared_repository_groups"] == 2
    assert result["pairs_without_declared_repo_commit"] == 1
    assert result["leave_one_declared_repository_out_delta_pp"] == {"min": -2.5, "max": 5.0}


def test_keeps_the_independently_rounded_published_delta():
    raw = ARCHIVE.replace(b"60.00,10.00", b"60.00,10.01")
    result = replay_table(raw, TABLE, parse_frame(declared(raw)))
    assert result["published_delta_mean_pp"] == 2.5025
    assert result["rounded_arm_difference_pp"] == 2.5


@pytest.mark.parametrize(
    "raw,message",
    [
        (HEADER + b"".join(ROWS[:-1]), "missing pairs"),
        (HEADER + b"".join((*ROWS[:3], ROWS[0])), "duplicate pair"),
        (ARCHIVE.replace(b"delta,batch1", b"unplanned,batch1"), "unexpected"),
        (ARCHIVE.replace(b"60.00,10.00", b",10.00"), "complete decimal"),
        (ARCHIVE.replace(b"60.00,10.00", b"101.00,10.00"), "percentage range"),
        (ARCHIVE.replace(b"60.00,10.00", b"60.00,10.02"), "delta disagrees"),
    ],
)
def test_incomplete_or_inconsistent_pairs_cannot_enter_an_aggregate(raw, message):
    with pytest.raises(ValueError, match=message):
        replay_table(raw, TABLE, parse_frame(declared(raw)))


def test_changed_bytes_fail_the_frozen_table_hash():
    with pytest.raises(ValueError, match="frozen hash"):
        replay_table(ARCHIVE.replace(b"\n", b"\r\n"), TABLE, parse_frame(declared(ARCHIVE)))


def test_source_may_be_unpinned_but_cannot_claim_a_commit_without_a_repository():
    value = declared(ARCHIVE)
    value["skills"]["delta"]["commit"] = "a" * 40
    with pytest.raises(ValueError, match="declared repository or commit"):
        parse_frame(value)


def test_frame_cannot_redirect_reads_outside_the_table_directory():
    value = declared(ARCHIVE)
    value["tables"]["../" + TABLE] = value["tables"].pop(TABLE)
    with pytest.raises(ValueError, match="publisher table identities"):
        parse_frame(value)


def test_cli_refuses_missing_archive_instead_of_dropping_a_configuration(tmp_path, capsys):
    frame_path = tmp_path / "frame.json"
    frame_path.write_text(json.dumps(declared(ARCHIVE)), encoding="utf-8")
    code = main(["--frame", str(frame_path), "--tables-dir", str(tmp_path)])
    report = json.loads(capsys.readouterr().out)
    assert code == 2
    assert report["status"] == "archive_not_verified"
    assert "configurations" not in report
