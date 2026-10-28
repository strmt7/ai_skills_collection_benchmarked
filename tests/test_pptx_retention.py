"""Corrupt retained facts while preserving their tokens elsewhere in output."""

import io
import struct
import zipfile

import _pptx_retention as retention
import pytest
from _pptx_retention import MAX_MARKDOWN_BYTES, evaluate_markdown, normalize_package
from defusedxml.common import DTDForbidden

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


def _zip(entries):
    """Construct a small owned ZIP from ordered names and bytes."""
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for name, content in entries:
            package.writestr(name, content)
    return target.getvalue()


@pytest.mark.parametrize("encoding", ["utf-8", "utf-16"])
def test_core_properties_reject_dtds_and_entities(encoding):
    """DTD and entity declarations are rejected in both supported XML encodings."""
    xml = '<!DOCTYPE core [<!ENTITY probe "expanded">]><core>&probe;</core>'.encode(encoding)
    with pytest.raises(DTDForbidden):
        normalize_package(_zip([("docProps/core.xml", xml)]))


@pytest.mark.parametrize("name", ["../outside", "/absolute", "C:/outside", "a/../outside", "a//b"])
def test_package_rejects_unsafe_member_paths(name):
    """Archive member names cannot escape a downstream extraction root."""
    with pytest.raises(ValueError, match="unsafe ZIP member"):
        normalize_package(_zip([(name, b"content")]))


def test_package_rejects_backslashes_duplicates_and_forged_sizes():
    """Malformed ZIP names and directory sizes are rejected before publication."""
    raw = _zip([("a/b", b"x")])
    assert raw.count(b"a/b") == 2
    with pytest.raises(ValueError, match="unsafe ZIP member"):
        normalize_package(raw.replace(b"a/b", b"a\\b"))
    with pytest.warns(UserWarning, match="Duplicate name"):
        duplicate = _zip([("same", b"1"), ("same", b"2")])
    with pytest.raises(ValueError, match="duplicate ZIP"):
        normalize_package(duplicate)
    corrupt = bytearray(_zip([("value.txt", b"12345678")]))
    directory = corrupt.find(b"PK\x01\x02")
    assert directory >= 0
    struct.pack_into("<I", corrupt, directory + 24, 1)
    with pytest.raises(zipfile.BadZipFile):
        normalize_package(bytes(corrupt))


@pytest.mark.parametrize("method", [zipfile.ZIP_BZIP2, zipfile.ZIP_LZMA])
def test_package_rejects_unsupported_compression(method):
    """The fixed fixture admits only stored and deflated ZIP members."""
    raw = bytearray(_zip([("content", b"small")]))
    directory = raw.find(b"PK\x01\x02")
    assert directory >= 0
    struct.pack_into("<H", raw, 8, method)
    struct.pack_into("<H", raw, directory + 10, method)
    with pytest.raises(ValueError, match="compression method"):
        normalize_package(bytes(raw))


def test_package_rejects_encrypted_members():
    """Encrypted members are rejected without attempting password resolution."""
    raw = bytearray(_zip([("content", b"small")]))
    directory = raw.find(b"PK\x01\x02")
    assert directory >= 0
    struct.pack_into("<H", raw, 6, 1)
    struct.pack_into("<H", raw, directory + 8, 1)
    with pytest.raises(ValueError, match="encrypted"):
        normalize_package(bytes(raw))


