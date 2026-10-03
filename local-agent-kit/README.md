# GPT-OSS local development kit

This optional kit adds two dependency-free MCP text-file tools, a focused Codex CLI profile, and a browser verification skill. GPT-OSS stays the coder; Gemma reads screenshots locally. No hosted vision fallback is configured.

## Restore on another Mac

Prerequisites: Codex, Python 3.11+, Node.js 22.19+, Ollama, and the normal codex-router installation. This kit is an add-on, not a replacement for router installation or authentication. Follow the repository installation instructions to configure the router on the new machine; credentials must be recreated locally.

```sh
git clone --branch fix/gpt-oss-codex-integration-2026-09-30 https://github.com/yohanceb-tech/codex-router.git ~/.local/share/codex-router
cd ~/.local/share/codex-router
git checkout gpt-oss-action-discipline-2026-10-03
ollama pull gpt-oss:20b
ollama pull gemma4:latest
# Complete normal router installation and publish GPT-OSS using its local-model controls.
python3 local-agent-kit/install.py
python3 local-agent-kit/test_files.py
codex --profile local-dev
```

The installer regenerates paths for the current user, backs up config.toml, preserves unrelated settings, installs the skill and MCP server, and pins the existing router vision bridge to Gemma on localhost. Rerunning it replaces its managed block rather than duplicating tools. Restart the Codex desktop app yourself to discover the MCP tools and skill. The focused profile is selected with the CLI; it does not change the desktop app's global instructions or default model. Profiles use separate local-dev.config.toml files supported by current Codex.

## Behavior and limitations

read_project_file returns a bounded excerpt and full-file SHA-256. write_project_file requires that hash (or `missing` for a new file), rejects paths resolving outside the specified root, and atomically replaces text. The project root is supplied by the agent, not an OS sandbox: the MCP process runs with the user’s filesystem access and does not enforce the shell sandbox. The two local file tools are explicitly configured for automatic approval, matching the authorized local development workflow. Hash checks catch intervening changes before the write, not every possible concurrent writer racing the final replace. Run syntax/build/tests after writing; the tool does not understand every language. It preserves existing file permission bits but does not promise extended metadata preservation. File content should never contain secrets unless required by the authorized project task.

The development skill guides the existing unified CUA runtime through actual user-flow checks, desktop/mobile screenshot review, relevant error/empty/loading states, and compact checkpoints. It is guidance, not a new autonomous browser driver or guaranteed visual-quality scorer. Missing APIs or checks must be reported as unverified. The focused profile retains browser/app plugins and disables configured document/review plugins and ambient app connectors; it is less minimal than the prior coding-only benchmark because browser capabilities remain available.

No model weights, account credentials, caller secrets, conversations, or private project data belong in this backup. Download weights and authenticate again on restore. Python and Node executables must be on PATH; Codex computer use requires its supported desktop runtime.

To undo the kit, remove the marked local-agent-kit block from config.toml, local-dev.config.toml, ~/.codex/local-agent-kit, and ~/.codex/skills/local-agent-development; choose your previous vision engine separately. Existing timestamped config backups are private local files and are not uploaded.

## Project context and repeatable evaluations

search_project_context searches current source and documentation with ranked lexical matches. Pass the project's absolute root and concrete feature/symbol/error terms. Results include paths, line numbers, and bounded excerpts. No embedding service, model, network, or persistent index is needed. It respects rg ignore files and excludes common secret filenames, node_modules, and generated directories; it is not a comprehensive secret scanner. Explicit file reads still follow the existing tool contract. Read applicable AGENTS.md and manifests separately. It needs ripgrep on PATH.

Run the disposable Weble-style suite:

```sh
python3 local-agent-kit/evaluate.py --output /absolute/path/to/a/new/evaluation-run
# Or select one case:
python3 local-agent-kit/evaluate.py --case filter --output /absolute/path/to/another/new/run
```

The suite measures title/status filtering, terminal-state cancellation, and stale polling preserving cancellations while including new jobs. Each case starts broken and is checked independently with immutable tests. It records successful retrieval tool use, independent behavior checks, whether the agent actually ran tests, latency, timeout, and Codex exit status. An overall pass requires the agent to run verification as well as produce correct code. The router exact-route header prevents silently substituting another model. The profile must already be installed. Use a fresh output directory each time. Compare repeated runs before claiming accuracy or speed improvement. These are synthetic coding tasks, not live Weble browser, backend, or production integration coverage. Keep results outside the source repository; logs are local evidence and should not be uploaded without review.

The action-capability instructions require inspecting real offered tools before declaring browser/chat operations unavailable. `check_actions.py INSTRUCTIONS_FILE OUTPUT_DIRECTORY` performs a compact native-Ollama tool-selection check with mock tool definitions; it never logs in, edits a site, or messages chats. This check is not a substitute for an end-to-end desktop test.
