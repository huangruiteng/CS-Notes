"""Import accepted Git cards through the registered source, preserving authority.

Git is evidence for reviewed fields/order, never for user completion. Existing
records and backing stay byte-for-byte intact. Intake and ranking use separate
revisions; application binds the plan to live source, reviews and Git bytes.
"""
import copy
import json
import re
import uuid
from collections import Counter

import material_queue
import material_queue_sync as sync
from material_reconcile import git, git_catalog, merge_ranked_orders, metadata


def build(catalog, reviews, baseline, incoming, commit):
    """Pure proposal; no file writes, grants, lifecycle changes or source reads."""
    material_queue.validate(baseline)
    material_queue.validate(incoming)
    intake = copy.deepcopy(catalog)
    records = {r['stable_id']: r for r in intake['records']}
    decisions = {r['material_ref']: copy.deepcopy(r) for r in reviews['records']}
    if len(records) != len(intake['records']) or len(decisions) != len(reviews['records']):
        raise ValueError('duplicate source/review identity')
    aliases = {d.get('public_material_ref', ref): ref for ref, d in decisions.items()}
    old_cards = {aliases.get(c['material_ref'], c['material_ref']): metadata(c)
                 for c in baseline['entries']}
    cards = {}
    for card in incoming['entries']:
        ref = aliases.get(card['material_ref'], card['material_ref'])
        if ref in cards:
            raise ValueError('duplicate canonical public identity')
        cards[ref] = card
    content = {}
    added, updated, archived = [], [], []
    evidence = 'git:' + commit + ':Learning-Materials/catalog.json'
    used = [int(label[1:]) for r in records.values() for label in r['legacy_labels']
            if re.fullmatch(r'U\d+', label)]
    next_label = max(used, default=0) + 1
    for ref, card in cards.items():
        record = records.get(ref)
        if record and record['lifecycle_state'] == 'archived':
            archived.append(ref)
            continue
        if record is None:
            if card['lifecycle'] != 'candidate':
                raise ValueError('new remote material needs separate lifecycle evidence: ' + ref)
            label = 'U' + str(next_label)
            next_label += 1
            body = {'schema_version': 'git_reviewed_material_v1', 'material_ref': ref,
                    'legacy_label': label, 'title': card['title'],
                    'sources': {'source_' + str(i): {'url': url, 'read_status':
                        'imported reviewed card; original-source read not repeated'}
                        for i, url in enumerate(card['sources'])},
                    'core_judgment': card['note'],
                    'classification': {'user_reading': card['note'], 'tier': card['tier'],
                                       'reason': '沿用已审查的远端卡片与排序；本次同步不重新评分。'},
                    'recommended_action': card['note'], 'public_card_snapshot': card,
                    'source_status_override': '仅核对并导入已提交的公开卡片；保留其读取范围，未在本次同步重读原文。',
                    'evidence': {'exact_read_ref': evidence, 'scope': 'committed public card',
                                 'inherited_read_scope': card['read_scope']}}
            payload = sync.canonical_json(body)
            digest = sync.digest(payload)
            content[digest] = payload
            record = {'stable_id': ref, 'source_id': 'managed-native',
                      'source_entry_ref': evidence, 'source_ref': evidence,
                      'source_material_revision': commit, 'legacy_labels': [label],
                      'lifecycle_state': 'candidate',
                      'heading_digest': sync.digest(card['title'].encode()),
                      'entry_digest': digest, 'identical_entry_occurrence': 0,
                      'sequence': max((r['sequence'] for r in records.values()), default=-1) + 1,
                      'candidate_record_ref': 'candidate-record-' + ref,
                      'content_backing_ref': 'managed-content-' + digest,
                      'content_digest': 'sha256:' + digest, 'content_size_bytes': len(payload),
                      'exact_read_ref': evidence}
            intake['records'].append(record)
            records[ref] = record
            added.append(ref)
        elif card['lifecycle'] != record['lifecycle_state']:
            raise ValueError('Git lifecycle differs; separate material completion evidence required: ' + ref)
        desired = metadata(card)
        desired['material_ref'] = ref
        previous = decisions.get(ref)
        current = previous.get('public_card') if previous else None
        base = copy.deepcopy(old_cards.get(ref))
        if base:
            base['material_ref'] = ref
        if previous and (previous['entry_digest'] != record['entry_digest'] or
                         previous.get('record_digest') != sync.digest(sync.canonical_json(record))):
            raise ValueError('stale source review; review current backing first: ' + ref)
        if ref not in added and current != desired:
            if current != base and desired != base:
                raise ValueError('concurrent reviewed-card conflict: ' + ref)
            if desired == base:
                continue  # Unchanged Git must not overwrite a newer source review.
        if current == desired:
            continue
        decisions[ref] = {**(previous or {}), 'material_ref': ref,
            'entry_digest': record['entry_digest'],
            'record_digest': sync.digest(sync.canonical_json(record)),
            'classification': 'external', 'reason': 'Accepted Git card; original read scope retained.',
            'mixed_sources': False, 'lifecycle': record['lifecycle_state'],
            'reviewed_fields': list(desired), 'review_ref': evidence, 'public_card': desired}
        if ref != card['material_ref']:
            decisions[ref]['public_material_ref'] = card['material_ref']
        if ref not in added:
            updated.append(ref)
    intake['item_count'] = len(records)
    intake['native_content_backing_count'] = sum(r['source_id'] == 'managed-native' for r in records.values())
    intake['lifecycle_counts'] = dict(sorted(Counter(r['lifecycle_state'] for r in records.values()).items()))
    ranked = copy.deepcopy(intake)
    entries = ranked['rankings']['ranked_entries']['entries']
    if any(len(e['material_refs']) != 1 for e in entries):
        raise ValueError('source sync requires independently ranked materials')
    byref = {e['material_refs'][0]: e for e in entries}
    if len(byref) != len(entries):
        raise ValueError('duplicate ranked identity')
    desired_order = [ref for ref, card in sorted(cards.items(), key=lambda x: x[1]['queue_rank'] or 10**9)
                     if card['queue_rank'] is not None and ref not in archived]
    for ref in desired_order:
        if ref not in byref:
            card = cards[ref]
            byref[ref] = {'entry_ref': 'git-queue-' + ref, 'source_entry_ref': evidence,
                'material_refs': [ref], 'labels': records[ref]['legacy_labels'], 'title': card['title'],
                'reading_stage': card['tier'] + ' / accepted Git order', 'reading_action': card['note'],
                'ranking_judgment': 'Preserve accepted remote order during sync; no new scoring.',
                'reading_url': card['sources'][0], 'evidence_refs': [evidence]}
    old_order = [e['material_refs'][0] for e in entries]
    for ref in updated:
        if ref in byref:
            entry, card = byref[ref], cards[ref]
            entry.setdefault('prior_public_context', []).append({
                'title': entry.get('title'), 'reading_action': entry.get('reading_action'),
                'superseded_by': evidence})
            entry['title'] = card['title']
            old_action = entry.get('reading_action', '')
            if card['note'] and card['note'] not in old_action:
                entry['reading_action'] = (old_action + '\n\n最新来源补充：' + card['note']).strip()
    order = merge_ranked_orders(old_order, desired_order)
    merged = [byref[ref] for ref in order]
    external = {ref for ref, d in decisions.items() if d['classification'] == 'external'}
    public_rank = 0
    for rank, entry in enumerate(merged, 1):
        entry['rank'] = rank
        if 'target_rank' in entry:
            entry['target_rank'] = rank
        if entry['material_refs'][0] in external:
            public_rank += 1
            entry['public_queue_rank'] = public_rank
    ranking = ranked['rankings']['ranked_entries']
    window = ranking.get('constraints', {}).get('top_window_size', 30)
    ranking['entries'] = merged
    ranking['plan_ref'] = evidence
    summary = ranking.setdefault('summary', {})
    summary.update(source_entry_count=len(merged), rebuilt_entry_count=len(merged),
                   material_ref_count=len(merged), top_window_size=window,
                   top_window_entry_count=min(window, len(merged)),
                   ranked_backlog_entry_count=max(0, len(merged)-window),
                   public_ranked_count=public_rank, private_ranked_count=len(merged)-public_rank)
    ranked['rankings']['top30']['slots'] = copy.deepcopy(merged[:window])
    ranked['rankings']['ranked_backlog']['entries'] = copy.deepcopy(merged[window:])
    result_reviews = copy.deepcopy(reviews)
    result_reviews['records'] = sorted(decisions.values(), key=lambda d: records[d['material_ref']]['sequence'])
    return intake, ranked, result_reviews, content, {
        'added': added, 'updated': updated, 'archived_skipped': archived,
        'records_before': len(catalog['records']), 'records_after': len(records),
        'ranked_before': len(old_order), 'ranked_after': len(order),
        'settlements': {ref: ('top_window' if order.index(ref) < window else 'ranked_backlog')
                        if ref in order else 'no_change' for ref in added},
        'no_change_reasons': {ref: 'Accepted remote card is unranked; sync does not invent a new priority.'
                              for ref in added if ref not in order}}


