"""Insert source-verified new rows without discarding annotated reading text."""
import re
from collections import defaultdict, deque


def merge_annotated_rows(text, entries, render_new):
    """The caller verifies source identity/order; display labels may repeat.

    This supports additive projection repair only. Removals/reorders require a
    source-backed semantic merge instead of guessing from non-unique labels.
    """
    rows = list(re.finditer(r'^\|[ \t]*\d+[ \t]*\|[ \t]*([A-Z]\d+[a-z]?)[ \t]*·.*$', text, re.M))
    if not rows:
        raise ValueError('annotated view has no material rows')
    if any(text[a.end():b.start()] != '\n' for a,b in zip(rows, rows[1:])):
        raise ValueError('annotations between table rows need a semantic merge')
    previous = [m[1] for m in rows]
    current = [e['labels'][0] for e in entries]
    if [label for label in current if label in previous] != previous:
        raise ValueError('annotated view order/removal needs semantic reconciliation')
    bylabel = defaultdict(deque)
    for match in rows:
        bylabel[match[1]].append(match[0])
    merged = []
    for rank, entry in enumerate(entries, 1):
        label = entry['labels'][0]
        if bylabel[label]:
            row = re.sub(r'^\|[ \t]*\d+[ \t]*\|', f'| {rank} |', bylabel[label].popleft(), count=1)
        else:
            row = render_new(rank, entry)
        merged.append(row)
    if any(bylabel.values()):
        raise ValueError('annotated rows were not fully preserved')
    return text[:rows[0].start()] + '\n'.join(merged) + text[rows[-1].end():]
