#!/usr/bin/env python3
"""Read-only three-way material inventory. Absence never proves completion."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import material_queue


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                    separators=(",", ":")).encode()).hexdigest()


def metadata(card):
    return {key: value for key, value in card.items() if key != "queue_rank"}


def merge_ranked_orders(current_order, incoming_order):
    """Merge an accepted incoming order without redistributing local-only refs.

    Keep local-only entries before their next surviving shared anchor. If shared
    anchors were reordered, incoming order wins while local-only order remains
    intact. An incoming omission never removes a local entry; callers resolve
    lifecycle/visibility and canonical aliases before invoking this helper.
    """
    for order in (current_order, incoming_order):
        if len(order) != len(set(order)):
            raise ValueError("duplicate material in ranked order")
    positions = {ref: i for i, ref in enumerate(incoming_order)}
    next_anchor = len(incoming_order)
    slots = {}
    for ref in reversed(current_order):
        if ref in positions:
            next_anchor = positions[ref]
        else:
            slots[ref] = next_anchor
    buckets = [[] for _ in range(len(incoming_order) + 1)]
    previous_slot = 0
    for ref in current_order:
        if ref not in positions:
            previous_slot = max(previous_slot, slots[ref])
            buckets[previous_slot].append(ref)
    merged = []
    for i, ref in enumerate(incoming_order):
        merged.extend(buckets[i])
        merged.append(ref)
    merged.extend(buckets[-1])
    return merged


def reconcile(base, local, remote):
    """Compare reviewed cards; return observations, never lifecycle writes."""
    catalogs = {"base": base, "local": local, "remote": remote}
    indexed = {}
    for name, catalog in catalogs.items():
        material_queue.validate(catalog)
        indexed[name] = {card["material_ref"]: card for card in catalog["entries"]}
    b, l, r = (indexed[name] for name in ("base", "local", "remote"))
    changes, counts = [], {}
    for ref in sorted(set(b) | set(l) | set(r)):
        before, ours, theirs = (metadata(c[ref]) if ref in c else None for c in (b, l, r))
        if before is None:
            if ours is not None and theirs is None:
                kind, action = "local_addition", "preserve_local_intake"
            elif ours is None:
                kind, action = "remote_addition", "review_remote_intake"
            elif ours == theirs:
                kind, action = "shared_addition", "keep_once_by_stable_id"
            else:
                kind, action = "conflicting_addition", "review_both_versions"
        elif ours is None or theirs is None:
            if ours is None and theirs is None:
                kind = "absent_both"
            elif ours is None:
                kind = "local_absence"
            else:
                kind = "remote_absence"
            action = "require_source_disposition_evidence"
        elif ours == theirs:
            kind = "unchanged" if ours == before else "shared_update"
            action = "keep_once_by_stable_id"
        elif ours == before:
            kind, action = "remote_update", "review_remote_update"
        elif theirs == before:
            kind, action = "local_update", "preserve_local_update"
        else:
            kind, action = "conflicting_update", "review_both_versions"
        counts[kind] = counts.get(kind, 0) + 1
        if kind != "unchanged":
            changes.append({"material_ref": ref, "kind": kind, "action": action,
                            "metadata_digests": {name: digest(metadata(cards[ref]))
                                                 if ref in cards else None
                                                 for name, cards in indexed.items()}})
    orders = {name: [c["material_ref"] for c in sorted(
        (c for c in catalog["entries"] if c["queue_rank"] is not None),
        key=lambda c: c["queue_rank"])] for name, catalog in catalogs.items()}
    return {"schema_version": "material_reconciliation_plan_v1",
            "catalog_digests": {name: digest(c) for name, c in catalogs.items()},
            "counts": counts, "changes": changes,
            "ranking_changed": {"local": orders["local"] != orders["base"],
                                "remote": orders["remote"] != orders["base"]},
            "ranked_orders": orders,
            "lifecycle_transitions": [], "implicit_archive_allowed": False,
            "read_only": True}


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE)


def git_catalog(repo, revision, path):
    return json.loads(git(repo, "show", revision + ":" + path))


def git_plan(repo, upstream, catalog_path="Learning-Materials/catalog.json"):
    repo = Path(git(repo, "rev-parse", "--show-toplevel").decode().strip())
    path = Path(catalog_path)
    if path.is_absolute() or ".." in path.parts or not path.parts or upstream.startswith("-"):
        raise ValueError("expected a repository-relative catalog and Git upstream ref")
    if (repo / path).is_symlink():
        raise ValueError("catalog must be a regular repository file")
    head = git(repo, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    remote = git(repo, "rev-parse", "--verify", upstream + "^{commit}").decode().strip()
    base = git(repo, "merge-base", head, remote).decode().strip()
    local_bytes = (repo / path).read_bytes()
    index_bytes = git(repo, "show", ":" + path.as_posix())
    plan = reconcile(git_catalog(repo, base, path.as_posix()), json.loads(local_bytes),
                     git_catalog(repo, remote, path.as_posix()))
    plan["git_snapshot"] = {"base": base, "head": head, "upstream": remote,
                            "upstream_ref": upstream, "catalog_path": path.as_posix(),
                            "working_bytes_digest": hashlib.sha256(local_bytes).hexdigest(),
                            "index_bytes_digest": hashlib.sha256(index_bytes).hexdigest(),
                            "index_differs_from_working": index_bytes != local_bytes}
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--upstream", default="origin/master",
                        help="Already-fetched Git ref; this command does not fetch")
    parser.add_argument("--catalog-path", default="Learning-Materials/catalog.json")
    args = parser.parse_args()
    try:
        plan = git_plan(args.repo, args.upstream, args.catalog_path)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(2, "Cannot verify the three-way material snapshot: " + str(error) + "\n")
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
