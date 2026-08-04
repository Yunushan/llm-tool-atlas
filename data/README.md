# Catalog Data

These JSON files are the canonical source for generated comparison tables.

| File | Contents | Schema |
| --- | --- | --- |
| `tools.json` | Coding agents, editors, extensions, GUIs, and local runtimes | [`tool.schema.json`](../schema/tool.schema.json) |
| `gateways.json` | Gateways, routers, inference clouds, and model platforms | [`gateway.schema.json`](../schema/gateway.schema.json) |
| `models.json` | Coding-relevant model families and representative pricing | [`model-family.schema.json`](../schema/model-family.schema.json) |

## Conventions

- IDs are stable, lowercase, and hyphenated.
- Dates use ISO `YYYY-MM-DD`.
- URLs point to official sources only.
- Prices are USD before tax unless the source says otherwise.
- `starting_price_usd_month` is the lowest current paid individual subscription,
  not an estimate of total monthly cost.
- `null` means unknown, variable, or not directly comparable.
- A free client with paid inference has `free_tier: true` and a pricing note that
  separates client cost from model cost.
- Model `api_pricing` is one representative first-party API rate, not a promise
  that every context tier, cache mode, region, or host costs the same.
- `open_source` describes the software client or gateway. Model weights are
  separately represented by `open_weights`.

Run validation and rebuild generated tables after every data change:

```bash
python3 scripts/validate_catalog.py
python3 scripts/render_catalog.py
python3 -m unittest discover -s tests -v
```
