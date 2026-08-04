# Coding Agents: Practical Comparison

This page compares the products most often treated as direct substitutes. It
uses the product state verified on 2026-08-04; consult the generated catalog and
official links before purchase.

## Core matrix

| Tool | Primary surface | Model policy | Local tools | Managed cloud work | Local-model path | Client source | Advertised entry point* |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenAI Codex | Desktop, web, CLI, IDE | OpenAI-first; API-compatible custom paths exist | Yes | Yes | Custom provider path, not the first-party subscription path | Apache-2.0 client | Free; Go $8; Plus $20; Pro from $100 |
| Claude Code | CLI, IDE, desktop, web | Claude family | Yes | Yes | No offline inference | Proprietary | Pro $20; Max from $100; API/cloud billing |
| Cursor | Standalone editor, CLI, cloud | Curated multi-model | Yes | Yes | No first-class local inference | Proprietary | Hobby free; Pro $20 |
| Qoder | Editor, JetBrains, CLI, SDK, cloud | Curated plus selected BYOK | Yes | Yes | Custom compatible endpoints depend on feature | Proprietary | Free; Pro $20; Pro+ $60; Ultra $200 |
| Qwen Code | CLI/headless/server | Provider-agnostic | Yes | No required managed agent | Yes: Ollama, vLLM, LM Studio | Apache-2.0 | Client free; inference/plan separate |
| Gemini CLI | CLI, IDE companion, CI | Gemini family | Yes | Limited related cloud workflows | No | Apache-2.0 | Personal quota free; API/Code Assist paid |
| GitHub Copilot | Many IDEs, CLI, GitHub | Curated multi-model; CLI BYOK | Yes | Yes | CLI supports compatible local endpoints | Proprietary | Free; Pro $10; Pro+ $39; Max $100 |
| Windsurf / Devin Desktop | Standalone editor, plugins, CLI, cloud | Curated multi-model | Yes | Yes | No general local-model path | Proprietary | Free; Pro $20; Max $200 |
| Cline | VS Code family, JetBrains, CLI | Provider-agnostic | Yes | Automation available | Yes | Apache-2.0 | Core free; ClinePass $9.99; inference separate |
| Kilo Code | IDE, CLI, cloud, review | Provider-agnostic | Yes | Yes | Yes | MIT | Platform free; Pass $19; inference/compute separate |
| OpenCode | CLI, desktop, web, IDE, CI | Provider-agnostic | Yes | Optional | Yes | MIT | Core free; Go $10 after intro; Zen PAYG |
| Aider | CLI | Provider-agnostic | Yes | No | Yes | Apache-2.0 | Client free; inference separate |
| Zed | Native editor | Provider-agnostic | Yes | Agent threads, not a full remote IDE | Yes | GPL-3.0-or-later | Editor/BYOK/local free; Pro $10 |

\* USD/month before tax unless noted. “Free” can include request or model
restrictions. Subscription quotas are not token equivalents.

## Where each approach is strongest

### Deep, integrated first-party agents

Codex and Claude Code give their model vendors control of both model behavior
and the agent harness. That integration can improve tool use, permissions,
context handling, and feature rollout. The tradeoff is model lock-in and a
usage pool that is harder to compare with raw API prices.

### AI-native editors

Cursor, Qoder, Windsurf/Devin Desktop, and Zed minimize context switching. They
can combine completions, inline edits, multi-file agents, terminal access, and
visual diff review. The migration cost is real: extensions, settings, keymaps,
remote-development workflows, and enterprise policy may differ from an existing
VS Code or JetBrains setup.

### Provider-neutral agents

Qwen Code, OpenCode, Aider, Cline, Kilo Code, and Zed let you route among hosted
providers, gateways, and local runtimes. This improves portability and cost
experimentation, but “supports model X” does not guarantee identical tool use,
prompt caching, images, context limits, or reasoning controls.

### GitHub-centered teams

Copilot has the broadest native GitHub workflow: completion, chat, local agent,
CLI, pull-request review, issues, and a cloud coding agent. Codex, Devin,
OpenHands, and other agents also integrate with GitHub, but their control plane
and review flow differ.

## Important 2026 status notes

- Continue is a **legacy/archived** project after its team joined Cursor. It is
  useful for existing configurations, not a default recommendation for a new
  long-lived deployment.
- Roo Code **shut down on 2026-05-15**. Its source remains available, but new
  users should choose a maintained successor.
- Official Windsurf documentation now uses **Devin Desktop** for the standalone
  editor while Windsurf pricing and plugin names remain visible. Treat them as
  one transitional product family.
- Qwen Code remains an active Apache-2.0 client, but the built-in **Qwen OAuth
  free tier ended on 2026-04-15**. Use a paid coding plan, provider key, gateway,
  or local model.

## Bottom line by persona

- Choose **Codex** when you want the broadest first-party local/cloud workflow
  and complex end-to-end coding with OpenAI models.
- Choose **Claude Code** when Claude quality and a mature terminal agent matter
  more than model choice.
- Choose **Cursor or Qoder** when an integrated editor is the product you want,
  not merely an extension.
- Choose **GitHub Copilot** when GitHub and multi-editor integration outweigh
  having the deepest standalone agent harness.
- Choose **Qwen Code, OpenCode, Aider, Cline, Kilo Code, or Zed** when BYOK,
  gateways, or local inference are requirements.

These are starting points. Use the test card in [Choose a tool](../choosing-a-tool.md)
on your own repository before committing to a yearly plan.
