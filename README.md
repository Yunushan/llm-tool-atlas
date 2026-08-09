<div align="center">

# LLM Tool Atlas

**A vendor-neutral, source-linked atlas of AI coding agents, LLMs, editors,
IDEs, CLIs, GUIs, gateways, local runtimes, pricing, capabilities, benefits,
and tradeoffs.**

[![validate](https://github.com/Yunushan/llm-tool-atlas/actions/workflows/validate.yml/badge.svg)](https://github.com/Yunushan/llm-tool-atlas/actions/workflows/validate.yml)
[![license: 0BSD](https://img.shields.io/badge/license-0BSD-blue.svg)](LICENSE)
[![catalog: 33 tools](https://img.shields.io/badge/catalog-33_tools-0ea5e9.svg)](docs/generated/tools.md)
[![gateways: 13](https://img.shields.io/badge/gateways-13-8b5cf6.svg)](docs/generated/gateways.md)
[![model families: 14](https://img.shields.io/badge/model_families-14-d946ef.svg)](docs/generated/models.md)
[![sources: official](https://img.shields.io/badge/sources-official_only-16a34a.svg)](docs/methodology.md)
[![verified: 2026-08-04](https://img.shields.io/badge/verified-2026--08--04-f59e0b.svg)](CHANGELOG.md)

**[Quick chooser](docs/choosing-a-tool.md) ·
[Coding agents](docs/comparisons/coding-agents.md) ·
[Model families](docs/generated/models.md) ·
[Gateways](docs/comparisons/gateways.md) ·
[Pricing](docs/pricing.md) ·
[Local AI](docs/comparisons/local-models.md) ·
[Security](docs/privacy-security.md) ·
[Contributing](CONTRIBUTING.md) ·
[Releasing](docs/releasing.md)**

</div>

LLM Tool Atlas is a maintainable comparison project for choosing an AI coding
stack without confusing a **model**, an **agent harness**, an **editor**, and a
**gateway**. It covers products such as OpenAI Codex, Claude Code, Cursor,
Qoder, Qwen Code, Gemini CLI, GitHub Copilot, OpenCode, Kilo Code, Aider,
OpenRouter, LiteLLM, local runtimes, and the model families behind them.

The atlas does not claim that one product is universally best, and it does not
pretend that every LLM release can remain current in one hand-written table.
Canonical JSON records, official-source links, verification dates, generated
tables, validation, and scheduled freshness checks make the scope broad without
making the comparison dishonest.

> [!IMPORTANT]
> Prices are USD before tax and were checked on the date shown in each record.
> Subscription quotas, API tokens, credits, and “unlimited” fair-use plans are
> different units and are never converted into one another without an official
> vendor conversion.

## Start with the workflow, not the logo

| Your priority | Compare first | Why |
| --- | --- | --- |
| Deep terminal agent with local and cloud work | **Codex**, **Claude Code**, **Gemini CLI** | Strong first-party harnesses with commands, repository context, and automation |
| Full AI-native editor | **Cursor**, **Qoder**, **Windsurf / Devin Desktop**, **Zed** | Completion, inline edits, agents, terminal, and diff review in one environment |
| Keep VS Code or JetBrains | **GitHub Copilot**, **Codex**, **Cline**, **Kilo Code**, **JetBrains AI Assistant** | Lower editor-migration cost and broad extension coverage |
| Bring any provider or local model | **Qwen Code**, **OpenCode**, **Aider**, **Cline**, **Kilo Code**, **Zed** | BYOK, gateway, OpenAI-compatible, Ollama, LM Studio, or llama.cpp paths |
| Background issue-to-PR work | **Codex cloud**, **Copilot coding agent**, **Devin**, **OpenHands**, **Replit Agent** | Managed or self-hosted sandboxes and asynchronous delegation |
| One API across many providers | **OpenRouter**, **LiteLLM**, **Portkey**, **Vercel AI Gateway** | Unified API, routing, fallback, policy, budgets, and observability |
| Fully local stack | **Aider/Qwen Code/OpenCode** + **Ollama/LM Studio/llama.cpp** | Code, prompts, inference, and logs can stay under your control |
| Enterprise cloud governance | **Bedrock**, **Vertex AI**, **Microsoft Foundry**, **Portkey**, **LiteLLM Enterprise** | Identity, audit, private networking, regions, policies, and support |

See the [six-step decision process](docs/choosing-a-tool.md) and test candidates
on your own repository before paying annually.

## Headline comparison

This compact view covers the names most people compare first. The full,
source-linked matrix is generated from [`data/tools.json`](data/tools.json).

| Product | Type | Model choice | Local tools | Cloud agent | Local inference | Open client | Current price shape* |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| **OpenAI Codex** | Desktop + web + CLI + IDE | OpenAI-first; API-compatible custom routes | Yes | Yes | Custom route | Yes | Free; Go $8; Plus $20; Pro from $100; API PAYG |
| **Claude Code** | CLI + IDE + desktop + web | Claude family | Yes | Yes | No | No | Pro $20; Max from $100; API/cloud PAYG |
| **Cursor** | AI editor + CLI + cloud | Curated multi-model + BYOK | Yes | Yes | No first-class path | No | Hobby free; Pro $20; higher tiers |
| **Qoder** | AI editor + JetBrains + CLI + cloud | Curated + selected BYOK | Yes | Yes | Feature-dependent custom endpoints | No | Free; Pro $20; Pro+ $60; Ultra $200 |
| **Qwen Code** | CLI + headless + server | Provider-agnostic | Yes | Not required | Yes | Yes | Client free; coding plan/API/local cost separate |
| **Gemini CLI** | CLI + IDE companion + CI | Gemini family | Yes | Related Google workflows | No | Yes | Personal quota free; API/Code Assist paid |
| **GitHub Copilot** | IDE + CLI + GitHub | Curated; CLI BYOK | Yes | Yes | CLI compatible endpoints | No | Free; Pro $10; Pro+ $39; Max $100 |
| **OpenCode** | CLI + desktop + web + IDE | Provider-agnostic | Yes | Optional | Yes | Yes | Core free; Go $10 after intro; Zen PAYG |
| **Kilo Code** | IDE + CLI + cloud | Provider-agnostic | Yes | Yes | Yes | Yes | Platform free; Pass $19; inference/compute separate |
| **Zed** | Native editor + agents | Hosted + BYOK + local + ACP | Yes | Limited | Yes | Yes | Editor/BYOK/local free; Pro $10 |
| **OpenRouter** | Model gateway, not an IDE | Hundreds of hosted models | N/A | N/A | No | No | Limited free models; PAYG list rate + platform fee |

\* Advertised entry prices checked 2026-08-04. Limits, annual billing, model
multipliers, overages, and enterprise terms differ. Follow each official pricing
link in the generated catalog.

## What is inside

| Area | Canonical data or guide | Questions it answers |
| --- | --- | --- |
| Coding tools | [Tool catalog](docs/generated/tools.md) | Interface, OS/editor support, execution, model policy, BYOK, openness, price, strengths, limitations |
| Models | [Model-family catalog](docs/generated/models.md) | Current representatives, controlled inputs/outputs, capabilities, access, open weights, context, API price, coding notes |
| Gateways | [Gateway catalog](docs/generated/gateways.md) | Marketplace vs gateway vs inference cloud, BYOK, self-hosting, fees, routing, observability |
| Direct comparisons | [Coding agents](docs/comparisons/coding-agents.md) | Codex vs Claude Code vs Cursor vs Qoder vs Qwen Code and provider-neutral alternatives |
| Local deployment | [Local models](docs/comparisons/local-models.md) | Agents, runtimes, hardware/operations tradeoffs, offline evaluation |
| Cost | [Pricing guide](docs/pricing.md) | Subscription vs token vs credit vs pass-through gateway economics |
| Governance | [Privacy and security](docs/privacy-security.md) | Permissions, retention, BYOK path, sandboxing, branch protection, review |
| Method | [Methodology](docs/methodology.md) | Sources, freshness, normalization, editorial boundaries, no fake universal score |

## Important status notes

- **Continue is legacy/archived.** Existing configurations may remain useful,
  but it is not ranked as an active choice for a new long-lived deployment.
- **Plandex is legacy.** Its self-hosted/local client remains available, while
  Plandex Cloud wound down and stopped accepting new users in October 2025.
- **Roo Code shut down on 2026-05-15.** The frozen source remains cataloged so
  readers do not mistake old recommendations for current advice.
- **Windsurf's standalone editor is now documented as Devin Desktop.** The atlas
  keeps both names in one entry while the brand transition remains visible.
- **Qwen Code's built-in Qwen OAuth free tier ended on 2026-04-15.** The
  Apache-2.0 client remains active with coding plans, BYOK providers, gateways,
  and local inference.

## Repository layout

| Path | Purpose |
| --- | --- |
| [`data/`](data/) | Human-editable canonical JSON catalogs |
| [`schema/`](schema/) | JSON Schemas for tools, gateways, and model families |
| [`docs/generated/`](docs/generated/) | Deterministic Markdown tables—do not edit by hand |
| [`docs/comparisons/`](docs/comparisons/) | Scenario-based editorial comparisons |
| [`scripts/validate_catalog.py`](scripts/validate_catalog.py) | Dependency-free structural, date, source, and uniqueness checks |
| [`scripts/render_catalog.py`](scripts/render_catalog.py) | Rebuilds or verifies generated tables |
| [`scripts/audit_links.py`](scripts/audit_links.py) | Bounded official-link audit with JSON report output |
| [`scripts/verify.py`](scripts/verify.py) | Cross-platform structural, generated-file, link, release, and test gate |
| [`.github/workflows/validate.yml`](.github/workflows/validate.yml) | CI, tests, generated-file drift, and scheduled freshness gate |

## Validate or extend the atlas

Only Python's standard library is required:

```bash
git clone https://github.com/Yunushan/llm-tool-atlas.git
cd llm-tool-atlas
python scripts/verify.py
```

After changing canonical data:

```bash
python scripts/verify.py
```

Corrections should include a direct official pricing page, documentation page,
model card, release note, or upstream repository plus the date checked. See
[Contributing](CONTRIBUTING.md).

## Principles

- **Vendor-neutral:** no sponsored ranks, referral codes, or affiliate links.
- **Source-linked:** every record points to official evidence.
- **Freshness-visible:** each record says when it was verified.
- **No fake precision:** unknown and incomparable values remain unknown.
- **Facts before scores:** readers can apply weights that match their workflow.
- **Broad but maintainable:** model families and structured data scale better
  than a claim to list every temporary preview ID.

## License and disclaimer

Repository code, canonical JSON data, schemas, and original documentation are released under the
[Zero-Clause BSD (0BSD) license](LICENSE). Product names and trademarks belong
to their respective owners. Linked third-party material and model weights keep
their own licenses and terms.

This project is independent and is not endorsed by OpenAI, Anthropic, Google,
GitHub, Alibaba, Cursor, Qoder, OpenRouter, or any other listed vendor. Prices,
limits, regions, models, and product names change quickly; verify the linked
official source before making a purchasing, security, or compliance decision.
