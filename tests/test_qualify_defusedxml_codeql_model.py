"""Check that CodeQL model evidence fails closed when it is incomplete."""

import json
import sys

import pytest
import qualify_defusedxml_codeql_model as control


def sarif(*, model=True, successful=True, uri="fixture.py", lines=(14,)):
    extensions = []
    if model:
        extensions.append({"name": control.MODEL_NAME, "properties": {"isCodeQLModelPack": True}})
    return {
        "runs": [
            {
                "tool": {"extensions": extensions},
                "invocations": [{"executionSuccessful": successful}],
                "results": [
                    {
                        "ruleId": "py/path-injection",
                        "locations": [
                            {"physicalLocation": {"artifactLocation": {"uri": uri}, "region": {"startLine": line}}}
                        ],
                    }
                    for line in lines
                ],
            }
        ]
    }


def test_analysis_verification_requires_the_model(tmp_path):
    path = tmp_path / "analysis.sarif"
    path.write_text(json.dumps(sarif(model=False)), encoding="utf-8")
    with pytest.raises(ValueError, match="model pack absent"):
        control.verify_analysis(tmp_path)
    wrong_kind = sarif()
    wrong_kind["runs"][0]["tool"]["extensions"][0]["properties"]["isCodeQLModelPack"] = False
    path.write_text(json.dumps(wrong_kind), encoding="utf-8")
    with pytest.raises(ValueError, match="model pack absent"):
        control.verify_analysis(tmp_path)
    path.write_text(json.dumps(sarif()), encoding="utf-8")
    assert control.verify_analysis(tmp_path)["analysis_runs_checked"] == 1
    path.write_text(json.dumps(sarif(successful=False)), encoding="utf-8")
    with pytest.raises(ValueError, match="successful execution"):
        control.verify_analysis(tmp_path)


def test_analysis_verification_rejects_absent_results(tmp_path):
    with pytest.raises(ValueError, match="No CodeQL analysis"):
        control.verify_analysis(tmp_path)
    (tmp_path / "analysis.sarif").write_text('{"runs": []}', encoding="utf-8")
    with pytest.raises(ValueError, match="No CodeQL runs"):
        control.verify_analysis(tmp_path)


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (sarif(successful=False), "successful execution"),
        (sarif(uri="different.py"), "Unexpected source file"),
        (sarif(lines=(14, 14)), "Duplicate"),
    ],
)
def test_native_evidence_rejects_invalid_runs(tmp_path, data, message):
    path = tmp_path / "control.sarif"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        control.locations(path)


def test_cli_rejects_incomplete_arguments_and_existing_output(tmp_path, capsys):
    assert control.main([]) == 1
    assert json.loads(capsys.readouterr().err)["passed"] is False
    assert control.main(["--codeql", "codeql", "--model", str(tmp_path), "--output", str(tmp_path)]) == 1
    assert json.loads(capsys.readouterr().err)["passed"] is False


def test_native_command_logs_preserve_non_utf8_bytes_and_failures(tmp_path):
    log = tmp_path / "native.log"
    control.run([sys.executable, "-c", "import sys; sys.stdout.buffer.write(bytes([255]))"], log)
    assert log.read_bytes() == b"\xff\n"
    with pytest.raises(RuntimeError, match="CodeQL command failed"):
        control.run([sys.executable, "-c", "import sys; sys.stderr.buffer.write(bytes([254])); sys.exit(2)"], log)
    assert log.read_bytes() == b"\n\xfe"
