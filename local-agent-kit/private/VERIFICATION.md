# Private mode verification — 2026-10-06

Machine: Apple-silicon Mac Studio M2 Ultra, 64 GB. Installed Codex CLI from ChatGPT.app, Python 3.14, Node 24.21, Ollama 0.34.2. Ollama was verified listening only on 127.0.0.1:11434 with local gpt-oss:20b and gemma4:latest present.

| Outcome | Status | Evidence |
| --- | --- | --- |
| Agent direct remote connections fail | Verified | Exact launcher sandbox denied a socket to 1.1.1.1:443 with EPERM, including a child Python process |
| Agent cannot bypass private adapter via shared router/Ollama | Verified | Exact sandbox denied 127.0.0.1:4202 and :11434; authorized private adapter health succeeded |
| Public research still works | Verified | Broker searched public web and read Python.org; actual GPT-OSS/Codex run searched official asyncio documentation, fetched the page and cited it |
| Known OpenAI web destinations fail before fetch | Verified | api.openai.com, chatgpt.com, trailing-dot/case/Unicode-dot variants rejected; redirect negative control proves second connection was not attempted |
| Private-network web proxying fails | Verified | IP-literal, nonstandard port and mixed public/private DNS results rejected; SSL connects to the validated address |
| Hosted inference/unknown endpoints fail | Verified | Hosted model slug and embeddings endpoint refused locally; fixed adapter only targets loopback Ollama |
| Screenshot reading stays local | Verified | Inline synthetic SABLE 731 image described by local Gemma, then read correctly by GPT-OSS |
| Compaction stays local and preserves a requirement | Verified | V1 and V2 local checkpoints replayed; subsequent GPT-OSS response retained required CEDAR 912 label |
| Project tools simplify arguments without removing revision checks | Verified | Stale write rejected after intervening edit; fresh read/write succeeds; traversal/absolute paths/root overrides rejected |
| Coding agent executes verification | Verified | Two complete real Codex private suites: filtering, cancellation and stale-poll merging all passed independent immutable tests and agent-run verification (6/6) |
| Cleanup | Verified | No gateway/broker process remained after normal test completion |
| Full independent browser/desktop task completion | Not applicable | Private CLI does not expose signed-in desktop/browser tools |
| All app/machine traffic never reaches OpenAI | Not claimed | Other running applications and public sites' downstream sharing are outside this process boundary |
| Windows/Linux enforcement | Not applicable | Launcher and installer refuse unsupported platforms |

The first coding run failed all three cases because the model mistyped roots and hashes and produced malformed calls. The project-bound facade removed those argument burdens while retaining server-side revision checks. Two subsequent suites passed: 13.8/9.7/14.0 seconds, then 11.7/9.0/43.8 seconds. The slow final case still required recovery. These are tiny synthetic cases, not production Weble integration or a general capability benchmark.

Earlier setup probes also exposed a compressed-page decoding problem, opaque local reasoning replay, and missing message type normalization during a compaction probe. Those were corrected; the final live privacy/model probe passed thirteen checks, including both compaction formats. Intermediate evidence is retained locally rather than concealed. No private project data was transmitted by these probes.

Automated verification after the final runtime changes: seven private boundary/facade tests, six existing local-kit tests, 61 namespace/compaction/runtime regressions, Python compilation, Node syntax checking, and npm run check passed. The existing multi-provider router source was not modified. Its failover state was explicitly disabled; analytics and feedback were disabled in the user config. No Windows or full provider/release matrix was run for this macOS-only add-on.

The guide describes the precise scope: direct model/telemetry egress is denied for private processes, while a constrained public-web broker may contact third-party search sites and pages. This is not an encrypted VM, a universal DLP system, a desktop-wide firewall or proof of GPT-5.6 parity.
