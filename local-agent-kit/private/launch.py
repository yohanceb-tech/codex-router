#!/usr/bin/env python3
"""macOS private Codex launcher with inherited network restrictions."""
import fcntl,json,os,secrets,shutil,signal,subprocess,sys,tempfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path.home()/'.local/share/codex-private'
CODEX='/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'

def policy(ports,protect=()):
    q=lambda s:json.dumps(str(s))
    return '\n'.join(['(version 1)','(allow default)','(deny network*)','(deny appleevent-send)',
        '(deny mach-lookup)', '(allow mach-lookup (global-name "com.apple.cfprefsd.agent") (global-name "com.apple.cfprefsd.daemon"))']+
        [f'(allow network-outbound (remote tcp "localhost:{int(p)}"))' for p in ports]+
        [f'(deny file-write* (subpath {q(p)}))' for p in protect])

def wait_port(path,proc):
    for _ in range(100):
        if path.exists():return json.loads(path.read_text())['port']
        if proc.poll() is not None:raise RuntimeError('Private service failed to start; inspect local service log')
        time.sleep(.05)
    raise RuntimeError('Private service startup timed out')

def config(inference_port):
    q=lambda s:json.dumps(str(s))
    return f'''model = "gpt-oss:20b"
model_provider = "private-ollama"
model_reasoning_effort = "medium"
model_context_window = 131072
model_auto_compact_token_limit = 100000
model_instructions_file = {q(HERE/'instructions.md')}
approval_policy = "never"
sandbox_mode = "danger-full-access"
web_search = "disabled"
cli_auth_credentials_store = "file"
check_for_update_on_startup = false
[model_providers.private-ollama]
name = "Private local GPT-OSS"
base_url = "http://127.0.0.1:{inference_port}/v1"
wire_api = "responses"
env_key = "PRIVATE_AGENT_TOKEN"
requires_openai_auth = false
request_max_retries = 1
stream_max_retries = 1
stream_idle_timeout_ms = 300000
[analytics]
enabled = false
[feedback]
enabled = false
[otel]
exporter = "none"
log_user_prompt = false
[features]
apps = false
plugins = false
remote_plugin = false
daemon_auto_start = false
skill_search = false
skill_mcp_dependency_install = false
skip_host_skill_discovery = true
[apps._default]
enabled = false
[mcp_servers.files]
command = {q(sys.executable)}
args = [{q(HERE/'files_mcp.py')}]
env_vars = ["PRIVATE_PROJECT_ROOT"]
[mcp_servers.files.tools.write_project_file]
approval_mode = "approve"
[mcp_servers.files.tools.run_project_check]
approval_mode = "approve"
[mcp_servers.web]
command = {q(sys.executable)}
args = [{q(HERE/'web_mcp.py')}]
env_vars = ["PRIVATE_AGENT_TOKEN", "PRIVATE_WEB_PORT"]
'''

def main():
    if sys.platform!='darwin' or not Path('/usr/bin/sandbox-exec').exists():raise SystemExit('Private mode requires verified macOS sandbox-exec; refusing an unprotected launch')
    if not Path(CODEX).exists():raise SystemExit('Codex executable missing; update the launcher after verifying the installed path')
    ROOT.mkdir(parents=True,exist_ok=True);ROOT.chmod(0o700)
    lock=open(ROOT/'launch.lock','w')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit('Another private Codex session is active; close it before starting another')
    # No inherited cloud keys, proxy variables, router auth, or desktop session.
    env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','USER','LOGNAME','SHELL','TERM','LANG','LC_ALL','TMPDIR')}
    env['CODEX_HOME']=str(ROOT);env['PRIVATE_AGENT_TOKEN']=secrets.token_hex(32)
    env['NO_PROXY']='*';env['DO_NOT_TRACK']='1';env['OTEL_SDK_DISABLED']='true'
    signal.signal(signal.SIGTERM,lambda *_:sys.exit(143))
    processes=[]
    try:
        with tempfile.TemporaryDirectory(prefix='run-',dir=ROOT) as run:
            run=Path(run);log=open(ROOT/'last-services.log','w');os.chmod(ROOT/'last-services.log',0o600)
            node=shutil.which('node')
            if not node:raise RuntimeError('Node is required')
            # Inference adapter itself can connect only to Ollama. It cannot reach cloud providers.
            gateway=subprocess.Popen(['/usr/bin/sandbox-exec','-p',policy([11434])+'\n(allow network-bind (local tcp "localhost:*"))\n(allow network-inbound (local tcp "localhost:*"))',node,str(HERE/'gateway.mjs'),str(run/'gateway.json')],env=env,stdout=log,stderr=log)
            processes.append(gateway);inference=wait_port(run/'gateway.json',gateway)
            broker=subprocess.Popen([sys.executable,str(HERE/'broker.py'),str(run/'web.json')],env=env,stdout=log,stderr=log)
            processes.append(broker);web=wait_port(run/'web.json',broker)
            env['PRIVATE_WEB_PORT']=str(web)
            (ROOT/'config.toml').write_text(config(inference));(ROOT/'config.toml').chmod(0o600)
            # No cloud auth file is copied. A previous accidental login is refused.
            if (ROOT/'auth.json').exists():raise RuntimeError('Unexpected auth.json in private home; review it before continuing')
            protected=[HERE.parent.parent,ROOT/'config.toml',ROOT/'AGENTS.md',Path.home()/'.codex']
            sandbox=['/usr/bin/sandbox-exec','-p',policy([inference,web],protected)]
            args=sys.argv[1:]
            project=Path.cwd()
            for i,arg in enumerate(args):
                if arg in ('-C','--cd') and i+1<len(args):project=Path(args[i+1]).expanduser().resolve(strict=True)
                elif arg.startswith('--cd='):project=Path(arg.split('=',1)[1]).expanduser().resolve(strict=True)
            env['PRIVATE_PROJECT_ROOT']=str(project)
            if args[:1]==['--privacy-check']:
                check=HERE/'probe.py'
                return subprocess.call(sandbox+[sys.executable,str(check),str(inference),str(web),*args[1:]],env=env)
            if args and args[0] in ('login','app','cloud','remote-control','app-server','mcp','plugin'):
                raise RuntimeError('This operation is disabled in private mode')
            print('Private GPT-OSS: local inference, no model fallback, shell network blocked; public web tools available.',file=sys.stderr)
            return subprocess.call(sandbox+[CODEX,'--no-daemon',*args],env=env)
    finally:
        for p in processes:
            if p.poll() is None:p.terminate()
        for p in processes:
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:p.kill();p.wait()
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
