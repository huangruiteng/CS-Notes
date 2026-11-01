"""Provider-injected lifecycle settlement; no identity or source configuration.

The source supplies authorization, immutable catalogs, backing validation and
CAS. The injected API supplies serialization, inventory/receipt helpers and
QueuePublisher. Evidence packets are private inputs, never publication data.
"""
import copy
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

TRANSITIONS = {('candidate', 'archived'), ('active', 'archived'),
               ('candidate', 'active'), ('archived', 'candidate'), ('archived', 'active')}


def validate_decisions(plan, evidence):
    """A catalog omission or assistant reading claim is never completion."""
    packet = json.loads(evidence)
    if not isinstance(packet, dict) or packet.get('schema_version') != 'material_lifecycle_decisions_v1':
        raise ValueError('per-material lifecycle decisions required; queue omission is not completion')
    decisions = packet.get('decisions', [])
    if not isinstance(decisions, list) or not all(
            isinstance(d, dict) and isinstance(d.get('material_ref'), str) for d in decisions):
        raise ValueError('invalid per-material lifecycle decisions')
    byref = {d['material_ref']: d for d in decisions}
    if len(byref) != len(decisions) or set(byref) != {x['material_ref'] for x in plan['transitions']}:
        raise ValueError('lifecycle evidence must cover exactly the selected materials')
    for change in plan['transitions']:
        decision = byref[change['material_ref']]
        if not all(isinstance(decision.get(k), str) and decision[k].strip()
                   for k in ('source_ref', 'statement')):
            raise ValueError('lifecycle decision needs an attributable statement and source')
        states = change['from_state'], change['to_state']
        if states not in TRANSITIONS:
            raise ValueError('unsupported completion transition')
        if states[1] == 'archived' or states == ('candidate', 'active'):
            expected = 'user_completed' if states[1] == 'archived' else 'user_keep_read_reference'
            if decision.get('action') != expected or decision.get('actor') != 'human_user':
                raise ValueError('assistant read_scope, note publication and remote omission cannot prove user completion')
            if decision.get('kind') not in {'user_statement', 'verified_remote_user_statement'}:
                raise ValueError('explicit human completion evidence required')
            if decision['kind'] == 'verified_remote_user_statement' and not (
                    decision.get('user_message_ref') and decision.get('remote_commit')):
                raise ValueError('remote completion needs the original human message and commit')
        elif states[0] == 'archived' and states[1] in {'candidate', 'active'}:
            if decision.get('action') != 'correct_false_archive' or decision.get('actor') not in {'human_user', 'source_audit'}:
                raise ValueError('archive correction evidence required')
            if not decision.get('archive_ref') or not decision.get('invalid_completion_evidence_ref'):
                raise ValueError('correction must identify the erroneous archive and evidence')
        else:
            raise ValueError('unsupported completion transition')
    return byref


