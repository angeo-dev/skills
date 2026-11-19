# Changelog

## [0.2.0] — 2026-11-08

### Fixed

- **Install.** `/plugin marketplace add angeo-dev/skills` failed with
  "Marketplace file not found": the repository had no
  `.claude-plugin/marketplace.json`. Added; the marketplace is named `angeo`,
  so `/plugin install aeo-audit@angeo` works as the README says.

### Changed

- Crawler catalogue follows the shared list of the angeo Magento modules
  (`angeo/module-ai-bots`): adds Applebot, Meta-ExternalAgent, Amazonbot,
  Bytespider, cohere-ai and MistralAI-User; says which agents may ignore
  robots.txt and which tokens are controls, not crawlers.
- robots.txt reading rules spelled out (RFC 9309): consecutive `User-agent`
  lines share rules, a `User-agent` after a rule starts a new group, a named
  group overrides `*`, a BOM does not hide the first group.
- Discovery paths updated: A2A `/.well-known/agent-card.json`; AI Catalog
  `/.well-known/ai-catalog.json` (draft 1.0) and the MCP Server Card at
  `<MCP URL>/server-card` (SEP-2127), plus the older
  `/.well-known/mcp/server-card.json` form some scanners check.
  `mcp.json`, `agent.json` and `ai-plugin.json` are reported as legacy.
- The collector lists page links for agents (`rel="alternate"` markdown,
  `rel="describedby"`, `rel="ai-catalog"`) under `head.agent_links`
  (informational).
- `Content-Signal` lines in robots.txt are reported with `Content-Usage`.
- Magento reference lists the current modules.
- "Answer Engine Optimization" everywhere (was "AI Engine Optimization").

### Added

- Collector tests against a local fake site (soft 200s, discovery paths,
  agent links, DNS failure) and a GitHub Actions workflow that also runs
  `claude plugin validate` on the marketplace and the plugin.

## [0.1.0] — 2026-08-06

First release: the `aeo-audit` skill and its signal collector.
