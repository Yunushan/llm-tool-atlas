# Gateways, Routers, and Inference Platforms

These products are often grouped together, but they solve different problems.

| Layer | What it does | Representative options |
| --- | --- | --- |
| Model marketplace | One API and account for many upstream providers/models | OpenRouter, Hugging Face Inference Providers |
| Managed AI gateway | Policies, routing, logging, and budgets in a hosted control plane | Vercel AI Gateway, Cloudflare AI Gateway, Portkey, Helicone |
| Self-hostable gateway | Provider-neutral proxy operated in your environment | LiteLLM, Portkey Gateway, Helicone |
| Inference cloud | Hosts mostly open/custom models on optimized hardware | Together AI, Fireworks AI, GroqCloud |
| Hyperscaler model platform | Governed catalog, private networking, identity, and regional deployment | Amazon Bedrock, Google Vertex AI, Microsoft Foundry |

## Quick comparison

| Need | Strong starting candidates | Main tradeoff |
| --- | --- | --- |
| Maximum ready-to-use model breadth | OpenRouter | Hosted control plane and platform/credit fee |
| AI SDK and Vercel integration | Vercel AI Gateway | Best value is inside the Vercel ecosystem |
| Self-hosted OpenAI-compatible routing | LiteLLM | You operate data plane, database, cache, scaling, and upgrades |
| Gateway plus governance suite | Portkey | Advanced managed controls are paid |
| Observability-first proxy | Helicone | Retention and compliance are tiered |
| Hub-to-inference discovery | Hugging Face Inference Providers | Less routing-policy depth |
| Fast/open-model inference | Together AI, Fireworks AI, GroqCloud | Not neutral third-party-key gateways |
| AWS governance | Bedrock | Region/model matrix and AWS lock-in |
| GCP and Gemini | Vertex AI | GCP-specific auth and deployment model |
| Azure enterprise controls | Microsoft Foundry | Complex region, quota, and deployment pricing |

## Fee patterns to check

A “single API” may use any combination of:

- upstream model list price;
- a percentage added when credits are purchased;
- a fee after a BYOK allowance;
- monthly platform or observability subscription;
- request overage;
- log storage and retention;
- dedicated deployment or GPU-hour cost; and
- regional, priority, batch, cache, or data-residency multipliers.

OpenRouter currently publishes a platform fee on PAYG credits. Vercel says its
gateway has no token markup. LiteLLM's open-source proxy does not impose a token
fee, but you pay to operate it. Those statements are not equivalent cost models.

## Architecture questions

Before adopting a gateway, answer:

1. Does prompt content pass through the gateway, or only credentials/metadata?
2. Can request and response bodies be disabled in logs?
3. Which region stores logs, prompts, traces, and keys?
4. Does BYOK still incur a gateway fee?
5. Are provider-specific Responses, Messages, caching, images, reasoning, and
   tool-call features preserved?
6. How are retries billed, and can fallback cross a data-policy boundary?
7. What happens when the gateway is unavailable?
8. Can applications export usage, traces, prompts, and routing configuration?

See the source-linked [generated gateway catalog](../generated/gateways.md) for
the full set of entries.
