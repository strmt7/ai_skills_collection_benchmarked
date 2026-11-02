"""Check selected FlowIO examples against independent byte-level expectations."""

from __future__ import annotations

import argparse
import array
import hashlib
import io
import json
import platform
import struct
import tempfile
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
from flowio import FlowData, create_fcs

ROOT = Path(__file__).resolve().parents[3]
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/flowio-fcs-basics"
)
FIXTURE_SHA256 = "cba7812f5bbce700786d22d97cf9858c1301878aa840c64eadcd263a3a0a5508"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run(fixture: Path) -> dict[str, Any]:
    require(version("flowio") == "1.4.0", "The control requires FlowIO 1.4.0")
    skill = (OVERLAY / "SKILL.md").read_text(encoding="utf-8")
    snippets = [part.split("```", 1)[0] for part in skill.split("```python\n")[1:]]
    require(len(snippets) == 2, "Expected two maintained examples")
    original = (OVERLAY / "provenance/original.SKILL.md").read_text(encoding="utf-8")
    require("create_fcs('output.fcs', data, channels)" in original, "The original writer example changed")
    values = np.array([[100, 200, 50], [150, 180, 60]], dtype=np.float64)
    channels = ["FSC-A", "SSC-A", "FL1-A"]
    with tempfile.TemporaryDirectory(prefix="flowio-fcs-control-") as directory:
        root = Path(directory)
        original_path = root / "original-example.fcs"
        try:
            create_fcs(str(original_path), values, channels)
        except ValueError:
            pass
        else:
            raise ValueError("The original two-dimensional writer unexpectedly succeeded")
        try:
            create_fcs(io.BytesIO(), values.ravel().tolist(), channels, metadata={"src": "x"})
        except TypeError:
            pass
        else:
            raise ValueError("The original metadata keyword unexpectedly succeeded")

        output_path = root / "valid.fcs"
        context: dict[str, Any] = {
            "input_events": values,
            "channel_names": channels,
            "display_names": ["forward", "side", "green"],
            "output_path": output_path,
        }
        exec(compile(snippets[0], str(OVERLAY / "SKILL.md"), "exec"), context)
        written = output_path.read_bytes()
        start = int(written[26:34])
        require(
            struct.unpack("<6f", written[start : start + 24]) == tuple(values.ravel()),
            "Independent float32 DATA read differs from fixture",
        )
        read_context: dict[str, Any] = {"input_path": output_path}
        exec(compile(snippets[1], str(OVERLAY / "SKILL.md"), "exec"), read_context)
        flow = read_context["flow"]
        require(np.array_equal(read_context["raw_events"], values), "Raw event values changed")
        require(
            flow.pnn_labels == channels and read_context["source"] == "generated example",
            "Channels or normalized source metadata differ",
        )
        require(flow.text.get("$SRC") is None, "Unexpected original uppercase metadata key")
        require(isinstance(flow.events, array.array), "Raw events are not the observed numeric array")
        try:
            exec(compile(snippets[0], str(OVERLAY / "SKILL.md"), "exec"), dict(context))
        except FileExistsError:
            pass
        else:
            raise ValueError("An existing output was overwritten")
        require(output_path.read_bytes() == written, "Existing output changed")

        for name, invalid in (
            ("nonfinite", [[1, float("nan"), 2]]),
            ("overflow", [[1, 1e100, 2]]),
            ("shape", [[1, 2]]),
            ("empty", np.empty((0, 3))),
        ):
            invalid_path = root / f"{name}.fcs"
            invalid_context = {**context, "input_events": invalid, "output_path": invalid_path}
            try:
                exec(compile(snippets[0], str(OVERLAY / "SKILL.md"), "exec"), invalid_context)
            except ValueError:
                pass
            else:
                raise ValueError(f"Invalid {name} input was accepted")
            require(not invalid_path.exists(), f"Invalid {name} input created a file")

        gain_path = root / "gain.fcs"
        with gain_path.open("xb") as handle:
            create_fcs(handle, values.ravel().tolist(), channels, metadata_dict={"p1g": "2.0"})
        gained = FlowData(str(gain_path))
        require(np.array_equal(gained.as_array(preprocess=False)[:, 0], [100, 150]), "Raw gain input changed")
        require(np.array_equal(gained.as_array(preprocess=True)[:, 0], [50, 75]), "Unexpected gain scaling")
        null = FlowData(str(output_path), null_channel_list=["FL1-A"])
        require(
            null.channel_count == 3 and null.as_array(preprocess=False).shape == (2, 3),
            "Null-channel classification changed array columns",
        )
        require(null.fluoro_indices == [], "The null channel remained classified as fluorescent")

    fixture_bytes = fixture.read_bytes()
    require(hashlib.sha256(fixture_bytes).hexdigest() == FIXTURE_SHA256, "Unexpected public tutorial fixture")
    start = int(fixture_bytes[26:34])
    expected_first_ten = (323, 218, 220, 394, 267, 5, 183, 0, 70, 43)
    require(
        struct.unpack(">10H", fixture_bytes[start : start + 20]) == expected_first_ten,
        "Independent tutorial DATA read differs",
    )
    example = FlowData(str(fixture))
    require(
        example.version == "2.0" and example.event_count == 13367 and example.channel_count == 8,
        "Tutorial fixture metadata differs from the published tutorial",
    )
    require(tuple(example.events[:10]) == expected_first_ten, "Tutorial raw events differ")
    metadata = FlowData(str(fixture), only_text=True)
    require(metadata.events is None and metadata.event_count == 13367, "Metadata-only behavior differs")
    return {
        "schema_version": 1,
        "platform": platform.system(),
        "python": platform.python_version(),
        "flowio": version("flowio"),
        "numpy": np.__version__,
        "skill_sha256": hashlib.sha256((OVERLAY / "SKILL.md").read_bytes()).hexdigest(),
        "fixture_sha256": FIXTURE_SHA256,
        "checks": [
            "original_writer_arguments_fail",
            "original_metadata_keyword_fails",
            "float32_data_bytes_and_raw_round_trip",
            "normalized_metadata_and_channels",
            "existing_output_not_overwritten",
            "invalid_values_rejected_before_write",
            "gain_divides_in_tested_case",
            "null_channel_does_not_drop_columns",
            "tutorial_file_metadata_and_independent_raw_bytes",
            "tutorial_metadata_only",
        ],
        "agent_performance_tested": False,
        "full_skill_reviewed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.fixture), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
