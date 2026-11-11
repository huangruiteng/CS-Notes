"""Deterministic horizon-wave, effort-stratified material rerank planner.

Separates reading effort from topic importance, enforces primary-over-secondary
source precedence, verifies load-bearing deliverable citations are ranked, and
prevents orthogonal trend items from crowding out active decision-horizon waves
in the Top-N window while preserving 100% membership and untouched order.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Mapping, Sequence

HORIZON_WAVES = (
    "imminent_gate",
    "active_sprint",
    "foundational_track",
    "orthogonal_backlog",
)
EFFORT_BANDS = (
    "quick_slice",
    "focused_study",
    "deep_monograph",
)
EVIDENCE_ROLES = (
    "load_bearing_primary",
    "method_comparator",
    "foundational_reference",
    "secondary_or_commentary",
    "orthogonal_signal",
)

_WAVE_ORDER = {
    "imminent_gate": 0,
    "active_sprint": 1,
    "foundational_track": 2,
    "orthogonal_backlog": 3,
    "untouched": 4,
}
_EFFORT_DIVISOR = {
    "quick_slice": 1.0,
    "focused_study": 2.0,
    "deep_monograph": 6.0,
}
_EFFORT_ORDER = {
    "quick_slice": 0,
    "focused_study": 1,
    "deep_monograph": 2,
}
_ROLE_ORDER = {
    "load_bearing_primary": 0,
    "method_comparator": 1,
    "foundational_reference": 2,
    "secondary_or_commentary": 3,
    "orthogonal_signal": 4,
}


def _token(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(ch.isspace() for ch in value):
        raise ValueError(f"{field} must be a non-empty compact token")
    return value


def _unique_tokens(values: Sequence[str] | None, *, field: str) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{field} must be a sequence of compact tokens")
    refs = [_token(v, field=f"{field}[]") for v in values]
    if len(set(refs)) != len(refs):
        raise ValueError(f"{field} values must be unique")
    return refs


def _topological_respecting_priority(
    refs: list[str],
    priority_key: Mapping[str, tuple[Any, ...]],
    precedes: Mapping[str, set[str]],
) -> list[str]:
    """Order refs by priority_key while guaranteeing u precedes v for v in precedes[u]."""
    ref_set = set(refs)
    indegree = {r: 0 for r in refs}
    adj: dict[str, list[str]] = {r: [] for r in refs}
    for earlier, laters in precedes.items():
        if earlier not in ref_set:
            continue
        for later in laters:
            if later not in ref_set:
                continue
            if earlier == later:
                raise ValueError(f"self-referential primary_source_refs on {earlier}")
            adj[earlier].append(later)
            indegree[later] += 1

    ready = [r for r in refs if indegree[r] == 0]
    ready.sort(key=lambda r: priority_key[r])
    out: list[str] = []
    queue = deque(ready)
    while queue:
        # Pop the highest-priority currently unlocked item.
        items = sorted(queue, key=lambda r: priority_key[r])
        current = items[0]
        queue = deque(items[1:])
        out.append(current)
        for nxt in adj[current]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(out) != len(refs):
        raise ValueError("cycle detected in primary_source_refs lineage constraints")
    return out


def plan_wave_rerank(
    ordered_material_refs: Sequence[str],
    candidates: Sequence[Mapping[str, Any]],
    *,
    top_window_size: int = 30,
    protected_material_refs: Sequence[str] | None = None,
    required_load_bearing_refs: Sequence[str] | None = None,
    max_orthogonal_in_top_window: int = 0,
) -> tuple[list[str], dict[str, Any]]:
    """Compute a lossless, effort- and horizon-aware wave rerank over a ranked queue."""
    refs = _unique_tokens(ordered_material_refs, field="ordered_material_refs")
    if not refs:
        raise ValueError("ordered_material_refs must contain at least one item")
    if type(top_window_size) is not int or top_window_size < 1:
        raise ValueError("top_window_size must be a positive integer")
    if type(max_orthogonal_in_top_window) is not int or max_orthogonal_in_top_window < 0:
        raise ValueError("max_orthogonal_in_top_window must be a non-negative integer")

    ref_index = {ref: idx for idx, ref in enumerate(refs)}
    protected = _unique_tokens(protected_material_refs, field="protected_material_refs")
    if not set(protected).issubset(ref_index):
        raise ValueError("protected_material_refs must belong to ordered_material_refs")
    protected_set = set(protected)

    required_lb = _unique_tokens(required_load_bearing_refs, field="required_load_bearing_refs")
    missing_lb = [ref for ref in required_lb if ref not in ref_index]
    if missing_lb:
        raise ValueError(
            "unranked or missing load-bearing primary materials must be settled via intake first: "
            + ", ".join(missing_lb)
        )

    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Sequence):
        raise TypeError("candidates must be a sequence of mappings")

    annotations: dict[str, dict[str, Any]] = {}
    precedes: dict[str, set[str]] = {}
    demoted_monographs: list[str] = []

    for idx, raw in enumerate(candidates):
        if not isinstance(raw, Mapping):
            raise TypeError(f"candidates[{idx}] must be an object")
        mref = _token(raw.get("material_ref"), field=f"candidates[{idx}].material_ref")
        if mref not in ref_index:
            raise ValueError(
                f"candidates[{idx}].material_ref ({mref}) is not in ordered_material_refs; settle intake first"
            )
        if mref in annotations:
            raise ValueError(f"duplicate candidate annotation for {mref}")
        if mref in protected_set:
            raise ValueError(f"protected material {mref} cannot be re-annotated for movement")

        wave = _token(raw.get("horizon_wave"), field=f"candidates[{idx}].horizon_wave")
        if wave not in HORIZON_WAVES:
            raise ValueError(f"unsupported horizon_wave: {wave}")
        effort = _token(raw.get("effort_band"), field=f"candidates[{idx}].effort_band")
        if effort not in EFFORT_BANDS:
            raise ValueError(f"unsupported effort_band: {effort}")
        role = _token(raw.get("evidence_role"), field=f"candidates[{idx}].evidence_role")
        if role not in EVIDENCE_ROLES:
            raise ValueError(f"unsupported evidence_role: {role}")

        gain = raw.get("decision_gain_score", 50.0)
        if isinstance(gain, bool) or not isinstance(gain, (int, float)) or not (0.0 <= float(gain) <= 100.0):
            raise ValueError(f"candidates[{idx}].decision_gain_score must be finite in [0, 100]")
        gain_val = float(gain)

        blocks = raw.get("blocks_active_deliverable", False)
        if not isinstance(blocks, bool):
            raise TypeError(f"candidates[{idx}].blocks_active_deliverable must be a boolean")
        sliced = raw.get("scoped_slice_ready", False)
        if not isinstance(sliced, bool):
            raise TypeError(f"candidates[{idx}].scoped_slice_ready must be a boolean")

        primaries = _unique_tokens(
            raw.get("primary_source_refs"),
            field=f"candidates[{idx}].primary_source_refs",
        )
        missing_primaries = [p for p in primaries if p not in ref_index]
        if missing_primaries:
            raise ValueError(
                f"candidates[{idx}] cites unranked primary_source_refs: {', '.join(missing_primaries)}"
            )
        for p in primaries:
            precedes.setdefault(p, set()).add(mref)

        effective_wave = wave
        if role == "orthogonal_signal":
            effective_wave = "orthogonal_backlog"
        elif (
            effort == "deep_monograph"
            and not sliced
            and wave in {"imminent_gate", "active_sprint"}
        ):
            effective_wave = "foundational_track"
            demoted_monographs.append(mref)

        voi = gain_val / _EFFORT_DIVISOR[effort]
        annotations[mref] = {
            "material_ref": mref,
            "declared_wave": wave,
            "effective_wave": effective_wave,
            "effort_band": effort,
            "evidence_role": role,
            "decision_gain_score": gain_val,
            "cost_adjusted_voi": round(voi, 4),
            "blocks_active_deliverable": blocks,
            "scoped_slice_ready": sliced,
            "primary_source_refs": primaries,
        }

    movable_refs = [r for r in refs if r not in protected_set]
    priority_key: dict[str, tuple[Any, ...]] = {}
    for r in movable_refs:
        ann = annotations.get(r)
        if ann is None:
            priority_key[r] = (_WAVE_ORDER["untouched"], 1, 99, 0.0, 99, ref_index[r])
        else:
            priority_key[r] = (
                _WAVE_ORDER[ann["effective_wave"]],
                0 if ann["blocks_active_deliverable"] else 1,
                _ROLE_ORDER[ann["evidence_role"]],
                -ann["cost_adjusted_voi"],
                _EFFORT_ORDER[ann["effort_band"]],
                ref_index[r],
            )

    movable_ordered = _topological_respecting_priority(movable_refs, priority_key, precedes)

    def is_orthogonal(ref: str) -> bool:
        ann = annotations.get(ref)
        return bool(
            ann
            and (
                ann["effective_wave"] == "orthogonal_backlog"
                or ann["evidence_role"] == "orthogonal_signal"
            )
        )

    # Assemble into non-protected slots while enforcing max_orthogonal_in_top_window.
    window_cap = min(top_window_size, len(refs))
    reordered: list[str | None] = [None] * len(refs)
    for pref in protected:
        reordered[ref_index[pref]] = pref

    non_orth = deque([r for r in movable_ordered if not is_orthogonal(r)])
    orth = deque([r for r in movable_ordered if is_orthogonal(r)])
    merged_movable = deque(movable_ordered)

    orth_in_window = 0
    placed: set[str] = set()
    for slot in range(len(refs)):
        if reordered[slot] is not None:
            continue
        while merged_movable and merged_movable[0] in placed:
            merged_movable.popleft()
        while non_orth and non_orth[0] in placed:
            non_orth.popleft()
        while orth and orth[0] in placed:
            orth.popleft()

        in_top_window = slot < window_cap
        candidate = merged_movable[0]
        if in_top_window and is_orthogonal(candidate) and orth_in_window >= max_orthogonal_in_top_window and non_orth:
            chosen = non_orth.popleft()
        else:
            chosen = merged_movable.popleft()
            if is_orthogonal(chosen) and in_top_window:
                orth_in_window += 1
        reordered[slot] = chosen
        placed.add(chosen)

    final_refs = [r for r in reordered if r is not None]
    if len(final_refs) != len(refs) or sorted(final_refs) != sorted(refs):
        raise AssertionError("wave rerank violated lossless set membership")

    final_pos = {r: idx + 1 for idx, r in enumerate(final_refs)}
    for earlier, laters in precedes.items():
        for later in laters:
            if final_pos[earlier] >= final_pos[later]:
                raise ValueError(
                    f"primary source {earlier} (rank {final_pos[earlier]}) must precede {later} (rank {final_pos[later]})"
                )

    for mref, ann in annotations.items():
        if ann["blocks_active_deliverable"] and ann["evidence_role"] == "load_bearing_primary":
            if final_pos[mref] > window_cap:
                raise ValueError(
                    f"load-bearing deliverable blocker {mref} landed outside top window at rank {final_pos[mref]}"
                )

    moves = [
        {
            "material_ref": r,
            "from_rank": ref_index[r] + 1,
            "to_rank": idx + 1,
        }
        for idx, r in enumerate(final_refs)
        if ref_index[r] != idx
    ]
    max_disp = max((abs(m["from_rank"] - m["to_rank"]) for m in moves), default=1)
    wave_counts: dict[str, int] = {w: 0 for w in (*HORIZON_WAVES, "untouched")}
    for r in final_refs:
        ann = annotations.get(r)
        wave_counts[ann["effective_wave"] if ann else "untouched"] += 1

    return final_refs, {
        "constraints": {
            "target_window_size": len(refs),
            "max_moved_items": max(1, len(moves)),
            "max_rank_displacement": max(1, max_disp),
            "protected_material_refs": protected,
        },
        "moves": moves,
        "demoted_unsliced_monographs": demoted_monographs,
        "wave_counts": wave_counts,
        "orthogonal_in_top_window": sum(
            1 for r in final_refs[:window_cap] if is_orthogonal(r)
        ),
    }
