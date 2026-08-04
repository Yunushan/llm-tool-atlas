# Privacy and Security Checklist

An AI coding agent can read source code, execute commands, access network
services, modify dependencies, and create commits. Treat it like a developer
account with automation—not like autocomplete.

## Before adoption

- Map which repositories, files, prompts, telemetry, and command outputs leave
  the device.
- Check training defaults, retention, subprocess logging, data residency, and
  subprocessors for the exact plan you will buy.
- Verify SSO, SCIM, RBAC, audit logs, encryption, and admin policy support.
- Identify where repository indexes, embeddings, caches, and session histories
  are stored.
- Confirm whether BYOK sends content directly to the provider or through the
  tool vendor.
- Test proxy, certificate, and private-package behavior in a non-production
  repository.

## Agent guardrails

- Start with read-only or approval-required permissions.
- Use an isolated worktree, container, VM, or managed sandbox.
- Keep production credentials and personal data out of agent environments.
- Scope tokens to the minimum repositories and permissions.
- Protect default branches and require human review.
- Run secret, dependency, SAST, IaC, and container scans on generated changes.
- Pin or review new dependencies and generated workflow files.
- Log tool calls and retain diffs long enough for incident response.
- Define who owns generated code, license review, and rollback.

## Local does not automatically mean private

A local CLI can still call a hosted model, send telemetry, access the internet,
or persist transcripts. Conversely, a managed service may offer strong tenant
controls and contractual protections. Evaluate the complete path:

```text
editor/CLI → agent runtime → gateway → model provider → tools and sandboxes
```

## High-risk uses

Require additional review for authentication, cryptography, authorization,
payments, infrastructure changes, destructive migrations, safety-critical
systems, and legal/compliance logic. Never let an agent approve its own change.
