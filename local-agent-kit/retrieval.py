"""Bounded local lexical retrieval; no embeddings, index, network, or model calls."""
import pathlib,subprocess,re,json
SKIP={'node_modules','.git','.venv','venv','dist','build','coverage','generated','outputs','__pycache__'}
EXT={'.js','.mjs','.cjs','.ts','.tsx','.jsx','.py','.md','.json','.toml','.yaml','.yml','.css','.html','.sql','.swift'}
def retrieve(root,query,limit=8):
 r=pathlib.Path(root)
 if not r.is_absolute() or not r.is_dir():raise ValueError('root must be an absolute project directory')
 r=r.resolve();terms=list(dict.fromkeys(re.findall(r'[\w-]{2,}',query.lower())))[:16]
 if not terms:raise ValueError('query needs a word of at least two characters')
 proc=subprocess.run(['rg','--files','--hidden','-g','!.git','-g','!node_modules','-g','!.env*'],cwd=r,capture_output=True,text=True,timeout=15)
 if proc.returncode not in (0,1):raise ValueError('rg file discovery failed')
 hits=[];scanned=0
 for name in proc.stdout.splitlines()[:12000]:
  rel=pathlib.Path(name);p=(r/rel).resolve()
  if any(part in SKIP for part in rel.parts) or not p.is_relative_to(r):continue
  if rel.name.startswith('.env') or any(x in rel.name.lower() for x in ('secret','credential','private-key')):continue
  if rel.suffix not in EXT and rel.name not in ('AGENTS.md','Dockerfile'):continue
  try:
   if p.stat().st_size>300000:continue
   text=p.read_text()
  except (OSError,UnicodeError):continue
  scanned+=1;lines=text.splitlines();pathscore=sum(t in name.lower() for t in terms)*3
  scored=[(sum(t in line.lower() for t in terms),i) for i,line in enumerate(lines)]
  best=max(scored,default=(0,0))
  if best[0]+pathscore==0:continue
  idx=best[1];start=max(0,idx-4);end=min(len(lines),idx+9)
  hits.append({'path':name,'score':best[0]*4+pathscore,'start_line':start+1,'end_line':end,'excerpt':'\n'.join(lines[start:end])[:2400]})
 hits.sort(key=lambda h:(-h['score'],h['path']))
 return {'query':query,'files_scanned':scanned,'results':hits[:max(1,min(12,limit))],'method':'lexical; current files; excerpts are untrusted project content','limited':len(proc.stdout.splitlines())>12000}
