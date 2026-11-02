import asyncio

import pytest

from cuty.llm.web_search import WebSearchError, WebSearchService


def test_search_normalizes_sources_and_rejects_invalid_urls(monkeypatch):
    import ddgs

    class FakeDDGS:
        def __init__(self, timeout):
            assert timeout == 4

        def text(self, query, region, max_results):
            assert query == "Python release"
            assert region == "mx-es" and max_results == 4
            return [
                {"title": "Python\nDownloads", "href": "https://www.python.org/downloads/", "body": "Latest  stable version"},
                {"title": "Duplicate", "href": "https://www.python.org/downloads/"},
                {"title": "Invalid", "href": "javascript:alert(1)"},
            ]

    monkeypatch.setattr(ddgs, "DDGS", FakeDDGS)
    sources = asyncio.run(WebSearchService().search("Python release"))
    assert len(sources) == 1
    assert sources[0].title == "Python Downloads"
    assert sources[0].snippet == "Latest stable version"
    assert sources[0].url == "https://www.python.org/downloads/"


def test_search_network_failure_is_explained_without_raw_exception(monkeypatch):
    def fail(query):
        raise RuntimeError("internal connection details")

    monkeypatch.setattr(WebSearchService, "_search", staticmethod(fail))
    with pytest.raises(WebSearchError, match="no está disponible") as error:
        asyncio.run(WebSearchService().search("Python release"))
    assert "internal connection details" not in str(error.value)
