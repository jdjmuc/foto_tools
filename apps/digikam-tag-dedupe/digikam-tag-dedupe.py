#!/usr/bin/env python3

import argparse
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class TagMerge:
    source_id: int
    target_id: int
    name: str
    target_path: str


def tag_path(tag_id: int, tags: dict[int, tuple[str, int | None]]) -> str:
    parts: list[str] = []
    current_id: int | None = tag_id
    while current_id is not None and current_id in tags:
        name, parent_id = tags[current_id]
        parts.append(name)
        current_id = parent_id
    return "/".join(reversed(parts))


def find_merges(connection: sqlite3.Connection) -> tuple[list[TagMerge], list[str]]:
    rows = connection.execute("SELECT id, name, pid FROM Tags ORDER BY id").fetchall()
    tags = {row["id"]: (row["name"], row["pid"]) for row in rows}
    top_level: dict[str, list[int]] = {}
    nested: dict[str, list[int]] = {}

    for row in rows:
        if row["pid"] is None or row["pid"] == 0:
            top_level.setdefault(row["name"], []).append(row["id"])
        else:
            nested.setdefault(row["name"], []).append(row["id"])

    merges: list[TagMerge] = []
    skipped: list[str] = []
    for name, source_ids in top_level.items():
        target_ids = nested.get(name, [])
        if not target_ids:
            continue
        if len(target_ids) != 1:
            skipped.append(
                f"Skipping {name!r}: found {len(target_ids)} nested tags with that name"
            )
            continue
        target_id = target_ids[0]
        target_path = tag_path(target_id, tags)
        merges.extend(
            TagMerge(source_id, target_id, name, target_path)
            for source_id in source_ids
        )
    return merges, skipped


def merge_tag(connection: sqlite3.Connection, merge: TagMerge) -> None:
    source_id = merge.source_id
    target_id = merge.target_id

    connection.execute(
        """
        INSERT OR IGNORE INTO ImageTags (imageid, tagid)
        SELECT imageid, ? FROM ImageTags WHERE tagid = ?
        """,
        (target_id, source_id),
    )
    connection.execute("DELETE FROM ImageTags WHERE tagid = ?", (source_id,))

    connection.execute(
        """
        INSERT INTO TagProperties (tagid, property, value)
        SELECT DISTINCT ?, src.property, src.value
        FROM TagProperties AS src
        WHERE src.tagid = ?
          AND NOT EXISTS (
              SELECT 1 FROM TagProperties AS dst
              WHERE dst.tagid = ?
                AND dst.property IS src.property
                AND dst.value IS src.value
          )
        """,
        (target_id, source_id, target_id),
    )
    connection.execute("DELETE FROM TagProperties WHERE tagid = ?", (source_id,))

    connection.execute(
        """
        INSERT INTO ImageTagProperties (imageid, tagid, property, value)
        SELECT DISTINCT src.imageid, ?, src.property, src.value
        FROM ImageTagProperties AS src
        WHERE src.tagid = ?
          AND NOT EXISTS (
              SELECT 1 FROM ImageTagProperties AS dst
              WHERE dst.imageid IS src.imageid
                AND dst.tagid = ?
                AND dst.property IS src.property
                AND dst.value IS src.value
          )
        """,
        (target_id, source_id, target_id),
    )
    connection.execute(
        "DELETE FROM ImageTagProperties WHERE tagid = ?", (source_id,)
    )

    connection.execute("DELETE FROM TagsTree WHERE id = ?", (source_id,))
    connection.execute("DELETE FROM Tags WHERE id = ?", (source_id,))


def make_backup(connection: sqlite3.Connection, database: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = database.with_name(f"{database.name}.{timestamp}.bak")
    suffix = 1
    while backup.exists():
        backup = database.with_name(f"{database.name}.{timestamp}-{suffix}.bak")
        suffix += 1

    with sqlite3.connect(backup) as backup_connection:
        connection.backup(backup_connection)
    return backup


def main() -> int:
    default_database = Path(__file__).resolve().parents[2] / "data" / "digikam4.db"
    parser = argparse.ArgumentParser(
        description=(
            "Merge root tags into the unique nested tag with the exact same name."
        )
    )
    parser.add_argument(
        "database",
        nargs="?",
        type=Path,
        default=default_database,
        help=f"Digikam SQLite database (default: {default_database})",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the merges; otherwise only show the planned changes",
    )
    args = parser.parse_args()
    database = args.database.expanduser().resolve()

    if not database.is_file():
        print(f"Error: database not found: {database}", file=sys.stderr)
        return 1

    try:
        if args.apply:
            with sqlite3.connect(database) as connection:
                connection.row_factory = sqlite3.Row
                backup = make_backup(connection, database)
                connection.execute("BEGIN IMMEDIATE")
                merges, skipped = find_merges(connection)
                for merge in merges:
                    merge_tag(connection, merge)
                connection.commit()
        else:
            uri = f"{database.as_uri()}?mode=ro"
            with sqlite3.connect(uri, uri=True) as connection:
                connection.row_factory = sqlite3.Row
                merges, skipped = find_merges(connection)
            backup = None
    except sqlite3.Error as error:
        print(f"Database error: {error}", file=sys.stderr)
        return 1

    for merge in merges:
        print(
            f"{'Merged' if args.apply else 'Would merge'} "
            f"{merge.name!r} (id {merge.source_id}) -> "
            f"{merge.target_path!r} (id {merge.target_id})"
        )
    for message in skipped:
        print(message, file=sys.stderr)

    if args.apply:
        print(f"Applied {len(merges)} merge(s). Backup: {backup}")
    else:
        print(
            f"Found {len(merges)} merge(s). No changes made; "
            "pass --apply to execute them."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
