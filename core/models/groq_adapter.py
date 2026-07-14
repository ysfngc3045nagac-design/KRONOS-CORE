"""
core/models/groq_adapter.py

interface.py'deki ModelAdapter sözleşmesinin Groq API ile dolduruluşu.
Groq, OpenAI ile uyumlu bir API sunar ve araç çağırma (tool/function
calling) konusunda Gemini'nin aksine ekstra "düşünce imzası" gibi
karmaşıklıklar gerektirmez - bu yüzden Kronos'un ana modeli olarak
Groq'u kullanıyoruz.

Ortam değişkeni gerekli: GROQ_API_KEY
(Render'da: Environment > Add Environment Variable)

Ücretsiz anahtar: https://console.groq.com/keys
"""

import json
import os
from typing import Any, Optional

import requests

from core.models.interface import ModelAdapter, ModelResponse, ToolCall

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqAdapter(ModelAdapter):
    def __init__(self, model: str = "llama-3.3-70b-versatile", api_key: Optional[str] = None):
        self.model_name = model
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY bulunamadı. Render ortam değişkenlerine eklemen gerekiyor."
            )

    def name(self) -> str:
        return f"groq:{self.model_name}"

    def _tools_to_openai(self, tools: Optional[list[dict[str, Any]]]):
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
                },
            }
            for t in tools
        ]

    def _to_openai_messages(
        self, messages: list[dict[str, Any]], system: str
    ) -> list[dict[str, Any]]:
        openai_messages: list[dict[str, Any]] = []
        if system:
            openai_messages.append({"role": "system", "content": system})

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            if isinstance(content, str):
                openai_messages.append({"role": role, "content": content})
                continue

            # content bir blok listesi (text / tool_use / tool_result)
            text_parts = []
            tool_calls = []
            tool_result_messages = []

            for block in content:
                btype = block.get("type")
                if btype == "text":
                    text_parts.append(block.get("text", ""))
                elif btype == "tool_use":
                    tool_calls.append(
                        {
                            "id": block["id"],
                            "type": "function",
                            "function": {
                                "name": block["name"],
                                "arguments": json.dumps(block.get("input", {})),
                            },
                        }
                    )
                elif btype == "tool_result":
                    tool_result_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": block["tool_use_id"],
                            "content": str(block.get("content", "")),
                        }
                    )

            if tool_calls:
                openai_messages.append(
                    {
                        "role": "assistant",
                        "content": "".join(text_parts) or None,
                        "tool_calls": tool_calls,
                    }
                )
            elif text_parts:
                openai_messages.append({"role": role, "content": "".join(text_parts)})

            openai_messages.extend(tool_result_messages)

        return openai_messages

    def complete(
        self,
        messages: list[dict[str, Any]],
        system: str = "",
        tools: Optional[list[dict[str, Any]]] = None,
        max_tokens: int = 1024,
    ) -> ModelResponse:
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": self._to_openai_messages(messages, system),
            "max_tokens": max_tokens,
        }
        openai_tools = self._tools_to_openai(tools)
        if openai_tools:
            payload["tools"] = openai_tools

        resp = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]["message"]
        text = choice.get("content") or ""

        tool_calls: list[ToolCall] = []
        for tc in choice.get("tool_calls", []) or []:
            try:
                args = json.loads(tc["function"]["arguments"])
            except (json.JSONDecodeError, KeyError):
                args = {}
            tool_calls.append(
                ToolCall(name=tc["function"]["name"], arguments=args, call_id=tc["id"])
            )

        usage = None
        if "usage" in data:
            usage = {
                "input_tokens": data["usage"].get("prompt_tokens"),
                "output_tokens": data["usage"].get("completion_tokens"),
            }

        return ModelResponse(text=text, tool_calls=tool_calls, raw=data, usage=usage)
