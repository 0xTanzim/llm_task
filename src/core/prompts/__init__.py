"""Prompt templates module."""

from .templates import (
    CODE_PROMPT,
    DATABASE_PROMPT,
    GENERAL_PROMPT,
    select_prompt_for_tools,
)

__all__ = [
    "DATABASE_PROMPT",
    "CODE_PROMPT",
    "GENERAL_PROMPT",
    "select_prompt_for_tools",
]
