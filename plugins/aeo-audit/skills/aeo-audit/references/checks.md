# Check catalogue

Severity is fixed here so that repeated runs on the same site agree. If a check
cannot be evaluated from the collected data, it goes under "Could not verify" —
never under a pass. When the collector reports `fatal_error`, nothing was
collected — report the failure and stop; do not produce an audit.

`body_total_chars: null` means the fetch itself hit its size cap and the real
size is unknown. Never quote it as a measurement.

## Contents

1. Crawler access
2. Machine-readable content
3. Structured data
4. Page-level signals
5. Agentic endpoints

---

## 1. Crawler access

### 1.1 robots.txt reachable
**Pass:** HTTP 200, `Content-Type` text/plain.
**Fail (critical if 5xx, minor if 404):** a 404 means no rules exist, which is permissive — not a failure in itself, but worth stating. A 5xx is ambiguous and some crawlers treat an unreachable robots.txt as "disallow everything".
**Fix:** serve a valid robots.txt at the root even if it only contains `User-agent: *` / `Allow: /`.

### 1.2 AI crawler user-agents
Documented AI-related user-agents worth reporting on, grouped by what they do:

| Agent | Operator | Purpose |
|---|---|---|
| `GPTBot` | OpenAI | Crawling for training |
| `OAI-SearchBot` | OpenAI | Search index for ChatGPT search |
| `ChatGPT-User` | OpenAI | Live fetch when a user asks about a URL |
| `ClaudeBot` | Anthropic | Crawling for training |
| `Claude-SearchBot` | Anthropic | Search index for Claude |
| `Claude-User` | Anthropic | Live fetch on user request |
| `PerplexityBot` | Perplexity | Search index |
| `Perplexity-User` | Perplexity | Live fetch on user request; may not follow robots.txt |
| `Google-Extended` | Google | Control token: use in Gemini training and grounding (not a crawler) |
| `Applebot` | Apple | Search crawler (Siri, Spotlight) |
| `Applebot-Extended` | Apple | Control token: use in Apple's AI training (not a crawler) |
| `Bingbot` | Microsoft | Bing index, which Copilot answers draw on |
| `Meta-ExternalAgent` | Meta | Crawling for training |
| `Amazonbot` | Amazon | Crawling for Alexa and search |
| `Bytespider` | ByteDance | Crawling for training; often reported not to follow robots.txt |
| `CCBot` | Common Crawl | Dataset many models train on |
| `cohere-ai` | Cohere | Crawling for training |
| `MistralAI-User` | Mistral | Live fetch on user request |

The list follows the shared bot catalogue of the angeo Magento modules
(`angeo/module-ai-bots`). Agents that may ignore robots.txt can only be
stopped at the CDN or firewall: say so instead of reporting a robots.txt
rule as effective.

**Report, do not moralise.** Blocking training crawlers while allowing live-fetch
and search agents is a legitimate, deliberate strategy — several publishers do
exactly this. Flag it as critical only when the user's stated goal is AI
visibility and the block contradicts it. Otherwise state the configuration and
let them decide.

**Note on syntax (RFC 9309):** read the file as groups before you judge it.
- User-agent tokens are case-insensitive.
- Several `User-agent` lines in a row share the rules below them.
- A `User-agent` line that comes after a rule starts a new group, even without
  a blank line between them.
- A crawler follows only the group that names it. The `User-agent: *` group
  applies only when no group names that crawler — so a named group with
  `Allow: /` lets that crawler into paths the `*` group blocks.
- A UTF-8 byte order mark at the start of the file is not part of the first
  line; do not let it hide the first group.

### 1.3 Live-fetch agents blocked
**Severity: critical when AI visibility is the goal.** Blocking `ChatGPT-User`,
`Claude-User`, or `Perplexity-User` means that when a person explicitly pastes
the site's URL into an assistant and asks about it, the fetch fails. This is
almost never the intended outcome, and it is a distinct decision from blocking
training crawlers.