def prepare(source, base_ref, public_ref):
    if not base_ref or base_ref.startswith('-') or public_ref.startswith('-'):
        raise ValueError('reconciliation requires the pre-sync base commit')
    repo = source.repo
    base_commit = git(repo, 'rev-parse', '--verify', base_ref+'^{commit}').decode().strip()
    commit = git(repo, 'rev-parse', '--verify', public_ref+'^{commit}').decode().strip()
    public = git_catalog(repo, commit, 'Learning-Materials/catalog.json')
    baseline = git_catalog(repo, base_commit, 'Learning-Materials/catalog.json')
    if sync.load(repo/'Learning-Materials/catalog.json') != public:
        raise ValueError('working public catalog differs from accepted commit; reconcile local edits first')
    before = source.current_pointer()['authority_revision']
    catalog = source.load_catalog(before)
    source.load_material_content(catalog)
    reviews_bytes = source.reviews.read_bytes()
    intake, ranked, reviews, contents, audit = build(catalog, json.loads(reviews_bytes), baseline, public, commit)
    binding = {'action': 'reconciliation_prepare', 'before': before, 'public_commit': commit,
               'reviews_digest': sync.digest(reviews_bytes)}
    source.authorize_operation('reconciliation_prepare', binding)
    source.stage_contents(contents)
    source.load_material_content(ranked)
    intake_rev = source.stage_catalog(intake, action='reconciliation_prepare')
    after = source.stage_catalog(ranked, action='reconciliation_prepare')
    # Store exact rollback bytes and inputs, then bind all of them by digest.
    plan = {'schema_version': 'source_git_reconciliation_v1', 'store_id': source.store_id,
            'project_scope': source.cfg['project_scope'], 'before': before, 'intake': intake_rev,
            'after': after, 'base_commit': base_commit, 'public_commit': commit,
            'working_digest': sync.current_digest(repo/'Learning-Materials/catalog.json'),
            'reviews_before': reviews_bytes.decode(), 'reviews_after': reviews, 'audit': audit}
    path = source.root/'reconciliation-plans'/('plan-'+sync.digest(sync.canonical_json(plan))+'.json')
    sync.write_immutable(path, sync.canonical_json(plan))
    return {'status': 'prepared', 'plan_file': str(path), **audit}


