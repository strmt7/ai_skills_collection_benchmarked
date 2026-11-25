import json
import sqlite3
import sys
from email.utils import format_datetime, parsedate_to_datetime
from pathlib import Path

output = Path(sys.argv[1])
connection = sqlite3.connect(":memory:")
with connection:
    connection.executescript(
        """
        CREATE TABLE messages (id TEXT PRIMARY KEY, created_at TEXT NOT NULL);
        CREATE INDEX created_id_asc ON messages(created_at DESC, id ASC);
        CREATE INDEX created_id_desc ON messages(created_at DESC, id DESC);
        """
    )
    connection.executemany(
        "INSERT INTO messages VALUES (?,?)",
        [
            ("a", "2026-11-01T12:00:00Z"),
            ("b", "2026-11-01T12:00:00Z"),
            ("c", "2026-11-01T12:00:00Z"),
            ("d", "2026-11-01T12:00:00Z"),
        ],
    )
    baseline = {
        mode: [
            connection.execute(
                f"SELECT id FROM messages INDEXED BY {index} ORDER BY created_at DESC LIMIT 2 OFFSET ?", (offset,)
            ).fetchall()
            for index, offset in zip(indexes, (0, 2), strict=True)
        ]
        for mode, indexes in {
            "one-plan": ("created_id_asc", "created_id_asc"),
            "changed-plan": ("created_id_asc", "created_id_desc"),
        }.items()
    }
    ordered = [
        connection.execute(
            f"SELECT id FROM messages INDEXED BY {index} ORDER BY created_at DESC, id DESC LIMIT 2 OFFSET ?", (offset,)
        ).fetchall()
        for index, offset in zip(("created_id_asc", "created_id_desc"), (0, 2), strict=True)
    ]
    first = connection.execute(
        "SELECT id,created_at FROM messages ORDER BY created_at DESC, id DESC LIMIT 2"
    ).fetchall()
    tail_id, tail_time = first[-1]
    connection.execute("INSERT INTO messages VALUES (?,?)", ("new", "2026-11-01T12:01:00Z"))
    second = connection.execute(
        "SELECT id, created_at FROM messages WHERE (created_at,id) < (?,?) ORDER BY created_at DESC,id DESC LIMIT 2",
        (tail_time, tail_id),
    ).fetchall()
assert [[row[0] for row in page] for page in baseline["one-plan"]] == [["a", "b"], ["c", "d"]]
assert [[row[0] for row in page] for page in baseline["changed-plan"]] == [["a", "b"], ["b", "a"]]
assert [[row[0] for row in page] for page in ordered] == [["d", "c"], ["b", "a"]]
assert [[row[0] for row in page] for page in [first, second]] == [["d", "c"], ["b", "a"]]
example = "Sat, 01 Jan 2026 00:00:00 GMT"
corrected = format_datetime(parsedate_to_datetime(example), usegmt=True)
assert corrected == "Thu, 01 Jan 2026 00:00:00 GMT"
result = {
    "sqlite": sqlite3.sqlite_version,
    "baseline_same_plan": [[r[0] for r in p] for p in baseline["one-plan"]],
    "baseline_plan_change": [[r[0] for r in p] for p in baseline["changed-plan"]],
    "unique_offset_order_plan_change": [[r[0] for r in p] for p in ordered],
    "unique_cursor_order_after_insertion": [[r[0] for r in p] for p in (first, second)],
    "example_http_date": example,
    "calendar_verified_date": corrected,
}
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(result))
connection.close()
