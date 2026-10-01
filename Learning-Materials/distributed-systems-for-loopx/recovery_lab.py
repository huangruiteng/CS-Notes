#!/usr/bin/env python3
"""Isolated teaching lab: SQLite boundaries plus one abstract scheduling model.

No LoopX imports, network, credentials, or persistent user data. Temporary
databases are removed on exit. Lost responses/exceptions are simulated; this
does not qualify OS-crash or power-loss durability, or distributed fencing.
"""

import json
import sqlite3
import tempfile
from pathlib import Path


class LostResponse(Exception):
    pass


class BeforeCommit(Exception):
    pass


def connect(path):
    return sqlite3.connect(path, isolation_level=None)


def initialize(path):
    db = connect(path)
    try:
        db.executescript("""
            CREATE TABLE account (id INTEGER PRIMARY KEY, balance INTEGER);
            INSERT INTO account VALUES (1, 100);
            CREATE TABLE receipts (
                op_id TEXT PRIMARY KEY, amount INTEGER NOT NULL,
                balance_after INTEGER NOT NULL
            );
            CREATE TABLE resource (
                id INTEGER PRIMARY KEY, epoch INTEGER NOT NULL, value TEXT
            );
            INSERT INTO resource VALUES (1, 7, 'initial');
            CREATE TABLE projection (
                id INTEGER PRIMARY KEY, revision INTEGER NOT NULL, value TEXT
            );
            INSERT INTO projection VALUES (1, 0, 'initial');
        """)
    finally:
        db.close()


def row(path, sql):
    db = connect(path)
    try:
        return db.execute(sql).fetchone()
    finally:
        db.close()


