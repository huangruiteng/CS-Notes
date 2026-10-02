import importlib.util
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('toc',ROOT/'.codex/skills/markdown-toc/scripts/extract_toc.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class TocTests(unittest.TestCase):
 def headings(self,text):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'A&B note.md';p.write_text(text);return m.extract_toc(p)
 def test_fenced_code_is_not_outline(self):
  self.assertEqual(self.headings('# Real\n```python\n# Fake\n```\n~~~\n## Fake\n~~~\n## End\n'),[(1,'Real',1),(2,'End',8)])
 def test_shorter_or_different_fence_does_not_close(self):
  self.assertEqual(self.headings('````\n```\n# Fake\n~~~\n## Fake\n````\n# Real\n'),[(1,'Real',7)])
 def test_unclosed_fence(self):
  self.assertEqual(self.headings('# Before\n```\n# Fake'),[(1,'Before',1)])

if __name__=='__main__':unittest.main()
