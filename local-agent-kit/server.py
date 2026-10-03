#!/usr/bin/env python3
"""Dependency-free MCP stdio file tools; writes require a matching content hash."""
import sys,json,pathlib,hashlib,os,tempfile
from retrieval import retrieve
from checks import check

def digest(text): return hashlib.sha256(text.encode()).hexdigest()
def target(root,path):
 if not pathlib.Path(root).is_absolute(): raise ValueError('root must be absolute')
 r=pathlib.Path(root).resolve(strict=True)
 if not r.is_dir(): raise ValueError('root must be a directory')
 p=(r/path).resolve()
 if not p.is_relative_to(r): raise ValueError('path escapes project root')
 return p

ACTIVE_ROOT = None
def call(name,a):
 global ACTIVE_ROOT
 if name=='run_project_check':
  root=a.get('root') or ACTIVE_ROOT
  if not root:raise ValueError('read/search a project first or provide root')
  return check(root,a['kind'],a.get('path'),a.get('script'),a.get('timeout_seconds',90))
 if name=='search_project_context':
  result=retrieve(a['root'],a['query'],a.get('limit',8));ACTIVE_ROOT=str(pathlib.Path(a['root']).resolve());return result
 p=target(a['root'],a['path'])
 if name=='read_project_file':
  text=p.read_text(); ACTIVE_ROOT=str(pathlib.Path(a['root']).resolve()); lines=text.splitlines(keepends=True); start=max(1,a.get('start_line',1)); count=min(400,max(1,a.get('line_count',160)))
  return {'sha256':digest(text),'total_lines':len(lines),'start_line':start,'text':''.join(lines[start-1:start-1+count])[:24000]}
 if name!='write_project_file': raise ValueError('unknown tool')
 old=p.read_text() if p.exists() else None
 expected=a['expected_sha256']
 if (digest(old) if old is not None else 'missing')!=expected: raise ValueError('file changed: read again before writing')
 text=a['content']
 if len(text.encode())>2_000_000: raise ValueError('file too large')
 p.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(dir=p.parent)
 try:
  with os.fdopen(fd,'w') as f: f.write(text)
  if p.exists(): os.chmod(tmp,p.stat().st_mode & 0o777)
  os.replace(tmp,p)
 finally:
  if os.path.exists(tmp): os.unlink(tmp)
 return {'path':str(p),'sha256':digest(text),'bytes':len(text.encode())}

base={'root':{'type':'string','description':'Absolute project directory'},'path':{'type':'string','description':'Path relative to project root'}}
def schema(extra,required): return {'type':'object','properties':dict(base,**extra),'required':['root','path']+required,'additionalProperties':False}
tools=[{'name':'read_project_file','description':'Read a bounded text file excerpt and full-file hash.','inputSchema':schema({'start_line':{'type':'integer'},'line_count':{'type':'integer'}},[])},{'name':'write_project_file','description':'Atomically write text only if the full-file hash matches. Use missing for a new file. Run relevant syntax/tests afterward.','inputSchema':schema({'expected_sha256':{'type':'string'},'content':{'type':'string'}},['expected_sha256','content'])}]
tools.append({'name':'search_project_context','description':'Retrieve ranked code/docs excerpts with file paths and line numbers from the current local project. No network or persistent index.','inputSchema':{'type':'object','properties':{'root':base['root'],'query':{'type':'string'},'limit':{'type':'integer'}},'required':['root','query'],'additionalProperties':False}})
tools.append({'name':'run_project_check','description':'Execute a project check and return observed exit code/output. Omit root after a successful project read/search to reuse that project directory. Use node_file to run a verification script, node_test for Node tests, node_syntax for parsing, package_script for an existing test/build/typecheck/lint script.','inputSchema':{'type':'object','properties':{'root':base['root'],'kind':{'type':'string','enum':['node_file','node_test','node_syntax','package_script']},'path':{'type':'string'},'script':{'type':'string','enum':['test','build','typecheck','lint']},'timeout_seconds':{'type':'integer'}},'required':['kind'],'additionalProperties':False}})
for tool in tools:
 tool['annotations']={'readOnlyHint':tool['name'] in ('read_project_file','search_project_context'),'destructiveHint':tool['name'] in ('write_project_file','run_project_check'),'openWorldHint':False,'idempotentHint':tool['name'] in ('read_project_file','search_project_context')}
def main():
 for line in sys.stdin:
  try:
   req=json.loads(line); method=req.get('method'); ident=req.get('id')
   if ident is None: continue
   if method=='initialize': result={'protocolVersion':req.get('params',{}).get('protocolVersion','2024-11-05'),'capabilities':{'tools':{}},'serverInfo':{'name':'local-agent-files','version':'1.0.0'}}
   elif method=='tools/list': result={'tools':tools}
   elif method=='tools/call':
    try: result={'content':[{'type':'text','text':json.dumps(call(req['params']['name'],req['params']['arguments']))}]}
    except Exception as e: result={'isError':True,'content':[{'type':'text','text':str(e)}]}
   elif method=='ping': result={}
   else:
    print(json.dumps({'jsonrpc':'2.0','id':ident,'error':{'code':-32601,'message':'Unknown method'}}),flush=True); continue
   print(json.dumps({'jsonrpc':'2.0','id':ident,'result':result}),flush=True)
  except Exception as e:
   print(json.dumps({'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':str(e)}}),flush=True)
if __name__=='__main__': main()
