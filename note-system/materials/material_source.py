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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('command', choices=['status', 'prepare', 'apply', 'check', 'rollback', 'complete'])
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--phase', choices=['prepare', 'apply', 'rollback'], default='prepare')
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--expected-queue-revision')
    args = parser.parse_args(argv)
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
