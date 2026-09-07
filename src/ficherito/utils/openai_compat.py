"""Helpers for OpenAI-compatible chat completions across providers.

Newer OpenAI models (e.g. the ``o`` and ``gpt-5`` families) reject the
``max_tokens`` parameter and require ``max_completion_tokens`` instead, while
other OpenAI-compatible providers (DashScope, etc.) only understand
``max_tokens``. These helpers send ``max_tokens`` first and transparently retry
with ``max_completion_tokens`` when the provider reports it as unsupported.
"""

from typing import Optional

from openai import BadRequestError


def _needs_max_completion_tokens(error: BadRequestError) -> bool:
    """Return True if the error asks for ``max_completion_tokens``."""
    return "max_completion_tokens" in str(error)


def create_chat_completion(client, *, max_tokens: Optional[int] = None, **kwargs):
    """Create a chat completion (sync), handling the token-parameter split."""
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    try:
        return client.chat.completions.create(**kwargs)
    except BadRequestError as e:
        if max_tokens is None or not _needs_max_completion_tokens(e):
            raise
        kwargs.pop("max_tokens", None)
        kwargs["max_completion_tokens"] = max_tokens
        return client.chat.completions.create(**kwargs)


async def create_chat_completion_async(
    client, *, max_tokens: Optional[int] = None, **kwargs
):
    """Create a chat completion (async), handling the token-parameter split."""
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    try:
        return await client.chat.completions.create(**kwargs)
    except BadRequestError as e:
        if max_tokens is None or not _needs_max_completion_tokens(e):
            raise
        kwargs.pop("max_tokens", None)
        kwargs["max_completion_tokens"] = max_tokens
        return await client.chat.completions.create(**kwargs)
