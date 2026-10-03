"""Structured project verification; argv only, bounded time/output, no shell string."""
import pathlib,subprocess,os,signal,json,time

def check(root,kind,path=None,script=None,timeout=90):
 r=pathlib.Path(root)
 if not r.is_absolute() or not r.is_dir():raise ValueError('root must be an absolute directory')
 r=r.resolve()
 if kind in ('node_file','node_test','node_syntax'):
  if not path:raise ValueError('path required')
  p=(r/path).resolve(strict=True)
  if not p.is_relative_to(r) or not p.is_file():raise ValueError('path escapes project or is not a file')
  argv=['node']+({'node_file':[],'node_test':['--test'],'node_syntax':['--check']}[kind])+[str(p)]
 elif kind=='package_script':
  if script not in ('test','build','typecheck','lint'):raise ValueError('script must be test/build/typecheck/lint')
  manifest=json.loads((r/'package.json').read_text())
  if script not in manifest.get('scripts',{}):raise ValueError('script absent from package.json')
  argv=['npm','run',script]
 else:raise ValueError('unsupported check kind')
 start=time.monotonic();timed=False
 with __import__('tempfile').TemporaryFile() as capture:
  proc=subprocess.Popen(argv,cwd=r,stdout=capture,stderr=subprocess.STDOUT,start_new_session=True)
  try:proc.wait(timeout=max(1,min(120,timeout)))
  except subprocess.TimeoutExpired:
   timed=True;os.killpg(proc.pid,signal.SIGKILL);proc.wait()
  capture.seek(0,2);size=capture.tell();capture.seek(max(0,size-16000));output=capture.read().decode(errors='replace')
 return {'argv':argv,'exit_code':proc.returncode,'timeout':timed,'seconds':round(time.monotonic()-start,2),'output':output,'truncated':size>16000,'passed':proc.returncode==0 and not timed}
