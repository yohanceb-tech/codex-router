import unittest,tempfile,pathlib,importlib.util,json,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent))
spec=importlib.util.spec_from_file_location('files',pathlib.Path(__file__).with_name('server.py')); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Files(unittest.TestCase):
 def test_edit_conflict_escape(self):
  with tempfile.TemporaryDirectory() as d:
   a={'root':d,'path':'src/demo.js','expected_sha256':'missing','content':'const value = 1;\n'}
   m.call('write_project_file',a); read=m.call('read_project_file',a)
   a.update(expected_sha256=read['sha256'],content='const value = 2;\n');m.call('write_project_file',a)
   with self.assertRaises(ValueError): m.call('write_project_file',a)
   self.assertEqual((pathlib.Path(d)/a['path']).read_text(),a['content'])
   with self.assertRaises(ValueError):m.call('read_project_file',{'root':d,'path':'../outside'})
   (pathlib.Path(d)/'link').symlink_to('/tmp')
   with self.assertRaises(ValueError):m.call('write_project_file',dict(a,path='link/escape'))
 def test_protocol(self):
  data='\n'.join(json.dumps(v) for v in [{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05'}},{'jsonrpc':'2.0','id':2,'method':'tools/list'},{'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'read_project_file','arguments':{'root':'/not-existing','path':'x'}}}])+'\n'
  p=subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name('server.py'))],input=data,text=True,capture_output=True,check=True)
  rows=[json.loads(v) for v in p.stdout.splitlines()]
  self.assertEqual(len(rows[1]['result']['tools']),4);self.assertTrue(rows[2]['result']['isError'])
class Retrieval(unittest.TestCase):
 def test_relevance_freshness_and_exclusions(self):
  with tempfile.TemporaryDirectory() as d:
   r=pathlib.Path(d);(r/'jobs.mjs').write_text('export function cancelJob(id) { return id; }')
   (r/'.env').write_text('cancelJob=hidden');(r/'credentials.json').write_text('cancelJob hidden')
   (r/'node_modules').mkdir();(r/'node_modules/x.js').write_text('cancelJob')
   result=m.call('search_project_context',{'root':d,'query':'cancelJob'})
   self.assertEqual([x['path'] for x in result['results']],['jobs.mjs'])
   (r/'jobs.mjs').write_text('export function retryJob() {}')
   self.assertEqual(m.call('search_project_context',{'root':d,'query':'cancelJob'})['results'],[])
class Checks(unittest.TestCase):
 def test_checks_and_failures(self):
  with tempfile.TemporaryDirectory() as d:
   r=pathlib.Path(d);(r/'verify.mjs').write_text("console.log('VERIFIED');")
   result=m.call('run_project_check',{'root':d,'kind':'node_file','path':'verify.mjs'})
   self.assertTrue(result['passed']);self.assertIn('VERIFIED',result['output'])
   m.call('read_project_file',{'root':d,'path':'verify.mjs'})
   self.assertTrue(m.call('run_project_check',{'kind':'node_file','path':'verify.mjs'})['passed'])
   (r/'verify.mjs').write_text("throw new Error('failure');")
   self.assertFalse(m.call('run_project_check',{'root':d,'kind':'node_file','path':'verify.mjs'})['passed'])
   (r/'verify.mjs').write_text('setInterval(()=>{},1000)')
   self.assertTrue(m.call('run_project_check',{'root':d,'kind':'node_file','path':'verify.mjs','timeout_seconds':1})['timeout'])
   with self.assertRaises(ValueError):m.call('run_project_check',{'root':d,'kind':'package_script','script':'evil; echo x'})
class Installer(unittest.TestCase):
 def test_restore_idempotence(self):
  from unittest.mock import patch
  import runpy,tomllib,contextlib,io
  with tempfile.TemporaryDirectory() as d:
   home=pathlib.Path(d); codex=home/'.codex';codex.mkdir()
   config=codex/'config.toml';config.write_text('model = "existing"\n[plugins."pdf@openai-primary-runtime"]\nenabled = true\n')
   with patch('pathlib.Path.home',return_value=home),patch('subprocess.run') as run,contextlib.redirect_stdout(io.StringIO()):
    runpy.run_path(str(pathlib.Path(__file__).with_name('install.py')))
    first=config.read_text()
    runpy.run_path(str(pathlib.Path(__file__).with_name('install.py')))
   parsed=tomllib.loads(config.read_text()); profile=tomllib.loads((codex/'local-dev.config.toml').read_text())
   self.assertEqual(first,config.read_text());self.assertEqual(parsed['model'],'existing')
   self.assertEqual(parsed['mcp_servers']['local-agent-files']['tools']['write_project_file']['approval_mode'],'approve')
   self.assertEqual(profile['model'],'local/gpt-oss:20b');self.assertFalse(profile['plugins']['pdf@openai-primary-runtime']['enabled'])
   self.assertTrue((codex/'skills/local-agent-development/SKILL.md').exists());self.assertEqual(run.call_count,2)
class Evaluation(unittest.TestCase):
 def test_oracles(self):
  import evaluate
  solutions={'filter':"export function filterJobs(j,q,s){return j.filter(x=>x.title.toLowerCase().includes(q.toLowerCase())&&(s==='all'||x.status===s));}", 'cancel':"export function cancelJob(j){return ['queued','running'].includes(j.status)?{...j,status:'cancelled'}:{...j};}", 'merge':"export function mergePoll(l,s){const ids=new Set(l.filter(x=>x.status==='cancelled').map(x=>x.id));return s.map(x=>ids.has(x.id)?{...x,status:'cancelled'}:{...x});}"}
  with tempfile.TemporaryDirectory() as d:
   r=pathlib.Path(d)
   for name,c in evaluate.CASES.items():
    (r/'verify.mjs').write_text("import assert from 'node:assert/strict';\nimport {"+c['symbol']+"} from './jobs.mjs';\n"+c['checks'])
    (r/'jobs.mjs').write_text(c['source']);self.assertNotEqual(subprocess.run(['node','verify.mjs'],cwd=r,capture_output=True).returncode,0)
    (r/'jobs.mjs').write_text(solutions[name]);self.assertEqual(subprocess.run(['node','verify.mjs'],cwd=r,capture_output=True).returncode,0)
if __name__=='__main__':unittest.main()
