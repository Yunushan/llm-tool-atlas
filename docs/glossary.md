# Glossary

**Agent** — A system that lets a model plan, call tools, inspect results, and
iterate toward a goal.

**Agentic IDE/editor** — An editor with integrated multi-file changes, commands,
tests, or background agents beyond inline completion.

**BYOK** — Bring your own key. The user supplies credentials for a model
provider or gateway; routing and fees still vary by tool.

**CLI agent** — A terminal interface that can reason over a repository and
usually edit files or run commands.

**Cloud/background agent** — An agent working asynchronously in a managed
sandbox, often producing a branch or pull request.

**Context window** — The maximum token budget a model can consider in one
request, including input and generated output under provider-specific rules.

**Gateway/router** — A layer offering one API across providers, often adding
fallbacks, policies, cost controls, caching, or observability.

**Hosted model** — Model inference run by a vendor or cloud service.

**Local runtime** — Software that runs model weights on hardware you control.

**MCP** — Model Context Protocol, a protocol for connecting compatible agents
to tools and data sources.

**Open source** — Software source code under an OSI-approved or otherwise
specified source license. This does not imply that the model weights are open.

**Open weights** — Downloadable model parameters. Usage rights depend on the
model's specific license and may not meet every definition of open source.

**Reasoning tokens** — Internal or visible tokens used by some models to work
through a problem; billing and visibility differ by provider.

**Reranker/router policy** — Logic that chooses a model based on quality, cost,
latency, availability, or metadata.

**RAG** — Retrieval-augmented generation: selecting relevant external content
and adding it to the model input.

**Tool call** — Structured model output asking an agent runtime to perform an
operation such as reading a file, running a command, or searching documentation.
