"""Bind source-owned operations to an existing native host write grant.

The profile is explicit owner setup, not permission inferred from a catalog.
The host reader supplies the live caller/Turn; a Core resolver supplied by the
adapter maps that verified grant to project context without creating a Session.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from material_host_context import resolve_native_owner_turn
from material_queue_sync import canonical_json, digest, write_immutable


class NativeSourceGate:
    def __init__(self, profile, *, resolve_host=resolve_native_owner_turn,
                 resolve_project, clock=lambda: datetime.now(timezone.utc)):
        self.profile = Path(profile).resolve()
        self.resolve_host = resolve_host
        self.resolve_project = resolve_project
        self.clock = clock

    def context(self):
        payload = self.profile.read_bytes()
        cfg = json.loads(payload)
        if (cfg.get('schema_version') != 'native_material_source_profile_v1'
                or cfg.get('enabled') is not True or cfg.get('revoked') is True
                or cfg.get('owner_uid') != os.getuid()
                or self.profile.stat().st_uid != os.getuid()
                or cfg.get('audience') != 'local_owner'
                or not cfg.get('accepted_request_ref')):
            raise ValueError('material source profile is inactive or not owned by this caller')
        workspace = Path(cfg['workspace'])
        if not workspace.is_dir() or workspace.resolve() != workspace:
            raise ValueError('material workspace moved or was retargeted')
        root = Path(cfg['source_root'])
        if root.resolve() != self.profile.parent or not root.is_relative_to(workspace):
            raise ValueError('material source root is outside its registered workspace')
        host = self.resolve_host(workspace)
        # The resolver must receive the independently verified host grant;
        # never construct a write context from a project-ref string alone.
        context = self.resolve_project(workspace, host)
        if (context.get('project_ref') != cfg['project_scope']['project_ref']
                or context.get('workspace_path') != str(workspace)
                or context.get('grant') != 'workspace_write'
                or context.get('audience') != cfg['audience']):
            raise ValueError('live Core project context does not match the source profile')
        return cfg, host, digest(payload)

    def issue(self, intent):
        cfg, host, profile_digest = self.context()
        if intent.get('action') not in cfg['allowed_operations']:
            raise ValueError('operation is outside the material source profile')
        now = self.clock()
        gate = {'schema_version': 'native_material_owner_gate_v1',
                'store_id': cfg['store_id'], 'project_scope': cfg['project_scope'],
                'audience': cfg['audience'], 'host': host, 'intent': intent,
                'profile_digest': profile_digest, 'issued_at': now.isoformat(),
                'expires_at': (now + timedelta(minutes=15)).isoformat()}
        payload = canonical_json(gate)
        ref = 'native-' + digest(payload)
        write_immutable(self.profile.parent/'owner-gates'/f'{ref}.json', payload)
        return ref

    def authorize(self, ref, *, intent=None):
        cfg, host, profile_digest = self.context()
        if not isinstance(ref, str) or len(ref) != 71 or not ref.startswith('native-'):
            raise ValueError('invalid native owner gate reference')
        if any(c not in '0123456789abcdef' for c in ref[7:]):
            raise ValueError('invalid native owner gate digest')
        path = self.profile.parent/'owner-gates'/f'{ref}.json'
        payload = path.read_bytes()
        if digest(payload) != ref[7:] or path.stat().st_uid != os.getuid():
            raise ValueError('owner gate integrity or ownership mismatch')
        gate = json.loads(payload)
        now = self.clock()
        if not datetime.fromisoformat(gate['issued_at']) <= now < datetime.fromisoformat(gate['expires_at']):
            raise ValueError('native owner gate expired or not yet valid')
        if (gate['host'] != host or gate['profile_digest'] != profile_digest
                or gate['store_id'] != cfg['store_id']
                or gate['project_scope'] != cfg['project_scope']
                or gate['audience'] != cfg['audience']):
            raise ValueError('owner gate caller, Turn or source profile changed')
        if intent is not None and gate['intent'] != intent:
            raise ValueError('owner gate does not cover this operation')
        return gate
