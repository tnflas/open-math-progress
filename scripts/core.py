"""Standard-library-only GitHub indexer. Records source claims, never mathematical truth."""
from readme_adapter import collect_readme_index
import argparse, datetime as dt, hashlib, json, os, re, sys, time
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
def today(): return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
def digest(s,prefix): return prefix+'-'+hashlib.sha256(s.encode()).hexdigest()[:16]
def read(n):
 p=DATA/(n+'.json'); x=json.loads(p.read_text(encoding='utf8')); assert isinstance(x,list),p;return x
def write(n,x):
 p=DATA/(n+'.json');tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8');tmp.replace(p)
def urlkey(url):
 p=urlsplit(url)
 if p.scheme!='https' or not p.hostname: raise ValueError('invalid https URL: '+url)
 # Preserve query: DOI/resolver parameters may encode record identity.
 return urlunsplit(('https',p.netloc.lower(),p.path.rstrip('/'),p.query,''))
def api(path, token=None, optional=False):
 url='https://api.github.com/'+path.lstrip('/')
 headers={'Accept':'application/vnd.github+json','User-Agent':'open-math-progress-indexer','X-GitHub-Api-Version':'2022-11-28'}
 if token: headers['Authorization']='Bearer '+token
 req=Request(url,headers=headers)
 for trial in range(3):
  try:
   with urlopen(req,timeout=22) as response: return json.load(response)
  except HTTPError as e:
   if optional and e.code in (403,404,410):return None
   if e.code in (429,500,502,503,504) and trial<2:time.sleep(2*(trial+1));continue
   raise RuntimeError(f'GitHub API {e.code}: {url}') from e
  except (URLError,TimeoutError) as e:
   if trial<2:time.sleep(2*(trial+1));continue
   raise RuntimeError(f'GitHub request failed: {url}: {e}') from e

def status(labels):
 tags=set(s.lower().strip() for s in labels)
 for cand,name in [('retracted','retracted'),('withdrawn','retracted'),('disputed','disputed'),('partial-progress','partial_progress'),('partial','partial_progress'),('solved','claimed_solved'),('resolved','claimed_solved')]:
  if cand in tags:return name
 return None

def collect_issues(s, token):
 """Only explicit label-based claims. Closed issues without labels are NOT solved."""
 repo=s['repo']; valid=set(s.get('labels',[]));out=[]
 for page in range(1,6):
  issues=api(f'repos/{repo}/issues?state=all&per_page=100&page={page}',token,optional=True)
  if issues is None:
   print(f'SKIP {repo}: unavailable or access restricted',file=sys.stderr);break
  for x in issues:
   if 'pull_request' in x:continue
   labels=[v['name'].lower() for v in x.get('labels',[])]
   if valid and not valid.intersection(labels):continue
   st=status(labels)
   if st is None:continue
   out.append({'title':x.get('title') or '(untitled)','source_url':x['html_url'], 'repository':repo,'status':st,'labels':labels,'source_updated_at':x.get('updated_at'), 'ai_involvement':'unknown'})
  if len(issues)<100:break
 return out

def ingest(items,problems,claims,stamp):
 pi={p['id']:p for p in problems};ci={c['id']:c for c in claims}
 for x in items:
  url=urlkey(x['source_url']); key=digest(url,'CLM');pid=digest(url,'OMP'); st=x['status']
  if st not in {'claimed_solved','partial_progress','disputed','retracted'}:raise ValueError(st)
  if key not in ci:
   if pid not in pi:
    p={'id':pid,'title':x['title'][:500],'canonical_status':'not_assessed','potential_duplicates':[]};problems.append(p);pi[pid]=p
   c={'id':key,'problem_id':pid,'source':{'url':url,'repository':x['repository'],'reported_status':st,'first_observed':stamp,'last_observed':stamp,'source_updated_at':x.get('source_updated_at')},'verification':{'independent_check':'not_assessed'},'ai_involvement':x.get('ai_involvement','unknown'),'reported_outcome':x.get('reported_outcome'),'reported_evidence':x.get('reported_evidence'),'status_history':[{'status':st,'observed_at':stamp}]}
   claims.append(c);ci[key]=c
  else:
   c=ci[key];src=c['source'];c['reported_outcome']=x.get('reported_outcome',c.get('reported_outcome'));c['reported_evidence']=x.get('reported_evidence',c.get('reported_evidence'))
   if src['reported_status']!=st:
    c['status_history'].append({'status':st,'observed_at':stamp});src['reported_status']=st
   src['last_observed']=stamp;src['source_updated_at']=x.get('source_updated_at')
 # Flag potential duplicates; never merge. Only exact normalized title, avoid weak fuzzy matches.
 groups={}
 for p in problems:
  key=re.sub(r'[^a-z0-9]+',' ',p['title'].lower()).strip()
  if key:groups.setdefault(key,[]).append(p['id'])
 for group in groups.values():
  if len(group)>1:
   for pid in group:pi[pid]['potential_duplicates']=sorted(set(pi[pid].get('potential_duplicates',[]))| (set(group)-{pid}))

