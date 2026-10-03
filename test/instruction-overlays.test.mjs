import assert from "node:assert/strict";
import { test } from "node:test";

import {
  applyGrokFileToolsOverlay,
  applyInstructionOverlay,
  grokFileToolsOverlayFor,
} from "../src/instruction-overlays.mjs";
import { MODEL_BY_SLUG } from "../src/model-registry.mjs";

test("Grok 4.6 OAuth distinguishes local files from discovered MCP resources", () => {
  const model = MODEL_BY_SLUG.get("grok-oauth/grok-4.6");
  assert.equal(model?.instructionOverlay, "filesystem-mcp-discipline");

  const instructions = applyInstructionOverlay("Base instructions.", model.instructionOverlay);
  assert.match(instructions, /local filesystem paths as files, never as MCP resource URIs/i);
  assert.match(instructions, /server name and URI returned by MCP.*discovery/i);
  assert.match(instructions, /Never invent an MCP server name such as file/i);
  assert.match(instructions, /unknown server or invalid URI.*do not repeat/is);
  assert.match(instructions, /Keep using read_mcp_resource for valid resources/i);
});

test("Grok file-tool overlay is available without replacing the catalog MCP overlay", () => {
  const model = MODEL_BY_SLUG.get("grok-oauth/grok-4.6");
  assert.equal(model?.instructionOverlay, "filesystem-mcp-discipline");
  const gated = applyInstructionOverlay("Base instructions.", "grok-file-tools");
  assert.match(gated, /search_replace/);
  assert.match(gated, /read_file/);
  assert.match(gated, /run_terminal_command is only for processes/i);
  assert.match(gated, /Do not dump minified node_modules/i);
  assert.doesNotMatch(gated, /Create files with write/);
  assert.doesNotMatch(gated, /write is create-only/);
  const withWrite = applyInstructionOverlay("Base instructions.", "grok-file-tools-write");
  assert.match(withWrite, /Create files with write/);
  assert.match(withWrite, /write is create-only/);
});

test("file-tool overlay only names the installed façade tools", () => {
  const searchOnly = grokFileToolsOverlayFor(new Set(["search_replace"]));
  assert.match(searchOnly, /search_replace/);
  assert.doesNotMatch(searchOnly, /read_file/);
  assert.doesNotMatch(searchOnly, /run_terminal_command/);
  const applied = applyGrokFileToolsOverlay("Base.", new Set(["search_replace", "write"]));
  assert.match(applied, /Create files with write/);
  assert.doesNotMatch(applied, /read_file/);
});

test("GPT-OSS local memory overlay pins machine and model identity", () => {
  const instructions = applyInstructionOverlay("Base instructions.", "durable-local-memory-gpt-oss");
  assert.match(instructions, /M2 Ultra and 64 GB/i);
  assert.match(instructions, /gpt-oss:20b/i);
  assert.match(instructions, /qwen3-coder-next:q4_K_M/i);
  assert.match(instructions, /Never pass visible to Chrome or Edge/i);
  assert.match(instructions, /immediately retry once without visible/i);
  assert.match(instructions, /tab title, URL, or accessibility tree as proof/i);
  assert.match(instructions, /Hosted web_search is unavailable/i);
  assert.match(instructions, /createBrowserTab\("iab", url, \{ visible: false \}\)/i);
  assert.match(instructions, /Cite the source URLs you actually inspected/i);
  assert.match(instructions, /tool schema as authoritative/i);
  assert.match(instructions, /cmd as one shell-command string/i);
  assert.match(instructions, /omit justification during ordinary sandboxed work/i);
  assert.match(instructions, /approval policy is never or permissions are disabled/i);
  assert.match(instructions, /read the applicable AGENTS\.md/i);
  assert.match(instructions, /package\/build manifest before choosing commands/i);
  assert.match(instructions, /Do not guess pytest, npm, or another test runner/i);
  assert.match(instructions, /complete raw patch string/i);
  assert.match(instructions, /Do not use recursive directory dumps/i);
  assert.match(instructions, /Correct the arguments once/i);
  assert.match(instructions, /Preserve unrelated user changes/i);
  assert.match(instructions, /Separate observed facts from inference/i);
  assert.match(instructions, /Type stripping.*is not static type-checking/i);
  assert.match(instructions, /AGENTS\.md Remembered context/i);
});

test("GPT-OSS checks actual tools before denying website or chat capability", () => {
 const text=applyInstructionOverlay("Base.","durable-local-memory-gpt-oss");
 assert.match(text,/inspect the offered tools before answering/);
 assert.match(text,/limitation only if the needed tool is absent or an attempted call/);
 assert.match(text,/list_threads tool/);assert.match(text,/then read_thread/);
 assert.match(text,/Never message another chat without explicit user authorization/);
 assert.match(text,/before transmitting credentials/);
});
