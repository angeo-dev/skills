#!/usr/bin/env python3
"""Collect the raw signals an AEO audit needs, in one pass.

Usage:
    python3 fetch_signals.py https://example.com [extra-url ...]

Prints a single JSON object to stdout. Every fetch reports its own outcome:
a failure is recorded as an error string, never as an empty pass.

Standard library only. No JavaScript execution — this approximates what a
plain crawler sees, which is the point.
"""

import json
import re
import socket
import ssl
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlparse

UA = "Mozilla/5.0 (compatible; aeo-audit/0.1; +https://angeo.dev/)"
TIMEOUT = 20
MAX_BODY = 400_000

WELL_KNOWN = [
    "/.well-known/mcp.json",
    "/.well-known/ucp",
    "/.well-known/ucp.json",
    "/.well-known/ai-plugin.json",
    "/.well-known/agent.json",
    "/.well-known/security.txt",
]


def slice_body(r, limit, expect_json=False):
    """Keep a bounded slice of a fetched body, and say so when it was cut.

    A silently truncated sitemap looks like a short sitemap. Any check that
    counts entries or looks for a pattern near the end would then report a
    confident wrong answer, so truncation has to be visible in the output.

    For endpoints that must return JSON, a 200 is not evidence of presence.
    Sites with catch-all routing — WordPress most of all — answer 200 with an
    HTML page for paths that don't exist. Parse it and say whether it parsed.
    """
    body = r["body"]
    out = {
        "status": r["status"],
        "error": r["error"],
        "content_type": r["content_type"],
        "body_truncated": len(body) > limit,
        "body_total_chars": len(body),
        "body": body[:limit],
    }
    out["fetch_capped"] = r.get("fetch_capped", False)
    if out["fetch_capped"]:
        out["body_total_chars"] = None  # the read itself was capped; unknown

    stripped = body.lstrip()[:300].lower()
    out["looks_like_html"] = stripped.startswith(("<!doctype html", "<html"))

    if expect_json:
        try:
            json.loads(body)
            out["json_valid"] = True
        except (json.JSONDecodeError, ValueError):
            out["json_valid"] = False
    return out

ROOT_FILES = ["/robots.txt", "/llms.txt", "/llms-full.txt", "/sitemap.xml", "/ai.txt"]