def preview(source, input_path, api, *, historical_rollback=False):
    source.context()
    plan = api.load(input_path)
    if (plan.get('schema_version') != 'project_material_completion_v1'
            or plan.get('store_id') != source.store_id
            or plan.get('project_scope') != source.cfg['project_scope']):
        raise ValueError('completion belongs to another source scope')
    before = plan['authority_revision']
    original = source.load_catalog(before)
    source.load_material_content(original)
    evidence = Path(plan['evidence_file']).read_bytes()
    if not evidence or api.sha(evidence) != plan['evidence_digest']:
        raise ValueError('completion evidence digest mismatch')
    decisions = ({} if historical_rollback and json.loads(evidence).get('schema_version')
                 != 'material_lifecycle_decisions_v1' else validate_decisions(plan, evidence))
    evidence_ref = 'completion:' + api.sha(evidence)
    api.sync.write_immutable(source.root/'completion-evidence'/f'{api.sha(evidence)}.json', evidence)
    changes = {x['material_ref']: x for x in plan['transitions']}
    if not changes or len(changes) != len(plan['transitions']):
        raise ValueError('empty or duplicate completion identity')
    catalog = copy.deepcopy(original)
    known = {r['stable_id'] for r in original['records']}
    if not set(changes) <= known:
        raise ValueError('unknown completion material')
    archived = set()
    reactivated = set()
    for record in catalog['records']:
        ref = record['stable_id']
        if ref not in changes:
            continue
        change = changes[ref]
        if (api.sha(api.data(record)) != change['record_digest']
                or record['lifecycle_state'] != change['from_state']):
            raise ValueError('completion record digest/state mismatch')
        if (change['from_state'], change['to_state']) not in TRANSITIONS:
            raise ValueError('unsupported completion transition')
        if change['to_state'] == 'archived':
            archive = {'record': copy.deepcopy(record), 'evidence_ref': evidence_ref,
                       'ranked_entries': [copy.deepcopy(e) for e in original['rankings']['ranked_entries']['entries']
                                          if ref in e['material_refs']]}
            archive_ref = 'archive:' + api.sha(api.data(archive))
            api.immutable(source.root/'archives'/f'{archive_ref}.json', archive)
            record['archive_ref'] = archive_ref
            archived.add(ref)
        if change['from_state'] == 'archived':
            decision = decisions[ref]
            previous = api.load(source.root/'archives'/f"{record['archive_ref']}.json")
            if (decision['archive_ref'] != record['archive_ref']
                    or decision['invalid_completion_evidence_ref'] != record['completion_evidence_ref']
                    or previous['evidence_ref'] != record['completion_evidence_ref']
                    or previous['record']['stable_id'] != ref
                    or previous['record']['lifecycle_state'] != change['to_state']
                    or previous['record']['content_digest'] != record['content_digest']):
                raise ValueError('archive correction must restore its exact original lifecycle and backing')
            record['archive_correction_evidence_ref'] = evidence_ref
            reactivated.add(ref)
        record['lifecycle_state'] = change['to_state']
        if ref not in reactivated:
            record['completion_evidence_ref'] = evidence_ref
    ranked = api.ranked_refs(original)
    if len(set(ranked)) != len(ranked) or not set(ranked) <= known:
        raise ValueError('invalid source ranked membership')
    remaining = [ref for ref in ranked if ref not in archived]
    # Give restored ranked intakes provisional backlog membership. Their final
    # position is settled separately through the existing ranking owner.
    remaining += [ref for ref in changes if ref in reactivated and ref not in remaining]
    # Lifecycle settlement must not rebuild ranked entries from IDs: their
    # titles, reading actions, stable entry IDs and evidence are durable data.
    entries = copy.deepcopy(original['rankings']['ranked_entries']['entries'])
    if any(len(e['material_refs']) != 1 for e in entries):
        raise ValueError('completion requires independently ranked single materials')
    byref = {e['material_refs'][0]: e for e in entries}
    for ref in reactivated:
        record = next(r for r in catalog['records'] if r['stable_id'] == ref)
        archive = api.load(source.root/'archives'/f"{record['archive_ref']}.json")
        saved = archive.get('ranked_entries', [])
        if saved:
            byref[ref] = copy.deepcopy(saved[0])
        else:
            byref[ref] = {'material_refs': [ref]}
    entries = [byref[ref] for ref in remaining]
    for rank, entry in enumerate(entries, 1):
        entry['rank'] = rank
        if 'target_rank' in entry:
            entry['target_rank'] = rank
    public_rank = 0
    for entry in entries:
        if 'public_queue_rank' in entry:
            public_rank += 1
            entry['public_queue_rank'] = public_rank
    ranking = catalog['rankings']['ranked_entries']
    ranking['entries'] = entries
    if 'lifecycle_settlement_ref' in ranking:
        ranking['lifecycle_settlement_ref'] = evidence_ref
    if 'previous_authority_revision' in ranking:
        ranking['previous_authority_revision'] = before
    window = ranking.get('constraints', {}).get('top_window_size', 30)
    if 'summary' in ranking:
        summary = ranking['summary']
        counts = {'material_ref_count': len(remaining), 'rebuilt_entry_count': len(entries),
                  'source_entry_count': len(entries), 'top_window_entry_count': min(window, len(entries)),
                  'ranked_backlog_entry_count': max(0, len(entries)-window),
                  'public_ranked_count': public_rank, 'private_ranked_count': len(entries)-public_rank}
        summary.update({k: v for k, v in counts.items() if k in summary})
    if 'top30' in catalog['rankings']:
        catalog['rankings']['top30']['slots'] = copy.deepcopy(entries[:window])
    if 'ranked_backlog' in catalog['rankings']:
        catalog['rankings']['ranked_backlog']['entries'] = copy.deepcopy(entries[window:])
    if 'lifecycle_counts' in catalog:
        catalog['lifecycle_counts'] = dict(sorted(Counter(r['lifecycle_state'] for r in catalog['records']).items()))
    # Exact IDs, content, untouched records and every remaining relative order.
    if [r['stable_id'] for r in catalog['records']] != [r['stable_id'] for r in original['records']]:
        raise ValueError('lifecycle transition changed source membership')
    for old, new in zip(original['records'], catalog['records']):
        if old['stable_id'] not in changes:
            if old != new:
                raise ValueError('lifecycle transition changed an unrelated record')
        else:
            lifecycle_fields = {'lifecycle_state', 'archive_ref', 'completion_evidence_ref',
                                'archive_correction_evidence_ref'}
            if any(old[k] != new[k] for k in old if k not in lifecycle_fields):
                raise ValueError('lifecycle transition changed source content or identity')
    source.load_material_content(catalog)
    after = source.stage_catalog(catalog)
    if source.load_catalog(before) != original:
        raise ValueError('lifecycle rollback snapshot changed')
    inventory = api.build_material_store_inventory(project_scope=source.scope,
        store_id=source.store_id, store_revision=before, observed_at=api.now(),
        source_snapshot_ref='snapshot:'+before, backup_ref='backup:'+before,
        source_digest='sha256:'+api.sha(api.data(original)),
        lifecycle_counts={state:sum(r['lifecycle_state']==state for r in original['records'])
                          for state in ('candidate','unread','active','archived','carryover')},
        stable_ids_verified=True, backup_verified=True)
    return {'schema_version':'source_completion_preview_v1',
        'plan_digest':api.sha(api.data(plan)), 'before_revision':before, 'after_revision':after,
        'evidence_ref':evidence_ref, 'changed_refs':list(changes), 'archived_refs':sorted(archived),
        'reactivated_refs':sorted(reactivated),
        'canonical_count':len(catalog['records']), 'before_ranked':len(ranked),
        'after_ranked':len(remaining), 'inventory':inventory,
        'lossless_verified':True, 'rollback_rehearsed':True}


