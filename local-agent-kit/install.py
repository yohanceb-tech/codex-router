#!/usr/bin/env python3
"""Install the optional focused Codex profile and tools without replacing defaults."""
from pathlib import Path
import sys,shutil,tomllib,datetime,subprocess
kit=Path(__file__).resolve().parent
home=Path.home()/'.codex'; home.mkdir(exist_ok=True)
dest=home/'local-agent-kit'; dest.mkdir(exist_ok=True)
for name in ['server.py','instructions.md']: shutil.copy2(kit/name,dest/name)
skill=home/'skills/local-agent-development'; skill.mkdir(parents=True,exist_ok=True); shutil.copy2(kit/'SKILL.md',skill/'SKILL.md')
config=home/'config.toml'; text=config.read_text() if config.exists() else ''
begin='# BEGIN local-agent-kit-managed'; end='# END local-agent-kit-managed'
if begin in text: text=text[:text.index(begin)]+text[text.index(end)+len(end):]
import json
q=lambda v: json.dumps(str(v))
block=f'''{begin}
[mcp_servers.local-agent-files]
command = {q(sys.executable)}
args = [{q(dest/'server.py')}]
startup_timeout_sec = 20
[mcp_servers.local-agent-files.tools.read_project_file]
approval_mode = "approve"
[mcp_servers.local-agent-files.tools.write_project_file]
approval_mode = "approve"

model = "local/gpt-oss:20b"
model_provider = "codex-router"
model_reasoning_effort = "medium"
sandbox_mode = "workspace-write"
model_instructions_file = {q(dest/'instructions.md')}
[apps._default]
enabled = false
{end}
'''
parsed=tomllib.loads(text)
plugins=parsed.get('plugins',{})
extra=''
for name in plugins:
 if name.split('@')[0] in {'codex-app-tools','browser','unified-computer-use','chrome','computer-use'}: continue
 extra+=f'\n[plugins.{q(name)}]\nenabled = false\n'
block=block.replace(end,extra+'\n'+end)
mcp_block,profile_block=block.split('model = "local/gpt-oss:20b"',1)
new=text.rstrip()+'\n\n'+mcp_block+end+'\n'; tomllib.loads(new)
profile='model = "local/gpt-oss:20b"'+profile_block
profile=profile.replace(end,'')
tomllib.loads(profile)
profile_path=home/'local-dev.config.toml'
if profile_path.exists(): shutil.copy2(profile_path,profile_path.with_suffix('.toml.backup'))
profile_path.write_text(profile)
profile_path.chmod(0o600)
if config.exists(): shutil.copy2(config,config.with_name('config.toml.local-agent-kit-backup-'+datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
config.write_text(new); config.chmod(0o600)
subprocess.run(['node','--input-type=module','-e','import {setVisionBridgeLocal,setVisionBridgeEnabled} from "./src/vision-bridge-state.mjs";setVisionBridgeLocal({model:"gemma4:latest",baseUrl:"http://127.0.0.1:11434/v1"});setVisionBridgeEnabled(true);'],cwd=kit.parent,check=True)
print('Installed local-dev profile, file tools, development skill, and local Gemma vision setting. Restart Codex to discover new MCP tools; CLI: codex --profile local-dev')
