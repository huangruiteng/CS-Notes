"""Native caller provenance checks against disposable host metadata only."""

import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from material_host_context import resolve_native_owner_turn


class NativeOwnerTurnTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.workspace = self.home / "project"
        self.workspace.mkdir()
        self.thread = "11111111-1111-4111-8111-111111111111"
        self.turn = "22222222-2222-4222-8222-222222222222"
        self.env = {"CODEX_THREAD_ID": self.thread, "CODEX_SESSION_ID": self.thread}
        self.rollout = self.home / "sessions/rollout.jsonl"
        self.rollout.parent.mkdir()
        self.records = [
            {"type": "session_meta", "payload": {"id": self.thread, "cwd": str(self.workspace), "source": "vscode", "originator": "Codex Desktop"}},
            {"type": "event_msg", "payload": {"type": "task_started", "turn_id": self.turn}},
            {"type": "turn_context", "payload": {"turn_id": self.turn, "cwd": str(self.workspace), "sandbox_policy": {"type": "workspace-write"}}},
            {"type": "response_item", "payload": {"private_fixture": "must not enter the returned context"}},
        ]
        self.index = self.home / "state_5.sqlite"
        with sqlite3.connect(self.index) as connection:
            connection.execute("CREATE TABLE threads (id TEXT, cwd TEXT, rollout_path TEXT, archived INTEGER)")
            connection.execute("INSERT INTO threads VALUES (?, ?, ?, 0)", (self.thread, str(self.workspace), str(self.rollout)))
        self.flush()

    def flush(self):
        self.rollout.write_text("".join(json.dumps(r) + "\n" for r in self.records))

    def resolve(self):
        return resolve_native_owner_turn(self.workspace, environ=self.env, homes=[self.home])

    def test_real_indexed_active_turn_needs_no_bot_session_and_exposes_no_payloads(self):
        before = self.index.read_bytes(), self.rollout.read_bytes()
        context = self.resolve()
        self.assertEqual((context["host_surface"], context["turn_id"]), ("codex-app", self.turn))
        self.assertNotIn("private_fixture", json.dumps(context))
        self.assertNotIn(str(self.workspace), json.dumps(context))
        self.assertEqual(before, (self.index.read_bytes(), self.rollout.read_bytes()))

    def test_environment_identity_without_native_index_is_rejected(self):
        self.env["CODEX_THREAD_ID"] = "33333333-3333-4333-8333-333333333333"
        self.env["CODEX_SESSION_ID"] = self.env["CODEX_THREAD_ID"]
        with self.assertRaisesRegex(ValueError, "missing or ambiguous"):
            self.resolve()

    def test_session_mismatch_is_rejected(self):
        self.env["CODEX_SESSION_ID"] = "another-session"
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.resolve()

    def test_native_cli_turn_is_supported(self):
        self.records[0]["payload"].update(source="cli", originator="codex_cli_rs")
        self.flush()
        self.assertEqual(self.resolve()["host_surface"], "codex-cli")

    def test_loopx_native_app_server_turn_keeps_provenance_and_write_fences(self):
        self.records[0]["payload"].update(source="vscode", originator="loopx_chat")
        self.flush()
        before = self.index.read_bytes(), self.rollout.read_bytes()
        context = self.resolve()
        self.assertEqual(context["host_surface"], "codex-app")
        self.assertEqual(context["turn_id"], self.turn)
        self.assertNotIn("private_fixture", json.dumps(context))
        self.assertEqual(before, (self.index.read_bytes(), self.rollout.read_bytes()))
        for policy in ("read-only", "external-sandbox"):
            with self.subTest(policy=policy):
                self.records[2]["payload"]["sandbox_policy"] = {"type": policy}
                self.flush()
                with self.assertRaisesRegex(ValueError, "does not grant workspace writes"):
                    self.resolve()
        self.records[2]["payload"]["sandbox_policy"] = {"type": "workspace-write"}
        self.records.append({"type": "event_msg", "payload": {"type": "task_complete", "turn_id": self.turn}})
        self.flush()
        with self.assertRaisesRegex(ValueError, "not active"):
            self.resolve()

    def test_loopx_origin_does_not_allow_a_different_or_structured_host_source(self):
        for source in ("cli", "unknown", {"subagent": {"other": "fixture"}}):
            with self.subTest(source=source):
                self.records[0]["payload"].update(source=source, originator="loopx_chat")
                self.flush()
                with self.assertRaisesRegex(ValueError, "unsupported native Codex host"):
                    self.resolve()

    def test_unreadable_host_index_is_rejected(self):
        self.index.write_bytes(b"invalid fixture database")
        with self.assertRaisesRegex(ValueError, "unavailable or incompatible"):
            self.resolve()

    def test_completed_aborted_and_missing_context_turns_are_rejected(self):
        for event in ("task_complete", "turn_aborted", "task_started"):
            with self.subTest(event=event):
                self.records.append({"type": "event_msg", "payload": {"type": event, "turn_id": self.turn}})
                self.flush()
                with self.assertRaisesRegex(ValueError, "not active"):
                    self.resolve()
                self.records.pop()

    def test_foreign_workspace_and_read_only_context_are_rejected(self):
        for key, value in (("cwd", str(self.home / "elsewhere")), ("sandbox_policy", {"type": "read-only"})):
            with self.subTest(key=key):
                old = self.records[2]["payload"][key]
                self.records[2]["payload"][key] = value
                self.flush()
                with self.assertRaises(ValueError):
                    self.resolve()
                self.records[2]["payload"][key] = old

    def test_unknown_origin_and_wrong_metadata_identity_are_rejected(self):
        for key, value in (("originator", "unregistered host"), ("id", "another-thread")):
            with self.subTest(key=key):
                old = self.records[0]["payload"][key]
                self.records[0]["payload"][key] = value
                self.flush()
                with self.assertRaises(ValueError):
                    self.resolve()
                self.records[0]["payload"][key] = old

    def test_archived_thread_and_external_rollout_are_rejected(self):
        for column, value in (("archived", 1), ("rollout_path", str(self.home / "external.jsonl"))):
            with self.subTest(column=column):
                with sqlite3.connect(self.index) as connection:
                    connection.execute(f"UPDATE threads SET {column} = ?", (value,))
                with self.assertRaises(ValueError):
                    self.resolve()
                with sqlite3.connect(self.index) as connection:
                    connection.execute("UPDATE threads SET archived=0, rollout_path=?", (str(self.rollout),))

    def test_new_turn_invalidates_the_previous_caller_context(self):
        previous = self.resolve()
        new_turn = "33333333-3333-4333-8333-333333333333"
        self.records.extend([
            {"type": "event_msg", "payload": {"type": "task_started", "turn_id": new_turn}},
            {"type": "turn_context", "payload": {**self.records[2]["payload"], "turn_id": new_turn}},
        ])
        self.flush()
        self.assertNotEqual(previous, self.resolve())

    def test_incomplete_native_record_fails_closed(self):
        with self.rollout.open("a") as stream:
            stream.write('{"type":')
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.resolve()


if __name__ == "__main__":
    unittest.main()