def naive_debit(path, amount, lose_response=False):
    db = connect(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        db.execute("UPDATE account SET balance = balance - ? WHERE id = 1", (amount,))
        db.commit()
    finally:
        db.close()
    if lose_response:
        raise LostResponse("committed; caller did not receive the response")


def debit_once(path, op_id, amount, lose_response=False, fail_before_commit=False):
    if amount <= 0:
        raise ValueError("amount must be positive")
    db = connect(path)
    try:
        # Serializes writers in this SQLite file. Receipt and balance are in
        # the SAME transaction; this would not protect an external API call.
        db.execute("BEGIN IMMEDIATE")
        prior = db.execute(
            "SELECT amount, balance_after FROM receipts WHERE op_id = ?", (op_id,)
        ).fetchone()
        if prior is not None:
            if prior[0] != amount:
                raise ValueError("same operation id, different payload")
            result = {"balance_after": prior[1], "replayed": True}
        else:
            changed = db.execute(
                "UPDATE account SET balance = balance - ? "
                "WHERE id = 1 AND balance >= ?", (amount, amount)
            ).rowcount
            if changed != 1:
                raise ValueError("insufficient balance")
            balance = db.execute("SELECT balance FROM account WHERE id = 1").fetchone()[0]
            db.execute("INSERT INTO receipts VALUES (?, ?, ?)", (op_id, amount, balance))
            result = {"balance_after": balance, "replayed": False}
        if fail_before_commit:
            raise BeforeCommit("caller interrupts the transaction before commit")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    if lose_response:
        raise LostResponse("committed receipt and balance; response unavailable")
    return result


def fence_lab(path):
    db = connect(path)
    try:
        # Authority epoch and protected resource share ONE database boundary.
        # No wall-clock lease and no distributed token installer is simulated.
        db.execute("UPDATE resource SET epoch = 8, value = 'new-owner' WHERE id = 1")
        db.execute("UPDATE resource SET value = 'old-owner' WHERE id = 1")
        assert db.execute("SELECT value FROM resource").fetchone()[0] == "old-owner"
        db.execute("UPDATE resource SET value = 'new-owner' WHERE id = 1")
        stale = db.execute(
            "UPDATE resource SET value = ? WHERE id = 1 AND epoch = ?", ("old-owner", 7)
        ).rowcount
        current = db.execute(
            "UPDATE resource SET value = ? WHERE id = 1 AND epoch = ?", ("current-update", 8)
        ).rowcount
        assert stale == 0 and current == 1
        assert db.execute("SELECT value FROM resource").fetchone()[0] == "current-update"
        return {"unguarded_old_write": "overwrote new owner", "stale_rejected": True}
    finally:
        db.close()


def install_snapshot(path, revision, value):
    db = connect(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        old_revision, old_value = db.execute(
            "SELECT revision, value FROM projection WHERE id = 1"
        ).fetchone()
        if revision == old_revision and value != old_value:
            raise ValueError("same revision with conflicting snapshot")
        changed = db.execute(
            "UPDATE projection SET revision = ?, value = ? "
            "WHERE id = 1 AND revision < ?", (revision, value, revision)
        ).rowcount
        db.commit()
        return changed == 1
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def write_skew_model():
    # An abstract interleaving, NOT a SQLite snapshot-isolation experiment.
    snapshot_for_a = {"a": True, "b": True}
    snapshot_for_b = dict(snapshot_for_a)
    state = dict(snapshot_for_a)
    a_may_leave = snapshot_for_a["b"]
    b_may_leave = snapshot_for_b["a"]
    if a_may_leave:
        state["a"] = False
    if b_may_leave:
        state["b"] = False
    assert not any(state.values())  # The specified invariant is violated.

    serial = {"a": True, "b": True}
    if serial["b"]:
        serial["a"] = False
    if serial["a"]:
        serial["b"] = False
    assert any(serial.values())
    return {"concurrent_snapshot_remaining": 0, "serial_remaining": 1}


def main():
    with tempfile.TemporaryDirectory(prefix="loopx-learning-") as temporary:
        root = Path(temporary)
        naive, durable, rollback = [root / name for name in ("naive.db", "durable.db", "rollback.db")]
        for path in (naive, durable, rollback):
            initialize(path)

        try:
            naive_debit(naive, 10, lose_response=True)
        except LostResponse:
            naive_debit(naive, 10)
        naive_balance = row(naive, "SELECT balance FROM account")[0]
        assert naive_balance == 80

        try:
            debit_once(durable, "op-7", 10, lose_response=True)
        except LostResponse:
            recovered = debit_once(durable, "op-7", 10)
        assert recovered == {"balance_after": 90, "replayed": True}
        assert row(durable, "SELECT balance FROM account")[0] == 90
        assert row(durable, "SELECT COUNT(*) FROM receipts")[0] == 1
        try:
            debit_once(durable, "op-7", 20)
        except ValueError as error:
            assert "different payload" in str(error)
        else:
            raise AssertionError("conflicting intent was accepted")
        assert row(durable, "SELECT balance FROM account")[0] == 90

        try:
            debit_once(rollback, "op-8", 10, fail_before_commit=True)
        except BeforeCommit:
            pass
        assert row(rollback, "SELECT balance FROM account")[0] == 100
        assert row(rollback, "SELECT COUNT(*) FROM receipts")[0] == 0

        fence_result = fence_lab(durable)
        assert install_snapshot(durable, 11, "new")
        assert not install_snapshot(durable, 10, "old")
        assert not install_snapshot(durable, 11, "new")
        assert row(durable, "SELECT revision, value FROM projection") == (11, "new")
        try:
            install_snapshot(durable, 11, "conflict")
        except ValueError:
            pass
        else:
            raise AssertionError("conflicting projection revision was accepted")

        print(json.dumps({
            "status": "teaching expectations passed",
            "sqlite_version": sqlite3.sqlite_version,
            "lost_response": {"naive_balance": naive_balance, "idempotent_balance": 90},
            "payload_conflict": "rejected without a second debit",
            "before_commit": "balance and receipt rolled back together",
            "fencing": fence_result,
            "projection": "revision 11 preserved after 10 and duplicate 11",
            "write_skew_abstract_model": write_skew_model(),
            "limits": ["no actual process kill or power loss", "no network or multi-host authority",
                       "projection uses full snapshots, not deltas", "no LoopX production qualification"]
        }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
