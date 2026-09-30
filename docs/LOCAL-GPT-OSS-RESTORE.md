# Restore the local GPT-OSS Codex setup

This guide recreates the working local-model setup on another Apple-silicon Mac. The Git repository preserves the router changes and custom-model instructions. Ollama model weights, account credentials, and private Codex memory are intentionally not stored in GitHub.

## 1. Install prerequisites

Install:

- Codex desktop
- Git
- Node.js 22.19 or newer
- Python 3.10 or newer
- Ollama

## 2. Clone the saved fork and select the backup

```bash
mkdir -p ~/.local/share
git clone git@github.com:yohanceb-tech/codex-router.git ~/.local/share/codex-router
cd ~/.local/share/codex-router
git switch fix/gpt-oss-codex-integration-2026-09-30
```

For an immutable copy of the verified state, use the backup tag instead of the branch:

```bash
git switch --detach gpt-oss-codex-backup-2026-09-30
```

## 3. Install the router into Codex

Run the guided installer and select the Codex target. Hosted-provider credentials are optional when only local Ollama models are needed.

```bash
./install.sh --target codex --guided --with-tray
```

## 4. Install and expose GPT-OSS

```bash
./bin/control local-models install gpt-oss:20b --yes
./bin/control picker set 'local/gpt-oss:20b' show
./bin/model-router codex skills install
./bin/control service restart
```

If the model-fit safety check rejects the install on a machine where the model is known to fit, repeat the local-model command with `--force`.

## 5. Verify the restored setup

```bash
./bin/model-router codex doctor
./bin/control status
npm test -- --runInBand test/codex-custom-model-overlay.test.mjs test/codex-local-model-integration.test.mjs test/codex-native-responses.test.mjs
```

Open a fresh Codex chat, choose **GPT OSS · 20b (local)**, and test both a shell request and a Chrome request. Chrome and Edge calls must not include the `visible` option; that option belongs only to the in-app browser.

## 6. Restore private memory separately

The following files are deliberately excluded from the public fork because they can contain personal context:

- `~/.codex/AGENTS.md`
- `~/.codex/MEMORY.md`

Copy them privately from the old computer, or recreate them on the new computer. Never commit passwords, API keys, tokens, private keys, or provider credentials. Re-enter any provider credentials through the installer or Codex settings.

## What GitHub does and does not preserve

GitHub preserves the router source, fixes, documentation, commit history, branch, and immutable backup tag. It does not preserve installed Ollama weights, running services, local credentials, Codex application settings, or private memory files.
