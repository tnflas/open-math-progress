import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import ingest, urlkey
class IngestTests(unittest.TestCase):
 def test_idempotent_and_status_change(self):
  p=[];c=[];x={'title':'Problem A','source_url':'https://github.com/test/repo/issues/1','repository':'test/repo','status':'claimed_solved'}
  ingest([x],p,c,'2026-10-20T00:00:00Z');ingest([x],p,c,'2026-10-21T00:00:00Z')
  self.assertEqual((len(p),len(c),len(c[0]['status_history'])),(1,1,1))
  ingest([{**x,'status':'retracted'}],p,c,'2026-10-22T00:00:00Z')
  self.assertEqual(len(c[0]['status_history']),2)
 def test_distinct_sources_not_merged(self):
  p=[];c=[]
  for n in (1,2):ingest([{'title':'Same problem','source_url':f'https://github.com/test/repo/issues/{n}','repository':'test/repo','status':'claimed_solved'}],p,c,'2026-10-20')
  self.assertEqual(len(p),2);self.assertTrue(p[0]['potential_duplicates'])
if __name__=='__main__':unittest.main()
