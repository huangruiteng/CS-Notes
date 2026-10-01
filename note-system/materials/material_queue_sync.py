"""Publish reviewed public/private queue projections from a source adapter.

The adapter owns source reads, private configuration and LoopX validation.
This module owns partitioning, staging, CAS checks, readback and rollback;
it never changes source lifecycle or ranking. No private adapter is required
by the renderer or the synthetic tests. See note-system/materials/README.md.
"""

import argparse
import copy
import fcntl
import hashlib
import json
import os
import pathlib
import tempfile
from datetime import datetime

import material_queue as public


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def canonical_json(value):
    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("ascii")


def current_digest(path):
    return digest(path.read_bytes()) if path.exists() else None


def load(path):
    return json.loads(path.read_bytes())


def fsync_directory(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write(path, payload, *, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    temporary = pathlib.Path(name)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(payload)
            output.flush()
            os.fchmod(output.fileno(), mode)
            os.fsync(output.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)
    if path.read_bytes() != payload:
        raise RuntimeError("atomic write readback mismatch")


def write_immutable(path, payload):
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError("immutable artifact mismatch")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as output:
        output.write(payload)
        output.flush()
        os.fchmod(output.fileno(), 0o400)
        os.fsync(output.fileno())
    fsync_directory(path.parent)


def partition(catalog, reviews):
    decisions = {d["material_ref"]: d for d in reviews["records"]}
    if len(decisions) != len(reviews["records"]):
        raise ValueError("duplicate review identity")
    external = []
    private = []
    archived = []
    for record in catalog["records"]:
        ref = record["stable_id"]
        d = decisions.get(ref)
        if record["lifecycle_state"] == "archived":
            archived.append(ref)
            continue
        valid = (
            d is not None
            and d["entry_digest"] == record["entry_digest"]
            and d.get("record_digest") == digest(canonical_json(record))
        )
        if valid and d["classification"] == "external" and d.get("public_card"):
            card = copy.deepcopy(d["public_card"])
            if card["material_ref"] != ref:
                raise ValueError("review/card identity mismatch")
            card["lifecycle"] = record["lifecycle_state"]
            card["queue_rank"] = None
            external.append(card)
        else:
            private.append(
                {
                    "material_ref": ref,
                    "classification": d["classification"] if valid else "unreviewed",
                    "reason": d["reason"]
                    if valid
                    else "New or changed source; public review required.",
                    "queue_rank": None,
                }
            )
    byref = {c["material_ref"]: c for c in external + private}
    external_refs = {c["material_ref"] for c in external}
    ranks = {"external": 0, "private": 0}
    seen = set()
    ranked_entries = catalog["rankings"]["ranked_entries"]["entries"]
    source_ranks = [entry["rank"] for entry in ranked_entries]
    if any(type(rank) is not int for rank in source_ranks) or sorted(
        source_ranks
    ) != list(range(1, len(source_ranks) + 1)):
        raise ValueError("source ranks must be unique and contiguous")
    for entry in sorted(ranked_entries, key=lambda entry: entry["rank"]):
        # Current adapter intentionally has one primary material per reading unit.
        if len(entry["material_refs"]) != 1:
            raise ValueError(
                "review semantic grouping before splitting a multi-material entry"
            )
        ref = entry["material_refs"][0]
        if ref in seen or ref not in byref:
            raise ValueError("invalid ranked membership")
        seen.add(ref)
        q = "external" if ref in external_refs else "private"
        ranks[q] += 1
        byref[ref]["queue_rank"] = ranks[q]
    refs = [c["material_ref"] for c in external + private] + archived
    if len(refs) != len(set(refs)) or set(refs) != {
        r["stable_id"] for r in catalog["records"]
    }:
        raise ValueError("queue partition is not lossless")
    return external, private, archived


class QueuePublisher:
    def __init__(self, adapter):
        self.adapter = adapter
        self.root = pathlib.Path(adapter.root)
        self.reviews = pathlib.Path(adapter.reviews)
        self.pointer = self.root / "queue-publication/current.json"
        self.targets = {
            name: pathlib.Path(path) for name, path in adapter.targets.items()
        }
        if set(self.targets) != {
            "catalog.json",
            "QUEUE.md",
            "CANDIDATES.md",
            "PRIVATE_QUEUE.md",
        }:
            raise ValueError("unexpected publication outputs")
        if len({p.resolve() for p in self.targets.values()}) != len(self.targets):
            raise ValueError("publication outputs overlap")

    def prepare(self):
        pointer = self.adapter.current_pointer()
        revision = pointer["authority_revision"]
        catalog = self.adapter.load_catalog(revision)
        contents = self.adapter.load_material_content(
            catalog
        )  # verifies every legacy/native backing
        reviews_payload = self.reviews.read_bytes()
        reviews = json.loads(reviews_payload)
        if reviews["scope"] != "current_only":
            raise ValueError("unexpected publication scope")
        external, private, archived = partition(catalog, reviews)
        # Source validation keeps canonical identities. Only the exported cards
        # use reviewed aliases when source identifiers contain private context.
        public_entries = copy.deepcopy(external)
        decisions = {d["material_ref"]: d for d in reviews["records"]}
        canonical_refs = {r["stable_id"] for r in catalog["records"]}
        for card in public_entries:
            ref = card["material_ref"]
            alias = decisions[ref].get("public_material_ref", ref)
            if not isinstance(alias, str):
                raise ValueError("invalid public material alias")
            if alias != ref and alias in canonical_refs:
                raise ValueError("public alias collides with a canonical identity")
            card["material_ref"] = alias
        public_catalog = {
            "schema_version": public.SCHEMA,
            "queue_id": "external",
            "top_window_size": 30,
            "entries": public_entries,
        }
        pages, counts = public.render(public_catalog)
        now = datetime.now().astimezone().isoformat()
        receipts = {}
        for name, queue in [("external", external), ("private", private)]:
            _, receipts[name] = self.adapter.build_projection(
                queue, contents, revision, len(catalog["records"]), now, name
            )
        lines = [
            "# 私有材料队列",
            "",
            f"来源 catalog：`{revision}`。此文件是投影，勿直接改排名。",
            "",
            "内部材料、待确认来源与未经公开审查的新记录均留在这里；原始正文仍在 immutable backing。",
            "",
        ]
        for label, group in [
            (
                "有排名",
                sorted(
                    (x for x in private if x["queue_rank"] is not None),
                    key=lambda x: x["queue_rank"],
                ),
            ),
            ("未排名", [x for x in private if x["queue_rank"] is None]),
        ]:
            lines += ["## " + label, ""]
            for x in group:
                c = contents[x["material_ref"]]
                lines += [
                    f"### {x['queue_rank'] or '候选'}. {c.heading}",
                    "",
                    f"- ID：`{x['material_ref']}`",
                    f"- 分类：{x['classification']}",
                    f"- 原因：{x['reason']}",
                    "",
                ]
        outputs = {
            "catalog.json": json_bytes(public_catalog),
            **{k: v.encode() for k, v in pages.items()},
            "PRIVATE_QUEUE.md": "\n".join(lines).encode(),
        }
        seed = {
            "source_revision": revision,
            "reviews_digest": digest(reviews_payload),
            "outputs": {k: digest(v) for k, v in outputs.items()},
        }
        if self.adapter.current_pointer()[
            "authority_revision"
        ] != revision or current_digest(self.reviews) != digest(reviews_payload):
            raise ValueError("catalog/review changed during preparation")
        queue_revision = "queues-" + digest(json_bytes(seed))[:20]
        folder = self.root / "queue-publication/revisions" / queue_revision
        folder.mkdir(parents=True, exist_ok=True)
        for name, data in outputs.items():
            write_immutable(folder / name, data)
        receipt = {
            "schema_version": "private_material_queue_publication_v1",
            "queue_revision": queue_revision,
            **seed,
            "owner_gate_ref": reviews["owner_gate_ref"],
            "catalog_count": len(catalog["records"]),
            "external_count": len(external),
            "private_count": len(private),
            "archived_count": len(archived),
            "external_ranked_count": counts["ranked"],
            "private_ranked_count": sum(c["queue_rank"] is not None for c in private),
            "expected_destination_digests": {
                k: current_digest(p) for k, p in self.targets.items()
            },
            "expected_pointer_digest": current_digest(self.pointer),
            "loopx_projection_receipts": receipts,
            "partition_unique_and_complete": True,
            "observed_at": now,
        }
        # Preview may be re-created against unchanged data after a prior publication.
        proposal = self.root / "queue-publication/proposal.json"
        atomic_write(proposal, json_bytes(receipt))
        print(
            json.dumps(
                {
                    k: receipt[k]
                    for k in (
                        "queue_revision",
                        "external_count",
                        "private_count",
                        "archived_count",
                        "external_ranked_count",
                        "private_ranked_count",
                    )
                },
                ensure_ascii=False,
            )
        )
        return receipt

    def apply(self):
        receipt = load(self.root / "queue-publication/proposal.json")
        if (
            self.adapter.current_pointer()["authority_revision"]
            != receipt["source_revision"]
            or current_digest(self.reviews) != receipt["reviews_digest"]
        ):
            raise ValueError("catalog/review drift; prepare again")
        if (
            self.pointer.exists()
            and load(self.pointer)["queue_revision"] == receipt["queue_revision"]
            and all(
                current_digest(path) == receipt["outputs"][name]
                for name, path in self.targets.items()
            )
        ):
            print(
                json.dumps(
                    {
                        "status": "no_change",
                        "queue_revision": receipt["queue_revision"],
                    }
                )
            )
            return
        if current_digest(self.pointer) != receipt["expected_pointer_digest"]:
            raise ValueError("queue pointer CAS conflict")
        for name, path in self.targets.items():
            if current_digest(path) != receipt["expected_destination_digests"][name]:
                raise ValueError("destination edited since preview")
        revision = receipt["queue_revision"]
        folder = self.root / "queue-publication/revisions" / revision
        backups = {
            k: (p.read_bytes() if p.exists() else None) for k, p in self.targets.items()
        }
        old_pointer = self.pointer.read_bytes() if self.pointer.exists() else None
        receipt["backup_ref"] = (
            "before-" + revision + "-" + digest(json_bytes(receipt))[:12]
        )
        backup_root = self.root / "queue-publication/backups" / receipt["backup_ref"]
        backup_root.mkdir(parents=True, exist_ok=True)
        for k, data in backups.items():
            if data is not None:
                write_immutable(backup_root / k, data)
        write_immutable(
            backup_root / "manifest.json",
            json_bytes(
                {k: digest(v) if v is not None else None for k, v in backups.items()}
            ),
        )
        if old_pointer is not None:
            write_immutable(backup_root / "previous-pointer.json", old_pointer)
        # Rehearse exact restoration in isolation before publishing.
        rehearsal = self.root / "queue-publication/rehearsals" / revision
        rehearsal.mkdir(parents=True, exist_ok=True)
        for name, data in backups.items():
            path = rehearsal / name
            atomic_write(path, (folder / name).read_bytes())
            if data is None:
                path.unlink()
            else:
                atomic_write(path, data)
            if current_digest(path) != receipt["expected_destination_digests"][name]:
                raise ValueError("rollback rehearsal failed")
        try:
            for name, path in self.targets.items():
                data = (folder / name).read_bytes()
                if digest(data) != receipt["outputs"][name]:
                    raise ValueError("staged output drift")
                if current_digest(path) != digest(data):
                    atomic_write(
                        path, data, mode=0o600 if name == "PRIVATE_QUEUE.md" else 0o644
                    )
            if (
                self.adapter.current_pointer()["authority_revision"]
                != receipt["source_revision"]
                or current_digest(self.reviews) != receipt["reviews_digest"]
            ):
                raise ValueError("catalog/review changed during publication")
            for name, path in self.targets.items():
                if current_digest(path) != receipt["outputs"][name]:
                    raise ValueError("publication readback mismatch")
            receipt.update(
                status="applied", readback_verified=True, rollback_rehearsed=True
            )
            atomic_write(self.pointer, json_bytes(receipt))
            write_immutable(
                folder / ("receipt-" + digest(json_bytes(receipt))[:20] + ".json"),
                json_bytes(receipt),
            )
        except Exception:
            for name, path in self.targets.items():
                if backups[name] is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write(
                        path,
                        backups[name],
                        mode=0o600 if name == "PRIVATE_QUEUE.md" else 0o644,
                    )
            if old_pointer is None:
                self.pointer.unlink(missing_ok=True)
            else:
                atomic_write(self.pointer, old_pointer)
            raise
        print(
            json.dumps(
                {
                    "status": "applied",
                    "queue_revision": revision,
                    "readback_verified": True,
                    "rollback_rehearsed": True,
                }
            )
        )

    def check(self):
        receipt = load(self.pointer)
        if (
            self.adapter.current_pointer()["authority_revision"]
            != receipt["source_revision"]
            or current_digest(self.reviews) != receipt["reviews_digest"]
        ):
            raise ValueError("queue publication stale; prepare/apply required")
        for name, path in self.targets.items():
            if current_digest(path) != receipt["outputs"][name]:
                raise ValueError("queue output drift: " + name)
        print(
            json.dumps(
                {"status": "verified", "queue_revision": receipt["queue_revision"]}
            )
        )

    def rollback(self, expected):
        receipt = load(self.pointer)
        if receipt["queue_revision"] != expected:
            raise ValueError("rollback queue revision conflict")
        for name, path in self.targets.items():
            if current_digest(path) != receipt["outputs"][name]:
                raise ValueError("edited destination; refusing rollback")
        backup_ref = receipt.get("backup_ref", "before-" + expected)
        if pathlib.Path(backup_ref).name != backup_ref:
            raise ValueError("invalid backup reference")
        backup = self.root / "queue-publication/backups" / backup_ref
        manifest = load(backup / "manifest.json")
        if manifest != receipt["expected_destination_digests"]:
            raise ValueError("rollback manifest drift")
        payloads = {}
        for name, previous_digest in manifest.items():
            if name not in self.targets:
                raise ValueError("unknown rollback output")
            data = (backup / name).read_bytes() if previous_digest is not None else None
            if data is not None and digest(data) != previous_digest:
                raise ValueError("rollback backup corrupted")
            payloads[name] = data
        if set(payloads) != set(self.targets):
            raise ValueError("incomplete rollback backup")
        old = backup / "previous-pointer.json"
        if current_digest(old) != receipt["expected_pointer_digest"]:
            raise ValueError("previous pointer backup mismatch")
        published = {name: path.read_bytes() for name, path in self.targets.items()}
        current_pointer = self.pointer.read_bytes()
        try:
            for name, data in payloads.items():
                if data is None:
                    self.targets[name].unlink(missing_ok=True)
                else:
                    atomic_write(
                        self.targets[name],
                        data,
                        mode=0o600 if name == "PRIVATE_QUEUE.md" else 0o644,
                    )
                if current_digest(self.targets[name]) != manifest[name]:
                    raise ValueError("rollback readback mismatch")
            if old.exists():
                atomic_write(self.pointer, old.read_bytes())
            else:
                self.pointer.unlink()
        except Exception:
            for name, data in published.items():
                atomic_write(
                    self.targets[name],
                    data,
                    mode=0o600 if name == "PRIVATE_QUEUE.md" else 0o644,
                )
            atomic_write(self.pointer, current_pointer)
            raise
        atomic_write(
            self.root / "queue-publication/last-rollback.json",
            json_bytes(
                {
                    "from_revision": expected,
                    "output_readback_verified": True,
                    "material_authority_unchanged": True,
                }
            ),
        )
        print(
            json.dumps(
                {
                    "status": "rolled_back",
                    "from_revision": expected,
                    "material_authority_unchanged": True,
                }
            )
        )

    def main(self, argv=None):
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument(
            "command", choices=["prepare", "apply", "check", "rollback"]
        )
        parser.add_argument("--expected-queue-revision")
        args = parser.parse_args(argv)
        folder = self.root / "queue-publication"
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (folder / "lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if args.command == "rollback":
                if not args.expected_queue_revision:
                    parser.error("rollback requires --expected-queue-revision")
                return self.rollback(args.expected_queue_revision)
            return getattr(self, args.command)()
