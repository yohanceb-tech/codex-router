# Private GPT-OSS + Codex on this Mac

Use `~/.local/bin/codex-private -C /absolute/project/path` in Terminal. The launcher uses the installed Codex CLI with GPT-OSS, independent of the signed-in desktop chat. For a simple launch, double-click `~/.local/share/codex-private/GPT-OSS Private.command`; it starts in Documents/Codex. Select the actual project with `-C` for project-bound tools.

This is an optional macOS-only private mode. It refuses to run without the tested macOS network sandbox. Ordinary Codex desktop chats are **not** covered by this mode. They can still use OpenAI services. This setup conversation itself used a hosted model.

## Privacy boundary

- Codex and its shell/MCP descendants can connect only to two per-session loopback ports. Direct public Internet, the shared model router, direct Ollama, Unix network sockets and Apple Events are blocked. Mach service lookup is denied except the two preferences services required by Codex. The exact private profile and this kit's checkout are protected against agent writes.
- A small inference adapter has a separate network restriction allowing only local Ollama. It accepts only GPT-OSS 20B. Inline images go to local Gemma4. It imports pure protocol helpers, never the multi-provider router or account discovery. No ChatGPT auth file, cloud key, inherited proxy, or desktop session is copied into the private environment.
- Hosted tools and unknown endpoints are refused. Conversation compaction uses local GPT-OSS and source-grounded local checkpoints. There is no fallback model, hosted summarizer, or encrypted-payload relay to OpenAI.
- A separate broker performs public HTTPS search/page reading. It has no conversation/inference endpoint and cannot execute scripts or upload files. It blocks known OpenAI-related domains, IP-literal/private-network destinations and credential-bearing URLs; it pins validated public DNS addresses and rechecks redirects. Search uses public DuckDuckGo HTML with Bing RSS as a fallback. Search sites receive the search terms and your public IP; visited sites receive the requested URL. Do not send private identifiers, code or secrets in queries. These checks are not a complete data-loss-prevention system, and third-party sites' own data-sharing practices remain outside this kit's control.
- The installer disables global Codex analytics and feedback submission, with a local config backup, and turns off the shared router's automatic model failover. That reduces exposure in ordinary sessions but does not make the signed-in desktop app offline.
- Private histories/state are in `~/.local/share/codex-private`, whose directory is owner-only. They are local plaintext, not separately encrypted. `exec --ephemeral` avoids normal session persistence for a run. Other applications running on the same Mac are outside this process boundary; this is not a separate VM or a machine-wide firewall.

The enforced claim is narrowly testable: the private agent and inference adapter cannot directly connect to remote model/telemetry services, and the web broker rejects known OpenAI destinations. This does not promise that all activity on the Mac is offline or that an arbitrary public website never shares data with a third party.

## Reliability and performance

The private file tools bind the project once at launch. Read, write, retrieve and check tools take relative paths; the server remembers read revisions and still rejects stale writes. This removes long path/hash transcription from the model's job. Existing path/symlink confinement and atomic-write checks remain in use. Shell commands retain the user's file privileges except protected paths, so this is primarily a network boundary, not a general project filesystem sandbox.

GPT-OSS uses medium reasoning, a 131K advertised window and a 100K compaction threshold. The adapter caches up to twelve local screenshot descriptions in memory for the session to avoid repeatedly asking Gemma about the same image. It supplies only focused local file/check and public research MCP tools. Agent instructions require actual verification and concrete failures. The CLI permits one transport retry, always to the same local adapter; there is no automatic switch to another model.

For difficult debugging, explicitly use `~/.local/bin/codex-private -C /path -c model_reasoning_effort='"high"'`. Medium is the installed profile default; this does not change another chat's thinking setting. A stronger local specialist can be evaluated separately later, but Qwen Coder Next's memory pressure on this 64 GB machine makes it a poor automatic fallback. Qwen Coder 30B remains experimental. Tests and narrow tasks currently provide more dependable safeguards than model voting.

The private CLI retains coding, code retrieval, local tests/builds, public research and local screenshot interpretation. It does not expose Codex's signed-in desktop/browser/chat/cloud tools. Shell network restrictions also prevent package downloads, remote Git operations and ordinary development-server listening. Install dependencies separately for a trusted project before entering private mode. Do not claim end-to-end website editing or GPT-5.6 parity from these tests.

## Install and restore

Prerequisites: the existing Codex app/CLI at the path in launch.py, Python 3.11+, Node 22.19+, ripgrep, macOS sandbox-exec, and Ollama on 127.0.0.1:11434 with gpt-oss:20b and gemma4:latest downloaded. No new package manager or model weight is installed by this kit.

From the verified repository checkpoint:

```sh
git checkout gpt-oss-private-agent-2026-10-06-r1
python3 local-agent-kit/private/install.py
~/.local/bin/codex-private --privacy-check
~/.local/bin/codex-private -C /absolute/project/path
```

The installer keeps the launcher pointing at the stable repository checkout. Keep that checkout available. It changes only its own launcher files, the two explicit analytics/feedback flags and router failover state. It never reads or uploads auth.json. Current managed launcher files are replaceable on rerun; an unrelated existing codex-private command is refused. Only one private session runs at a time, preventing config/port races. Each session owns and terminates its two services.

Verification commands:

```sh
python3 local-agent-kit/private/test_private.py
python3 local-agent-kit/test_files.py
~/.local/bin/codex-private --privacy-check
python3 local-agent-kit/evaluate.py --private --output /absolute/new/evaluation-directory
```

The optional `--privacy-check --model-check` also needs the synthetic vision-probe.png fixture in the private home; it exercises local compaction/continuation and Gemma image reading. No private project content is used in these probes.

For removal, delete only the managed ~/.local/bin/codex-private command and the private launch icon after closing the private session. Keep or remove private histories separately by choice. The main Codex config backup can restore prior preferences after checking for newer unrelated edits. Router failover can be explicitly re-enabled with the repository control command; doing so weakens ordinary local-route privacy but does not affect the private adapter, which contains no fallback route.

OpenAI's documented [analytics controls](https://learn.chatgpt.com/docs/config-file/config-advanced#metrics) and [custom model provider configuration](https://learn.chatgpt.com/docs/config-file/config-reference) inform the config. The concrete network guarantee comes from the tested macOS process restriction and fixed local adapter, not from a model instruction.
