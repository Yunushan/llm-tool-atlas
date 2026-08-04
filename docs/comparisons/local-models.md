# Local Models and Self-Hosted Coding

“Local” has three different meanings:

- the agent edits and runs tools on your machine but calls a cloud model;
- the model server runs on hardware you control; or
- the entire stack, including indexes, logs, gateway, and model, is offline.

Only the last one is an air-gapped workflow.

## Building blocks

| Role | Options | What it provides |
| --- | --- | --- |
| Coding agent | Aider, Qwen Code, OpenCode, Cline, Kilo Code, Zed, OpenHands | Repository context, edits, commands, tests, and review |
| Desktop runtime | LM Studio, Jan | Model download, chat, and local compatible API |
| CLI/server runtime | Ollama, llama.cpp, LocalAI | Model serving and hardware backends |
| Team web UI | Open WebUI, AnythingLLM | Multi-user chat, RAG, tools, and administration |
| Self-hosted gateway | LiteLLM, Portkey, Helicone | Keys, policy, routing, budgets, and observability |

## Benefits

- Code and prompts can remain inside your network.
- There is no per-token model invoice after hardware cost.
- You control versions, quantization, retention, and availability.
- OpenAI-compatible endpoints work with many coding agents.

## Costs and constraints

- Hardware, power, cooling, storage, and engineering time replace API cost.
- Context windows and concurrent sessions consume significant RAM/VRAM.
- A model that writes good snippets may still perform poorly at tool calling,
  patch application, long-horizon planning, or error recovery.
- Quantization can reduce memory and also change quality.
- The operator owns authentication, TLS, rate limits, isolation, updates, and
  model-license compliance.

## Minimum evaluation

Test the exact model, quantization, runtime, context length, and agent together:

1. answer a repository architecture question;
2. implement a multi-file change with tests;
3. recover from a failing command;
4. review an intentionally vulnerable patch;
5. measure tokens per second, time to first token, peak memory, task success,
   and human correction time; and
6. repeat with concurrent users.

Do not compare a local model's zero token price with a cloud subscription while
ignoring hardware depreciation and operator time.
