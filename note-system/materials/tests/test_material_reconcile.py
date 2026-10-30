"""Three-way regression cases, including unpublished material preservation."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import material_queue
import material_reconcile as reconcile


def catalog(*names):
    return {"schema_version": material_queue.SCHEMA, "queue_id": "external",
            "top_window_size": 30, "entries": [
                {"material_ref": "material-" + name, "title": name,
                 "sources": ["https://example.org/" + name], "tier": "A",
                 "lifecycle": "candidate", "read_scope": "recorded_review",
                 "note": "Assistant read; user completion unknown.", "queue_rank": i + 1}
                for i, name in enumerate(names)]}


class ReconciliationTests(unittest.TestCase):
    def test_rank_insertions_preserve_complete_existing_order(self):
        current = ["a", "private-1", "b", "private-2", "c"]
        incoming = ["a", "new-1", "b", "new-2", "c"]
        before = (current[:], incoming[:])
        merged = reconcile.merge_ranked_orders(current, incoming)
        self.assertEqual([x for x in merged if x in current], current)
        self.assertEqual([x for x in merged if x in incoming], incoming)
        self.assertEqual(set(merged), set(current) | set(incoming))
        self.assertEqual(len(merged), len(set(merged)))
        self.assertEqual((current, incoming), before)

    def test_rank_no_change_does_not_redistribute_private_entries(self):
        current = ["a", "b", "private-1", "private-2", "c", "private-3"]
        self.assertEqual(reconcile.merge_ranked_orders(current, ["a", "b", "c"]), current)

    def test_accepted_rank_moves_keep_both_subsequence_orders(self):
        current = ["a", "private-1", "b", "private-2", "c"]
        incoming = ["c", "new", "a", "b"]
        merged = reconcile.merge_ranked_orders(current, incoming)
        self.assertEqual([x for x in merged if x in incoming], incoming)
        self.assertEqual([x for x in merged if x.startswith("private")], ["private-1", "private-2"])

    def test_rank_omission_keeps_local_material_and_empty_orders_work(self):
        self.assertEqual(reconcile.merge_ranked_orders(["a", "local", "b"], ["a", "b"]), ["a", "local", "b"])
        self.assertEqual(reconcile.merge_ranked_orders(["a"], []), ["a"])
        self.assertEqual(reconcile.merge_ranked_orders([], ["b"]), ["b"])
        self.assertEqual(reconcile.merge_ranked_orders([], []), [])
        for current, incoming in [(["a", "a"], []), ([], ["b", "b"])]:
            with self.assertRaisesRegex(ValueError, "duplicate"):
                reconcile.merge_ranked_orders(current, incoming)

    def test_unpublished_intake_is_preserved_and_never_archived(self):
        plan = reconcile.reconcile(catalog("existing"), catalog("existing", "new"), catalog("existing"))
        self.assertEqual(plan["changes"][0]["kind"], "local_addition")
        self.assertEqual(plan["changes"][0]["action"], "preserve_local_intake")
        self.assertEqual(plan["lifecycle_transitions"], [])
        self.assertFalse(plan["implicit_archive_allowed"])

    def test_true_remote_removal_still_requires_completion_evidence(self):
        plan = reconcile.reconcile(catalog("old"), catalog("old"), catalog())
        self.assertEqual(plan["changes"][0]["kind"], "remote_absence")
        self.assertEqual(plan["changes"][0]["action"], "require_source_disposition_evidence")
        self.assertEqual(plan["lifecycle_transitions"], [])

    def test_matching_additions_do_not_duplicate_and_conflicts_are_explicit(self):
        local, remote = catalog("new"), catalog("new")
        self.assertEqual(reconcile.reconcile(catalog(), local, remote)["counts"], {"shared_addition": 1})
        remote["entries"][0]["note"] = "A different reviewed summary"
        self.assertEqual(reconcile.reconcile(catalog(), local, remote)["counts"], {"conflicting_addition": 1})

    def test_updates_and_rank_changes_are_separate(self):
        base, local, remote = catalog("one", "two"), catalog("one", "two"), catalog("two", "one")
        plan = reconcile.reconcile(base, local, remote)
        self.assertEqual(plan["changes"], [])
        self.assertTrue(plan["ranking_changed"]["remote"])
        local["entries"][0]["note"] = "Local summary"
        remote["entries"][1]["note"] = "Remote summary"
        plan = reconcile.reconcile(base, local, remote)
        self.assertEqual(plan["changes"][0]["kind"], "conflicting_update")

    def test_invalid_catalog_rejected_before_a_partial_plan(self):
        invalid = catalog("one", "two")
        invalid["entries"][1]["material_ref"] = "material-one"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            reconcile.reconcile(catalog(), invalid, catalog())

    def test_git_plan_uses_merge_base_and_preserves_working_index_and_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def git(*args):
                return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE)
            git("init", "-q");git("config", "user.name", "Fixture");git("config", "user.email", "fixture@example.org")
            p = root / "Learning-Materials/catalog.json";p.parent.mkdir()
            p.write_text(json.dumps(catalog("base")))
            git("add", ".");git("commit", "-qm", "base")
            base = git("rev-parse", "HEAD").decode().strip()
            git("checkout", "-qb", "upstream")
            p.write_text(json.dumps(catalog("base", "remote")))
            git("add", ".");git("commit", "-qm", "remote")
            git("checkout", "-q", "-b", "local", base)
            p.write_text(json.dumps(catalog("base", "local")))
            before = (p.read_bytes(), git("status", "--porcelain"), git("show", ":Learning-Materials/catalog.json"), git("show-ref"))
            plan = reconcile.git_plan(root, "upstream")
            self.assertEqual(plan["git_snapshot"]["base"], base)
            self.assertTrue(plan["git_snapshot"]["index_differs_from_working"])
            self.assertEqual(plan["counts"], {"unchanged": 1, "local_addition": 1, "remote_addition": 1})
            self.assertEqual(before, (p.read_bytes(), git("status", "--porcelain"), git("show", ":Learning-Materials/catalog.json"), git("show-ref")))
            self.assertTrue(plan["read_only"])


if __name__ == "__main__":
    unittest.main()
