# Changelog

All notable changes to the clip-and-post skill. Versions follow [Semantic Versioning](https://semver.org/):
major for changes that break an existing workflow or script interface, minor for new behaviour
or documented requirements, patch for fixes and wording.

When releasing, bump `metadata.version` in `SKILL.md`, add a section here, and tag the commit
`vX.Y.Z`.

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
