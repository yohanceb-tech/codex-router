#!/usr/bin/env python3
"""Install the optional private launcher; no credentials or model weights copied."""
from pathlib import Path
import datetime,json,os,shutil,subprocess,sys,tomllib,re
if sys.platform!='darwin':raise SystemExit('Private mode is verified for macOS only; refusing installation')
HERE=Path(__file__).resolve().parent
repo=HERE.parent.parent
root=Path.home()/'.local/share/codex-private';root.mkdir(parents=True,exist_ok=True);root.chmod(0o700)
bin_dir=Path.home()/'.local/bin';bin_dir.mkdir(parents=True,exist_ok=True)
launcher=bin_dir/'codex-private'
import shlex
text='#!/bin/sh\nexec '+shlex.quote(sys.executable)+' '+shlex.quote(str(HERE/'launch.py'))+' "$@"\n'
if launcher.exists() and 'local-agent-kit/private/launch.py' not in launcher.read_text():raise SystemExit('Existing codex-private command is not managed by this kit; refusing to overwrite')
launcher.write_text(text);launcher.chmod(0o700)
command=root/'GPT-OSS Private.command'
command.write_text('#!/bin/sh\ncd '+shlex.quote(str(Path.home()/'Documents/Codex'))+' || exit 1\nexec '+shlex.quote(str(launcher))+' --no-alt-screen\n');command.chmod(0o700)
# Global defense in depth. The strict boundary remains the private launcher.
config=Path.home()/'.codex/config.toml';original=config.read_text();s=original;a=tomllib.loads(s)
for name in ('analytics','feedback'):
    if name not in a:s+='\n['+name+']\nenabled = false\n'
    else:
        m=re.search(r'(?ms)^\['+name+r'\]\s*\n(.*?)(?=^\[|\Z)',s)
        if not m:raise SystemExit('Unexpected config table syntax; refusing to rewrite')
        b=m[1]
        b=re.sub(r'(?m)^enabled\s*=.*$','enabled = false',b) if re.search(r'(?m)^enabled\s*=',b) else 'enabled = false\n'+b
        s=s[:m.start(1)]+b+s[m.end(1):]
tomllib.loads(s)
if s!=original:
    backup=config.with_name('config.toml.private-backup-'+datetime.datetime.now().strftime('%Y%m%d%H%M%S'));shutil.copy2(config,backup);backup.chmod(0o600)
    config.write_text(s);config.chmod(0o600)
subprocess.run(['node','--input-type=module','-e','import {setFailoverEnabled} from "./src/model-failover.mjs";setFailoverEnabled(false);'],cwd=repo,check=True)
print('Installed '+str(launcher))
print('Private launch icon: '+str(command))
print('Router failover, Codex analytics and feedback disabled. Ordinary desktop chats are not the private mode.')
