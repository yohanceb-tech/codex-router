---
name: local-agent-development
description: Build and verify local web applications with GPT-OSS in Codex, including reliable text edits, browser flow checks, and screenshot review.
---
Use the project manifest to choose its existing development, build, and test commands. Use read_project_file and write_project_file when offered; hash conflicts require a fresh read. Run syntax/build checks after edits and relevant behavior tests for changed flows.

For UI changes, read the applicable Codex computer-use skill and use the supplied unified CUA runtime. Start the project's documented local development server, retaining its session so it can be stopped afterward. Open the resulting local URL through a documented browser entry point. Use only returned API documentation to choose browser actions; do not install another browser driver.

Verify a concrete user flow: input, primary action, resulting state. Inspect console errors when the documented browser API provides them. Review desktop and a narrow/mobile layout using documented resize/emulation controls if available; otherwise report the mobile check as unverified. Check loading, empty, and error states relevant to the changed feature, visible labels, keyboard access, contrast, and content overflow. Capture and inspect screenshots for visual claims; GPT-OSS screenshots are interpreted by the configured local Gemma bridge. Fix observed problems and repeat only the affected checks. Report observed outcomes separately from untested expectations.

Keep a compact checkpoint in the project's existing notes convention when the task is long or compaction is near: changed files, commands/results, unresolved issue, next action. Never save credentials or screenshot contents as durable memory. Stop only development processes started for this task unless the user wants them left running.
