"""Publication failure tests; synthetic sources only, no LoopX/private state."""

import contextlib
import copy
import io
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import material_queue_sync as q


class QueuePublication(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="material-queues-test-")
        self.addCleanup(self.tmp.cleanup)
        self.local = Path(self.tmp.name) / "private"
        self.local.mkdir()
        output = Path(self.tmp.name) / "public"
        self.records = [
            {
                "stable_id": "material-" + name,
                "entry_digest": "content-" + name,
                "lifecycle_state": "archived" if name == "archive" else "candidate",
            }
            for name in ("public", "internal", "new", "archive")
        ]
        self.catalog = {
            "records": self.records,
            "rankings": {
                "ranked_entries": {
                    "entries": [
                        {"rank": 1, "material_refs": ["material-public"]},
                        {"rank": 2, "material_refs": ["material-internal"]},
                    ]
                }
            },
        }
        card = {
            "material_ref": "material-public",
            "title": "Public paper",
            "sources": ["https://example.org/paper"],
            "tier": "A",
            "lifecycle": "candidate",
            "read_scope": "recorded_review",
            "note": "",
        }
        self.reviews = {
            "scope": "current_only",
            "owner_gate_ref": "owner-test",
            "records": [],
        }
        for record in self.records:
            if record["stable_id"] == "material-new":
                continue
            decision = {
                "material_ref": record["stable_id"],
                "entry_digest": record["entry_digest"],
                "record_digest": q.digest(q.canonical_json(record)),
                "classification": "internal"
                if record["stable_id"] == "material-internal"
                else "external",
                "reason": "Reviewed source",
            }
            if record["stable_id"] == "material-public":
                decision["public_card"] = card
            self.reviews["records"].append(decision)
        self.source = {"authority_revision": "managed-test-source"}
        self.adapter = SimpleNamespace(
            root=self.local,
            reviews=self.local / "reviews.json",
            targets={
                name: (self.local if name == "PRIVATE_QUEUE.md" else output) / name
                for name in (
                    "catalog.json",
                    "QUEUE.md",
                    "CANDIDATES.md",
                    "PRIVATE_QUEUE.md",
                )
            },
            current_pointer=lambda: dict(self.source),
            load_catalog=lambda revision: self.catalog,
            load_material_content=lambda catalog: {
                r["stable_id"]: SimpleNamespace(heading="Fixture " + r["stable_id"])
                for r in catalog["records"]
            },
            # Source capability validation is tested by the connected project.
            build_projection=lambda *args: (b"", {"synthetic": True}),
        )
        self.publisher = q.QueuePublisher(self.adapter)
        self.write_reviews()
        self.addCleanup(patch.stopall)
        patch("sys.stdout", new=io.StringIO()).start()

    def write_reviews(self):
        self.adapter.reviews.write_bytes(q.json_bytes(self.reviews))

    def snapshot(self):
        return {
            str(p): p.read_bytes() if p.exists() else None
            for p in [*self.publisher.targets.values(), self.publisher.pointer]
        }

    def publish(self):
        self.publisher.main(["prepare"])
        self.publisher.main(["apply"])
        self.publisher.main(["check"])

    def prepare_change(self):
        self.reviews["records"][0]["public_card"]["note"] = "A new public summary"
        self.write_reviews()
        self.publisher.main(["prepare"])

    @contextlib.contextmanager
    def fail_one_write(self):
        real = q.atomic_write
        failed = False

        def fail(path, data, **kwargs):
            nonlocal failed
            if path == self.publisher.targets["QUEUE.md"] and not failed:
                failed = True
                raise OSError("injected write failure")
            return real(path, data, **kwargs)

        with patch.object(q, "atomic_write", fail):
            yield

    def test_partition_preserves_all_ids_and_separate_ranks(self):
        external, private, archived = q.partition(self.catalog, self.reviews)
        self.assertEqual([c["material_ref"] for c in external], ["material-public"])
        self.assertEqual(
            {c["material_ref"] for c in private}, {"material-internal", "material-new"}
        )
        self.assertEqual(archived, ["material-archive"])
        self.assertEqual((external[0]["queue_rank"], private[0]["queue_rank"]), (1, 1))

    def test_changed_content_or_lifecycle_evidence_revokes_review(self):
        for field in ("entry_digest", "lifecycle_transition_ref"):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.catalog)
                changed["records"][0][field] = "new-evidence"
                self.assertEqual(q.partition(changed, self.reviews)[0], [])

    def test_duplicate_membership_and_noncontiguous_source_ranks_rejected(self):
        for mode in ("duplicate", "gap"):
            changed = copy.deepcopy(self.catalog)
            entries = changed["rankings"]["ranked_entries"]["entries"]
            if mode == "duplicate":
                entries[1]["material_refs"] = entries[0]["material_refs"]
            else:
                entries[1]["rank"] = 3
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                q.partition(changed, self.reviews)

    def test_public_output_never_contains_private_title_and_retry_is_idempotent(self):
        self.publish()
        before = self.snapshot()
        self.publisher.main(["apply"])
        self.assertEqual(before, self.snapshot())
        for name, path in self.publisher.targets.items():
            if name != "PRIVATE_QUEUE.md":
                self.assertNotIn("material-internal", path.read_text())

    def test_source_review_pointer_and_destination_conflicts_rejected(self):
        self.publish()
        self.prepare_change()
        before = self.snapshot()
        self.source["authority_revision"] = "managed-drift"
        with self.assertRaises(ValueError):
            self.publisher.main(["apply"])
        self.source["authority_revision"] = "managed-test-source"
        review_bytes = self.adapter.reviews.read_bytes()
        self.adapter.reviews.write_bytes(review_bytes + b" ")
        with self.assertRaises(ValueError):
            self.publisher.main(["apply"])
        self.adapter.reviews.write_bytes(review_bytes)
        self.publisher.pointer.write_bytes(before[str(self.publisher.pointer)] + b" ")
        with self.assertRaises(ValueError):
            self.publisher.main(["apply"])
        self.publisher.pointer.write_bytes(before[str(self.publisher.pointer)])
        target = self.publisher.targets["QUEUE.md"]
        target.write_text("user edit")
        with self.assertRaises(ValueError):
            self.publisher.main(["apply"])
        self.assertEqual(target.read_text(), "user edit")

    def test_partial_apply_failure_restores_all_files(self):
        self.publish()
        self.prepare_change()
        before = self.snapshot()
        with self.fail_one_write(), self.assertRaises(OSError):
            self.publisher.main(["apply"])
        self.assertEqual(before, self.snapshot())
        self.publisher.main(["apply"])
        self.publisher.main(["check"])

    def test_review_change_during_apply_restores_all_files(self):
        self.publish()
        self.prepare_change()
        before = self.snapshot()
        real = q.atomic_write

        def change_review(path, data, **kwargs):
            real(path, data, **kwargs)
            if path == self.publisher.targets["QUEUE.md"]:
                self.adapter.reviews.write_bytes(
                    self.adapter.reviews.read_bytes() + b" "
                )

        with (
            patch.object(q, "atomic_write", change_review),
            self.assertRaises(ValueError),
        ):
            self.publisher.main(["apply"])
        self.assertEqual(before, self.snapshot())

    def test_rollback_validates_backups_recovers_failures_and_allows_reapply(self):
        self.publish()
        first = self.snapshot()
        self.prepare_change()
        self.publisher.main(["apply"])
        second = self.snapshot()
        receipt = q.load(self.publisher.pointer)
        revision = receipt["queue_revision"]
        with self.assertRaises(ValueError):
            self.publisher.main(["rollback", "--expected-queue-revision", "wrong"])
        backup = (
            self.local
            / "queue-publication/backups"
            / receipt["backup_ref"]
            / "catalog.json"
        )
        saved = backup.read_bytes()
        backup.chmod(0o600)
        backup.write_text("corrupt")
        with self.assertRaises(ValueError):
            self.publisher.main(["rollback", "--expected-queue-revision", revision])
        backup.write_bytes(saved)
        with self.fail_one_write(), self.assertRaises(OSError):
            self.publisher.main(["rollback", "--expected-queue-revision", revision])
        self.assertEqual(second, self.snapshot())
        self.publisher.main(["rollback", "--expected-queue-revision", revision])
        self.assertEqual(first, self.snapshot())
        self.assertEqual(self.source["authority_revision"], "managed-test-source")
        self.publish()
        self.assertEqual(q.load(self.publisher.pointer)["queue_revision"], revision)


if __name__ == "__main__":
    unittest.main()
