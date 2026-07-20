"""
core/models/gemini_adapter.py
"""

import os
import uuid
from typing import Any, Optional

import google.generativeai as genai

from core.models.interface import ModelAdapter, ModelResponse, ToolCall


class GeminiAdapter(ModelAdapter):
    def __init__(self, model: str = "gemini-flash-latest", api_key: Optional[str] = None):
        self.model_name = model
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY bulunamadi. Render ortam degiskenlerine eklemen gerekiyor."
            )
        genai.configure(api_key=key)
        self._call_id_to_name: dict[str, str] = {}
        self._call_id_to_signature: dict[str, str] = {}

    def name(self) -> str:
        return f"gemini:{self.model_name}"

    def _tools_to_gemini(self, tools):
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

    def _to_gemini_contents(self, messages):
        contents = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            if isinstance(content, str):
                gemini_role = "model" if role == "assistant" else "user"
                if content:
                    contents.append({"role": gemini_role, "parts": [{"text": content}]})
                continue

            parts = []
            for block in content:
                btype = block.get("type")

                if btype == "text" and block.get("text"):
                    parts.append({"text": block["text"]})

                elif btype == "tool_use":
                    self._call_id_to_name[block["id"]] = block["name"]
                    part_dict = {
                        "function_call": {
                            "name": block["name"],
                            "args": block.get("input", {}),
                        }
                    }
                    signature = self._call_id_to_signature.get(
                        block["id"], "skip_thought_signature_validator"
                    )
                    part_dict["thought_signature"] = signature
                    parts.append(part_dict)

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

    def complete(self, messages, system: str = "", tools=None, max_tokens: int = 1024):
        contents = self._to_gemini_contents(messages)
        gemini_tools = self._tools_to_gemini(tools)

        model_kwargs = {}
        if system:
            model_kwargs["system_instruction"] = system
        if gemini_tools:
            model_kwargs["tools"] = gemini_tools

        model = genai.GenerativeModel(self.model_name, **model_kwargs)

        response = model.generate_content(
            contents,
            generation_config={"max_output_tokens": max_tokens},
        )

        text_parts = []
        tool_calls = []

        if response.candidates:
            for idx, part in enumerate(response.candidates[0].content.parts):
                if getattr(part, "text", None):
                    text_parts.append(part.text)
                elif getattr(part, "function_call", None) and part.function_call.name:
                    fc = part.function_call
                    # DUZELTME: call_id eskiden f"{fc.name}_{idx}" idi. GeminiAdapter
                    # tek bir global ornek olarak butun oturumlar arasinda paylasildigi
                    # icin (bkz. interface/api/main.py: tek _model), iki farkli
                    # kullanicinin ayni araci ayni indexte cagirmasi call_id
                    # cakismasina ve _call_id_to_signature/_call_id_to_name
                    # sozluklerinin birbirinin verisini ezmesine yol acabiliyordu.
                    # uuid4 ile her cagriya gercekten benzersiz bir id veriliyor.
                    call_id = f"{fc.name}_{uuid.uuid4().hex[:12]}"
                    self._call_id_to_name[call_id] = fc.name
                    signature = getattr(part, "thought_signature", None)
                    if signature:
                        self._call_id_to_signature[call_id] = signature
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
