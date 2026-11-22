#!/usr/bin/env python3
"""Single-pass read-only preflight for CS-Notes sync and public-safety checks.

Combines Git divergence/dirty/overlap inspection, public-safety path and diff
scanning, curated skills manifest verification, and three-way material
reconciliation (with upstream commit attribution for remote_absence entries) so
agents do not read implementation files or scan unrelated session logs.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import material_reconcile  # noqa: E402


FORBIDDEN_PREFIXES = (".local/", "公司项目/")
FORBIDDEN_FILENAMES = {".env", ".env.local", ".env.production", ".env.development"}
FORBIDDEN_SUFFIXES = (".pem", ".key", ".p12", ".pfx")

LEAK_PATTERNS = (
    ("local_user_path", re.compile(r"(?<![A-Za-z0-9])/(?:Users|home)/[A-Za-z0-9._-]+")),
    ("file_uri_local_path", re.compile(r"file:///(?:Users|home|private/var|private/tmp)/")),
    ("private_decision_context_path", re.compile(r"(?<!\\)\.local/" + r"decision-advisor\b")),
    ("private_key_header", re.compile(r"-----BEGIN " + r"[A-Z0-9 ]*PRIVATE KEY-----")),
    ("secret_token_prefix", re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b")),
)


def _git_bytes(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE)


def _git_text(repo: Path, *args: str) -> str:
    return _git_bytes(repo, *args).decode("utf-8", errors="replace")


def _has_control_chars(path_str: str) -> bool:
    return any(ord(ch) < 32 or ord(ch) == 127 for ch in path_str)


def _is_forbidden_path(rel_path: str) -> str | None:
    norm = rel_path.replace("\\", "/").lstrip("./")
    if _has_control_chars(rel_path):
        return "control_char_filename"
    if any(norm == p.rstrip("/") or norm.startswith(p) for p in FORBIDDEN_PREFIXES):
        return "private_directory"
    name = Path(norm).name
    if name in FORBIDDEN_FILENAMES or name.startswith(".env."):
        return "dotenv_file"
    if norm.lower().endswith(FORBIDDEN_SUFFIXES):
        return "private_key_file"
    return None


def _parse_status_z(raw: bytes) -> tuple[list[str], list[str], list[str], list[str]]:
    staged, unstaged, untracked, stray = [], [], [], []
    entries = raw.split(b"\x00")
    i = 0
    while i < len(entries):
        item = entries[i]
        i += 1
        if not item:
            continue
        xy = item[:2].decode("ascii", errors="replace")
        path = item[3:].decode("utf-8", errors="surrogateescape")
        if xy[0] in ("R", "C") and i < len(entries):
            i += 1  # skip original path in -z porcelain v1
        if xy == "??":
            untracked.append(path)
        else:
            if xy[0] not in (" ", "?"):
                staged.append(path)
            if xy[1] not in (" ", "?"):
                unstaged.append(path)
        if _has_control_chars(path):
            stray.append(path)
    return sorted(set(staged)), sorted(set(unstaged)), sorted(set(untracked)), sorted(set(stray))


def inspect_git_state(repo: Path, upstream: str) -> dict:
    branch = _git_text(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
    head = _git_text(repo, "rev-parse", "--verify", "HEAD^{commit}").strip()
    remote = _git_text(repo, "rev-parse", "--verify", f"{upstream}^{{commit}}").strip()
    merge_base = _git_text(repo, "merge-base", head, remote).strip()
    counts = _git_text(repo, "rev-list", "--left-right", "--count", f"{head}...{remote}").strip().split()
    ahead, behind = (int(counts[0]), int(counts[1])) if len(counts) == 2 else (0, 0)
    staged, unstaged, untracked, stray = _parse_status_z(_git_bytes(repo, "status", "--porcelain=v1", "-z", "-uall"))

    upstream_changed = set()
    if merge_base != remote:
        raw_names = _git_bytes(repo, "diff", "--name-only", "-z", f"{merge_base}..{remote}")
        upstream_changed = {p.decode("utf-8", errors="replace") for p in raw_names.split(b"\x00") if p}
    dirty = set(staged) | set(unstaged) | set(untracked)
    overlapping = sorted(dirty & upstream_changed)

    upstream_commits = []
    if merge_base != remote:
        log_text = _git_text(
            repo, "log", "--reverse", "--format=%H\t%h\t%ai\t%s", f"{merge_base}..{remote}"
        )
        for line in log_text.splitlines():
            parts = line.split("\t", 3)
            if len(parts) == 4:
                upstream_commits.append(
                    {"oid": parts[0], "short_oid": parts[1], "date": parts[2], "subject": parts[3]}
                )

    return {
        "branch": branch,
        "head": head,
        "upstream_ref": upstream,
        "upstream": remote,
        "merge_base": merge_base,
        "ahead": ahead,
        "behind": behind,
        "fast_forwardable": merge_base == head,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
        "stray_files": stray,
        "overlapping_dirty_files": overlapping,
        "upstream_commits": upstream_commits,
    }


def _scan_lines_for_leaks(rel_path: str, lines_with_lineno: list[tuple[int, str]]) -> list[dict]:
    findings = []
    for lineno, text in lines_with_lineno:
        for rule_name, pattern in LEAK_PATTERNS:
            if pattern.search(text):
                findings.append({"path": rel_path, "line": lineno, "rule": rule_name})
    return findings


def audit_public_safety(repo: Path, git_state: dict) -> dict:
    candidates = sorted(set(git_state["staged"]) | set(git_state["unstaged"]) | set(git_state["untracked"]))
    forbidden_paths = []
    for rel in candidates:
        reason = _is_forbidden_path(rel)
        if reason:
            forbidden_paths.append({"path": rel, "reason": reason})

    leak_findings = []
    # Scan added lines in git diff HEAD for tracked files (avoids flagging unchanged context).
    tracked_dirty = [p for p in sorted(set(git_state["staged"]) | set(git_state["unstaged"])) if not _is_forbidden_path(p)]
    if tracked_dirty:
        diff_text = _git_text(repo, "diff", "--unified=0", "HEAD", "--", *tracked_dirty)
        current_file = None
        new_lineno = 0
        added_by_file: dict[str, list[tuple[int, str]]] = {}
        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                current_file = line[6:]
            elif line.startswith("@@ ") and current_file:
                m = re.search(r"\+(\d+)", line)
                new_lineno = int(m.group(1)) if m else 1
            elif line.startswith("+") and not line.startswith("+++") and current_file:
                added_by_file.setdefault(current_file, []).append((new_lineno, line[1:]))
                new_lineno += 1
        for rel, items in added_by_file.items():
            leak_findings.extend(_scan_lines_for_leaks(rel, items))

    # Scan untracked regular files (up to 2 MiB text files).
    for rel in git_state["untracked"]:
        if _is_forbidden_path(rel):
            continue
        full = repo / rel
        if not full.is_file() or full.is_symlink() or full.stat().st_size > 2 * 1024 * 1024:
            continue
        raw = full.read_bytes()
        if b"\x00" in raw[:4096]:
            continue
        lines = [(idx, ln) for idx, ln in enumerate(raw.decode("utf-8", errors="replace").splitlines(), 1)]
        leak_findings.extend(_scan_lines_for_leaks(rel, lines))

    return {
        "ok": not forbidden_paths and not leak_findings,
        "forbidden_paths": forbidden_paths,
        "leak_findings": leak_findings,
    }


def check_skills_manifest(repo: Path) -> dict:
    check_script = repo / "note-system/skills/check.py"
    if not check_script.is_file():
        return {"ok": True, "configured": False}
    spec = importlib.util.spec_from_file_location("cs_notes_skills_check", check_script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        count = module.check(refresh=False)
        return {"ok": True, "configured": True, "verified_skills": count}
    except Exception as exc:
        return {
            "ok": False,
            "configured": True,
            "error": str(exc),
            "remediation": "Review skill diffs for public-safety, then run: python3 note-system/skills/check.py --refresh",
        }


def _attribute_remote_absences(
    repo: Path, merge_base: str, upstream: str, catalog_path: str, missing_refs: list[str], base_titles: dict[str, str]
) -> list[dict]:
    if not missing_refs:
        return []
    commit_lines = _git_text(
        repo, "log", "--reverse", "--format=%H\t%h\t%ai\t%s", f"{merge_base}..{upstream}", "--", catalog_path
    ).splitlines()
    commits = []
    for line in commit_lines:
        parts = line.split("\t", 3)
        if len(parts) == 4:
            commits.append({"oid": parts[0], "short_oid": parts[1], "date": parts[2], "subject": parts[3]})

    remaining = set(missing_refs)
    removed_by: dict[str, dict] = {}
    for c in commits:
        if not remaining:
            break
        try:
            cat = material_reconcile.git_catalog(repo, c["oid"], catalog_path)
        except Exception:
            continue
        present = {entry["material_ref"] for entry in cat.get("entries", [])}
        newly_absent = remaining - present
        for ref in newly_absent:
            removed_by[ref] = c
        remaining -= newly_absent

    return [
        {
            "material_ref": ref,
            "title": base_titles.get(ref, ""),
            "removed_in_commit": removed_by.get(ref),
        }
        for ref in missing_refs
    ]


def inspect_materials(repo: Path, upstream: str, catalog_path: str = "Learning-Materials/catalog.json") -> dict:
    if not (repo / catalog_path).is_file():
        return {"configured": False}
    plan = material_reconcile.git_plan(repo, upstream, catalog_path)
    snap = plan["git_snapshot"]
    base_cat = material_reconcile.git_catalog(repo, snap["base"], catalog_path)
    base_titles = {e["material_ref"]: e.get("title", "") for e in base_cat.get("entries", [])}

    by_kind: dict[str, list[str]] = {}
    for ch in plan["changes"]:
        by_kind.setdefault(ch["kind"], []).append(ch["material_ref"])

    remote_absences = _attribute_remote_absences(
        repo, snap["base"], snap["upstream"], catalog_path, by_kind.get("remote_absence", []), base_titles
    )

    source_status = {"configured": False}
    binding = repo / ".local/material-lifecycle/source-binding.json"
    if binding.is_file():
        proc = subprocess.run(
            [sys.executable, str(repo / "note-system/materials/material_source.py"), "--repo", str(repo), "status"],
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            parsed = json.loads(proc.stdout) if proc.stdout.strip() else {}
        except json.JSONDecodeError:
            parsed = {"raw": proc.stdout.strip()}
        source_status = {"configured": proc.returncode == 0, "exit_code": proc.returncode, "detail": parsed}

    conflicts = (
        by_kind.get("conflicting_addition", [])
        + by_kind.get("conflicting_update", [])
    )
    blocked_by_remote_absence = bool(remote_absences) and source_status.get("configured", False)
    if conflicts:
        next_step = "resolve_card_conflicts_with_user"
    elif blocked_by_remote_absence:
        next_step = "sync_non_material_changes_and_confirm_remote_completions_with_user"
    elif plan["counts"].get("remote_addition") or plan["counts"].get("remote_update") or plan["ranking_changed"]["remote"]:
        next_step = "reconcile_source_and_publish"
    else:
        next_step = "publish_or_commit_clean_queue"

    return {
        "configured": True,
        "git_snapshot": snap,
        "counts": plan["counts"],
        "ranking_changed": plan["ranking_changed"],
        "local_addition_refs": by_kind.get("local_addition", []),
        "local_update_refs": by_kind.get("local_update", []),
        "remote_addition_refs": by_kind.get("remote_addition", []),
        "remote_update_refs": by_kind.get("remote_update", []),
        "local_absence_refs": by_kind.get("local_absence", []),
        "conflict_refs": conflicts,
        "remote_absences": remote_absences,
        "source_status": source_status,
        "queue_publish_blocked_by_unverified_remote_absence": blocked_by_remote_absence,
        "recommended_next_step": next_step,
    }


def write_backup(repo: Path, backup_dir: Path, git_state: dict) -> dict:
    backup_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(backup_dir, 0o700)
    files_dir = backup_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(files_dir, 0o700)

    dirty_paths = sorted(set(git_state["staged"]) | set(git_state["unstaged"]) | set(git_state["untracked"]))
    manifest_entries = []
    for idx, rel in enumerate(dirty_paths):
        full = repo / os.fsdecode(rel.encode("utf-8", errors="surrogateescape"))
        if not full.exists() or full.is_dir():
            continue
        raw = full.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        safe_rel = rel if not _has_control_chars(rel) else f"_control_char_{idx}_{sha[:12]}.bin"
        dest = files_dir / safe_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(full, dest)
        os.chmod(dest, 0o600)
        manifest_entries.append({"path": rel, "backup_rel": f"files/{safe_rel}", "sha256": sha, "bytes": len(raw)})

    patch_bytes = _git_bytes(repo, "diff", "--binary", "HEAD")
    patch_path = backup_dir / "head.diff"
    patch_path.write_bytes(patch_bytes)
    os.chmod(patch_path, 0o600)

    manifest = {
        "schema_version": "sync_backup_manifest_v1",
        "head": git_state["head"],
        "upstream_ref": git_state["upstream_ref"],
        "upstream": git_state["upstream"],
        "merge_base": git_state["merge_base"],
        "patch_sha256": hashlib.sha256(patch_bytes).hexdigest(),
        "files": manifest_entries,
    }
    manifest_path = backup_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(manifest_path, 0o600)
    return {"backup_dir": str(backup_dir), "backed_up_files": len(manifest_entries)}


def run_preflight(repo: Path, upstream: str = "origin/master", catalog_path: str = "Learning-Materials/catalog.json", backup_dir: Path | None = None) -> dict:
    repo = Path(_git_text(repo, "rev-parse", "--show-toplevel").strip())
    git_state = inspect_git_state(repo, upstream)
    backup_info = write_backup(repo, backup_dir, git_state) if backup_dir is not None else None
    public_safety = audit_public_safety(repo, git_state)
    skills_manifest = check_skills_manifest(repo)
    materials = inspect_materials(repo, upstream, catalog_path)
    return {
        "schema_version": "material_sync_preflight_v1",
        "git": git_state,
        "backup": backup_info,
        "public_safety": public_safety,
        "skills_manifest": skills_manifest,
        "materials": materials,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--upstream", default="origin/master", help="Already-fetched Git ref (run git fetch first)")
    parser.add_argument("--catalog-path", default="Learning-Materials/catalog.json")
    parser.add_argument("--backup-dir", type=Path, help="Optional private directory (e.g. .local/sync-backups/<ts>) to save lossless copies before merge")
    args = parser.parse_args(argv)
    try:
        report = run_preflight(args.repo, args.upstream, args.catalog_path, args.backup_dir)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
