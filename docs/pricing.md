# Pricing Without the Marketing Fog

AI coding tools commonly sell access in four incompatible ways. Compare within
a price type first, then estimate a real workload.

## Subscription

A fixed monthly price is easy to budget, but the included usage may depend on
the selected model, task size, reasoning level, execution location, request
window, or “fast” versus “slow” pool. Published multipliers are not direct token
allowances unless the vendor explicitly says so.

## API tokens

API pricing usually separates input and output tokens. Agentic coding can resend
large repository context, generate reasoning tokens, call tools, and iterate
several times, so a single user-visible request may produce many model calls.

For a model with input price \(P_i\) and output price \(P_o\), a simplified
estimate is:

\[
\text{cost} = \frac{T_i}{1{,}000{,}000}P_i +
              \frac{T_o}{1{,}000{,}000}P_o
\]

Add cache writes, cache reads, search, sandbox, storage, and gateway fees when
they apply.

## Credits and request pools

Credits may represent tokens, model calls, agent steps, or compute time. Record
the vendor's native unit. A request to a frontier model and a request to a small
model may consume different numbers of credits.

## Pass-through gateways

A gateway may charge the upstream model price, a percentage fee, a platform
subscription, an observability fee, or a combination. BYOK can reduce prepaid
credit handling but does not always eliminate the gateway fee.

## Monthly workload template

Use your own logs where possible:

```text
interactive_developers = 3
active_days_per_developer = 18
agent_tasks_per_active_day = 12
average_input_tokens_per_task = 80,000
average_output_tokens_per_task = 12,000
cache_hit_rate = 40%
background_tasks_per_month = 60
```

Then compare at least three scenarios: normal, 2× context, and 3× retries. The
cheapest model per token is not necessarily the cheapest completed change.

## Rules used by this repository

- USD, excluding tax unless stated.
- Monthly and annual billing are not blended.
- Individual and team plans remain separate.
- “From” prices remain “from.”
- No unofficial token equivalent for subscriptions or credits.
- `null` is preferred to a guessed current price.

See the generated [tool catalog](generated/tools.md), [gateway catalog](generated/gateways.md),
and [model-family catalog](generated/models.md) for source-linked entries.
