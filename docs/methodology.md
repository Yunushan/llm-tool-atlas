# Methodology

LLM Tool Atlas compares products without pretending that one score can capture
every workflow. A terminal-first maintainer, a regulated enterprise, and a new
developer building a prototype have different definitions of “best.”

## Evidence hierarchy

Catalog claims should use sources in this order:

1. official documentation or pricing pages;
2. official model cards, release notes, or repositories;
3. official marketplace listings; and
4. a clearly labeled maintainer observation when the vendor publishes no answer.

Blog comparisons, social posts, referral pages, scraped pricing databases, and
search-result snippets are not accepted as the only evidence for a catalog fact.

Every record has a `last_verified` date. “Current” means verified on that date,
not guaranteed at the moment you read it.

## Facts, judgments, and unknowns

- **Facts** belong in `data/` and require official sources.
- **Judgments** belong in guides and must explain the workload or tradeoff.
- **Unknown or variable facts** are recorded as `null`, `varies`, or a short
  note. We would rather show an honest gap than manufacture precision.

No vendor pays for placement. The project uses no affiliate links.

## Pricing normalization

Prices are shown in USD and exclude taxes unless a source says otherwise.

| Price type | How it is represented |
| --- | --- |
| Individual subscription | Advertised monthly price; annual-only equivalents are labeled |
| Team subscription | Per user per month, with billing term noted |
| API | USD per one million tokens, separated into input, cached input, and output when published |
| Credit system | Original credit price and unit; no unofficial token conversion |
| Model pass-through | Provider price plus the gateway fee, if the fee is published |
| Enterprise | `Contact sales` unless a public price exists |

“Unlimited” is never interpreted as infinite. Fair-use rules, rate limits,
model multipliers, rolling windows, and regional availability may still apply.

## Comparison dimensions

The guides compare dimensions rather than produce a universal winner:

- interface fit: CLI, IDE extension, editor, desktop GUI, web, API, or CI;
- autonomy: completion, chat, multi-file editing, commands, tests, review, and
  background execution;
- model choice: fixed vendor, curated multi-model, BYOK, gateway, or local;
- control: permissions, sandboxing, approvals, checkpoints, and auditability;
- context: repository indexing, open files, retrieval, images, web, and MCP;
- deployment: managed cloud, local client, self-hosted service, or air-gapped;
- collaboration: shared rules, review, issues, pull requests, and admin controls;
- economics: subscription predictability, usage pricing, and high-volume value;
- openness: source license, open weights, exportability, and provider lock-in.

## Why there is no single 0–100 leaderboard

An overall score hides assumptions about budget, privacy, model preference, and
workflow. The atlas provides shortlists for scenarios and exposes the underlying
facts so readers can apply their own weights. Benchmark results may be linked in
future, but vendor benchmark claims will remain separate from independent,
reproducible results.

## Freshness policy

- Pricing and active-model claims should be rechecked at least every 90 days.
- Preview products and deprecation dates should be checked more frequently.
- A stale entry remains visible but is not silently presented as current.
- The validator flags future dates and malformed records; scheduled CI opens a
  report when records age past the configured threshold.

See [Contributing](../CONTRIBUTING.md) for the update workflow.
