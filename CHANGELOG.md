# Changelog

All notable changes to the clip-and-post skill. Versions follow [Semantic Versioning](https://semver.org/):
major for changes that break an existing workflow or script interface, minor for new behaviour
or documented requirements, patch for fixes and wording.

When releasing, bump `metadata.version` in `SKILL.md`, add a section here, and tag the commit
`vX.Y.Z`.

## [1.2.0] - 2026-09-29

### Added
- Batch mode: several sources in one request, videos and articles mixed. Each source keeps its own
  branch, folder and event; the topic question, draft approval and event approval are each asked
  once for the whole batch, answered per item. Publishing is staggered by default.
- `scripts/batch-read.sh`: runs the read step for every source in parallel, one numbered scratch
  directory each so articles don't overwrite each other's `article.html`.
- `scripts/upload.py`: uploads a local file to Blossom through a one-off nostr-java-mcp instance
  with `allow-private-hosts`, which the running MCP server refuses.

### Fixed
- The upload step now says `allow-private-hosts` has to be passed as a JVM system property
  (`JAVA_TOOL_OPTIONS`); a `--nostr.mcp...` program argument is silently ignored.

## [1.1.0] - 2026-09-26

### Added
- Version and changelog pointer in the `SKILL.md` frontmatter (`metadata.version`, `metadata.changelog`).
- `compatibility` frontmatter field listing platform and tool requirements.
- Prerequisites state that the skill is Linux only for now.
- Prerequisites explain when `libsecret-tools` (`secret-tool`) is needed: only with
  nostr-java-mcp's default `os-keychain` keystore, and why `encrypted-file` suits scheduled posts.

## [1.0.0] - 2026-09-26

### Added
- Initial release, extracted into its own repository: YouTube clips posted as kind 1 notes,
  article quotes as NIP-84 highlights (kind 9802), topic-first flow, approval gate, and
  scheduled publishing.
