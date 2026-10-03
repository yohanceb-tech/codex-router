#!/usr/bin/env python3
"""Compact native-Ollama tool-selection regression; does not perform website edits."""
import pathlib,json,urllib.request,sys,time
instructions=pathlib.Path(sys.argv[1]).read_text();out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
cases=[('chat','Look through Codex chats for info on the web pages. The chat is named Weble Website.','codex_app__list_threads',{'limit':{'type':'integer'}},[]),('browser','Use my signed-in Chrome session to inspect the admin page for my website. Start by checking available browser tabs.','mcp__cua_repl__js',{'code':{'type':'string'},'title':{'type':'string'}},['code'])]
results=[]
for name,prompt,tool,props,required in cases:
 body={'model':'gpt-oss:20b','stream':False,'think':'low','options':{'num_ctx':8192,'num_predict':1200,'temperature':0},'messages':[{'role':'system','content':instructions+'\nBrowser first call for inventory: await cua.getState(); Read its returned documentation before further API calls.'},{'role':'user','content':prompt}],'tools':[{'type':'function','function':{'name':tool,'description':'Inspect available chats' if name=='chat' else 'Unified computer use; inventory entry point is await cua.getState();','parameters':{'type':'object','properties':props,'required':required}}}]}
 start=time.monotonic();req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=120) as response:r=json.load(response)
 calls=r.get('message',{}).get('tool_calls',[]);passed=bool(calls) and calls[0].get('function',{}).get('name')==tool
 if passed and name=='browser':passed='cua.getState' in calls[0]['function'].get('arguments',{}).get('code','')
 results.append({'case':name,'seconds':round(time.monotonic()-start,1),'pass':passed,'response':r})
(out/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps([{k:v for k,v in x.items() if k!='response'} for x in results],indent=2))
if not all(x['pass'] for x in results):sys.exit(1)
