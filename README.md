# angeo skills

Agent Skills for AEO — checking whether AI assistants and their crawlers can
reach, parse, and cite a website.

Maintained by [angeo.dev](https://angeo.dev). MIT licensed.

## Install

```
/plugin marketplace add angeo-dev/skills
/plugin install aeo-audit@angeo
```

Then ask:

> Audit https://example.com for AI search visibility

## What's here

| Plugin | What it does |
|---|---|
| `aeo-audit` | Audits any URL for AI crawler access, `llms.txt`, JSON-LD structured data, sitemaps, and `.well-known` endpoints, then reports findings by severity with concrete fixes |

## What it checks

**Crawler access** — robots.txt rules for GPTBot, OAI-SearchBot, ChatGPT-User,
ClaudeBot, Claude-User, Claude-SearchBot, PerplexityBot, Perplexity-User,
Google-Extended, Applebot-Extended, Bingbot and CCBot; `X-Robots-Tag` headers.

**Machine-readable content** — `llms.txt`, `llms-full.txt`, XML sitemap (including
sitemap indexes), and whether the primary content exists in served HTML rather
than only in JavaScript.

**Structured data** — JSON-LD validity, entity coverage by page type, and offer
completeness: `price`, `priceCurrency`, `availability`, GTIN/MPN, return and
shipping policies.

**Page signals** — canonical, title, meta description, H1 count, `lang`, freshness.

**Agentic endpoints** — presence of `/.well-known/ucp`, `/.well-known/mcp.json`
and related discovery files, with the served content validated as JSON rather
than assumed from a 200.

## What it does not do

Stated plainly, because an audit that overclaims is worth less than none:

- **No JavaScript execution.** The collector reads served HTML, which approximates
  what a crawler receives. A client-rendered site is reported as *appearing*
  client-rendered, not as empty.
- **Homepage by default.** Other pages are fetched only when you name them. Product
  and category coverage needs a representative URL from you.
- **No claims about ranking.** Nobody outside OpenAI, Anthropic, Google or
  Perplexity knows how those systems select sources. This reports what is
  verifiable: access, presence, validity, completeness.
- **Presence, not protocol conformance.** A `.well-known` endpoint is reported as
  present or absent. No handshake is performed.
- **No content quality analysis.** Answer structure, topical coverage and entity
  consistency are out of scope for 0.1.

## Reliability

Signals that could not be fetched are reported as unverified, with the status
code — never as passes. Before release the collector was run against 14 sites
spanning single-page apps, publishers, hosted commerce platforms, documentation
sites and WAF-protected storefronts. Four classes of false verdict were found
and fixed:

- inline JavaScript counted as page text, which made client-rendered sites look
  content-rich
- an H1 regex that never matched real markup
- soft 200s — catch-all routing serving the app shell for `/llms.txt`,
  `/ai.txt` and every `.well-known` path
- silently truncated bodies reported as complete file sizes

## Requirements

Python 3 for the signal collector — standard library only, no dependencies —
and network access to the audited site.

## Related

The same checks run inside Magento 2 as a CLI command via
[`angeo/module-aeo-audit`](https://packagist.org/packages/angeo/module-aeo-audit),
part of an MIT-licensed suite of Magento 2 AEO modules on
[Packagist](https://packagist.org/packages/angeo/).

## Contributing

Issues and PRs welcome — particularly corrections to the crawler catalogue in
`plugins/aeo-audit/skills/aeo-audit/references/checks.md`, which goes stale as
vendors add, rename and deprecate agents.

## Licence

MIT — see [LICENSE](LICENSE).
