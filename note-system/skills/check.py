#!/usr/bin/env python3
"""Check or explicitly refresh the curated file manifest after content review."""
from pathlib import Path
import argparse
import hashlib
import json
import re
ROOT=Path(__file__).resolve().parents[2]
MANIFEST=Path(__file__).with_name('manifest.json')

def check(refresh=False):
 data=json.loads(MANIFEST.read_text())
 errors=[]
 for entry in data['skills']:
  root=ROOT/'.codex/skills'/entry['name']
  if root.is_symlink(): errors.append(f"symlink source: {entry['name']}");continue
  actual={}
  for p in root.rglob('*'):
   if p.is_symlink(): errors.append(f'symlink: {p}');continue
   if p.is_file(): actual[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
  text=(root/'SKILL.md').read_text()
  if not text.startswith('---\n') or f"name: {entry['name']}\n" not in text or not re.search(r'^description: .+',text,re.M): errors.append(f"invalid frontmatter: {entry['name']}")
  if refresh: entry['files']=dict(sorted(actual.items()))
  elif actual != entry['files']: errors.append(f"file/digest mismatch: {entry['name']}")
 if errors: raise ValueError('; '.join(errors))
 if refresh: MANIFEST.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 return len(data['skills'])

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--refresh',action='store_true',help='rewrite hashes only after public-safety review; inspect resulting Git diff')
 args=parser.parse_args()
 print(f'{check(args.refresh)} curated skills verified')
