import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import core
class UpgradeTest(unittest.TestCase):
 def test_distinct_anchors(self):
  a=core.urlkey('https://github.com/a/b/blob/main/z.md#one')
  b=core.urlkey('https://github.com/a/b/blob/main/z.md#two')
  self.assertNotEqual(a,b)
  self.assertEqual(core.urlkey(a),a)
 def test_source_normalization(self):
  self.assertEqual(core.urlkey('https://GITHUB.com/a/b/#one'),'https://github.com/a/b#one')
if __name__=='__main__':unittest.main()
