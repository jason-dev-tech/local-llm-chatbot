from tools.base import Tool
from tools.rewrite import rewrite_text_tool
from tools.summarize import summarize_text_tool


_TOOLS: dict[str, Tool] = {
    rewrite_text_tool.name: rewrite_text_tool,
    summarize_text_tool.name: summarize_text_tool,
}


def get_tool(name: str) -> Tool | None:
    return _TOOLS.get(name)


def get_registered_tools() -> dict[str, Tool]:
    return dict(_TOOLS)