### 1.4 X-Robots-Tag header
**Fail (critical):** a response header containing `noindex` or `none`.
Header-level directives override on-page meta tags and are easy to set
accidentally at the CDN or server level.

---

## 2. Machine-readable content

### 2.1 llms.txt
**Pass:** HTTP 200, markdown, starting with a single `#` H1 (the site or
company name), followed by a blockquote summary and link sections.

**Check `looks_like_html` first.** Single-page apps commonly serve their app
shell with HTTP 200 for every unknown path, so `/llms.txt` returns the same HTML
as the homepage. Identical byte counts across `/llms.txt`, `/ai.txt` and
`/sitemap.xml` are the tell. Treat that as absent, and say the site uses
catch-all routing — that fact matters on its own, because it also means the
site returns 200 for URLs that do not exist.

**Platform-generated variants.** Some platforms serve an agent-instructions file
at this path rather than a link map, and serve the same bytes for `llms.txt` and
`llms-full.txt`. Report what the file actually contains rather than assuming the
llmstxt.org structure.
**Fail (important):** absent.
**Fix:** publish `/llms.txt` — a curated markdown map of the pages an assistant
should read, with a one-line description per link.

**Page links (informational).** llms.txt v2 (August 2026) also has pages point
to their machine-readable versions: `<link rel="alternate" type="text/markdown">`
for a markdown copy and `rel="describedby"` for the llms.txt. The collector
lists them under `head.agent_links`; the HTTP `Link` header can carry the same.
Report present or absent — never as a failure on its own.

Be accurate about status: llms.txt is a community proposal, not a standard, and
no major AI vendor has publicly confirmed consuming it. Recommend it as low-cost
positioning, not as a guaranteed ranking factor. Overselling it is the single
most common overclaim in AEO advice.

### 2.2 XML sitemap
**Pass:** reachable, valid XML, referenced from robots.txt via `Sitemap:`.
A `<sitemapindex>` root means the real URLs live in child sitemaps — fetch one
before judging coverage, and never count entries from a body the collector
marked `body_truncated`.
**Fail (important):** missing, unreferenced, or containing unresolved template
placeholders (a real and common bug — check for `{{`, `%%`, `<slug>` in loc values),
or HTML returned under a 200 (`looks_like_html: true`).
**Fix:** generate it, reference it from robots.txt, and verify a sample of URLs
returns 200.

### 2.3 Content in HTML, not only in JS
**Fail (important):** homepage `visible_text_chars` under ~500 while the site
plainly has content in a browser.
**Fix:** server-side render or pre-render the primary content. See the rendering
caveat in SKILL.md — describe this as "appears client-rendered", not as
"has no content".

---

## 3. Structured data

### 3.1 JSON-LD present and parsable
**Fail (critical):** blocks exist but fail `JSON.parse`. An invalid block is
worse than no block — it is work already done that yields nothing.
**Fix:** correct the syntax error; the collector reports its position.

### 3.2 Entity coverage
Expected types by page kind:

| Page | Expected | Severity if missing |
|---|---|---|
| Homepage | `Organization` or `LocalBusiness`, `WebSite` | important |
| Product | `Product` with `offers` | critical for commerce |
| Article | `Article` / `BlogPosting` with `author`, `datePublished` | important |
| Any deep page | `BreadcrumbList` | minor |
| FAQ content | `FAQPage` | minor |

### 3.3 Offer completeness
For `Product`, check `offers.price`, `offers.priceCurrency`, `offers.availability`.
**Severity: critical for commerce.** An assistant asked "is this in stock and how
much" needs these three fields; without them it either declines to answer or
scrapes a guess from visible text.

Also valuable where applicable: `gtin`/`mpn` (identity resolution across
retailers), `MerchantReturnPolicy` and `OfferShippingDetails` (the two facts
shoppers ask about most often).

