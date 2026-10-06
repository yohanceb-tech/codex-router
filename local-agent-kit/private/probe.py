"""Run inside the exact private-agent sandbox. No sensitive data is transmitted."""
import json,os,socket,subprocess,sys,urllib.request,urllib.error,base64
from pathlib import Path

def request(port,path,data=None):
    r=urllib.request.Request(f'http://127.0.0.1:{port}{path}',data=None if data is None else json.dumps(data).encode(),headers={'Authorization':'Bearer '+os.environ['PRIVATE_AGENT_TOKEN'],'Content-Type':'application/json'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(r,timeout=60) as f:return f.status,json.load(f)
    except urllib.error.HTTPError as e:return e.code,json.load(e)

def main():
    inference,web=map(int,sys.argv[1:3])
    results={}
    status,v=request(inference,'/health');assert status==200 and v['fallback'] is False;results['local_gateway_allowed']=True
    for host,port in [('1.1.1.1',443),('127.0.0.1',11434),('127.0.0.1',4202)]:
        try:
            socket.create_connection((host,port),timeout=2).close()
            raise AssertionError(f'Unexpected connection to {host}:{port}')
        except PermissionError:results[f'blocked_{host}_{port}']=True
    child=subprocess.run([sys.executable,'-c','import socket;socket.create_connection(("1.1.1.1",443),2)'],capture_output=True,text=True)
    assert child.returncode!=0 and 'Operation not permitted' in child.stderr;results['child_process_network_blocked']=True
    for u in ['https://api.openai.com/v1/models','https://chatgpt.com/','https://127.0.0.1/','https://example.com:8443/']:
        status,v=request(web,'/fetch',{'url':u});assert status==400 and 'error' in v
    results['web_destination_policy']=True
    status,v=request(inference,'/v1/responses',{'model':'gpt-6.1-sol','input':'synthetic privacy probe'});assert status==400;results['hosted_model_blocked']=True
    status,v=request(inference,'/v1/embeddings',{});assert status==403;results['unhandled_endpoint_blocked']=True
    status,v=request(web,'/fetch',{'url':'https://www.python.org/'});assert status==200 and 'Python' in v['text'];results['public_page_fetch_works']=True
    status,v=request(web,'/search',{'query':'Python official documentation asyncio TaskGroup'});assert status==200 and v['results'];results['public_search_works']=True
    if '--model-check' in sys.argv:
        status,v=request(inference,'/v1/responses/compact',{'model':'gpt-oss:20b','input':[{'role':'user','content':[{'type':'input_text','text':'Build a local demo. The button must say CEDAR 912. Next step is to run the tests.'}]}]})
        assert status==200 and v.get('output'),v
        status,v=request(inference,'/v1/responses',{'model':'gpt-oss:20b','stream':False,'reasoning':{'effort':'low'},'input':v['output']+[{'role':'user','content':[{'type':'input_text','text':'What exact button label was required? Reply with only the label.'}]}]})
        answer=' '.join(p.get('text','') for i in v.get('output',[]) if i.get('type')=='message' for p in i.get('content',[]))
        assert status==200 and 'CEDAR 912' in answer,(status,answer)
        results['local_compaction_and_continuation']=True
        status,v=request(inference,'/v1/responses',{'model':'gpt-oss:20b','stream':False,'input':[{'type':'message','role':'user','content':[{'type':'input_text','text':'Required button label: CEDAR 912. Next step: test.'}]},{'type':'compaction_trigger'}]})
        assert status==200 and v['output'][0]['type']=='compaction',v
        status,v=request(inference,'/v1/responses',{'model':'gpt-oss:20b','stream':False,'reasoning':{'effort':'low'},'input':v['output']+[{'role':'user','content':[{'type':'input_text','text':'Return only the exact required button label.'}]}]})
        answer=' '.join(p.get('text','') for i in v.get('output',[]) if i.get('type')=='message' for p in i.get('content',[]))
        assert status==200 and 'CEDAR 912' in answer,(status,answer)
        results['local_v2_compaction_and_continuation']=True
        fixture=Path(os.environ['CODEX_HOME'])/'vision-probe.png'
        url='data:image/png;base64,'+base64.b64encode(fixture.read_bytes()).decode()
        status,v=request(inference,'/v1/responses',{'model':'gpt-oss:20b','stream':False,'reasoning':{'effort':'low'},'input':[{'role':'user','content':[{'type':'input_text','text':'Read the label in the attached image. Return only its exact text.'},{'type':'input_image','image_url':url}]}]})
        answer=' '.join(p.get('text','') for i in v.get('output',[]) if i.get('type')=='message' for p in i.get('content',[]))
        assert status==200 and 'SABLE 731' in answer,(status,answer)
        results['local_gemma_screenshot_reading']=True
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
