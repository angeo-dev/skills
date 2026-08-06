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
| `GPTBot` | OpenAI | Crawling for ChatGPT and training |
| `OAI-SearchBot` | OpenAI | Search index for ChatGPT |
| `ChatGPT-User` | OpenAI | Live fetch when a user asks about a URL |
| `ClaudeBot` | Anthropic | Crawling for Claude |
| `Claude-User` | Anthropic | Live fetch on user request |
| `Claude-SearchBot` | Anthropic | Search index |
| `PerplexityBot` | Perplexity | Index |
| `Perplexity-User` | Perplexity | Live fetch |
| `Google-Extended` | Google | Gemini / AI Overviews opt-out control |
| `Applebot-Extended` | Apple | Apple Intelligence opt-out control |
| `Bingbot` | Microsoft | Powers Copilot answers via the Bing index |
| `CCBot` | Common Crawl | Dataset many models train on |

**Report, do not moralise.** Blocking training crawlers while allowing live-fetch
and search agents is a legitimate, deliberate strategy — several publishers do
exactly this. Flag it as critical only when the user's stated goal is AI
visibility and the block contradicts it. Otherwise state the configuration and
let them decide.

**Note on syntax:** per RFC 9309, matching is on the most specific group, and
user-agent tokens are case-insensitive. A `Disallow: /` under `User-agent: *`
applies to every agent without its own group.

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

- `/.well-known/mcp.json` — Model Context Protocol server discovery
- `/.well-known/ucp` — UCP merchant profile (Google Universal Commerce Protocol)

Hosted commerce platforms may publish some of these for every store on the
platform, without the merchant doing anything. When one is present, check whether
the endpoint it advertises points at the merchant's own domain or at a platform
host — that distinction decides who controls the integration, and it is worth
stating plainly rather than scoring.
- `/.well-known/ai-plugin.json` — legacy OpenAI plugin manifest
- `/.well-known/agent.json` — agent card

**A 200 is not presence.** Sites with catch-all routing answer 200 with an HTML
page for paths that don't exist — WordPress does this constantly. Count the
endpoint as present only when the collector reports `json_valid: true`. A 200
with `looks_like_html: true` means the CMS served a page, not a profile; report
it as absent, and mention the soft-200 if the user seems to believe otherwise.

**Severity: informational.** Absence is normal and expected for most sites; only
flag it when the user has stated an agentic-commerce goal.

### 5.2 Content-Usage / licensing signals
Report the presence of a `Content-Usage` response header or licensing directives
in robots.txt. These express machine-readable terms for AI use. Informational —
emerging, not yet widely honoured.
