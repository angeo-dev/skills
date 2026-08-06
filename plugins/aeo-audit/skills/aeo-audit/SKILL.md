---
name: aeo-audit
description: Audit a website for AI Engine Optimization (AEO) — whether AI assistants and their crawlers can reach, parse, and cite it. Checks robots.txt AI-bot rules, llms.txt, JSON-LD structured data, sitemaps, canonical/meta signals, and .well-known endpoints, then reports findings by severity with concrete fixes. Use this whenever the user asks about AI search visibility, ChatGPT/Claude/Perplexity citations, AI crawler access, llms.txt, robots.txt bot rules, schema markup, structured data, "why doesn't AI mention my site", agentic commerce readiness, or asks to audit or review a site or URL for AI or LLM discoverability — even if they don't say "AEO".
---

# AEO Audit

Audit how a website looks to AI assistants and their crawlers, then report what to fix.

Traditional SEO asks whether a page ranks. AEO asks something different: can an AI system fetch the page at all, parse what it says, and cite it with confidence? Those are separate failure modes. A site can rank on page one and still be invisible to an assistant because its robots.txt blocks the crawler, or because the only place a price exists is in JavaScript that never runs.

## Scope and honesty

State what was measured, not what it implies. Two rules matter more than any individual check:

**Never guess at a signal you could not fetch.** If robots.txt returns a 500, that is a finding — "could not verify", not "no restrictions found". Silent failures that read as passes are the fastest way to make an audit worthless.

**Do not claim to know how any specific AI system ranks or selects sources.** Nobody outside those companies does. What is verifiable: whether a documented crawler is allowed, whether a machine-readable format is present and valid, whether facts are stated in the HTML rather than only in script. Report those. Frame everything else as a hypothesis.

## Workflow

### 1. Establish the target

Take the URL the user gave. If they gave a bare domain, use `https://` and follow redirects — note if the canonical host differs from what they typed (`example.com` → `www.example.com`), since that mismatch is itself a common source of split signals.

If they gave no URL, ask for one. Do not audit a hypothetical site.

### 2. Collect the raw signals

Run the bundled collector, which fetches everything in one pass and prints JSON:

```bash
python3 scripts/fetch_signals.py https://example.com
```

It returns status codes, headers, and bodies for `/robots.txt`, `/llms.txt`, `/sitemap.xml`, the homepage, and common `.well-known` paths, plus every JSON-LD block found in the homepage HTML. Read its output rather than fetching each URL by hand — it handles timeouts, redirects, and encoding consistently, and its failures are explicit.

If the script cannot run (no Python, no network egress), fall back to fetching the same URLs with whatever tool is available, and say in the report that collection was manual.

### 3. Evaluate

Work through `references/checks.md`. It lists each check, what counts as a pass, the severity when it fails, and the fix. Do not re-derive severities — the file exists so that two runs on the same site produce the same verdict.

Check only what the collected data supports. A homepage-only fetch cannot tell you whether product pages carry `Offer` schema; if the user cares about that, ask for a representative product URL and collect it too.

### 4. Report

Use this structure:

```markdown
# AEO audit — [domain]
[one-paragraph summary: what works, what is the single biggest problem]

## Critical
[findings that block AI access entirely]

## Important
[findings that degrade parsing or citation confidence]

## Minor
[polish]

## Could not verify
[signals that failed to fetch, with the status code]

## What this audit did not cover
[scope limits — e.g. homepage only, no JS rendering]
```

For each finding, give three things: what was observed (quote the actual line or status code), why it matters for an AI reader specifically, and the concrete fix. "Add structured data" is not a fix. "Add `Product` JSON-LD with `offers.price` and `offers.availability` to product templates" is.

Order findings by severity, not by the order the checks ran.

**Example finding:**

> **ChatGPT's crawler is blocked** — `robots.txt` line 12 contains `User-agent: GPTBot` followed by `Disallow: /`. OpenAI documents GPTBot as the crawler that fetches pages for ChatGPT's browsing and training. While that block stands, no amount of on-page work will make this site quotable in ChatGPT. Fix: remove the `Disallow: /` under `GPTBot`, or narrow it to the paths that genuinely need protection (`/checkout/`, `/customer/`).

If the site is in good shape, say so plainly and briefly. Padding a clean audit with invented problems destroys the credibility that makes the audit worth running.

## Rendering caveat

The collector fetches raw HTML without executing JavaScript. That is deliberate — it approximates what most crawlers see. But it means a client-rendered site will look far emptier than it appears in a browser. When the homepage HTML is nearly empty of text or structured data, do not report it as "no content"; report that the page appears to be client-rendered and that whether crawlers see content depends on the framework's server-rendering setup. Then say what to check.

## Platform specifics

When the site runs on a known platform, the fixes get concrete. Identify it from generator meta tags, cookie names, or asset paths in the collected HTML, and read the matching file if one exists:

- `references/magento.md` — Magento 2 / Adobe Commerce

For other platforms, keep advice platform-neutral rather than guessing at admin paths that may not exist.