def fetch(url):
    """Fetch one URL. Always returns a dict; never raises."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            raw = resp.read(MAX_BODY)
            charset = resp.headers.get_content_charset() or "utf-8"
            return {
                "url": url,
                "final_url": resp.geturl(),
                "status": resp.status,
                "content_type": resp.headers.get("Content-Type"),
                "headers": {
                    k: v
                    for k, v in resp.headers.items()
                    if k.lower()
                    in {
                        "content-type",
                        "x-robots-tag",
                        "content-usage",
                        "link",
                        "server",
                        "cache-control",
                    }
                },
                "fetch_capped": len(raw) >= MAX_BODY,
                "truncated": len(raw) >= MAX_BODY,
                "body": raw.decode(charset, errors="replace"),
                "error": None,
            }
    except urllib.error.HTTPError as e:
        return {
            "url": url,
            "final_url": url,
            "status": e.code,
            "content_type": None,
            "headers": {},
            "fetch_capped": False,
            "truncated": False,
            "body": "",
            "error": f"HTTP {e.code} {e.reason}",
        }
    except Exception as e:  # noqa: BLE001 — any failure is a finding, not a crash
        return {
            "url": url,
            "final_url": url,
            "status": None,
            "content_type": None,
            "headers": {},
            "fetch_capped": False,
            "truncated": False,
            "body": "",
            "error": f"{type(e).__name__}: {e}",
        }


def extract_jsonld(html):
    """Pull every ld+json block out of the HTML. Report unparsable ones."""
    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    out = []
    for i, block in enumerate(blocks):
        try:
            out.append({"index": i, "valid": True, "data": json.loads(block.strip())})
        except json.JSONDecodeError as e:
            out.append(
                {
                    "index": i,
                    "valid": False,
                    "error": str(e),
                    "excerpt": block.strip()[:300],
                }
            )
    return out


def _tag_attr(html, tag, key_attr, key_value, want_attr):
    """Find <tag ... key_attr="key_value" ...> and return want_attr, in any order.

    Attribute order is not fixed in real markup: <link rel=canonical href=...>
    and <link href=... rel=canonical> are both common, and a regex that assumes
    one order silently reports the signal as absent.
    """
    for m in re.finditer(rf"<{tag}\b([^>]*)>", html, re.IGNORECASE):
        attrs = m.group(1)
        if not re.search(
            rf'{key_attr}\s*=\s*["\']?\s*{key_value}\s*["\']?', attrs, re.IGNORECASE
        ):
            continue
        v = re.search(rf'{want_attr}\s*=\s*["\']([^"\']*)["\']', attrs, re.IGNORECASE)
        if v:
            return v.group(1).strip()
    return None


def visible_text(html):
    """Text a reader would see: script and style contents removed FIRST.

    Order matters. Stripping all tags before removing script blocks leaves the
    JavaScript and JSON-LD source in the text, which inflates the count and
    makes a client-rendered page look content-rich.
    """
    without_code = re.sub(
        r"<(script|style)\b[^>]*>.*?</\1\s*>",
        " ",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", without_code)).strip()


def head_signals(html):
    """Signals that live in the document head."""
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    lang = re.search(r"<html\b[^>]*\blang\s*=\s*[\"']([^\"']+)[\"']", html, re.IGNORECASE)

    return {
        "title": title.group(1).strip() if title else None,
        "meta_description": _tag_attr(html, "meta", "name", "description", "content"),
        "meta_robots": _tag_attr(html, "meta", "name", "robots", "content"),
        "canonical": _tag_attr(html, "link", "rel", "canonical", "href"),
        "generator": _tag_attr(html, "meta", "name", "generator", "content"),
        "lang": lang.group(1) if lang else None,
        "h1_count": len(re.findall(r"<h1[\s>]", html, re.IGNORECASE)),
        "visible_text_chars": len(visible_text(html)),
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2

    target = sys.argv[1]
    if not urlparse(target).scheme:
        target = "https://" + target

    result = {"target": target, "root_files": {}, "well_known": {}, "pages": {}}

    # Resolve first. If the name does not resolve, every subsequent request
    # fails the same way, and ten identical DNS errors read like ten findings
    # instead of one. Say it once and stop.
    host = urlparse(target).hostname
    try:
        socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        result["fatal_error"] = f"DNS resolution failed for {host}: {e}"
        result["note"] = (
            "Nothing was collected. This is a local network or DNS problem, "
            "not a finding about the site — do not report site signals from "
            "this run."
        )
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        print()
        return 1

    home = fetch(target)
    result["homepage"] = {k: v for k, v in home.items() if k != "body"}
    if home["body"]:
        result["homepage"]["head"] = head_signals(home["body"])
        result["homepage"]["jsonld"] = extract_jsonld(home["body"])

    base = home["final_url"] if home["final_url"] else target
    result["canonical_host"] = urlparse(base).netloc

    for path in ROOT_FILES:
        r = fetch(urljoin(base, path))
        result["root_files"][path] = slice_body(r, 60000)

    for path in WELL_KNOWN:
        r = fetch(urljoin(base, path))
        result["well_known"][path] = slice_body(r, 4000, expect_json=True)

    for extra in sys.argv[2:]:
        url = extra if urlparse(extra).scheme else urljoin(base, extra)
        r = fetch(url)
        page = {k: v for k, v in r.items() if k != "body"}
        if r["body"]:
            page["head"] = head_signals(r["body"])
            page["jsonld"] = extract_jsonld(r["body"])
        result["pages"][url] = page

    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
