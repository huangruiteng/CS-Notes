"""Native caller provenance checks against disposable host metadata only."""

import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from material_host_context import has_native_host_env, resolve_native_owner_turn


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

    def test_has_native_host_env_detects_supported_hosts_and_rejects_empty(self):
        self.assertFalse(has_native_host_env({}))
        self.assertTrue(has_native_host_env(self.env))
        self.assertTrue(has_native_host_env({"ANTIGRAVITY_AGENT": "1"}))
        self.assertTrue(has_native_host_env({"CLAUDECODE": "1"}))

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

    def test_ambiguous_multi_host_environment_fails_closed(self):
        mixed = {**self.env, "ANTIGRAVITY_AGENT": "1", "ANTIGRAVITY_CONVERSATION_ID": self.thread}
        with self.assertRaisesRegex(ValueError, "ambiguous native agent host"):
            resolve_native_owner_turn(self.workspace, environ=mixed, homes=[self.home])


class AntigravityAndClaudeNativeTurnTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "project"
        self.workspace.mkdir()
        self.conversation = "44444444-4444-4444-8444-444444444444"
        self.app_dir = self.root / "antigravity"
        self.transcript = self.app_dir / "brain" / self.conversation / ".system_generated/logs/transcript.jsonl"
        self.transcript.parent.mkdir(parents=True)

    def _write_lines(self, path, records):
        path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")

    def _agy_env(self, step_index, *, ws="outside-of-project"):
        return {
            "ANTIGRAVITY_AGENT": "1",
            "ANTIGRAVITY_CONVERSATION_ID": self.conversation,
            "ANTIGRAVITY_WORKSPACE_PATH": ws,
            "ANTIGRAVITY_SOURCE_METADATA": json.dumps(
                {"tool": {"conversationId": self.conversation, "stepIndex": step_index}}
            ),
        }

    def test_antigravity_active_turn_persists_across_tool_steps_and_rejects_replay_or_new_turn(self):
        records = [
            {"step_index": 3, "type": "USER_INPUT", "content": "private user text"},
            {"step_index": 4, "type": "PLANNER_RESPONSE", "tool_calls": [{"name": "run_command"}]},
        ]
        self._write_lines(self.transcript, records)
        ctx1 = resolve_native_owner_turn(
            self.workspace,
            environ=self._agy_env(5),
            antigravity_app_dir=self.app_dir,
        )
        self.assertEqual(ctx1["host_surface"], "antigravity")
        self.assertEqual(ctx1["turn_id"], f"antigravity:{self.conversation}:u3")
        self.assertNotIn("private user text", json.dumps(ctx1))
        self.assertNotIn(str(self.workspace), json.dumps(ctx1))

        # Once step 5 finishes, replaying stepIndex=5 is rejected; a second tool step 7 in the same user turn matches ctx1.
        records.extend([
            {"step_index": 5, "type": "GENERIC", "status": "DONE"},
            {"step_index": 6, "type": "PLANNER_RESPONSE", "truncated_fields": ["tool_calls"], "tool_calls": [{"name": "run_command"}]},
        ])
        self._write_lines(self.transcript, records)
        with self.assertRaisesRegex(ValueError, "not active"):
            resolve_native_owner_turn(self.workspace, environ=self._agy_env(5), antigravity_app_dir=self.app_dir)

        ctx2 = resolve_native_owner_turn(
            self.workspace,
            environ=self._agy_env(7),
            antigravity_app_dir=self.app_dir,
        )
        self.assertEqual(ctx1, ctx2)

        # Terminal planner response without tool calls closes the turn.
        records.extend([
            {"step_index": 7, "type": "GENERIC", "status": "DONE"},
            {"step_index": 8, "type": "PLANNER_RESPONSE", "tool_calls": []},
        ])
        self._write_lines(self.transcript, records)
        with self.assertRaisesRegex(ValueError, "not active"):
            resolve_native_owner_turn(self.workspace, environ=self._agy_env(9), antigravity_app_dir=self.app_dir)

        # Next user input produces a new turn_id.
        records.extend([
            {"step_index": 9, "type": "USER_INPUT", "content": "next turn"},
            {"step_index": 10, "type": "PLANNER_RESPONSE", "tool_calls": [{"name": "run_command"}]},
        ])
        self._write_lines(self.transcript, records)
        ctx3 = resolve_native_owner_turn(
            self.workspace,
            environ=self._agy_env(11),
            antigravity_app_dir=self.app_dir,
        )
        self.assertNotEqual(ctx1["turn_id"], ctx3["turn_id"])

        # Foreign bound workspace fails closed.
        other = self.root / "foreign"
        other.mkdir()
        with self.assertRaisesRegex(ValueError, "another workspace"):
            resolve_native_owner_turn(
                self.workspace,
                environ=self._agy_env(11, ws=str(other)),
                antigravity_app_dir=self.app_dir,
            )

    def test_claude_code_active_tool_turn_and_closed_turn_rejection(self):
        claude_home = self.root / "claude"
        session_id = "55555555-5555-4555-8555-555555555555"
        session_file = claude_home / "projects" / "proj" / f"{session_id}.jsonl"
        session_file.parent.mkdir(parents=True)
        records = [
            {"sessionId": session_id, "cwd": str(self.workspace), "type": "user", "uuid": "u-1", "message": {"content": "run sync"}},
            {"sessionId": session_id, "cwd": str(self.workspace), "type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash"}]}},
        ]
        self._write_lines(session_file, records)
        env = {"CLAUDECODE": "1", "CLAUDE_SESSION_ID": session_id}
        ctx = resolve_native_owner_turn(self.workspace, environ=env, claude_home=claude_home)
        self.assertEqual(ctx["host_surface"], "claude-code")
        self.assertEqual(ctx["turn_id"], f"claude:{session_id}:u-1")

        # Assistant reply without tool_use closes active tool turn.
        records.append(
            {"sessionId": session_id, "cwd": str(self.workspace), "type": "assistant", "message": {"content": [{"type": "text", "text": "done"}]}}
        )
        self._write_lines(session_file, records)
        with self.assertRaisesRegex(ValueError, "missing or ambiguous"):
            resolve_native_owner_turn(self.workspace, environ=env, claude_home=claude_home)


if __name__ == "__main__":
    unittest.main()
