"""Lifecycle guard/rollback tests using stdlib fixtures, no private installation."""
import copy
import dataclasses
import io
import json
import sys
import tempfile
import unittest
import uuid
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import material_completion as completion
import material_queue_sync as q


def write(path, value):
    q.atomic_write(Path(path), q.canonical_json(value))


def immutable(path, value):
    q.write_immutable(Path(path), q.canonical_json(value))


def ranked(catalog):
    return [e["material_refs"][0] for e in catalog["rankings"]["ranked_entries"]["entries"]]


@dataclasses.dataclass
class Transition:
    expected_revision: str
    target_revision: str


class FixtureSource:
    def __init__(self, root):
        self.root = root
        self.store_id = "store:fixture"
        self.cfg = {"project_scope": {"project_ref": "project:fixture",
            "source_profile_ref": "profile:fixture", "workspace_grant_ref": "grant:fixture"}}
        self.scope = self.cfg["project_scope"]
        self.context = Mock()
        self.authorize = Mock()
        self.issue_gate = Mock(return_value="gate:fixture")
        self.reviews = root / "reviews.json"
        self.targets = {name: root / "exports" / name for name in
                        ["catalog.json", "QUEUE.md", "CANDIDATES.md", "PRIVATE_QUEUE.md"]}
        body = b"Synthetic public material; no private data."
        self.body = root / "body.bin";self.body.write_bytes(body)
        self.records = [{"stable_id": "material-" + name, "title": name,
            "lifecycle_state": "candidate", "content_digest": q.digest(body),
            "entry_digest": q.digest(body), "content_size_bytes": len(body)} for name in ["one", "two"]]
        catalog = {"records": self.records, "rankings": {"ranked_entries": {"entries": [
            {"rank": i + 1, "material_refs": [r["stable_id"]]} for i, r in enumerate(self.records)]}}}
        revision = self.stage_catalog(catalog)
        write(root / "authority/current.json", {"authority_revision": revision})
        record = self.records[0]
        write(self.reviews, {"scope": "current_only", "owner_gate_ref": "gate:fixture", "records": [{
            "material_ref": record["stable_id"], "entry_digest": record["entry_digest"],
            "record_digest": q.digest(q.canonical_json(record)), "classification": "external",
            "reason": "Synthetic reviewed public source", "public_card": {
                "material_ref": record["stable_id"], "title": "one", "sources": ["https://example.org/paper"],
                "tier": "A", "lifecycle": "candidate", "read_scope": "metadata", "note": "Metadata only."}}]})
        self.publish()

    def current_pointer(self):
        return q.load(self.root / "authority/current.json")

    def load_catalog(self, revision):
        catalog = q.load(self.root / "catalogs" / (revision + ".json"))
        if self.revision(catalog) != revision:
            raise ValueError("fixture immutable digest mismatch")
        return catalog

    def revision(self, catalog):
        return "catalog-" + q.digest(q.canonical_json(catalog))[:24]

    def stage_catalog(self, catalog):
        revision = self.revision(catalog)
        immutable(self.root / "catalogs" / (revision + ".json"), catalog)
        return revision

    def load_material_content(self, catalog):
        body = self.body.read_bytes()
        for record in catalog["records"]:
            if record["content_digest"] != q.digest(body) or record["content_size_bytes"] != len(body):
                raise ValueError("fixture content digest mismatch")
        return {r["stable_id"]: SimpleNamespace(heading=r["title"]) for r in catalog["records"]}

    def build_projection(self, *args):
        return b"", {"synthetic": True}

    def switch_authority(self, **args):
        self.authorize(args["owner_gate_ref"])
        if self.current_pointer()["authority_revision"] != args["expected_revision"]:
            raise ValueError("fixture authority CAS conflict")
        self.load_catalog(args["target_revision"])
        write(self.root / "authority/current.json", {"authority_revision": args["target_revision"]})
        return Transition(args["expected_revision"], args["target_revision"])

    def publish(self):
        publisher = q.QueuePublisher(self)
        publisher.prepare();publisher.apply();publisher.check()


class CompletionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.output = redirect_stdout(io.StringIO());self.output.__enter__();self.addCleanup(self.output.__exit__, None, None, None)
        self.source = FixtureSource(Path(temp.name))
        self.api = SimpleNamespace(load=q.load, data=q.canonical_json, sha=q.digest,
            write=write, immutable=immutable, sync=q, uuid=uuid, ranked_refs=ranked,
            now=lambda: "2026-01-01T00:00:00Z", build_material_store_inventory=lambda **args: args)
        self.before = self.source.current_pointer()["authority_revision"]
        self.evidence = self.source.root / "evidence.json"
        self.decision = {"material_ref": "material-one", "action": "user_completed", "actor": "human_user",
                         "kind": "user_statement", "source_ref": "fixture:human-message",
                         "statement": "I finished this material; archive it."}
        self.plan = {"schema_version": "project_material_completion_v1", "store_id": self.source.store_id,
            "project_scope": self.source.scope, "authority_revision": self.before,
            "evidence_file": str(self.evidence), "transitions": [{"material_ref": "material-one",
                "record_digest": q.digest(q.canonical_json(self.source.records[0])),
                "from_state": "candidate", "to_state": "archived"}]}
        self.path = self.source.root / "plan.json"
        self.set_evidence({"schema_version": "material_lifecycle_decisions_v1", "decisions": [self.decision]})

    def set_evidence(self, packet):
        write(self.evidence, packet)
        self.plan["evidence_digest"] = q.digest(self.evidence.read_bytes())
        write(self.path, self.plan)

    def snapshot(self):
        paths = [self.source.root / "authority/current.json", self.source.root / "queue-publication/current.json",
                 *self.source.targets.values()]
        return {str(p): p.read_bytes() for p in paths}

    def assert_restored(self, before):
        after = self.snapshot()
        pointer = str(self.source.root / "queue-publication/current.json")
        old_receipt, new_receipt = json.loads(before.pop(pointer)), json.loads(after.pop(pointer))
        self.assertEqual(before, after)
        self.assertEqual(old_receipt["queue_revision"], new_receipt["queue_revision"])
        # A new publication receipt has fresh destination CAS metadata; verify
        # its source and exact output readback instead of comparing timestamps.
        q.QueuePublisher(self.source).check()

    def test_archive_and_rollback_preserve_original_body_membership_and_other_record(self):
        original = self.snapshot()
        completion.settle(self.source, self.path, "prepare", self.api)
        self.assertEqual(self.source.current_pointer()["authority_revision"], self.before)
        receipt = completion.settle(self.source, self.path, "apply", self.api)
        after = self.source.load_catalog(receipt["after_revision"])
        self.assertEqual(after["records"][0]["lifecycle_state"], "archived")
        self.assertEqual(after["records"][1], self.source.records[1])
        self.assertEqual(ranked(after), ["material-two"])
        self.source.load_material_content(after)
        self.assertEqual(q.load(self.source.targets["catalog.json"])["entries"], [])
        completion.settle(self.source, self.path, "rollback", self.api)
        self.assert_restored(original)

    def test_archive_preserves_rich_rank_entries_and_refreshes_derived_views(self):
        catalog=self.source.load_catalog(self.before)
        entries=catalog['rankings']['ranked_entries']['entries']
        for entry in entries:
            entry.update(entry_ref='entry-'+str(entry['rank']), title='Kept title',
                         reading_action='Keep the original reading action',
                         evidence_refs=['evidence:original'], public_queue_rank=entry['rank'])
        survivor=copy.deepcopy(entries[1])
        catalog['rankings']['ranked_entries'].update(
            constraints={'top_window_size':1},
            summary={'material_ref_count':2,'source_entry_count':2,'rebuilt_entry_count':2,
                     'top_window_entry_count':1,'ranked_backlog_entry_count':1,
                     'public_ranked_count':2,'private_ranked_count':0})
        catalog['rankings']['top30']={'slots':copy.deepcopy(entries[:1])}
        catalog['rankings']['ranked_backlog']={'entries':copy.deepcopy(entries[1:])}
        catalog['lifecycle_counts']={'candidate':2}
        self.before=self.source.stage_catalog(catalog)
        write(self.source.root/'authority/current.json',{'authority_revision':self.before})
        self.plan['authority_revision']=self.before
        write(self.path,self.plan)
        self.source.publish()
        receipt=completion.settle(self.source,self.path,'apply',self.api)
        after=self.source.load_catalog(receipt['after_revision'])
        survivor.update(rank=1,public_queue_rank=1)
        self.assertEqual(after['rankings']['ranked_entries']['entries'],[survivor])
        self.assertEqual(after['rankings']['top30']['slots'],[survivor])
        self.assertEqual(after['rankings']['ranked_backlog']['entries'],[])
        self.assertEqual(after['lifecycle_counts'],{'archived':1,'candidate':1})
        self.assertEqual(after['rankings']['ranked_entries']['summary']['material_ref_count'],1)

    def test_batch_prose_omission_and_assistant_reading_are_rejected_without_write(self):
        before = self.snapshot()
        for packet in [{"closed_public_refs": ["material-one"], "completion_declaration": "Batch read and organized"},
                       {"schema_version": "material_lifecycle_decisions_v1", "decisions": [{**self.decision, "actor": "assistant"}]},
                       {"schema_version": "material_lifecycle_decisions_v1", "decisions": [{**self.decision, "kind": "note_publication"}]}]:
            self.set_evidence(packet)
            with self.assertRaises(ValueError):completion.settle(self.source, self.path, "apply", self.api)
            self.assertEqual(before, self.snapshot())
        self.source.issue_gate.assert_not_called()

    def test_evidence_must_cover_each_material_exactly_and_bind_human_remote_source(self):
        for decision in [{**self.decision, "material_ref": "material-two"},
                         {**self.decision, "statement": " "},
                         {**self.decision, "kind": "verified_remote_user_statement"}]:
            self.set_evidence({"schema_version": "material_lifecycle_decisions_v1", "decisions": [decision]})
            with self.assertRaises(ValueError):completion.settle(self.source, self.path, "apply", self.api)
        decision = {**self.decision, "kind": "verified_remote_user_statement",
                    "user_message_ref": "fixture:original-human-message", "remote_commit": "a" * 40}
        self.set_evidence({"schema_version": "material_lifecycle_decisions_v1", "decisions": [decision]})
        self.assertTrue(completion.settle(self.source, self.path, "prepare", self.api)["lossless_verified"])

    def test_bad_digest_and_revoked_gate_leave_authority_and_publication_unchanged(self):
        before = self.snapshot()
        self.plan["evidence_digest"] = "wrong";write(self.path, self.plan)
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            completion.settle(self.source, self.path, "apply", self.api)
        self.set_evidence({"schema_version": "material_lifecycle_decisions_v1", "decisions": [self.decision]})
        self.source.authorize.side_effect = ValueError("revoked")
        with self.assertRaisesRegex(ValueError, "revoked"):
            completion.settle(self.source, self.path, "apply", self.api)
        self.assert_restored(before)

    def test_stale_apply_cannot_overwrite_a_newer_authority(self):
        completion.settle(self.source, self.path, "apply", self.api)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "CAS"):
            completion.settle(self.source, self.path, "apply", self.api)
        self.assertEqual(before, self.snapshot())

    def test_late_receipt_failure_restores_authority_and_outputs(self):
        before = self.snapshot()
        def fail_receipt(path, value):
            if Path(path).name.startswith("completion-receipt-"):
                raise OSError("receipt failure")
            immutable(path, value)
        with patch.object(self.api, "immutable", side_effect=fail_receipt):
            with self.assertRaisesRegex(OSError, "receipt failure"):
                completion.settle(self.source, self.path, "apply", self.api)
        self.assert_restored(before)

    def test_false_archive_correction_preserves_audit_and_can_be_completed_later(self):
        archive = completion.settle(self.source, self.path, "apply", self.api)
        record = self.source.load_catalog(archive["after_revision"])["records"][0]
        self.plan.update(authority_revision=archive["after_revision"], transitions=[{
            "material_ref": "material-one", "record_digest": q.digest(q.canonical_json(record)),
            "from_state": "archived", "to_state": "candidate"}])
        decision = {"material_ref": "material-one", "action": "correct_false_archive", "actor": "source_audit",
            "source_ref": "fixture:human-correction", "statement": "Only intake was requested.",
            "archive_ref": record["archive_ref"], "invalid_completion_evidence_ref": record["completion_evidence_ref"]}
        self.evidence = self.source.root / "correction.json";self.plan["evidence_file"] = str(self.evidence)
        self.set_evidence({"schema_version": "material_lifecycle_decisions_v1", "decisions": [decision]})
        corrected = completion.settle(self.source, self.path, "apply", self.api)
        restored = self.source.load_catalog(corrected["after_revision"])["records"][0]
        self.assertEqual(restored["lifecycle_state"], "candidate")
        self.assertEqual(restored["archive_ref"], record["archive_ref"])
        self.assertEqual(restored["content_digest"], record["content_digest"])
        self.assertEqual(ranked(self.source.load_catalog(corrected["after_revision"])), ["material-two", "material-one"])
        # Restored records require fresh full-record public review.
        self.assertEqual(q.load(self.source.targets["catalog.json"])["entries"], [])
        self.plan.update(authority_revision=corrected["after_revision"], transitions=[{
            "material_ref": "material-one", "record_digest": q.digest(q.canonical_json(restored)),
            "from_state": "candidate", "to_state": "archived"}])
        self.evidence = self.source.root / "later.json";self.plan["evidence_file"] = str(self.evidence)
        self.set_evidence({"schema_version": "material_lifecycle_decisions_v1", "decisions": [self.decision]})
        self.assertTrue(completion.settle(self.source, self.path, "apply", self.api)["readback_verified"])


if __name__ == "__main__":
    unittest.main()
