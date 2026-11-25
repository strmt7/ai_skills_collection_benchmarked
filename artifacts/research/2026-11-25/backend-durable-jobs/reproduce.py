"""Exercise a durable job contract across independent processes."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

CRASH = 73
SCHEMA = """
CREATE TABLE requests (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
CREATE TABLE jobs (
    request_id TEXT PRIMARY KEY REFERENCES requests(id),
    state TEXT NOT NULL DEFAULT 'ready' CHECK(state IN ('ready','leased','done')),
    generation INTEGER NOT NULL DEFAULT 0,
    lease_until INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE applied (request_id TEXT PRIMARY KEY REFERENCES requests(id));
"""


def accept(db: sqlite3.Connection, key: str, payload: str, stop: str) -> dict:
    db.execute("BEGIN IMMEDIATE")
    existing = db.execute("SELECT payload FROM requests WHERE id = ?", (key,)).fetchone()
    if existing is None:
        db.execute("INSERT INTO requests VALUES (?, ?)", (key, payload))
        db.execute("INSERT INTO jobs(request_id) VALUES (?)", (key,))
    elif existing[0] != payload:
        db.execute("ROLLBACK")
        return {"status": "conflict"}
    if stop == "before_commit":
        os._exit(CRASH)
    db.execute("COMMIT")
    if stop == "after_commit":
        os._exit(CRASH)
    return {"status": "accepted", "job": key}


def claim(db: sqlite3.Connection, now: int) -> dict:
    row = db.execute(
        """
        UPDATE jobs SET state = 'leased', generation = generation + 1, lease_until = ?
        WHERE request_id = (
            SELECT request_id FROM jobs
            WHERE state = 'ready' OR (state = 'leased' AND lease_until <= ?)
            ORDER BY request_id LIMIT 1
        )
        RETURNING request_id, generation, lease_until
        """,
        (now + 10, now),
    ).fetchone()
    if row is None:
        return {"status": "empty"}
    return {"status": "leased", "job": row[0], "generation": row[1], "expires": row[2]}


def finish(db: sqlite3.Connection, key: str, generation: int, now: int, stop: str) -> dict:
    db.execute("BEGIN IMMEDIATE")
    fenced = db.execute(
        """
        UPDATE jobs SET state = 'done'
        WHERE request_id = ? AND state = 'leased' AND generation = ? AND lease_until > ?
        RETURNING request_id
        """,
        (key, generation, now),
    ).fetchone()
    if fenced is None:
        db.execute("ROLLBACK")
        return {"status": "lease_rejected"}
    db.execute("INSERT INTO applied VALUES (?)", (key,))
    if stop == "before_commit":
        os._exit(CRASH)
    db.execute("COMMIT")
    if stop == "after_commit":
        os._exit(CRASH)
    return {"status": "completed"}


def state(db: sqlite3.Connection) -> dict:
    return {
        "requests": db.execute("SELECT id FROM requests ORDER BY id").fetchall(),
        "jobs": db.execute("SELECT request_id, state, generation FROM jobs ORDER BY request_id").fetchall(),
        "effects": db.execute("SELECT request_id FROM applied ORDER BY request_id").fetchall(),
    }


def child(database: Path, operation: str, parameters: list[str]) -> None:
    with closing(sqlite3.connect(database, isolation_level=None, timeout=3)) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        if operation == "initialize":
            assert db.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
            db.executescript(SCHEMA)
            result = {"status": "ready"}
        elif operation == "accept":
            key, payload, stop = parameters
            result = accept(db, key, payload, stop)
        elif operation == "claim":
            result = claim(db, int(parameters[0]))
        elif operation == "finish":
            key, generation, now, stop = parameters
            result = finish(db, key, int(generation), int(now), stop)
        elif operation == "state":
            result = state(db)
        else:
            raise ValueError(f"Unknown worker operation {operation}")
        print(json.dumps(result), flush=True)


def investigate(output: Path) -> dict:
    with TemporaryDirectory(dir=output.parent) as directory:
        database = Path(directory) / "queue.sqlite3"
        observed = []

        def expect(operation: str, parameters: list[str], result: dict | None) -> None:
            command = [sys.executable, "-B", str(Path(__file__).resolve()), "--database", str(database), operation]
            native = subprocess.run([*command, *parameters], cwd=directory, capture_output=True, timeout=8, check=False)
            assert not native.stderr, native.stderr.decode()
            if result is None:
                assert native.returncode == CRASH and not native.stdout
            else:
                assert native.returncode == 0 and json.loads(native.stdout) == result
            observed.append(
                {"operation": operation, "parameters": parameters, "exit": native.returncode, "value": result}
            )

        expect("initialize", [], {"status": "ready"})
        expect("accept", ["example-order", "blue", "before_commit"], None)
        expect("state", [], {"requests": [], "jobs": [], "effects": []})
        expect("accept", ["example-order", "blue", "after_commit"], None)
        expect("state", [], {"requests": [["example-order"]], "jobs": [["example-order", "ready", 0]], "effects": []})
        expect("accept", ["example-order", "blue", "none"], {"status": "accepted", "job": "example-order"})
        expect("accept", ["example-order", "green", "none"], {"status": "conflict"})
        expect("claim", ["10"], {"status": "leased", "job": "example-order", "generation": 1, "expires": 20})
        expect("claim", ["19"], {"status": "empty"})
        expect("finish", ["example-order", "1", "19", "before_commit"], None)
        expect("state", [], {"requests": [["example-order"]], "jobs": [["example-order", "leased", 1]], "effects": []})
        expect("claim", ["20"], {"status": "leased", "job": "example-order", "generation": 2, "expires": 30})
        expect("finish", ["example-order", "1", "22", "none"], {"status": "lease_rejected"})
        expect("finish", ["example-order", "2", "22", "after_commit"], None)
        expect("claim", ["30"], {"status": "empty"})
        expect(
            "state",
            [],
            {"requests": [["example-order"]], "jobs": [["example-order", "done", 2]], "effects": [["example-order"]]},
        )
    return {
        "scope": "Single SQLite database with a transactional local effect",
        "sqlite": sqlite3.sqlite_version,
        "events": observed,
        "model_attempts": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--database", type=Path)
    selection.add_argument("--output", type=Path)
    parser.add_argument("parameters", nargs="*")
    options = parser.parse_args()
    if options.database is not None:
        operation, *arguments = options.parameters
        child(options.database, operation, arguments)
        return
    if options.parameters:
        parser.error("Worker arguments require --database")
    report = investigate(options.output)
    with options.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"native_events": len(report["events"]), "model_attempts": 0}))


if __name__ == "__main__":
    main()
