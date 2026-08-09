# Security Policy

LLM Tool Atlas is a documentation and data project. It does not execute model
providers, store API keys, or proxy prompts.

## Supported versions

Only the latest `main` commit and the latest protected release are supported.
There are no supported older release branches. Consumers should pin a reviewed
release tag and verify its published checksums before importing catalog data.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting feature for vulnerabilities
in repository scripts or automation. Repository administrators must keep that
feature enabled; if it is temporarily unavailable, contact the maintainer
through the repository owner profile and do not disclose exploit details in a
public issue. Do not open a public issue containing a working exploit,
credential, personal data, or another party's private prompt.

We acknowledge reports within five business days, investigate reproducible
issues, and publish a coordinated fix or status update when practical. The
response target is not a guarantee for third-party products listed in the
catalog.

For a security problem in a listed product, report it to that product's vendor.
This project cannot coordinate third-party disclosures.

The official-link audit rejects credentials, local/special-use hosts, and
non-public DNS answers before connecting, pins each validated address for the
TLS request, and follows only validated HTTPS redirects. It is a catalog-link
integrity check, not a general-purpose web crawler or a guarantee about the
security of a linked vendor.

## Safe use

Treat every coding agent as privileged developer tooling. Review permissions,
data-retention terms, network access, shell commands, diffs, and generated
dependencies before using it with sensitive repositories or production systems.
