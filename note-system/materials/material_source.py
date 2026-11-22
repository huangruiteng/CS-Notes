#!/usr/bin/env python3
"""Stable entry point for an explicitly registered private source adapter."""
import argparse
import importlib.util
import json
from pathlib import Path


def load_source(repo):
    repo = Path(repo).resolve()
    binding = repo/'.local/material-lifecycle/source-binding.json'
    if not binding.is_file():
        raise ValueError('material_source_not_configured: register the existing store adapter; do not use a historical Goal')
    cfg = json.loads(binding.read_text())
    if cfg.get('schema_version') != 'material_source_binding_v1':
        raise ValueError('unsupported material source binding')
    adapter = (repo/cfg['adapter']).resolve()
    if not adapter.is_relative_to(repo/'.local/material-lifecycle'):
        raise ValueError('material source adapter is outside its registered directory')
    spec = importlib.util.spec_from_file_location('private_material_source', adapter)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.create_source(repo)


SCHEMAS = {
    'complete': {
        'description': 'Archive or update material lifecycle from verified human statements (two-phase prepare -> apply).',
        'prepare_shorthand_input': {
            'schema_version': 'material_lifecycle_decisions_v1',
            'decisions': [
                {
                    'material_ref': 'material-example-id',
                    'action': 'user_completed',
                    'actor': 'human_user',
                    'kind': 'user_statement',
                    'source_ref': 'host://conversation-id#turn',
                    'statement': 'Exact user completion quote',
                }
            ],
        },
        'remote_verified_variant': {
            'kind': 'verified_remote_user_statement',
            'user_message_ref': 'host://conversation-id#turn',
            'remote_commit': '<40-char-git-oid>',
        },
        'commands': [
            'python3 note-system/materials/material_source.py --repo . complete --evidence <decisions.json> --phase prepare',
            'python3 note-system/materials/material_source.py --repo . complete --plan <plan_file_from_prepare> --phase apply',
        ],
    },
    'reconcile': {
        'description': 'Three-way import of accepted remote public cards/order into registered source without inferring completion.',
        'commands': [
            'python3 note-system/materials/material_source.py --repo . reconcile --base-ref <pre_fetch_head> --public-ref HEAD --phase prepare',
            'python3 note-system/materials/material_source.py --repo . reconcile --plan <plan_file_from_prepare> --phase apply',
        ],
    },
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('command', nargs='?', choices=['status', 'prepare', 'apply', 'check', 'rollback', 'complete', 'reconcile', 'schema'])
    parser.add_argument('--schema', choices=sorted(SCHEMAS), help='Print JSON input schema and CLI recipe without reading source code')
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--phase', choices=['prepare', 'apply', 'rollback'], default='prepare')
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--expected-queue-revision')
    parser.add_argument('--base-ref', help='Pre-sync Git commit for reviewed-card three-way comparison')
    parser.add_argument('--public-ref', default='HEAD', help='Accepted merged public catalog commit')
    args = parser.parse_args(argv)
    if args.schema or args.command == 'schema':
        payload = SCHEMAS[args.schema] if args.schema else SCHEMAS
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if not args.command:
        parser.error('command or --schema is required')
    try:
        source = load_source(args.repo)
        result = source.run(args)
    except (ValueError, FileNotFoundError) as exc:
        print(json.dumps({'status': 'blocked', 'reason': str(exc)}, ensure_ascii=False))
        return 1
    if result is not None:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
