from __future__ import annotations

import json

try:
    from anthropic import Anthropic
except Exception:  # pragma: no cover
    Anthropic = None


class AnthropicClient:
    def __init__(self, api_key: str | None = None):
        self.enabled = bool(api_key and Anthropic)
        self.client = Anthropic(api_key=api_key) if self.enabled else None

    def complete(self, system: str, user: str, model: str, max_tokens: int = 1024) -> str:
        if not self.enabled:
            return json.dumps({"status": "mock", "message": "anthropic_disabled"})
        msg = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text
