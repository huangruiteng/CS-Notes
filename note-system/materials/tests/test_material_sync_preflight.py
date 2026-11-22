"""Synthetic tests for single-pass sync preflight, public-safety scan, and CLI schemas."""
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import material_completion
import material_queue
import material_queue_sync as sync
import material_source
import material_sync_preflight as preflight


def make_catalog(*names):
    return {
        "schema_version": material_queue.SCHEMA,
        "queue_id": "external",
        "top_window_size": 30,
        "entries": [
            {
                "material_ref": "material-" + name,
                "title": "Title " + name,
                "sources": ["https://example.org/" + name],
                "tier": "A",
                "lifecycle": "candidate",
                "read_scope": "recorded_review",
                "note": "Assistant read; user completion unknown.",
                "queue_rank": i + 1,
            }
            for i, name in enumerate(names)
        ],
    }


def git_run(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


class SyncPreflightTests(unittest.TestCase):
    def _init_repo(self, root: Path) -> Path:
        repo = root / "repo"
        repo.mkdir()
        git_run(repo, "init", "-b", "master")
        git_run(repo, "config", "user.email", "test@example.org")
        git_run(repo, "config", "user.name", "Test User")
        (repo / "Learning-Materials").mkdir()
        (repo / "AGENTS.md").write_text("# Rules\nline 1\nline 2\n", encoding="utf-8")
        (repo / "Learning-Materials/catalog.json").write_text(
            json.dumps(make_catalog("alpha", "beta"), indent=2) + "\n", encoding="utf-8"
        )
        git_run(repo, "add", "AGENTS.md", "Learning-Materials/catalog.json")
        git_run(repo, "commit", "-m", "initial")
        return repo

    def test_preflight_attributes_remote_absence_and_flags_stray_and_leaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._init_repo(root)

            # Create upstream commit archiving alpha and editing AGENTS.md
            git_run(repo, "checkout", "-q", "-b", "upstream-sim")
            (repo / "AGENTS.md").write_text("# Rules\nline 1 updated\nline 2\n", encoding="utf-8")
            (repo / "Learning-Materials/catalog.json").write_text(
                json.dumps(make_catalog("beta"), indent=2) + "\n", encoding="utf-8"
            )
            git_run(repo, "add", "AGENTS.md", "Learning-Materials/catalog.json")
            git_run(repo, "commit", "-m", "materials: archive alpha")
            upstream_oid = git_run(repo, "rev-parse", "HEAD")

            # Return to master and make local edits + accidental stray file + synthetic path leak
            git_run(repo, "checkout", "-q", "master")
            (repo / "AGENTS.md").write_text("# Rules\nline 1\nline 2\nlocal addition\n", encoding="utf-8")
            (repo / "Learning-Materials/catalog.json").write_text(
                json.dumps(make_catalog("alpha", "beta", "local-new"), indent=2) + "\n", encoding="utf-8"
            )
            (repo / "\x01").write_bytes(b"")
            synthetic_private_path = "/" + "Users" + "/synthetic_owner/notes.md"
            (repo / "Notes.md").write_text(f"Draft referencing {synthetic_private_path}\n", encoding="utf-8")

            backup_dir = root / "backup"
            report = preflight.run_preflight(repo, upstream="upstream-sim", backup_dir=backup_dir)

            self.assertEqual(report["git"]["behind"], 1)
            self.assertTrue(report["git"]["fast_forwardable"])
            self.assertEqual(
                report["git"]["overlapping_dirty_files"],
                ["AGENTS.md", "Learning-Materials/catalog.json"],
            )
            self.assertEqual(report["git"]["stray_files"], ["\x01"])

            self.assertFalse(report["public_safety"]["ok"])
            self.assertEqual(
                report["public_safety"]["forbidden_paths"],
                [{"path": "\x01", "reason": "control_char_filename"}],
            )
            self.assertEqual(
                report["public_safety"]["leak_findings"],
                [{"path": "Notes.md", "line": 1, "rule": "local_user_path"}],
            )
            # Ensure secret/path string itself is not echoed in findings
            self.assertNotIn("synthetic_owner", json.dumps(report["public_safety"]))

            mats = report["materials"]
            self.assertEqual(mats["local_addition_refs"], ["material-local-new"])
            self.assertEqual(len(mats["remote_absences"]), 1)
            absence = mats["remote_absences"][0]
            self.assertEqual(absence["material_ref"], "material-alpha")
            self.assertEqual(absence["title"], "Title alpha")
            self.assertEqual(absence["removed_in_commit"]["oid"], upstream_oid)
            self.assertEqual(absence["removed_in_commit"]["subject"], "materials: archive alpha")

            manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["upstream"], upstream_oid)
            self.assertEqual(len(manifest["files"]), 4)

    def test_public_safety_clean_repo_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._init_repo(Path(tmp))
            (repo / "Notes.md").write_text("# Clean Public Note\n\n Complexity $P \\subseteq NP$.\n", encoding="utf-8")
            report = preflight.run_preflight(repo, upstream="master")
            self.assertTrue(report["public_safety"]["ok"])
            self.assertEqual(report["git"]["stray_files"], [])

    def test_material_source_schema_cli_requires_no_private_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = material_source.main(["--repo", tmp, "--schema", "complete"])
            self.assertEqual(rc, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(
                payload["prepare_shorthand_input"]["schema_version"],
                "material_lifecycle_decisions_v1",
            )

    def test_decisions_shorthand_synthesizes_plan_and_rejects_assistant_actor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rec = {
                "stable_id": "material-alpha",
                "title": "Alpha",
                "lifecycle_state": "candidate",
                "content_digest": "sha256:1111",
            }
            cat = {
                "records": [rec],
                "rankings": {"ranked_entries": {"entries": [{"rank": 1, "material_refs": ["material-alpha"]}]}},
            }

            class FakeSource:
                store_id = "store-1"
                scope = "project:test"
                cfg = {"project_scope": "project:test"}

                def __init__(self, base: Path):
                    self.root = base
                    (base / "completion-evidence").mkdir(parents=True)
                    (base / "operations").mkdir(parents=True)
                    (base / "archives").mkdir(parents=True)

                def context(self):
                    return None

                def current_pointer(self):
                    return {"authority_revision": "rev-1"}

                def load_catalog(self, rev):
                    assert rev == "rev-1"
                    return json.loads(json.dumps(cat))

                def load_material_content(self, _catalog):
                    return {}

                def stage_catalog(self, _catalog):
                    return "rev-2"

            api = SimpleNamespace(
                load=lambda p: json.loads(Path(p).read_text(encoding="utf-8")),
                data=sync.canonical_json,
                sha=lambda b: hashlib.sha256(b).hexdigest(),
                immutable=lambda p, obj: sync.write_immutable(Path(p), sync.canonical_json(obj)),
                ranked_refs=lambda c: [e["material_refs"][0] for e in c["rankings"]["ranked_entries"]["entries"]],
                sync=sync,
                now=lambda: "2026-11-23T00:00:00Z",
                build_material_store_inventory=lambda **kw: kw,
            )
            src = FakeSource(root / "source")

            bad_file = root / "bad.json"
            bad_file.write_text(
                json.dumps(
                    {
                        "schema_version": "material_lifecycle_decisions_v1",
                        "decisions": [
                            {
                                "material_ref": "material-alpha",
                                "action": "user_completed",
                                "actor": "assistant",
                                "kind": "user_statement",
                                "source_ref": "turn:1",
                                "statement": "Assistant read it",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                material_completion.settle(src, bad_file, "prepare", api)

            good_file = root / "good.json"
            good_file.write_text(
                json.dumps(
                    {
                        "schema_version": "material_lifecycle_decisions_v1",
                        "decisions": [
                            {
                                "material_ref": "material-alpha",
                                "action": "user_completed",
                                "actor": "human_user",
                                "kind": "user_statement",
                                "source_ref": "turn:2",
                                "statement": "读完 Alpha",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = material_completion.settle(src, good_file, "prepare", api)
            self.assertEqual(out["archived_refs"], ["material-alpha"])
            self.assertTrue(Path(out["plan_file"]).is_file())


if __name__ == "__main__":
    unittest.main()
