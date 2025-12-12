"""Input validation utilities for chat requests."""

import re
from typing import Optional


def validate_message(message: str) -> str:
    """
    Validate and sanitize user message input.

    Prevents: injection attacks, excessive length, malicious content

    Raises:
        ValueError: If message fails validation (compatible with Pydantic)
    """
    if not message or not message.strip():
        raise ValueError("Message cannot be empty")

    message = message.strip()

    if len(message) > 10000:
        raise ValueError(
            "Message too long (max 10,000 characters). "
            "Please break your request into smaller parts."
        )

    if len(message) < 2:
        raise ValueError("Message too short (min 2 characters)")

    dangerous_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            raise ValueError(
                "Message contains potentially unsafe content. "
                "Please rephrase your question."
            )

    return message


def validate_thread_id(thread_id: Optional[str]) -> Optional[str]:
    """
    Validate thread ID format to prevent injection attacks.

    Thread IDs must match: thread_[a-f0-9]{16}

    Raises:
        ValueError: If thread_id format is invalid (compatible with Pydantic)
    """
    if thread_id is None:
        return None

    thread_id = thread_id.strip()

    if not re.match(r"^thread_[a-f0-9]{16}$", thread_id):
        raise ValueError(
            f"Invalid thread_id format. Expected 'thread_' followed by "
            f"16 hex characters, got: {thread_id[:50]}"
        )

    return thread_id


def validate_chat_request(
    message: str, thread_id: Optional[str]
) -> tuple[str, Optional[str]]:
    """
    Validate complete chat request.

    Returns:
        Tuple of (validated_message, validated_thread_id)

    Raises:
        ValueError: If validation fails (compatible with Pydantic)
    """
    validated_message = validate_message(message)
    validated_thread_id = validate_thread_id(thread_id)

    return validated_message, validated_thread_id