def test_package_limits_nesting_members_and_expansion():
    """Archive budgets apply cumulatively and allow their documented boundaries."""
    inner = _zip([("ok", b"x")])
    with pytest.raises(ValueError, match="depth"):
        normalize_package(_zip([("nested.xlsx", _zip([("too-deep.xlsx", inner)]))]))
    assert normalize_package(_zip([(f"member-{i}", b"") for i in range(retention.MAX_ARCHIVE_MEMBERS)]))
    with pytest.raises(ValueError, match="member"):
        normalize_package(_zip([(f"member-{i}", b"") for i in range(retention.MAX_ARCHIVE_MEMBERS + 1)]))
    member = b"x" * retention.MAX_MEMBER_BYTES
    assert normalize_package(_zip([("member", member)]))
    with pytest.raises(ValueError, match="member exceeds"):
        normalize_package(_zip([("member", member + b"x")]))
    maximum = [(f"file-{i}", member) for i in range(4)]
    assert normalize_package(_zip(maximum))
    with pytest.raises(ValueError, match="expanded byte"):
        normalize_package(_zip([*maximum, ("one-more", b"x")]))


def test_package_limit_accepts_boundary_and_rejects_excess():
    """A ZIP at the compressed byte limit passes and one byte more fails."""
    empty = io.BytesIO()
    with zipfile.ZipFile(empty, "w", compression=zipfile.ZIP_STORED) as package:
        package.writestr("payload", b"")
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as package:
        package.writestr("payload", b"x" * (retention.MAX_PACKAGE_BYTES - len(empty.getvalue())))
    raw = target.getvalue()
    assert len(raw) == retention.MAX_PACKAGE_BYTES
    assert normalize_package(raw)
    with pytest.raises(ValueError, match="compressed byte"):
        normalize_package(raw + b"x")


def test_embedded_packages_share_member_and_expansion_budgets(monkeypatch):
    """Limits apply across the presentation and its embedded workbook together."""
    workbook = _zip([("first", b"x"), ("second", b"y")])
    outer = _zip([("book.xlsx", workbook), ("outside", b"z")])
    monkeypatch.setattr(retention, "MAX_ARCHIVE_MEMBERS", 3)
    with pytest.raises(ValueError, match="archive member"):
        normalize_package(outer)
    monkeypatch.setattr(retention, "MAX_ARCHIVE_MEMBERS", 512)
    workbook = _zip([("content", b"x" * 700)])
    outer = _zip([("book.xlsx", workbook), ("outside", b"z" * 100)])
    assert len(workbook) + 100 < 800 < len(workbook) + 100 + 700
    monkeypatch.setattr(retention, "MAX_EXPANDED_BYTES", 800)
    with pytest.raises(ValueError, match="expanded byte"):
        normalize_package(outer)


def test_core_properties_limits_bytes_depth_and_nodes():
    """Core XML byte, depth and node boundaries are enforced before serialization."""
    xml = b"<core>" + b"x" * (retention.MAX_CORE_XML_BYTES - len(b"<core></core>")) + b"</core>"
    assert normalize_package(_zip([("docProps/core.xml", xml)]))
    with pytest.raises(ValueError, match="XML byte"):
        normalize_package(_zip([("docProps/core.xml", xml + b" ")]))
    depth = b"<x>" * retention.MAX_CORE_XML_DEPTH + b"</x>" * retention.MAX_CORE_XML_DEPTH
    assert normalize_package(_zip([("docProps/core.xml", depth)]))
    with pytest.raises(ValueError, match="XML structure"):
        normalize_package(_zip([("docProps/core.xml", b"<x>" + depth + b"</x>")]))
    nodes = b"<root>" + b"<x/>" * (retention.MAX_CORE_XML_NODES - 1) + b"</root>"
    assert normalize_package(_zip([("docProps/core.xml", nodes)]))
    with pytest.raises(ValueError, match="XML structure"):
        normalize_package(_zip([("docProps/core.xml", b"<root><x/>" + nodes[6:])]))


def test_uppercase_workbook_extension_is_normalized():
    """Embedded workbook extension casing does not skip normalization."""
    raw = normalize_package(_zip([("workbook.XLSX", _zip([("ok", b"x")]))]))
    with zipfile.ZipFile(io.BytesIO(raw)) as outer, zipfile.ZipFile(io.BytesIO(outer.read("workbook.XLSX"))) as inner:
        assert inner.getinfo("ok").date_time == (2026, 1, 1, 0, 0, 0)
