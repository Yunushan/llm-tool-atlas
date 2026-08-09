# Releasing and recovery

LLM Tool Atlas publishes versioned data rather than an installable application.
Each release contains the canonical JSON catalogs, their schemas, citation and
license metadata, a manifest, and checksums in deterministic ZIP and TAR.GZ
archives.

## Supported verification environment

Python 3.10 through the current tested Python release is supported. The hosted
matrix checks Python 3.10 and 3.14 on Ubuntu, plus Python 3.14 on Windows and
macOS. The repository uses only the Python standard library.

Run the complete local gate from PowerShell, Command Prompt, or a POSIX shell:

```text
python scripts/verify.py
```

On systems where the interpreter is named `python3`, substitute `python3`.
`make check` is an optional convenience wrapper, not a prerequisite.

The verifier checks canonical data, generated-file drift, local Markdown links,
release metadata, and the complete test suite. The weekly hosted workflow also
enforces the 90-day freshness limit and audits official-source URLs with bounded
timeouts and retries.

## Release identity

`VERSION` is the machine-readable release version. Before a release, the same
SemVer value must appear in all of these places:

- `VERSION`;
- the top-level `version` in `CITATION.cff`;
- a `## [VERSION] - YYYY-MM-DD` heading in `CHANGELOG.md`; and
- the Git tag, prefixed with `v`.

The changelog date and `CITATION.cff` `date-released` must also match. Verify a
prospective tag without creating it:

```text
python scripts/check_release.py --tag v0.1.0
```

## Prepare a release

1. Move completed changelog entries from `Unreleased` into a dated release
   heading.
2. Update `VERSION`, `CITATION.cff` version, and `date-released` together.
3. Run `python scripts/verify.py --tag vX.Y.Z`.
4. Build and inspect the exact assets locally:

   ```text
   python scripts/build_release.py --tag vX.Y.Z --output-dir dist
   ```

5. Verify `dist/SHA256SUMS`, archive membership, and the embedded
   `MANIFEST.json`.
6. Merge the reviewed release-preparation pull request only after the stable
   `catalog` check passes.
7. Create and push the matching tag only from the reviewed `main` history. The
   tag-triggered workflow verifies that ancestry, re-runs the complete gate,
   rebuilds the assets from the tagged tree, signs provenance attestations, and
   publishes the GitHub Release.

The release workflow uses only pinned official checkout/setup actions and the
GitHub CLI already present on the hosted runner. It does not persist checkout
credentials. Configure repository rules to protect `main` and `v*` tags, require
the `catalog` status, and enable immutable releases before publishing.

## Release artifacts

For version `X.Y.Z`, the builder emits:

- `llm-tool-atlas-data-vX.Y.Z.zip`;
- `llm-tool-atlas-data-vX.Y.Z.tar.gz`;
- `llm-tool-atlas-data-vX.Y.Z.manifest.json`; and
- `SHA256SUMS`.

The release workflow also attaches GitHub artifact attestations for the
published files. Verify them with the GitHub CLI's attestation commands in
addition to checking the SHA256 manifest.

Archive paths, file ordering, text newlines, timestamps, owners, permissions,
and ZIP storage mode are fixed. This makes repeated builds from the same tree
byte-for-byte identical across supported platforms. `SHA256SUMS` covers both
archives and the external manifest.

On POSIX systems, verify downloaded assets with:

```text
sha256sum --check SHA256SUMS
```

In PowerShell, compare each expected digest with `Get-FileHash -Algorithm
SHA256`.

## Rollback and recovery

Published releases are append-only. Never replace a tag or overwrite an asset
to repair a bad release.

For a catalog error, restore the last known-good files from its protected tag in
a new branch, apply the minimum correction, regenerate the tables, and publish a
new patch release through normal review. Tell consumers to pin the last
known-good release until the correction is available.

For a damaged local checkout, recover without rewriting shared history:

1. Fetch tags from the canonical remote.
2. Create a recovery branch from the selected `vX.Y.Z` tag.
3. Run `python scripts/verify.py --tag vX.Y.Z` against the untouched tag.
4. Apply recovery changes on a new branch and open a pull request.
5. Build the proposed higher patch version twice and compare its checksums.

If a published artifact or tag is suspected of compromise, do not delete the
evidence. Disable further releases, open a private security report, record the
affected hashes, and publish a new trusted version only after the incident is
understood. A GitHub administrator may need to coordinate any exceptional
revocation; ordinary corrections always use a higher version.