def settle(source, input_path, phase, api):
    packet = preview(source, input_path, api, historical_rollback=phase == 'rollback')
    before, after = packet['before_revision'], packet['after_revision']
    if phase == 'prepare':
        if source.current_pointer()['authority_revision'] != before:
            raise ValueError('completion authority CAS conflict')
        return packet
    if phase not in {'apply','rollback'}:
        raise ValueError('completion requires prepare/apply/rollback')
    restore = phase == 'rollback'
    expected, target = (after, before) if restore else (before, after)
    gate = source.issue_gate({'action':'completion_rollback' if restore else 'completion_apply',
        'plan_digest':packet['plan_digest'], 'before':expected, 'after':target})
    attempt = api.uuid.uuid4().hex
    journal = source.root/'operations'/f'completion-pending-{attempt}.json'
    receipt = {**packet, 'project_scope':source.cfg['project_scope'], 'store_id':source.store_id,
        'owner_gate_ref':gate, 'expected_revision':expected, 'target_revision':target, 'status':'prepared'}
    api.write(journal, receipt)
    switched = False
    try:
        transition = source.switch_authority(store_id=source.store_id, expected_revision=expected,
            target_revision=target, owner_gate_ref=gate, observed_at=api.now())
        switched = True
        publisher = api.sync.QueuePublisher(source)
        publication = publisher.prepare()
        source.authorize(gate)
        publisher.apply()
        publisher.check()
        source.authorize(gate)
        if source.current_pointer()['authority_revision'] != target:
            raise ValueError('completion authority readback mismatch')
        receipt.update(status='rolled_back' if restore else 'applied', readback_verified=True,
            transition=asdict(transition), publication=publication,
            rollback_ref='rollback:'+expected, rollback_ready=True)
        receipt_file=source.root/'operations'/f'completion-receipt-{attempt}.json'
        api.immutable(receipt_file, receipt)
        api.write(journal, receipt)
        return {**receipt, 'receipt_file':str(receipt_file)}
    except Exception as error:
        if switched:
            source.switch_authority(store_id=source.store_id, expected_revision=target,
                target_revision=expected, owner_gate_ref=gate, observed_at=api.now())
            source.publish()
        receipt.update(status='rolled_back' if switched else 'rejected', error=str(error))
        api.write(journal, receipt)
        raise
