"""Collector tests against a local fake site. Standard library only:

    python3 -m unittest discover -s tests -v

Each test is a false verdict the collector must not produce.
"""

import json
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "plugins/aeo-audit/skills/aeo-audit/scripts/fetch_signals.py"

APP_SHELL = "<!doctype html><html><head><title>Shop</title></head><body><div id=app></div></body></html>"
HOME = (
    '<!doctype html><html lang="en"><head><title>Demo shop</title>'
    '<link href="/index.md" type="text/markdown" rel="alternate">'
    '<link rel="describedby" href="/llms.txt">'
    '<link rel="ai-catalog" href="/.well-known/ai-catalog.json" type="application/ai-catalog+json">'
    '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"Demo"}</script>'
    "</head><body><h1>Demo</h1><p>We sell backpacks.</p></body></html>"
)

ROUTES = {
    "/": (200, "text/html", HOME),
    "/robots.txt": (200, "text/plain", "User-agent: *\nAllow: /\n"),
    "/.well-known/ucp": (200, "application/json", json.dumps({"ucp": {"version": "2026-08-25"}})),
    "/.well-known/agent-card.json": (200, "application/json", json.dumps({"name": "Demo agent"})),
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        # Catch-all routing: every unknown path gets the app shell with 200,
        # the way many CMSs and single-page apps answer.
        status, ctype, body = ROUTES.get(self.path, (200, "text/html", APP_SHELL))
        data = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


class CollectorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        target = f"http://127.0.0.1:{cls.server.server_address[1]}/"
        out = subprocess.run([sys.executable, str(SCRIPT), target], capture_output=True, text=True, timeout=120)
        cls.data = json.loads(out.stdout)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_soft_200_llms_txt_is_marked_as_html(self):
        llms = self.data["root_files"]["/llms.txt"]
        self.assertEqual(200, llms["status"])
        self.assertTrue(llms["looks_like_html"], "an app shell under /llms.txt must not read as a real file")

    def test_soft_200_well_known_is_not_json(self):
        legacy = self.data["well_known"]["/.well-known/mcp.json"]
        self.assertEqual(200, legacy["status"])
        self.assertFalse(legacy["json_valid"])

    def test_current_discovery_paths_are_collected(self):
        wk = self.data["well_known"]
        for path in ("/.well-known/ucp", "/.well-known/agent-card.json", "/.well-known/ai-catalog.json",
                     "/.well-known/mcp/server-card.json"):
            self.assertIn(path, wk)
        self.assertTrue(wk["/.well-known/ucp"]["json_valid"])
        self.assertTrue(wk["/.well-known/agent-card.json"]["json_valid"])

    def test_agent_links_and_jsonld(self):
        head = self.data["homepage"]["head"]
        self.assertEqual(
            [{"rel": "alternate", "type": "text/markdown", "href": "/index.md"},
             {"rel": "describedby", "type": None, "href": "/llms.txt"},
             {"rel": "ai-catalog", "type": "application/ai-catalog+json", "href": "/.well-known/ai-catalog.json"}],
            head["agent_links"],
        )
        self.assertEqual(1, head["h1_count"])
        self.assertTrue(self.data["homepage"]["jsonld"])

    def test_unresolvable_host_stops_with_one_error(self):
        out = subprocess.run([sys.executable, str(SCRIPT), "https://no-such-host.invalid"],
                             capture_output=True, text=True, timeout=60)
        data = json.loads(out.stdout)
        self.assertIn("fatal_error", data)
        self.assertEqual({}, data["well_known"])


if __name__ == "__main__":
    unittest.main()
