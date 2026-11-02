"""Public web search with no extra API key or Gemini Search quota."""

from __future__ import annotations

import asyncio
from urllib.parse import urlsplit

from cuty.llm.provider import WebSource


class WebSearchError(RuntimeError):
    pass


class WebSearchService:
    async def search(self, query: str) -> tuple[WebSource, ...]:
        try:
            return await asyncio.wait_for(asyncio.to_thread(self._search, query), timeout=8)
        except TimeoutError as exc:
            raise WebSearchError("La búsqueda tardó demasiado; no se pudo verificar la información.") from exc
        except WebSearchError:
            raise
        except Exception as exc:
            raise WebSearchError("El buscador no está disponible; no se pudo verificar la información.") from exc

    @staticmethod
    def _search(query: str) -> tuple[WebSource, ...]:
        from ddgs import DDGS

        rows = DDGS(timeout=4).text(query, region="mx-es", max_results=4)
        sources = []
        seen = set()
        for row in rows:
            url = str(row.get("href") or "").strip()
            try:
                parsed = urlsplit(url)
            except ValueError:
                continue
            if parsed.scheme not in {"http", "https"} or not parsed.netloc or any(c.isspace() for c in url):
                continue
            if url in seen:
                continue
            seen.add(url)
            title = " ".join(str(row.get("title") or parsed.netloc).split())[:200]
            snippet = " ".join(str(row.get("body") or "").split())[:800]
            sources.append(WebSource(title, url, snippet))
        if not sources:
            raise WebSearchError("No se encontraron fuentes web para esa consulta.")
        return tuple(sources[:4])
