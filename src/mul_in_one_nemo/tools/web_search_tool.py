"""NeMo Agent Toolkit tool: WebSearch.

Provides a structured tool for web searching and optional fetching of result pages.
"""

from __future__ import annotations

import logging
from typing import List, Optional, AsyncGenerator

from pydantic import BaseModel, Field, AnyUrl

from nat.builder.framework_enum import LLMFrameworkEnum
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from mul_in_one_nemo.service.web_tools import web_search, web_fetch

logger = logging.getLogger(__name__)


class WebSearchInput(BaseModel):
    query: str = Field(..., description="Search query string")
    top_k: int = Field(default=3, ge=1, le=8, description="Max number of search results")
    fetch_snippets: bool = Field(default=True, description="Whether to fetch page snippets for top results")


class WebSearchResult(BaseModel):
    title: str = Field(...)
    url: AnyUrl = Field(...)
    snippet: Optional[str] = Field(default=None)


class WebSearchOutput(BaseModel):
    results: List[WebSearchResult] = Field(default_factory=list)


class WebSearchToolConfig(FunctionBaseConfig, name="web_search_tool"):
    max_fetch_chars: int = Field(default=1200, ge=256, le=10000)
    timeout_s: float = Field(default=8.0, ge=2.0, le=30.0)


@register_function(config_type=WebSearchToolConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def web_search_tool(config: WebSearchToolConfig, builder):  # builder present for NAT contract
    async def _single(input_data: WebSearchInput) -> WebSearchOutput:
        try:
            pairs = await web_search(input_data.query, top_k=input_data.top_k, timeout=config.timeout_s)
            out: List[WebSearchResult] = []
            for title, url in pairs:
                snippet = None
                if input_data.fetch_snippets:
                    try:
                        snippet = (await web_fetch(url, timeout=config.timeout_s, max_chars=config.max_fetch_chars))
                    except Exception:
                        pass
                out.append(WebSearchResult(title=title, url=url, snippet=snippet))
            return WebSearchOutput(results=out)
        except Exception as e:
            logger.error("WebSearchTool failed: %s", e)
            return WebSearchOutput(results=[])

    async def _stream(input_data: WebSearchInput) -> AsyncGenerator[WebSearchOutput, None]:
        # Simple one-shot; stream emits a single chunk
        yield await _single(input_data)

    yield FunctionInfo.create(
        single_fn=_single,
        stream_fn=_stream,
        input_schema=WebSearchInput,
        single_output_schema=WebSearchOutput,
        stream_output_schema=WebSearchOutput,
        description="Search the web and optionally fetch short snippets for top results.",
    )
