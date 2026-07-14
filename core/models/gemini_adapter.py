"""
core/models/gemini_adapter.py

interface.py'deki ModelAdapter sözleşmesinin Google Gemini API ile
dolduruluşu. Faz 2: artık araç çağırma (function calling) da destekleniyor,
dispatcher.py'nin ürettiği Anthropic tarzı mesaj bloklarını (tool_use,
tool_result) Gemini'nin beklediği function_call / function_response
formatına çevirir.

Ortam değişkeni gerekli: GEMINI_API_KEY
(Render'da: Environment > Add Environment Variable)
"""

import os
from typing import Any, Optional

import google.generativeai as genai

from core.models.interface import ModelAdapter, ModelResponse, ToolCall


class GeminiAdapter(ModelAdapter):
    def __init__(self, model: str = "gemini-flash-latest", api_key: Optional[str] = None):
        self.model_name = model
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY bulunamadı. Render ortam değişkenlerine eklemen gerekiyor."
            )
        genai.configure(api_key=key)
        # call_id -> tool adı eşlemesi; tool_result bloklarında sadece
        # call_id geldiği için Gemini'nin function_response'unda gereken
        # "name" alanını buradan buluyoruz.
        self._call_id_to_name: dict[str, str] = {}

    def name(self) -> str:
        return f"gemini:{self.model_name}"

    def _tools_to_gemini(self, tools: Optional[list[dict[str, Any]]]):
        if not tools:
            return None
        declarations = []
        for t in tools:
            declarations.append(
                {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
                }
            )
        return [{"function_declarations": declarations}]

    def _to_gemini_contents(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        contents: list[dict[str, Any]] = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            if isinstance(content, str):
                gemini_role = "model" if role == "assistant" else "user"
                if content:
                    contents.append({"role": gemini_role, "parts": [{"text": content}]})
                continue

            # content bir blok listesi (text / tool_use / tool_result)
            parts = []
            for block in content:
                btype = block.get("type")

                if btype == "text" and block.get("text"):
                    parts.append({"text": block["text"]})

                elif btype == "tool_use":
                    self._call_id_to_name[block["id"]] = block["name"]
                    parts.append(
                        {
                            "function_call": {
                                "name": block["name"],
                                "args": block.get("input", {}),
                            }
                        }
                    )

                elif btype == "tool_result":
                    tool_name = self._call_id_to_name.get(block["tool_use_id"], "unknown_tool")
                    parts.append(
                        {
                            "function_response": {
                                "name": tool_name,
                                "response": {"result": block.get("content", "")},
                            }
                        }
                    )

            if parts:
                gemini_role = "model" if role == "assistant" else "user"
                contents.append({"role": gemini_role, "parts": parts})

        return contents

    def complete(
        self,
        messages: list[dict[str, Any]],
        system: str = "",
        tools: Optional[list[dict[str, Any]]] = None,
        max_tokens: int = 1024,
    ) -> ModelResponse:
        contents = self._to_gemini_contents(messages)
        gemini_tools = self._tools_to_gemini(tools)

        model_kwargs: dict[str, Any] = {}
        if system:
            model_kwargs["system_instruction"] = system
        if gemini_tools:
            model_kwargs["tools"] = gemini_tools

        model = genai.GenerativeModel(self.model_name, **model_kwargs)

        response = model.generate_content(
            contents,
            generation_config={"max_output_tokens": max_tokens},
        )

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []

        if response.candidates:
            for idx, part in enumerate(response.candidates[0].content.parts):
                if getattr(part, "text", None):
                    text_parts.append(part.text)
                elif getattr(part, "function_call", None) and part.function_call.name:
                    fc = part.function_call
                    call_id = f"{fc.name}_{idx}"
                    self._call_id_to_name[call_id] = fc.name
                    tool_calls.append(
                        ToolCall(
                            name=fc.name,
                            arguments=dict(fc.args) if fc.args else {},
                            call_id=call_id,
                        )
                    )

        usage = None
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "input_tokens": response.usage_metadata.prompt_token_count,
                "output_tokens": response.usage_metadata.candidates_token_count,
            }

        return ModelResponse(
            text="".join(text_parts),
            tool_calls=tool_calls,
            raw=response,
            usage=usage,
        )