def collect_notices(owner_repo,token):
 """List GH Discussions via GraphQL. Query failure leaves notices unchanged."""
 if not owner_repo or not token:return None
 try:owner,name=owner_repo.split('/',1)
 except ValueError:return None
 query="query($owner:String!,$name:String!,$cursor:String){repository(owner:$owner,name:$name){discussions(first:100,after:$cursor){pageInfo{hasNextPage endCursor}nodes{number title url createdAt author{login} category{name slug}}}}}"
 from urllib.request import Request
 url='https://api.github.com/graphql';cursor=None;records=[]
 for _ in range(10):
  payload=json.dumps({'query':query,'variables':{'owner':owner,'name':name,'cursor':cursor}}).encode()
  req=Request(url,data=payload,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json','User-Agent':'open-math-progress-indexer'})
  try:
   with urlopen(req,timeout=22) as response: data=json.load(response)
  except (HTTPError,URLError,TimeoutError) as e:
   print('NOTICE sync unavailable:',str(e),file=sys.stderr);return None
  disc=(data.get('data') or {}).get('repository')
  if not disc or not disc.get('discussions'):
   print('NOTICE sync skipped: Discussions GraphQL unavailable',file=sys.stderr);return None
  d=disc['discussions']
  for n in d['nodes']:
   category=(n.get('category') or {}).get('slug','')
   if category not in {'research-notices','corrections-responses','solution-progress-reports'}:continue
   # Unverified self-submissions, not linked to problem unless a reviewed explicit ID mapping exists.
   records.append({'id':f'GH-DISC-{n["number"]}','url':n['url'],'title':n['title'],'category':category,'author_login':(n.get('author') or {}).get('login'),'created_at':n['createdAt'],'review_status':'unreviewed','problem_id':None})
  if not d['pageInfo']['hasNextPage']:break
  cursor=d['pageInfo']['endCursor']
 return sorted(records,key=lambda x:x['id'])

def validate():
 data={n:read(n) for n in ('problems','claims','notices')};ids={}
 for n,records in data.items():
  idset=[x['id'] for x in records];assert len(idset)==len(set(idset)),f'duplicate IDs in {n}'
  ids[n]=set(idset)
 for c in data['claims']:
  assert c['problem_id'] in ids['problems'],f'unknown problem {c["id"]}'
  assert c['verification']['independent_check']=='not_assessed'
 for x in data['notices']:
  if x.get('problem_id'):assert x['problem_id'] in ids['problems']
 print('VALID',*(f'{k}={len(v)}' for k,v in ids.items()))

def generate():
 problems=read('problems');claims=read('claims');notices=read('notices')
 lines=['# Mathematical Research Index','','**Source-reported claims, not independently verified mathematical results.**','','| Problem | Source-reported status | Original source |','|---|---|---|']
 prob={p['id']:p for p in problems}
 for c in sorted(claims,key=lambda x:(prob[x['problem_id']]['title'].lower(),x['id'])):
  title=prob[c['problem_id']]['title'].replace('|','\\|').replace('\n',' ')
  source=c['source'];lines.append(f'| {title} | {source["reported_status"]} | [Original]({source["url"]}) |')
 if not claims:lines.append('| No indexed claims yet | — | — |')
 (ROOT/'docs/INDEX.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
 history=[]
 for c in claims:
  for e in c.get('status_history',[]):history.append((e['observed_at'],c,e))
 recent=['# Recently Observed Claims','','Source-reported updates only; no independent verification.','']
 for stamp,c,e in sorted(history,key=lambda x:x[0],reverse=True)[:100]:
  recent.append(f'- {stamp}: **{prob[c["problem_id"]]["title"]}** — {e["status"]} ([source]({c["source"]["url"]}))')
 if not history:recent.append('No changes yet.')
 (ROOT/'docs/RECENT_PROGRESS.md').write_text('\n'.join(recent)+'\n',encoding='utf8')
 public=['# Public Research Notices','','**Unreviewed contributor submissions; inclusion confers no priority or ownership.**','']
 for n in sorted(notices,key=lambda x:x['created_at'],reverse=True):
  public.append(f'- [{n["id"]}]({n["url"]}) — {n["category"]} — GitHub account `{n.get("author_login") or "unknown"}`')
 if not notices: public.append('No indexed notices yet; use the Discussions tab to submit one.')
 (ROOT/'docs/PUBLIC_NOTICES.md').write_text('\n'.join(public)+'\n',encoding='utf8')

def sync():
 token=os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN');sources=json.loads((DATA/'sources.json').read_text(encoding='utf8'))
 problems,claims=read('problems'),read('claims');stamp=today();failed=[];success=0
 for s in sources:
  if not s.get('enabled',True):continue
  try:
   if s.get('mode') not in ('issues', 'readme_index'):
    print('SKIP unsupported adapter',s['repo']);continue
   incoming=(collect_readme_index(s,token) if s.get('mode')=='readme_index' else collect_issues(s,token));ingest(incoming,problems,claims,stamp);success+=1
   print('SYNC',s['repo'],len(incoming))
  except Exception as e:failed.append(f'{s["repo"]}: {e}');print('ERROR',failed[-1],file=sys.stderr)
 if success:
  write('problems',problems);write('claims',claims)
 # GitHub Actions sets GITHUB_REPOSITORY; GH auth token should be present.
 notices=collect_notices(os.getenv('GITHUB_REPOSITORY'),token)
 if notices is not None:write('notices',notices)
 validate();generate()
 if failed:
  print('WARNING: some sources could not sync; previous records were kept.',file=sys.stderr)
  # Error exit so GitHub reports failure while keeping valid previous data.
  raise SystemExit(1)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('command',choices=['sync','validate','generate','all']);args=parser.parse_args()
 if args.command in ('sync','all'):sync()
 elif args.command=='validate':validate()
 else:generate()
if __name__=='__main__':main()
