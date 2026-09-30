---
name: codex-computer-use
description: Control local apps and browsers through the unified Computer Use runtime inside the Codex app. Use when the session uses a custom (non-OpenAI) model and the user asks to operate Chrome, Edge, the in-app browser, or a desktop app. Prefer purpose-built connectors, APIs, or CLIs when they exist.
---

# Codex Computer Use

The current Codex desktop runtime is exposed to custom models as
`mcp__cua_repl__js`. Its persistent JavaScript environment already contains
the initialized `cua` API. Do not import `@oai/sky`, start a separate REPL, or
look for the retired `mcp__node_repl__js` tool.

## First call

The first invocation must contain exactly one documented entry-point call,
optionally assigning its result to a variable. Choose the entry point that
matches the request:

```js
await cua.getState();
```

```js
let app = await cua.getApp("Example App");
```

```js
let tab = await cua.createBrowserTab("chrome", "https://example.com", { sessionName: "Browser task" });
```

```js
let tab = await cua.createBrowserTab("iab", "https://example.com", { visible: true });
```

Read the documentation and initial UI state returned by that call before
continuing. Reuse the returned `app` or `tab` binding on later invocations.

## Rules

- Use Chrome when the user asks for Chrome. Use `iab` only when they ask for
  the Codex in-app browser or do not require an external browser.
- For Chrome or Edge, never pass `visible`. That capability belongs only to
  `iab`. The correct Chrome call is exactly
  `await cua.createBrowserTab("chrome", url, { sessionName: "Browser task" })`.
- A returned tab title, URL, or accessibility tree proves that the browser
  opened successfully. Do not report failure when that evidence is present.
- If a Chrome call fails with `Capability is not available: visibility`, retry
  once immediately with the `visible` option removed. Do not ask the user for
  permission to retry; opening the requested page was already authorized.
- Use only APIs described by the tool or returned documentation.
- Prefer purpose-built connectors, APIs, and CLIs over computer use when they
  exist.
- Never start a side-channel driver or a separate Node/REPL process.

## If the tool is missing

Stop and report that `mcp__cua_repl__js` is not in the tool list. Do not invent
longer names such as `mcp__codex_apps__cua_repl__js` and do not build a
workaround.
