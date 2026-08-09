# Production-readiness assessment

This is an operational score for the repository and its release process. It is
not a ranking of the AI products in the catalog.

## Rubric

| Dimension | Weight | Initial score | Closure evidence |
| --- | ---: | ---: | --- |
| Code quality and tests | 35 | 22 | Strict full-file validation, complete schemas, generated-file drift checks, Markdown/local-link tests, release tests, and the cross-platform `catalog` gate |
| Security and supply chain | 25 | 15 | Safe URL/link handling, least-privilege pinned workflows, Dependabot, secret scanning/push protection, CodeQL, protected branches/tags, and private vulnerability reporting |
| Release and operations | 40 | 19 | Reproducible archives/checksums, version consistency, freshness/link-audit artifacts, rollback runbook, observed matrix, immutable releases, and a published reviewed tag |
| **Total** | **100** | **56** | All hosted controls and evidence must be present, not merely documented |

The initial score was fixed at 56/100 from the independent repository audit on
2026-08-04. The local hardening work is intended to close the code, catalog, and
release-process gaps; a final 100/100 score is not honest until the hosted
GitHub controls and at least one observed release are enabled and verified.

## Current worktree score

As of 2026-08-09, the uncommitted worktree earns a **91/100 local candidate
score**: code quality and tests **35/35**, security and supply chain **21/25**,
and release and operations **35/40**. The live default branch remains at the
previous **56/100** until this work is reviewed and published. The nine-point
gap is deliberately reserved for hosted settings and observed evidence rather
than inferred from local YAML: protected `main` and `v*` refs, GitHub security
settings, a passing hosted matrix/CodeQL/freshness run, and a published
attested release.

## Local closure checklist

- `python scripts/verify.py` passes on the supported Python versions.
- `python scripts/render_catalog.py --check` proves generated tables match the
  canonical JSON.
- `python -B -m unittest discover -s tests -v` covers validator, URL/SSRF
  boundaries, Markdown/link parsing, rendering, and deterministic releases.
- `python -B -m ruff check scripts tests` and
  `python -B -m mypy --strict scripts tests` provide clean lint and strict
  type-check gates for both production code and tests.
- `git diff --check` and workflow linting pass.
- `python scripts/build_release.py --tag vX.Y.Z` produces byte-identical
  archives and a manifest/checksum set on repeated builds.
- The weekly freshness workflow retains a JSON official-link audit and fails on
  terminal link failures.

## Hosted closure checklist

An administrator must complete and record these checks on the canonical GitHub
repository:

1. Protect `main` with pull requests, required `catalog`, no force-push or
   deletion, and an explicit review policy.
2. Protect `v*` tags from deletion and updates; require the reviewed release
   workflow and keep immutable releases enabled.
3. Enable private vulnerability reporting, vulnerability alerts, Dependabot
   security updates, automated fixes, and default CodeQL scanning.
4. Restrict GitHub Actions to approved/pinned actions and require full-length
   commit-SHA references.
5. Merge the reviewed change, observe the validation matrix and freshness/link
   workflows, then publish the matching version tag and verify the release
   assets/checksums and provenance.

Until those hosted steps are evidenced, report the score as a local candidate
score with the missing points called out rather than rounding to 100.
