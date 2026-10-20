"""Read source-reported statuses from AIM's RESOLVED.md only."""
import re
from urllib.request import Request,urlopen
from urllib.parse import urljoin

def collect_aim_resolved(source,token=None):
    repo=source['repo']
    url=f'https://raw.githubusercontent.com/{repo}/main/RESOLVED.md'
    with urlopen(Request(url,headers={'User-Agent':'open-math-progress-indexer'}),timeout=30) as r:
        body=r.read().decode('utf-8')
    base=f'https://github.com/{repo}/blob/main/'
    section=''; records=[]; observed=0
    for line in body.splitlines():
        if line.startswith('## '): section=line[3:].strip().lower()
        if not line.startswith('|'): continue
        cells=[x.strip() for x in line.strip().strip('|').split('|')]
        if len(cells)<6 or cells[0].lower() in ('id','---'): continue
        m=re.search(r'\[([^]]+)\]\(([^)]+)\)',cells[1])
        if not m: continue
        observed+=1
        if 'solved' in section and 'claimed' not in section:
            status='claimed_solved'
        elif any(k in section for k in ('claimed','pending','under review')):
            status='claimed_solved'  # explicitly source-reported only; evidence retains review category
        else:
            continue
        title,rel=m.groups()
        outcome=cells[3] if len(cells)>3 else ''
        original=urljoin(base,rel)
        records.append({'title':title,'source_url':original,'repository':repo,'status':status,
                        'reported_outcome':outcome,'reported_evidence':'AIM RESOLVED.md; section: '+section,
                        'ai_involvement':'unknown','source_updated_at':None})
    if observed and not records: raise RuntimeError('AIM resolved table parsed but no recognized sections')
    print(f'AIM {repo}: table_rows={observed} imported={len(records)}')
    return records
