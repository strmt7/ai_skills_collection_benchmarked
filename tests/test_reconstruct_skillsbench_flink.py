import gzip

import pytest
import reconstruct_skillsbench_flink as target


@pytest.mark.parametrize(
    ("times", "equal", "expected"),
    [
        ([0], True, 1),
        ([0, 599_999_999], True, 2),
        ([0, 600_000_000], True, 1),
        ([0, 600_000_000], False, 2),
        ([0, 600_000_001], False, 1),
        ([600_000_001, 0, 0, 1], True, 3),
        ([650_000_000, 0, 600_000_001, 600_000_000], True, 3),
    ],
)
def test_stage_boundaries_and_repeated_submissions(times, equal, expected):
    assert target.longest_stage(times, split_on_equal=equal) == expected


def test_no_observed_submissions_is_not_silently_a_stage():
    with pytest.raises(ValueError, match="at least one"):
        target.longest_stage([], split_on_equal=True)


def test_events_select_type_and_preserve_repeated_submits():
    data = gzip.compress(b"10,,7,1,,0\n10,,7,1,,0\n11,,7,1,,4\n20,,8,1,,0\n")
    assert target.parse_events(data, 5, "0") == {7: [10, 10], 8: [20]}


def test_reference_rejects_duplicates_and_malformed_rows():
    with pytest.raises(ValueError, match="Duplicate"):
        target.parse_reference(b"(7,2)\n(7,2)\n")
    with pytest.raises(ValueError, match="Malformed"):
        target.parse_reference(b"(7,2,3)\n")
