# Contributing

Thanks for helping keep LLM Tool Atlas useful and current. Small, sourced
corrections are just as valuable as new catalog entries.

## Before opening a change

1. Use an official product page, documentation page, pricing page, model card,
   or upstream repository as the primary source.
2. Record the date you verified the claim in `last_verified` using
   `YYYY-MM-DD`.
3. Separate facts from judgments. Put sourced facts in the catalog and explain
   subjective tradeoffs in a comparison guide.
4. Do not convert subscription quotas into token counts unless the vendor
   publishes that conversion.
5. Do not add affiliate or referral links.

## Local checks

The project intentionally uses only the Python standard library:

```bash
python3 scripts/validate_catalog.py
python3 scripts/render_catalog.py --check
python3 -m unittest discover -s tests -v
```

If generated tables are stale, rebuild them:

```bash
python3 scripts/render_catalog.py
```

## Adding a tool, gateway, or model family

- Follow the corresponding JSON schema in `schema/`.
- Use a stable, lowercase, hyphenated `id`.
- Prefer `null` or a clearly worded `pricing_note` over a guessed value.
- Add at least one official source and, for pricing claims, a direct pricing
  source.
- Keep strengths and limitations concrete. Avoid marketing superlatives.

## Pull requests

Keep each pull request focused. In the description, state:

- what changed;
- which official sources were checked;
- the verification date; and
- whether generated files were rebuilt.

By contributing, you agree that your contribution is provided under the
[0BSD license](LICENSE).
