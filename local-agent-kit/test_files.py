import unittest,tempfile,pathlib,importlib.util,json,subprocess,sys
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
  self.assertEqual(len(rows[1]['result']['tools']),2);self.assertTrue(rows[2]['result']['isError'])
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
if __name__=='__main__':unittest.main()
