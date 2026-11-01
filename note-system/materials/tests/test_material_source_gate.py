"""Source activation and operation gates; no real host metadata or private data."""
import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from material_source_gate import NativeSourceGate
from material_source import load_source


class SourceGateTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name).resolve()
        self.root = self.repo/'.local/material-lifecycle'; self.root.mkdir(parents=True)
        self.profile = self.root/'source-profile.json'
        self.host = {'host_surface':'codex-app', 'turn_id':'turn-one', 'thread_id':'thread-one',
                     'write_policy':'workspace-write', 'workspace_digest':'fixture-digest'}
        self.project = {'project_ref':'project-one', 'workspace_path':str(self.repo),
                        'grant':'workspace_write', 'audience':'local_owner'}
        self.cfg = {'schema_version':'native_material_source_profile_v1', 'enabled':True,
                    'owner_uid':os.getuid(), 'audience':'local_owner', 'accepted_request_ref':'user:setup',
                    'workspace':str(self.repo), 'source_root':str(self.root), 'store_id':'store-one',
                    'project_scope':{'project_ref':'project-one','source_profile_ref':'profile-one',
                                     'workspace_grant_ref':'grant-one'},
                    'allowed_operations':['completion_apply']}
        self.time = datetime(2026,1,1,tzinfo=timezone.utc)
        self.write_profile()
        self.guard = NativeSourceGate(self.profile,
            resolve_host=lambda path:copy.deepcopy(self.host),
            resolve_project=lambda path,host:copy.deepcopy(self.project), clock=lambda:self.time)
        self.intent = {'action':'completion_apply','before':'v1','after':'v2'}

    def write_profile(self):
        self.profile.write_text(json.dumps(self.cfg))

    def test_native_owner_can_apply_without_goal_or_bot_identity(self):
        ref = self.guard.issue(self.intent)
        gate = self.guard.authorize(ref, intent=self.intent)
        self.assertEqual(gate['host'], self.host)
        self.assertNotIn('goal_id', gate)
        self.assertNotIn('session_created', gate)

    def test_another_turn_and_thread_cannot_replay_gate(self):
        ref = self.guard.issue(self.intent)
        for key in ['turn_id','thread_id']:
            old=self.host[key];self.host[key]='another'
            with self.assertRaisesRegex(ValueError,'caller, Turn'): self.guard.authorize(ref)
            self.host[key]=old

    def test_profile_revocation_and_core_read_only_are_enforced_live(self):
        ref = self.guard.issue(self.intent)
        self.cfg['revoked']=True;self.write_profile()
        with self.assertRaisesRegex(ValueError,'inactive'):self.guard.authorize(ref)
        self.cfg.pop('revoked');self.write_profile();self.project['grant']='workspace_read'
        with self.assertRaisesRegex(ValueError,'Core project'):self.guard.authorize(ref)

    def test_expiry_operation_and_profile_rebinding_rejected(self):
        ref = self.guard.issue(self.intent)
        with self.assertRaisesRegex(ValueError,'this operation'):
            self.guard.authorize(ref,intent={**self.intent,'after':'v3'})
        self.time += timedelta(minutes=16)
        with self.assertRaisesRegex(ValueError,'expired'):self.guard.authorize(ref)
        self.time -= timedelta(minutes=16)
        self.cfg['store_id']='another';self.write_profile()
        with self.assertRaisesRegex(ValueError,'source profile changed'):self.guard.authorize(ref)

    def test_missing_or_unapproved_source_does_not_fall_back_to_goal(self):
        with self.assertRaisesRegex(ValueError,'material_source_not_configured'):load_source(self.repo)
        self.cfg['enabled']=False;self.write_profile()
        with self.assertRaisesRegex(ValueError,'inactive'):self.guard.issue(self.intent)
        self.assertFalse((self.root/'owner-gates').exists())

    def test_gate_tampering_and_path_traversal_rejected(self):
        ref=self.guard.issue(self.intent)
        path=self.root/'owner-gates'/f'{ref}.json'
        path.chmod(0o600)  # Deliberate corruption of this disposable fixture.
        path.write_text(path.read_text().replace('v2','v3'))
        with self.assertRaisesRegex(ValueError,'integrity'):self.guard.authorize(ref)
        with self.assertRaisesRegex(ValueError,'reference'):self.guard.authorize('../outside')


if __name__ == '__main__': unittest.main()
