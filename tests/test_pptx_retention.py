"""Corrupt retained facts while preserving their tokens elsewhere in output."""

import io
import zipfile

import pytest
from _pptx_retention import MAX_MARKDOWN_BYTES, evaluate_markdown, normalize_package

MARKDOWN = """# retention
## Slide 1
Unicode control Alpha β Omega Ω
\\## Slide 33
[Reference_link_control](https://example.invalid/evidence)
| Table_header_A | Table_header_B |
| --- | --- |
| Table_body_C | Table_body_D |
### Speaker Notes
Speaker_note_control_K26
## Slide 2
| Category | Bar_series |
| --- | --- |
| North_Unit | 0 |
| South_Unit | -7.125 |

| Series | Point | X | Y |
| --- | --- | --- | --- |
| XY_series_control | 1 | 1.25 | -2.5 |
| XY_series_control | 2 | 2.75 | 0 |
Grouped_text_control_δ
## Slide 3
Office14_choice_text_control
"""


def test_authored_facts_are_retained():
    assert all(evaluate_markdown(MARKDOWN).values())


@pytest.mark.parametrize(
    ("before", "after", "check"),
    [
        ("| 1 | 1.25 | -2.5 |", "| 1 | 2.75 | -2.5 |", "xy_coordinates"),
        ("| 2 | 2.75 | 0 |", "| 2 | 1.25 | 0 |", "xy_coordinates"),
        ("North_Unit | 0", "North_Unit | -7.125", "category_numeric_value"),
        ("South_Unit | -7.125", "South_Unit | 0", "category_numeric_value"),
        ("North_Unit | 0", "North_Unit | ", "category_numeric_value"),
        ("| 2 | 2.75 | 0 |", "| 1 | 2.75 | 0 |", "xy_coordinates"),
        ("| 2 | 2.75 | 0 |", "| 2 | 2.75 | NaN |", "xy_coordinates"),
        ("| Table_body_C | Table_body_D |", "| Table_body_D | Table_body_C |", "table_cells"),
        ("\\## Slide 33", "## Slide 33", "slide_heading_count"),
        ("## Slide 3", "## Slide 2", "slide_heading_count"),
    ],
)
def test_corrupted_associations_fail(before, after, check):
    assert not evaluate_markdown(MARKDOWN.replace(before, after))[check]


@pytest.mark.parametrize(
    ("token", "check"),
    [
        ("Unicode control Alpha β Omega Ω", "unicode_text"),
        ("Speaker_note_control_K26", "speaker_notes"),
        ("Grouped_text_control_δ", "grouped_text"),
        ("Office14_choice_text_control", "office14_choice_text"),
        ("[Reference_link_control](https://example.invalid/evidence)", "hyperlink"),
    ],
)
def test_tokens_moved_to_metadata_do_not_pass(token, check):
    corrupted = f"{token}\n" + MARKDOWN.replace(token, "removed")
    assert token in corrupted
    assert not evaluate_markdown(corrupted)[check]


def test_duplicate_tables_are_ambiguous():
    duplicate = "| Table_header_A | Table_header_B |\n| --- | --- |\n| wrong | wrong |\n"
    assert not evaluate_markdown(MARKDOWN.replace("### Speaker Notes", duplicate + "### Speaker Notes"))["table_cells"]


def test_equivalent_numeric_spellings_are_accepted():
    text = MARKDOWN.replace("North_Unit | 0", "North_Unit | 0.0").replace("| 1 | 1.25 |", "| 1.0 | 1.25e0 |")
    assert all(evaluate_markdown(text).values())


def test_evaluation_is_bounded():
    with pytest.raises(ValueError, match="one MiB"):
        evaluate_markdown("x" * (MAX_MARKDOWN_BYTES + 1))


def test_embedded_workbook_dates_do_not_change_fixture_bytes():
    def archive(date, workbook=None):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as package:
            package.writestr(
                zipfile.ZipInfo("docProps/core.xml", date_time=date),
                '<core xmlns:dcterms="http://purl.org/dc/terms/"><dcterms:created>'
                + str(date[0])
                + "-02-03T04:05:06Z</dcterms:created><dcterms:modified>"
                + str(date[0])
                + "-02-03T04:05:06Z</dcterms:modified></core>",
            )
            package.writestr("stable.txt", b"authored content")
            if workbook is not None:
                package.writestr("ppt/embeddings/chart.xlsx", workbook)
        return buffer.getvalue()

    early = (2024, 2, 3, 4, 5, 6)
    late = (2026, 9, 8, 7, 6, 5)
    first = archive(early, archive(early))
    second = archive(late, archive(late))
    assert first != second
    normalized = normalize_package(first)
    assert normalized == normalize_package(second)
    assert normalized == normalize_package(normalized)
    with zipfile.ZipFile(io.BytesIO(normalized)) as package:
        assert package.read("stable.txt") == b"authored content"
