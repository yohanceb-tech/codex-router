"""Project-bound facade: the host supplies the root and remembers read hashes.
The model supplies short relative paths and content; stale writes still fail.
"""
import copy,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import server as core
ROOT=Path(os.environ['PRIVATE_PROJECT_ROOT']).resolve(strict=True)
READS={}
TOOLS=copy.deepcopy(core.tools)
for t in TOOLS:
    s=t['inputSchema'];s['properties'].pop('root',None);s['required']=[k for k in s['required'] if k!='root']
    t['description']+=' Project directory is already bound by the launcher. Use relative paths; do not supply root.'
    if t['name']=='write_project_file':
        s['properties'].pop('expected_sha256',None);s['required'].remove('expected_sha256')
        t['description']='Write text to a relative project path after reading it. The server remembers the read revision and rejects intervening changes. For a new file, read the missing path first. Run verification after writing.'

def call(name,args):
    a=dict(args)
    if name not in {t['name'] for t in TOOLS}:raise ValueError('Unknown tool')
    allowed=next(t['inputSchema']['properties'] for t in TOOLS if t['name']==name)
    if set(a)-set(allowed):raise ValueError('Use only the offered arguments; root and revision are managed by the server')
    if 'path' in a:
        if Path(a['path']).is_absolute():raise ValueError('Use a relative project path')
        p=core.target(str(ROOT),a['path']);key=str(p)
    a['root']=str(ROOT)
    if name=='read_project_file':
        if not p.exists():READS[key]='missing';return {'path':args['path'],'exists':False,'text':''}
        result=core.call(name,a);READS[key]=result['sha256'];result.pop('sha256');result['revision_recorded']=True;return result
    if name=='write_project_file':
        if key not in READS:raise ValueError('Read this file first to establish a revision')
        a['expected_sha256']=READS[key]
        result=core.call(name,a);READS[key]=result['sha256'];result.pop('sha256');result['path']=args['path'];return result
    return core.call(name,a)

if __name__=='__main__':
    core.tools=TOOLS
    for line in sys.stdin:
        try:
            r=json.loads(line)
            if 'id' not in r:continue
            method=r.get('method');p=r.get('params',{})
            if method=='initialize':result={'protocolVersion':p.get('protocolVersion','2024-11-05'),'capabilities':{'tools':{}},'serverInfo':{'name':'private-project-files','version':'1.0'}}
            elif method=='ping':result={}
            elif method=='tools/list':result={'tools':TOOLS}
            elif method=='tools/call':
                try:result={'content':[{'type':'text','text':json.dumps(call(p['name'],p.get('arguments',{})))}]}
                except Exception as e:result={'isError':True,'content':[{'type':'text','text':str(e)}]}
            else:raise ValueError('Unknown method')
            print(json.dumps({'jsonrpc':'2.0','id':r['id'],'result':result}),flush=True)
        except Exception as e:print(json.dumps({'jsonrpc':'2.0','id':r.get('id'),'error':{'code':-32603,'message':str(e)}}),flush=True)
