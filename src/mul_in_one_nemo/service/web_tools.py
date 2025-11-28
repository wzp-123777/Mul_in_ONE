import re
import asyncio
from typing import List, Tuple

import httpx


DDG_HTML_SEARCH = "https://duckduckgo.com/html/?q={query}"


async def web_search(query: str, top_k: int = 5, timeout: float = 8.0) -> List[Tuple[str, str]]:
    """Perform a lightweight web search via DuckDuckGo HTML endpoint.

    Returns a list of (title, url) pairs.
    """
    async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent": "MulInOne/1.0"}) as client:
        r = await client.get(DDG_HTML_SEARCH.format(query=httpx.QueryParams({"q": query})))
        html = r.text
    # very lightweight parse: extract results from <a class="result__a" href="...">Title</a>
    results: List[Tuple[str, str]] = []
    for m in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL):
        url = m.group(1)
        title = re.sub(r"<[^>]+>", "", m.group(2))
        results.append((title.strip(), url.strip()))
        if len(results) >= top_k:
            break
    return results


async def web_fetch(url: str, timeout: float = 8.0, max_chars: int = 5000) -> str:
    """Fetch page content and return a cleaned text snippet."""
    async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent": "MulInOne/1.0"}) as client:
        r = await client.get(url, follow_redirects=True)
        text = r.text
    # strip scripts/styles and tags
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def extract_web_triggers(text: str) -> List[str]:
    """Find [[web:...]] triggers in a text and return queries."""
    queries: List[str] = []
    if not text:
        return queries
    for m in re.finditer(r"\[\[web:(.*?)\]\]", text, re.IGNORECASE):
        q = m.group(1).strip()
        if q:
            queries.append(q)
    return queries
