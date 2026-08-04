# Model Families for Coding

The best model for an agent is not necessarily the highest-scoring model on a
single code-generation benchmark. Repository work also depends on instruction
following, tool schemas, long-context retrieval, patch precision, error
recovery, latency, caching, and the surrounding agent harness.

## Use families, not stale “latest model” prose

The canonical [model-family catalog](../generated/models.md) records current
representative models with a verification date and official source. It groups
fast-changing model IDs by family so an update does not require rewriting every
guide.

## Closed API versus open weights

| Dimension | Closed API models | Open-weight models |
| --- | --- | --- |
| Setup | Usually easiest | Runtime, model format, and hardware required |
| Frontier capability | Often first to market | Strong and improving, but workload-dependent |
| Data control | Contract and provider controls | Can remain fully in your environment |
| Unit economics | Per token/request/subscription | Hardware and operations |
| Version control | Vendor may update or retire IDs | You can pin weights and runtime |
| Customization | Prompting, tools, fine-tuning when offered | Quantization, fine-tuning, serving, and adapters |
| License | API terms | Model-specific license; “open weights” may not be OSI open source |

## Model-selection checklist

- Does the chosen agent officially support the model's API format?
- Are parallel tool calls, strict schemas, images, prompt caching, and reasoning
  controls preserved through your gateway?
- What is the effective context after the agent's system prompt, tools, and
  output allowance?
- Does the provider bill thinking tokens as output?
- Is cache creation more expensive than normal input, and what is the TTL?
- Are regional endpoints, zero-data-retention, or enterprise terms available?
- Can you pin a dated model ID and receive deprecation notice?
- For open weights, what are the commercial, redistribution, and acceptable-use
  terms of that exact checkpoint?

## A fair coding trial

Run each candidate through the same agent harness and permission policy. Use at
least one bug fix, refactor, test task, unfamiliar-code explanation, and review.
Track task success, regressions, tool errors, retries, elapsed time, input/cache/
output tokens, and the minutes a human spends correcting the result.

A cheaper model that needs three retries may cost more than a premium model that
finishes once. A premium model may also be wasteful for deterministic formatting,
classification, or small edits. Route by task rather than using one model for
everything.
