#!/usr/bin/env python3
"""Fetch audit targets and summarize server-delivered HTML without JavaScript."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


class RedirectRecorder(HTTPRedirectHandler):
    def __init__(self) -> None:
        super().__init__()
        self.chain: list[dict[str, object]] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.chain.append({"status": code, "from": req.full_url, "to": newurl})
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class HTMLAuditParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title_parts: list[str] = []
        self.in_title = False
        self.in_heading: str | None = None
        self.heading_parts: list[str] = []
        self.headings: list[dict[str, str]] = []
        self.text_parts: list[str] = []
        self.links: list[dict[str, str]] = []
        self.meta: list[dict[str, str]] = []
        self.canonicals: list[str] = []
        self.alternates: list[dict[str, str]] = []
        self.jsonld_blocks: list[str] = []
        self.in_jsonld = False
        self.jsonld_parts: list[str] = []
        self.scripts: list[dict[str, str]] = []
        self.tag_counts: dict[str, int] = {}
        self.microdata_items: list[str] = []
        self.rdfa_markers: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        a = {str(k).lower(): ("" if v is None else str(v)) for k, v in attrs}
        self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
        if tag == "title":
            self.in_title = True
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.in_heading = tag
            self.heading_parts = []
        if tag == "a" and a.get("href"):
            self.links.append({"href": urljoin(self.base_url, a["href"]), "text": ""})
        if tag == "meta":
            self.meta.append(a)
        if tag == "link" and a.get("href"):
            rel = a.get("rel", "").lower()
            if "canonical" in rel:
                self.canonicals.append(urljoin(self.base_url, a["href"]))
            if "alternate" in rel:
                self.alternates.append({"href": urljoin(self.base_url, a["href"]), "hreflang": a.get("hreflang", "")})
        if tag == "script":
            self.scripts.append(a)
            if a.get("type", "").lower().split(";")[0].strip() == "application/ld+json":
                self.in_jsonld = True
                self.jsonld_parts = []
        if a.get("itemscope") is not None or "itemscope" in a:
            self.microdata_items.append(a.get("itemtype", "itemscope"))
        for key in ("vocab", "typeof", "property"):
            if a.get(key):
                self.rdfa_markers.append(f"{key}={a[key]}")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        if self.in_heading == tag:
            text = re.sub(r"\s+", " ", " ".join(self.heading_parts)).strip()
            self.headings.append({"level": tag, "text": text})
            self.in_heading = None
            self.heading_parts = []
        if tag == "script" and self.in_jsonld:
            self.jsonld_blocks.append("".join(self.jsonld_parts).strip())
            self.in_jsonld = False
            self.jsonld_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.in_heading:
            self.heading_parts.append(data)
        if self.in_jsonld:
            self.jsonld_parts.append(data)
        else:
            cleaned = re.sub(r"\s+", " ", data).strip()
            if cleaned:
                self.text_parts.append(cleaned)

    def summary(self, raw_text: str) -> dict[str, object]:
        metas = {}
        for item in self.meta:
            key = (item.get("name") or item.get("property") or item.get("http-equiv") or "").lower()
            if key:
                metas.setdefault(key, []).append(item.get("content", ""))
        parsed_jsonld = []
        for index, block in enumerate(self.jsonld_blocks):
            try:
                value = json.loads(block)
                parsed_jsonld.append({"index": index, "valid": True, "value": value})
            except Exception as exc:
                parsed_jsonld.append({"index": index, "valid": False, "error": str(exc), "excerpt": block[:300]})
        return {
            "title": re.sub(r"\s+", " ", " ".join(self.title_parts)).strip(),
            "meta": metas,
            "canonical": self.canonicals,
            "alternates": self.alternates,
            "headings": self.headings,
            "text_length": len(" ".join(self.text_parts)),
            "links_count": len(self.links),
            "links": self.links[:500],
            "forms": self.tag_counts.get("form", 0),
            "tables": self.tag_counts.get("table", 0),
            "iframes": self.tag_counts.get("iframe", 0),
            "canvas": self.tag_counts.get("canvas", 0),
            "svg": self.tag_counts.get("svg", 0),
            "noscript": self.tag_counts.get("noscript", 0),
            "jsonld": parsed_jsonld,
            "microdata_items": self.microdata_items,
            "rdfa_markers": self.rdfa_markers[:100],
            "script_count": len(self.scripts),
            "external_scripts": [urljoin(self.base_url, s["src"]) for s in self.scripts if s.get("src")],
            "framework_markers": {
                "next_data": "__NEXT_DATA__" in raw_text,
                "react": bool(re.search(r"data-react(root|id)|react-root", raw_text, re.I)),
                "angular": bool(re.search(r"ng-version|ng-app", raw_text, re.I)),
                "vue": bool(re.search(r"data-v-[0-9a-f]+|__VUE__", raw_text, re.I)),
                "drupal": bool(re.search(r"drupalSettings|sites/(default|all)/files", raw_text, re.I)),
            },
        }


def slug(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/") or "root"
    token = f"{parsed.scheme}_{parsed.netloc}_{path}"
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", token)[:180]


def fetch(url: str, out_dir: Path, timeout: float) -> dict[str, object]:
    redirects = RedirectRecorder()
    opener = build_opener(redirects)
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AEOAgentReadinessAudit/1.0; +https://openai.com/)",
            "Accept": "text/html,application/xhtml+xml,application/xml,text/plain,application/json,*/*;q=0.8",
            "Accept-Language": "es,en;q=0.8",
        },
    )
    result: dict[str, object] = {"requested_url": url, "redirect_chain": redirects.chain}
    body = b""
    headers: dict[str, str] = {}
    status: int | None = None
    final_url = url
    error = None
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read()
            status = response.getcode()
            final_url = response.geturl()
            headers = {k.lower(): v for k, v in response.headers.items()}
    except HTTPError as exc:
        status = exc.code
        final_url = exc.geturl()
        headers = {k.lower(): v for k, v in exc.headers.items()}
        body = exc.read()
        error = f"HTTPError: {exc}"
    except (URLError, TimeoutError, ssl.SSLError) as exc:
        error = f"{type(exc).__name__}: {exc}"

    token = slug(url)
    body_path = out_dir / f"{token}.body"
    headers_path = out_dir / f"{token}.headers.json"
    body_path.write_bytes(body)
    headers_path.write_text(json.dumps(headers, ensure_ascii=False, indent=2), encoding="utf-8")
    content_type = headers.get("content-type", "")
    charset_match = re.search(r"charset=([^;\s]+)", content_type, re.I)
    charset = charset_match.group(1).strip('"\'') if charset_match else "utf-8"
    try:
        decoded = body.decode(charset, errors="replace")
    except LookupError:
        decoded = body.decode("utf-8", errors="replace")

    result.update(
        {
            "status": status,
            "final_url": final_url,
            "content_type": content_type,
            "headers": headers,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "error": error,
            "body_path": str(body_path),
            "headers_path": str(headers_path),
        }
    )
    if "html" in content_type.lower() or re.search(r"<html\b", decoded[:1000], re.I):
        parser = HTMLAuditParser(final_url)
        parser.feed(decoded)
        result["html"] = parser.summary(decoded)
    else:
        result["body_excerpt"] = decoded[:4000]
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("urls", nargs="+")
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = [fetch(url, out_dir, args.timeout) for url in args.urls]
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
