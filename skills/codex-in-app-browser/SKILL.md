---
name: codex-in-app-browser
description: Drive the Codex in-app browser through the unified Computer Use runtime. Use when a custom (non-OpenAI) model is asked to open, navigate, click, type, inspect, or capture a page in the Codex browser panel.
---

# Codex In-App Browser

The current Codex desktop runtime is exposed to custom models as
`mcp__cua_repl__js`. Do not use the retired `mcp__node_repl__js` tool or load a
separate browser runtime.

## First call

To open a visible in-app browser tab, make this the only API call in the first
tool invocation:

```js
let tab = await cua.createBrowserTab("iab", "https://example.com", { visible: true });
```

For an existing tab mentioned by the user, use the matching `cua.getTab(...)`
entry point instead. Read the documentation and initial page state returned by
the first call, then reuse the `tab` binding for navigation and interaction.

## Rules

- Use only APIs described by the tool or returned documentation.
- `open_in_codex` can display a browser tab but cannot interact with it; use
  `mcp__cua_repl__js` for interaction.
- Never start a side-channel driver or separate Node/REPL process.

## If the tool is missing

Stop and report that `mcp__cua_repl__js` is not in the tool list. Do not invent
another namespace and do not build a workaround.
