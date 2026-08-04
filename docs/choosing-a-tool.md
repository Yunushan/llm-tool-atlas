# Choose a Tool by Workflow

Start with the surface where you want the agent to work, then choose the model
policy and control level. Do not start with a benchmark rank alone.

## Fast shortlist

| If you want… | Start by comparing… | Watch for… |
| --- | --- | --- |
| A terminal-native agent with deep repository work | Codex CLI, Claude Code, Gemini CLI, Qwen Code, OpenCode, Aider | Shell permissions, context cost, model lock-in |
| An all-in-one AI editor | Cursor, Devin Desktop/Windsurf, Qoder, Zed | Editor migration, subscription quotas, proprietary features |
| An agent inside existing VS Code | Codex, GitHub Copilot, Cline, Roo Code, Kilo Code, Continue | Extension trust, overlapping indexes, BYOK fees |
| Existing JetBrains workflow | GitHub Copilot, JetBrains AI Assistant, Continue, Tabnine | Feature parity with VS Code versions |
| Multiple model providers | OpenCode, Aider, Continue, Cline, Roo Code, Kilo Code plus a gateway | Provider-specific tool support and markup differences |
| Background work on issues or pull requests | Codex cloud, Copilot coding agent, Devin, Jules, Replit Agent | Sandbox, secrets, branch protection, review responsibility |
| Local or offline inference | Aider, Continue, OpenCode or Qwen Code with Ollama, LM Studio, llama.cpp, or LocalAI | Hardware, context size, tool-call reliability |
| One API for many providers | OpenRouter, LiteLLM, Portkey, Vercel AI Gateway | Routing policy, logging, markup, data residency, gateway fee |
| Enterprise governance | Native enterprise plans, Azure AI Foundry, Bedrock, Vertex AI, Portkey, LiteLLM Enterprise | SSO/RBAC tier, retention, region, audit export |

This is a discovery shortlist, not a ranking. Confirm current platform support
and pricing in the generated catalogs before buying.

## A practical decision sequence

1. **Choose the execution boundary.** Decide whether code may leave the device,
   whether commands may run, and whether a cloud sandbox is acceptable.
2. **Choose the interaction surface.** Terminal agents favor automation and
   composability; editor agents favor tight visual context and inline review;
   cloud agents favor parallel, asynchronous work.
3. **Choose the model policy.** A fixed model can be well-integrated. BYOK or a
   gateway improves choice, but adds configuration and sometimes weaker support
   for provider-specific features.
4. **Estimate your workload.** Compare subscription limits for interactive work
   and API prices for automation. Do not treat them as interchangeable.
5. **Run a representative trial.** Use one bug, one refactor, one test-writing
   task, and one code-review task from your real stack. Record elapsed time,
   human corrections, commands, and total cost.
6. **Set guardrails.** Add repository instructions, protected branches, secret
   scanning, approvals, and a review requirement before scaling usage.

## Suggested evaluation card

Score each candidate from 1–5 for your own workload:

| Dimension | Weight | Candidate score | Evidence |
| --- | ---: | ---: | --- |
| Task success on your repository | 30% |  |  |
| Reviewability and control | 20% |  |  |
| Total monthly cost | 15% |  |  |
| Model quality and choice | 15% |  |  |
| Interface fit | 10% |  |  |
| Privacy and administration | 10% |  |  |

Change the weights before testing, not after seeing the winner.
