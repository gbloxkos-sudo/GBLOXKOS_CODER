"""Web search and browsing engine for GBLOXKOS_CODER."""
import re
import json
import html
import time
import logging
from urllib.parse import urlparse

logger = logging.getLogger("gbloxkos.web")

SEARCH_ENGINES = [
    {
        "name": "DuckDuckGo",
        "url": "https://html.duckduckgo.com/html/",
        "method": "html",
    },
    {
        "name": "Startpage",
        "url": "https://www.startpage.com/sp/search",
        "method": "html",
    },
    {
        "name": "Bing",
        "url": "https://www.bing.com/search",
        "method": "html",
    },
]

BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31."}


def _get_session():
    try:
        import requests as _requests
    except ImportError:
        raise ImportError("requests library not installed: pip install requests")
    s = _requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return s


def _is_valid_url(url):
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname or ""
        if hostname in BLOCKED_HOSTS:
            return False
        # Check for private IP ranges
        if re.match(r'^192\.168\.', hostname) or re.match(r'^10\.', hostname) or re.match(r'^172\.(1[6-9]|2\d|3[01])\.', hostname) or hostname == "localhost":
            return False
        return True
    except Exception:
        return False


def search_ddg(query, max_results=8, timeout=15):
    try:
        import requests
    except ImportError:
        return {"error": "requests library not installed", "results": []}

    session = _get_session()
    results = []
    try:
        resp = session.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query, "b": ""},
            timeout=timeout,
        )
        resp.raise_for_status()
        body = resp.text

        blocks = re.findall(
            r'<a[^>]+class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            body, re.DOTALL
        )
        for url, title, snippet in blocks[:max_results]:
            title = re.sub(r'<[^>]+>', '', html.unescape(title)).strip()
            snippet = re.sub(r'<[^>]+>', '', html.unescape(snippet)).strip()
            if title and url:
                results.append({"title": title, "url": url, "snippet": snippet})

        if not results:
            alt_blocks = re.findall(
                r'<h2[^>]*class="result__title"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?</h2>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                body, re.DOTALL
            )
            for url, title, snippet in alt_blocks[:max_results]:
                title = re.sub(r'<[^>]+>', '', html.unescape(title)).strip()
                snippet = re.sub(r'<[^>]+>', '', html.unescape(snippet)).strip()
                if title and url:
                    results.append({"title": title, "url": url, "snippet": snippet})

    except requests.exceptions.Timeout:
        return {"error": f"DDG search timed out after {timeout}s", "results": []}
    except requests.exceptions.ConnectionError:
        return {"error": "Failed to connect to DuckDuckGo", "results": []}
    except Exception as e:
        logger.warning(f"DDG search error: {e}")
        return {"error": str(e), "results": []}

    return {"query": query, "count": len(results), "results": results, "engine": "DuckDuckGo"}


def search_startpage(query, max_results=8, timeout=15):
    try:
        import requests
    except ImportError:
        return {"error": "requests library not installed", "results": []}

    session = _get_session()
    results = []
    try:
        resp = session.post(
            "https://www.startpage.com/sp/search",
            data={"query": query, "language": "english"},
            timeout=timeout,
        )
        resp.raise_for_status()
        body = resp.text

        items = re.findall(
            r'<a[^>]+class="w-gl__result-title[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
            r'<p[^>]+class="w-gl__description[^"]*"[^>]*>(.*?)</p>',
            body, re.DOTALL
        )
        for url, title, snippet in items[:max_results]:
            title = re.sub(r'<[^>]+>', '', html.unescape(title)).strip()
            snippet = re.sub(r'<[^>]+>', '', html.unescape(snippet)).strip()
            if title:
                results.append({"title": title, "url": url, "snippet": snippet})

    except requests.exceptions.Timeout:
        return {"error": f"Startpage search timed out after {timeout}s", "results": []}
    except requests.exceptions.ConnectionError:
        return {"error": "Failed to connect to Startpage", "results": []}
    except Exception as e:
        logger.warning(f"Startpage search error: {e}")
        return {"error": str(e), "results": []}

    return {"query": query, "count": len(results), "results": results, "engine": "Startpage"}


