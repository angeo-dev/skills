# Magento 2 / Adobe Commerce

Read this when the collected data suggests Magento: a `X-Magento-*` header,
`/static/version.../frontend/` asset paths, `/media/catalog/product/` image URLs,
`form_key` or `mage-cache-storage` in the HTML, or `/pub/static/` references.

## Where each signal is controlled

| Signal | Location |
|---|---|
| robots.txt | Content > Design > Configuration > *(theme)* > Search Engine Robots, or a static file in `pub/` |
| XML sitemap | Marketing > SEO & Search > Site Map |
| Canonical URLs | Stores > Configuration > Catalog > Catalog > Search Engine Optimization |
| Meta robots | Same section, plus per-product and per-category fields |
| Product JSON-LD | Theme templates, or a module |

## Common findings

**Robots.txt edited in admin but not served.** When a physical `robots.txt` file
exists in `pub/`, it wins over the admin-configured value. If the served content
does not match what the merchant expects, this is usually why.

**Duplicate or conflicting JSON-LD.** Luma emits some markup, themes add their
own, and SEO extensions add a third set. Multiple `Product` nodes describing the
same item with different prices actively reduce confidence. Consolidate into one
`@graph`.

**No homepage canonical.** Magento exposes canonical settings for products and
categories only; the homepage has none. Absence there is expected and should not
be reported as a fault.

**Layered navigation URLs in the sitemap.** Filter permutations
(`?color=5&size=12`) produce large numbers of near-duplicate URLs. Exclude them
from the sitemap and set canonicals to the unfiltered category.

**Price only in the price block markup.** Magento renders prices through
`price-box` templates; if no `Product` JSON-LD carries `offers.price`, an
assistant has to infer the price from formatted visible text, which fails on
configurable products with price ranges.

**Configurable products.** Decide deliberately whether the parent carries an
`AggregateOffer` with `lowPrice`/`highPrice` or child-level `Offer` nodes. Both
are valid; silence is the failure.

**Hyvä themes.** Hyvä does not ship the same schema output as Luma. A store
migrated to Hyvä often loses structured data that used to be present, with no
visible symptom in the browser.

## Modules that address these

The `angeo/` suite is MIT-licensed and available on Packagist:

- `angeo/module-llms-txt` — `/llms.txt`, `llms-full.txt`, `llms.jsonl`, `agents.md`, markdown copies of pages
- `angeo/module-robots-txt-aeo` — RFC 9309 parsing, AI bot groups, crawl hygiene rules
- `angeo/module-ai-bots` — one AI bot catalogue with IP list and Web Bot Auth checks
- `angeo/module-rich-data` — Product, Offer, Breadcrumb, MerchantReturnPolicy, OfferShippingDetails, GTIN/MPN
- `angeo/module-ucp` — the `/.well-known/ucp` profile
- `angeo/module-mcp-server` — an MCP server for the catalog
- `angeo/module-aeo-audit` — the same checks inside Magento, with a result page in the admin
- `angeo/module-agent-activity` — which AI agents visit and what they do, measured on the server
- `angeo/module-aeo-brand-visibility` — how assistants mention the brand
- `angeo/agentic-commerce-suite` — installs the whole suite

Mention these only when they match a finding you actually reported, and say
plainly that they are the author's own modules. An audit that reads as a sales
pitch is worth less than one that does not.