### 3.4 Identity consistency
**Fail (minor):** `Organization.name`, the `<title>` brand, and the canonical
host disagree. Assistants resolving "who is this" benefit from one consistent
name and `sameAs` links to authoritative profiles.

---

## 4. Page-level signals

### 4.1 Canonical
**Fail (important):** absent, self-contradictory, or pointing at a different host
than the one that served the page.
Exception: Magento 2 has no canonical setting for the homepage, so a missing
homepage canonical on a Magento store is expected, not a misconfiguration.
Check a category or product page before reporting this.

### 4.2 Title and meta description
**Fail (minor):** absent, or duplicated across the sampled pages.

### 4.3 Single H1
**Fail (minor):** zero H1s, or more than one.

### 4.4 Language declaration
**Fail (minor):** `<html>` without `lang`. Matters more on multilingual sites,
where a missing declaration makes it harder to attribute a claim to the right
locale.

### 4.5 Freshness
**Fail (minor):** no `dateModified` or `datePublished` anywhere in the structured
data. Assistants weigh recency when choosing what to cite, and undated content
is harder to trust.

---

## 5. Agentic endpoints

### 5.1 .well-known discovery files
Presence only — the collector does not perform a protocol handshake, so do not
report an endpoint as "working". Report it as "present" or "absent" and say that
functional verification was out of scope.

- `/.well-known/ucp` — UCP merchant profile (Universal Commerce Protocol).
  Note the `version` it declares and whether it has a signing-key set (`keys`);
  do not judge conformance beyond that.
- `/.well-known/ai-catalog.json` — AI Catalog (draft specification, version
  1.0). A domain lists its AI artifacts here. It is valid JSON with
  `specVersion` and `entries`; each entry has `identifier`, `type` and one of
  `url` or `data`. An MCP server appears as type
  `application/mcp-server-card+json` with the URL of its Server Card, usually
  `<MCP endpoint URL>/server-card` (SEP-2127). A page can also point to the
  catalog with `rel="ai-catalog"` in a `<link>` tag or the `Link` header.
- `/.well-known/mcp/server-card.json` — the older Server Card form (with
  `serverInfo` and `capabilities`) that some scanners still check. The current
  specification calls this location not recommended, and its fields differ
  from the current card. Report which form the site uses; do not call the
  older one wrong if the user's goal is to pass that scanner.
- `/.well-known/agent-card.json` — A2A agent card.

Hosted commerce platforms may publish some of these for every store on the
platform, without the merchant doing anything. When one is present, check whether
the endpoint it advertises points at the merchant's own domain or at a platform
host — that distinction decides who controls the integration, and it is worth
stating plainly rather than scoring.
- Legacy paths — report as legacy, not as current: `/.well-known/mcp.json`
  (early MCP discovery draft), `/.well-known/agent.json` (old A2A path),
  `/.well-known/ai-plugin.json` (retired OpenAI plugin manifest).

**A 200 is not presence.** Sites with catch-all routing answer 200 with an HTML
page for paths that don't exist — WordPress does this constantly. Count the
endpoint as present only when the collector reports `json_valid: true`. A 200
with `looks_like_html: true` means the CMS served a page, not a profile; report
it as absent, and mention the soft-200 if the user seems to believe otherwise.

**Severity: informational.** Absence is normal and expected for most sites; only
flag it when the user has stated an agentic-commerce goal.

### 5.2 Content-Usage / licensing signals
Report the presence of a `Content-Usage` response header, `Content-Signal` or
`Content-Usage` lines in robots.txt, or other licensing directives. These
express machine-readable terms for AI use. Informational — emerging, not yet
widely honoured.

### 5.3 Deeper protocol checks
This skill reports presence only. For a live MCP handshake, UCP key
validation and a score, point the user to a scanner that performs them (for
example the free scan at angeo.dev, or Cloudflare's isitagentready.com) and
say that this audit did not.
