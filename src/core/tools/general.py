"""General-purpose tools for web search and API calls."""

import requests
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults


@tool
def search_web(query: str) -> str:
    """Search the web for current information using Tavily.

    Use this tool when you need to find current information, news, or facts
    that are not in your training data. Returns top search results with URLs.
    """
    try:
        tavily = TavilySearchResults(
            max_results=5,
            search_depth="basic",
            include_answer=True,
            include_raw_content=False,
        )
        results = tavily.invoke(query)

        if not results:
            return "No search results found."

        output = f"Found {len(results)} results for '{query}':\n\n"
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            content = result.get("content", "")
            output += f"{i}. **{title}**\n"
            if url:
                output += f"   URL: {url}\n"
            if content:
                output += f"   {content[:200]}...\n\n"

        return output
    except Exception as e:
        return f"Web search error: {str(e)}. Please try rephrasing your query."


@tool
def call_external_api(url: str, method: str = "GET") -> str:
    """Call external REST APIs to fetch data.

    Use this tool to make HTTP requests to external APIs.
    Currently supports GET requests with 10 second timeout.
    """
    try:
        if method.upper() != "GET":
            return f"Error: Only GET method is currently supported, got {method}"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        try:
            data = response.json()
            return f"API Response: {data}"
        except ValueError:
            return f"API Response (text): {response.text[:500]}"

    except requests.Timeout:
        return "API error: Request timed out after 10 seconds"
    except requests.RequestException as e:
        return f"API error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


general_tools = [search_web, call_external_api]
