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
python scripts/verify.py
```

If generated tables are stale, rebuild them:

```bash
python3 scripts/render_catalog.py
```

The verifier supports Python 3.10 through the current tested release on
Windows, macOS, and Linux. The scheduled freshness workflow also audits all
official HTTPS sources with bounded retries; if a network intercept is
required, provide its trusted PEM bundle with `scripts/audit_links.py --cafile`.

## Adding a tool, gateway, or model family

- Follow the corresponding JSON schema in `schema/`.
- Use a stable, lowercase, hyphenated `id`.
- Prefer `null` or a clearly worded `pricing_note` over a guessed value.
- Add at least one official source and, for pricing claims, a direct pricing
  source.
- Use the structured `platforms` dimensions and the controlled model modality
  and capability vocabularies. Explain inherited or non-applicable dimensions
  in `platforms.notes`.
- Keep strengths and limitations concrete. Avoid marketing superlatives.

## Pull requests

Keep each pull request focused. In the description, state:

- what changed;
- which official sources were checked;
- the verification date; and
- whether generated files were rebuilt.

By contributing, you agree that your contribution is provided under the
[0BSD license](LICENSE).