def search_bing(query, max_results=8, timeout=15):
    try:
        import requests
    except ImportError:
        return {"error": "requests library not installed", "results": []}

    session = _get_session()
    results = []
    try:
        resp = session.get(
            "https://www.bing.com/search",
            params={"q": query, "first": 1, "count": max_results},
            timeout=timeout,
        )
        resp.raise_for_status()
        body = resp.text

        items = re.findall(
            r'<li class="b_algo".*?>.*?<h2>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?</h2>.*?<p>(.*?)</p>',
            body, re.DOTALL
        )
        for url, title, snippet in items[:max_results]:
            title = re.sub(r'<[^>]+>', '', html.unescape(title)).strip()
            snippet = re.sub(r'<[^>]+>', '', html.unescape(snippet)).strip()
            if title and url:
                results.append({"title": title, "url": url, "snippet": snippet})

        if not results:
            items = re.findall(
                r'<a[^>]+class="tilk"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?<div[^>]*class="b_caption"[^>]*>.*?<p>(.*?)</p>',
                body, re.DOTALL
            )
            for url, title, snippet in items[:max_results]:
                title = re.sub(r'<[^>]+>', '', html.unescape(title)).strip()
                snippet = re.sub(r'<[^>]+>', '', html.unescape(snippet)).strip()
                if title and url:
                    results.append({"title": title, "url": url, "snippet": snippet})

    except requests.exceptions.Timeout:
        return {"error": f"Bing search timed out after {timeout}s", "results": []}
    except requests.exceptions.ConnectionError:
        return {"error": "Failed to connect to Bing", "results": []}
    except Exception as e:
        logger.warning(f"Bing search error: {e}")
        return {"error": str(e), "results": []}

    return {"query": query, "count": len(results), "results": results, "engine": "Bing"}


def web_search(query, max_results=8, timeout=20):
    if not query or not str(query).strip():
        return {"error": "Empty query", "results": []}

    query = str(query).strip()
    start = time.time()
    
    # Define search functions in order of preference
    search_functions = [
        ("DuckDuckGo", search_ddg),
        ("Startpage", search_startpage),
        ("Bing", search_bing),
    ]
    
    for name, func in search_functions:
        if time.time() - start > timeout:
            break
        remaining = timeout - (time.time() - start)
        if remaining < 2:
            break

        result = func(query, max_results, min(remaining, 12))

        if result.get("results"):
            return result

    return {
        "query": query,
        "count": 0,
        "results": [],
        "error": "All search engines failed or returned no results",
    }


def browse_url(url, timeout=20):
    try:
        import requests
    except ImportError:
        return {"error": "requests library not installed", "content": ""}

    if not url or not isinstance(url, str):
        return {"error": "Invalid URL", "content": ""}

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    if not _is_valid_url(url):
        return {"error": "Invalid or blocked URL", "content": ""}

    session = _get_session()
    try:
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        text = resp.text

        if "text/html" in content_type:
            text = _extract_readable_text(text, url)

        max_chars = 15000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[...content truncated...]"

        return {
            "url": url,
            "title": _extract_title(resp.text) if "text/html" in content_type else url,
            "content": text,
            "status": resp.status_code,
            "content_type": content_type,
        }

    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {timeout}s", "content": ""}
    except requests.exceptions.ConnectionError:
        return {"error": f"Failed to connect to {url}", "content": ""}
    except requests.exceptions.TooManyRedirects:
        return {"error": f"Too many redirects for {url}", "content": ""}
    except requests.exceptions.SSLError:
        return {"error": f"SSL error connecting to {url}", "content": ""}
    except Exception as e:
        return {"error": str(e), "content": ""}


def _extract_readable_text(html_content, base_url=""):
    if not html_content:
        return ""
    text = html_content

    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<nav[^>]*>.*?</nav>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<footer[^>]*>.*?</footer>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<header[^>]*>.*?</header>', '', text, flags=re.DOTALL | re.IGNORECASE)

    text = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'\n## \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n', text, flags=re.DOTALL)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'\1\n', text, flags=re.DOTALL)
    text = re.sub(r'<pre[^>]*>(.*?)</pre>', r'\n```\n\1\n```\n', text, flags=re.DOTALL)
    text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text, flags=re.DOTALL)

    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _extract_title(html_content):
    if not html_content:
        return ""
    m = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.DOTALL | re.IGNORECASE)
    if m:
        return html.unescape(m.group(1)).strip()
    return ""


def open_in_browser(url):
    import webbrowser
    try:
        if not url or not isinstance(url, str):
            return {"success": False, "output": "Invalid URL"}
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        if not _is_valid_url(url):
            return {"success": False, "output": "Invalid or blocked URL"}
        webbrowser.open(url)
        return {"success": True, "output": f"Opened in browser: {url}"}
    except Exception as e:
        return {"success": False, "output": f"Error opening browser: {e}"}