def apply(source, path):
    path = path.resolve()
    if not path.is_relative_to((source.root/'reconciliation-plans').resolve()):
        raise ValueError('reconciliation plan outside registered source')
    plan = sync.load(path)
    if (path.stem != 'plan-'+sync.digest(sync.canonical_json(plan)) or
            plan['store_id'] != source.store_id or plan['project_scope'] != source.cfg['project_scope']):
        raise ValueError('reconciliation plan identity mismatch')
    before, intake, after = (plan[k] for k in ('before', 'intake', 'after'))
    if (source.current_pointer()['authority_revision'] != before or
            source.reviews.read_bytes() != plan['reviews_before'].encode() or
            sync.current_digest(source.repo/'Learning-Materials/catalog.json') != plan['working_digest']):
        raise ValueError('reconciliation CAS conflict: source, reviews or public catalog changed')
    rebuilt = build(source.load_catalog(before), json.loads(plan['reviews_before']),
                    git_catalog(source.repo, plan['base_commit'], 'Learning-Materials/catalog.json'),
                    git_catalog(source.repo, plan['public_commit'], 'Learning-Materials/catalog.json'),
                    plan['public_commit'])
    if (rebuilt[0] != source.load_catalog(intake) or rebuilt[1] != source.load_catalog(after)
            or rebuilt[2] != plan['reviews_after'] or rebuilt[4] != plan['audit']):
        raise ValueError('reconciliation preview changed')
    source.load_material_content(rebuilt[1])
    transitions = [[before, intake], [intake, after]]
    gate = source.issue_gate({'action': 'reconciliation_apply', 'plan_digest': sync.digest(path.read_bytes()),
                              'transitions': transitions})
    attempt = path.stem+'-'+uuid.uuid4().hex
    receipt_path = source.root/'operations'/('reconciliation-'+attempt+'.json')
    receipt = {'status': 'prepared', 'plan_file': str(path), 'owner_gate_ref': gate,
               'before': before, 'intake': intake, 'after': after, **plan['audit']}
    outputs = source.reconciliation_outputs()
    backups = {p: p.read_bytes() if p.exists() else None for p in outputs}
    backup_dir = source.root/'reconciliation-backups'/attempt
    manifest = []
    for index, (p, payload) in enumerate(backups.items()):
        name = str(index)+'.bak'
        if payload is not None:
            sync.write_immutable(backup_dir/name, payload)
        manifest.append({'path': str(p), 'file': name if payload is not None else None,
                         'digest': sync.digest(payload) if payload is not None else None})
    sync.write_immutable(backup_dir/'manifest.json', sync.canonical_json(manifest))
    receipt['backup_ref'] = str(backup_dir)
    sync.atomic_write(receipt_path, sync.canonical_json(receipt))
    current = before
    try:
        for expected, target in transitions:
            if expected != target:
                source.switch_authority(store_id=source.store_id, expected_revision=expected,
                    target_revision=target, owner_gate_ref=gate, observed_at=source.now())
                current = target
            sync.write_immutable(source.root/'operations'/(attempt+'-'+target+'.json'),
                                 sync.canonical_json({'before': expected, 'after': target,
                                                      'owner_gate_ref': gate, 'readback_verified': True}))
        source.authorize(gate)
        sync.atomic_write(source.reviews, sync.canonical_json(plan['reviews_after']))
        source.publish()
        source.refresh_full_view()
        if source.current_pointer()['authority_revision'] != after:
            raise ValueError('reconciliation authority readback failed')
        receipt.update(status='applied', readback_verified=True, rollback_ref=before)
        sync.atomic_write(receipt_path, sync.canonical_json(receipt))
        return {**receipt, 'receipt_file': str(receipt_path)}
    except Exception:
        # Reverse only our exact transitions; a concurrent writer fails CAS.
        current = source.current_pointer()['authority_revision']
        if current not in {before, intake, after}:
            raise RuntimeError('reconciliation recovery requires review: concurrent source revision') from None
        for expected, target in reversed(transitions):
            if current == target and target != expected:
                source.switch_authority(store_id=source.store_id, expected_revision=target,
                    target_revision=expected, owner_gate_ref=gate, observed_at=source.now())
                current = expected
        source.authorize(gate)
        for p, payload in backups.items():
            if payload is None:
                p.unlink(missing_ok=True)
            else:
                sync.atomic_write(p, payload)
        receipt.update(status='rolled_back', readback_verified=False)
        sync.atomic_write(receipt_path, sync.canonical_json(receipt))
        raise
