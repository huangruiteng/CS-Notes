"""Native-source synchronization keeps backing, completion and rollback intact."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import material_source_reconcile as reconcile
import material_queue_sync as sync
from test_material_reconcile import catalog


def fixture():
    public = catalog('one', 'two')
    records = [{'stable_id': 'material-'+name, 'source_id': 'managed-native',
                'entry_digest': name, 'legacy_labels': ['U'+str(i)],
                'lifecycle_state': 'candidate', 'sequence': i, 'opaque': 'preserve'}
               for i, name in enumerate(['one', 'private', 'two'])]
    entries = [{'rank': i+1, 'material_refs': [r['stable_id']], 'labels': r['legacy_labels'],
                'title': r['stable_id'], 'reading_action': 'old annotation', 'extra': {'keep': True}}
               for i, r in enumerate(records)]
    source = {'records': records, 'rankings': {'ranked_entries': {'entries': entries},
              'top30': {'slots': entries}, 'ranked_backlog': {'entries': []}}}
    decisions = []
    for r in records:
        d = {'material_ref': r['stable_id'], 'entry_digest': r['entry_digest'],
             'record_digest': sync.digest(sync.canonical_json(r)),
             'classification': 'private' if r['stable_id']=='material-private' else 'external'}
        cards = [c for c in public['entries'] if c['material_ref']==r['stable_id']]
        if cards:
            d['public_card'] = reconcile.metadata(cards[0])
        decisions.append(d)
    return source, {'records': decisions}, public


class BuildTests(unittest.TestCase):
    def native_fixture(self):
        source, reviews, base = fixture()
        source['rankings'].pop('top30')
        source['rankings'].pop('ranked_backlog')
        for record in source['records']:
            for field in ('source_id', 'legacy_labels', 'sequence'):
                record.pop(field)
            record.update(title=record['stable_id'], sources=['https://example.org/source'],
                          source_revision='native-revision', read_scope='recorded_review',
                          tier='A', note='Native source record')
        byref = {r['stable_id']: r for r in source['records']}
        for review in reviews['records']:
            review['record_digest'] = sync.digest(sync.canonical_json(byref[review['material_ref']]))
        return source, reviews, base

    def test_native_records_need_no_legacy_identity_or_counter_fields(self):
        source, reviews, base = self.native_fixture()
        before = copy.deepcopy(source)
        intake, ranked, _, content, audit = reconcile.build(source, reviews, base, base, 'abc')
        self.assertEqual(intake, before)
        self.assertEqual(ranked['records'], before['records'])
        self.assertEqual(set(ranked['rankings']), set(before['rankings']))
        self.assertEqual(content, {})
        self.assertEqual(audit['added'], [])
        self.assertEqual([e['material_refs'] for e in ranked['rankings']['ranked_entries']['entries']],
                         [e['material_refs'] for e in before['rankings']['ranked_entries']['entries']])

    def test_new_native_card_has_readable_body_and_complete_native_metadata(self):
        source, reviews, base = self.native_fixture()
        intake, ranked, after_reviews, content, audit = reconcile.build(
            source, reviews, base, catalog('two', 'new', 'one'), 'abc')
        self.assertEqual(intake['records'][:-1], source['records'])
        record = intake['records'][-1]
        self.assertEqual(record['title'], 'new')
        self.assertEqual(record['source_revision'], 'abc')
        self.assertNotIn('legacy_labels', record)
        self.assertNotIn('source_id', record)
        payload = content[record['content_digest'].removeprefix('sha256:')]
        self.assertEqual(record['content_size_bytes'], len(payload))
        self.assertEqual(record['entry_digest'], record['content_digest'])
        self.assertIn('未在本次同步重读原文', json.loads(payload)['source_status_override'])
        decision = next(r for r in after_reviews['records'] if r['material_ref'] == 'material-new')
        self.assertEqual(decision['record_digest'], sync.digest(sync.canonical_json(record)))
        self.assertEqual(audit['settlements'], {'material-new': 'top_window'})

    def test_addition_retains_backing_annotations_and_both_orders(self):
        source, reviews, base = fixture()
        original = copy.deepcopy((source, reviews, base))
        incoming = catalog('two', 'new', 'one')
        intake, ranked, after_reviews, content, audit = reconcile.build(source, reviews, base, incoming, 'abc')
        self.assertEqual((source, reviews, base), original)
        self.assertEqual(intake['records'][:3], source['records'])
        self.assertEqual(intake['rankings'], source['rankings'])
        refs = [e['material_refs'][0] for e in ranked['rankings']['ranked_entries']['entries']]
        self.assertEqual([r for r in refs if r!='material-private'], ['material-two','material-new','material-one'])
        self.assertEqual(audit['settlements'], {'material-new':'top_window'})
        for entry in ranked['rankings']['ranked_entries']['entries']:
            if entry['material_refs'][0]!='material-new':
                self.assertEqual(entry['reading_action'], 'old annotation')
                self.assertEqual(entry['extra'], {'keep':True})
        self.assertEqual(len(content), 1)
        body = json.loads(next(iter(content.values())))
        self.assertIn('未在本次同步重读原文', body['source_status_override'])
        card = next(d['public_card'] for d in after_reviews['records'] if d['material_ref']=='material-new')
        self.assertEqual(card['read_scope'], 'recorded_review')

    def test_absence_cannot_delete_or_archive_and_stale_card_cannot_resurrect(self):
        source, reviews, base = fixture()
        source['records'][2]['lifecycle_state']='archived'
        source['records'][2]['completion_evidence_ref']='human-message'
        source['rankings']['ranked_entries']['entries'].pop()
        _, ranked, _, _, audit = reconcile.build(source, reviews, base, catalog('two'), 'abc')
        self.assertEqual(ranked['records'], source['records'])
        self.assertEqual(audit['archived_skipped'], ['material-two'])
        self.assertEqual([e['material_refs'][0] for e in ranked['rankings']['ranked_entries']['entries']],
                         ['material-one','material-private'])

    def test_local_field_edit_survives_unchanged_git_but_conflicts_are_rejected(self):
        source, reviews, base = fixture()
        reviews['records'][0]['public_card']['note']='local newer evidence'
        result = reconcile.build(source, reviews, base, base, 'abc')
        self.assertEqual(result[2]['records'][0]['public_card']['note'], 'local newer evidence')
        incoming = copy.deepcopy(base)
        incoming['entries'][0]['note']='different remote evidence'
        with self.assertRaisesRegex(ValueError, 'conflict'):
            reconcile.build(source,reviews,base,incoming,'abc')
        incoming['entries'][0]['lifecycle']='active'
        with self.assertRaisesRegex(ValueError, 'lifecycle'):
            reconcile.build(source,reviews,base,incoming,'abc')

    def test_updated_card_updates_full_view_without_erasing_old_guidance(self):
        source, reviews, base = fixture()
        incoming = copy.deepcopy(base)
        incoming['entries'][0].update(title='new title',note='new evidence')
        result = reconcile.build(source,reviews,base,incoming,'abc')
        entry = result[1]['rankings']['ranked_entries']['entries'][0]
        self.assertEqual(entry['title'],'new title')
        self.assertIn('old annotation',entry['reading_action'])
        self.assertIn('new evidence',entry['reading_action'])
        self.assertEqual(entry['prior_public_context'][0]['title'],'material-one')
        self.assertEqual(result[1]['records'],source['records'])


class FakeSource:
    def __init__(self, root):
        self.repo = root
        self.root = root/'private'
        self.root.mkdir()
        self.cfg = {'project_scope': {'fixture':True}}
        self.store_id = 'fixture'
        self.reviews = self.root/'reviews.json'
        self.output = root/'Learning-Materials/QUEUE.md'
        self.output.write_text('original queue')
        source, reviews, base = fixture()
        self.catalogs = {}
        self.current = self.stage_catalog(source)
        sync.atomic_write(self.reviews,sync.canonical_json(reviews))
        self.fail = False
        self.deny = False
        self.now = lambda:'fixture'
    def current_pointer(self): return {'authority_revision':self.current}
    def load_catalog(self, revision): return self.catalogs[revision]
    def load_material_content(self, catalog): pass
    def stage_catalog(self, catalog, **kwargs):
        revision = sync.digest(sync.canonical_json(catalog))
        self.catalogs[revision] = copy.deepcopy(catalog)
        return revision
    def authorize_operation(self, *args):
        if self.deny: raise ValueError('denied')
    def stage_contents(self, *args): self.authorize_operation()
    def issue_gate(self, intent):
        self.authorize_operation()
        self.intent = intent
        return 'gate'
    def authorize(self, gate): self.authorize_operation()
    def switch_authority(self, **kwargs):
        self.authorize_operation()
        if self.current != kwargs['expected_revision']: raise ValueError('CAS')
        self.current=kwargs['target_revision']
    def publish(self): self.output.write_text('published queue')
    def refresh_full_view(self):
        if self.fail: raise RuntimeError('view failed')
    def reconciliation_outputs(self): return [self.output,self.reviews]


class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        def git(*args):
            return subprocess.check_output(['git','-C',str(self.root),*args],stderr=subprocess.PIPE)
        self.git=git
        git('init','-q');git('config','user.name','Fixture');git('config','user.email','fixture@example.org')
        p=self.root/'Learning-Materials/catalog.json';p.parent.mkdir()
        p.write_text(json.dumps(catalog('one','two')))
        git('add','.');git('commit','-qm','base')
        self.base=git('rev-parse','HEAD').decode().strip()
        p.write_text(json.dumps(catalog('one','new','two')))
        git('add','.');git('commit','-qm','incoming')
        self.source=FakeSource(self.root)
        self.before=self.source.current
        self.plan=Path(reconcile.prepare(self.source,self.base,'HEAD')['plan_file'])

    def test_success_and_stale_plan(self):
        result=reconcile.apply(self.source,self.plan)
        self.assertEqual(result['status'],'applied')
        self.assertNotEqual(result['intake'],result['after'])
        self.assertEqual(self.source.current,result['after'])
        with self.assertRaisesRegex(ValueError,'CAS'):
            reconcile.apply(self.source,self.plan)

    def test_failure_after_publication_restores_source_reviews_and_outputs(self):
        old_reviews=self.source.reviews.read_bytes()
        self.source.fail=True
        with self.assertRaisesRegex(RuntimeError,'view failed'):
            reconcile.apply(self.source,self.plan)
        self.assertEqual(self.source.current,self.before)
        self.assertEqual(self.source.reviews.read_bytes(),old_reviews)
        self.assertEqual(self.source.output.read_text(),'original queue')
        self.source.fail=False
        self.assertEqual(reconcile.apply(self.source,self.plan)['status'],'applied')

    def test_revocation_rejects_before_source_write(self):
        self.source.deny=True
        with self.assertRaisesRegex(ValueError,'denied'):
            reconcile.apply(self.source,self.plan)
        self.assertEqual(self.source.current,self.before)

    def test_prepare_rejects_uncommitted_public_additions_instead_of_losing_them(self):
        (self.root/'Learning-Materials/catalog.json').write_text(json.dumps(catalog('one','local','two')))
        with self.assertRaisesRegex(ValueError,'working public catalog differs'):
            reconcile.prepare(self.source,self.base,'HEAD')
        self.assertEqual(self.source.current,self.before)
        self.source.deny=False
        (self.root/'Learning-Materials/catalog.json').write_text('changed concurrently')
        with self.assertRaisesRegex(ValueError,'CAS'):
            reconcile.apply(self.source,self.plan)
        self.assertEqual(self.source.current,self.before)


if __name__=='__main__': unittest.main()
