#!/usr/bin/env python3
"""Repeatable synthetic Weble coding evaluations through real Codex; no live account."""
import argparse,pathlib,json,subprocess,time,os,signal
CASES={
 'filter':{'query':'filterJobs status title','source':'export function filterJobs(jobs, query, status) { return jobs; }\n','task':'Fix filterJobs: match title case-insensitively, filter exact status unless all, preserve input order and objects.','checks':'''const jobs=[{title:'Ocean',status:'complete'},{title:'Launch',status:'failed'}];
assert.deepEqual(filterJobs(jobs,'LA','all'),[jobs[1]]);
assert.deepEqual(filterJobs(jobs,'','failed'),[jobs[1]]);
assert.deepEqual(filterJobs(jobs,'missing','all'),[]);
assert.equal(jobs.length,2);''','symbol':'filterJobs'},
 'cancel':{'query':'cancelJob terminal status','source':"export function cancelJob(job) { return {...job,status:'cancelled'}; }\n",'task':'Fix cancelJob: queued/running jobs become cancelled; complete/failed/cancelled jobs retain their state; never mutate input.','checks':'''for(const status of ['queued','running']){const job={id:1,status};assert.equal(cancelJob(job).status,'cancelled');assert.equal(job.status,status);}
for(const status of ['complete','failed','cancelled'])assert.equal(cancelJob({id:1,status}).status,status);''','symbol':'cancelJob'},
 'merge':{'query':'mergePoll local cancelled stale server','source':'export function mergePoll(local, server) { return server; }\n','task':'Fix mergePoll: return server jobs in server order, retain cancelled status for locally cancelled matching IDs despite stale server status, include new server jobs, do not mutate either input.','checks':'''const local=[{id:1,status:'cancelled'}];const server=[{id:1,status:'running'},{id:2,status:'queued'}];
const result=mergePoll(local,server);assert.deepEqual(result,[{id:1,status:'cancelled'},{id:2,status:'queued'}]);assert.equal(server[0].status,'running');assert.equal(local[0].status,'cancelled');
assert.deepEqual(mergePoll([],server),server);assert.deepEqual(mergePoll(local,[]),[]);''','symbol':'mergePoll'}
}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--case',choices=list(CASES));ap.add_argument('--timeout',type=int,default=180);ap.add_argument('--prepare-only',action='store_true');a=ap.parse_args()
 root=pathlib.Path(a.output).resolve();root.mkdir(parents=True,exist_ok=True)
 report=[]
 for name,c in CASES.items():
  if a.case and a.case!=name:continue
  dest=root/name;dest.mkdir(exist_ok=True)
  if list(dest.iterdir()):raise SystemExit('Use a new output directory; existing evidence is preserved')
  (dest/'jobs.mjs').write_text(c['source'])
  test="import assert from 'node:assert/strict';\nimport {"+c['symbol']+"} from './jobs.mjs';\n"+c['checks']+'\n'
  (dest/'verify.mjs').write_text(test)
  (dest/'AGENTS.md').write_text('Disposable synthetic Weble evaluation. Only modify jobs.mjs. Do not modify tests, use network, or delegate. Retrieve relevant project context before editing.\n')
  (dest/'architecture.md').write_text('Weble-style video jobs: queued, running, complete, failed, cancelled. A cancelled job must stay cancelled when an older poll response arrives.\n')
  baseline=subprocess.run(['node','verify.mjs'],cwd=dest,capture_output=True,text=True)
  if baseline.returncode==0:raise RuntimeError('Invalid evaluation: broken fixture passes')
  if a.prepare_only:
   report.append({'case':name,'baseline_fails':True,'prepared':True});continue
  prompt=c['task']+' Use search_project_context to locate relevant implementation and notes. Only edit jobs.mjs. Run node verify.mjs, fix failures, and report observed results.'
  start=time.monotonic();timed=False
  with (root/(name+'-events.jsonl')).open('w') as out,(root/(name+'-stderr.txt')).open('w') as err:
   proc=subprocess.Popen(['codex','exec','--profile','local-dev','--ephemeral','--skip-git-repo-check','--json','-c','model_providers.codex-router.http_headers.x-codex-router-exact-route="1"','-C',str(dest),prompt],stdout=out,stderr=err,start_new_session=True)
   try:proc.wait(timeout=a.timeout)
   except subprocess.TimeoutExpired:timed=True;os.killpg(proc.pid,signal.SIGTERM);proc.wait(timeout=15)
  verified=subprocess.run(['node','verify.mjs'],cwd=dest,capture_output=True,text=True)
  events=(root/(name+'-events.jsonl')).read_text()
  immutable=(dest/'verify.mjs').read_text()==test
  used=False;agent_test=False
  for line in events.splitlines():
   try:
    row=json.loads(line);item=row.get('item',{})
    if row.get('type')=='item.completed' and item.get('type')=='command_execution' and 'node verify.mjs' in item.get('command','') and item.get('exit_code')==0:agent_test=True
    if row.get('type')=='item.completed' and item.get('tool')=='search_project_context' and item.get('status')=='completed' and not item.get('error'):used=True
   except json.JSONDecodeError:pass
  report.append({'case':name,'seconds':round(time.monotonic()-start,1),'timeout':timed,'exit':proc.returncode,'baseline_fails':True,'tests_unchanged':immutable,'behavior_pass':verified.returncode==0 and immutable,'retrieval_used':used,'agent_ran_tests':agent_test,'pass':verified.returncode==0 and immutable and used and agent_test and not timed,'test_output':verified.stdout+verified.stderr})
 (root/'results.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
